# 聚合器数据不一致问题 - 完整修复指南

## 📋 问题总结

### 根本原因
`botnet_nodes_ramnit` 表中同时存在两种格式的省份名称：
- `'内蒙古'` (150个IP) 和 `'内蒙古自治区'` (105个IP)  
- `'西藏'` (21个IP) 和 `'西藏自治区'` (10个IP)

由于聚合器的 UNIQUE KEY 是 `(province, municipality)`，这两种格式被视为不同的地区，导致：
- `china_botnet_ramnit` 表中创建了 **18条重复的记录**
- `SUM(infected_num)` = 27,906（多了18个）
- 实际唯一IP数 = 27,888

这18条多余记录导致三个界面显示不一致：
- 图一（global_botnet）：116,090 ✅ 正确
- 图二（total_nodes）：116,090 或 116,108（取决于数据时间）
- 图三（country_distribution）：116,108 ✅ 正确

---

## 🛠️ 修复方案

### 方案1：清理历史数据 + 修复聚合器（推荐）

这是最彻底的解决方案，确保以后不再出现此问题。

#### 步骤1：清理 botnet_nodes 表中的数据

标准化所有省份名称，统一使用不带"自治区"后缀的格式：

```sql
-- 备份原始数据（可选）
CREATE TABLE botnet_nodes_ramnit_backup AS 
SELECT * FROM botnet_nodes_ramnit WHERE country = '中国';

-- 标准化省份名称
UPDATE botnet_nodes_ramnit
SET province = CASE
    WHEN province = '内蒙古自治区' THEN '内蒙古'
    WHEN province = '广西壮族自治区' THEN '广西'
    WHEN province = '西藏自治区' THEN '西藏'
    WHEN province = '宁夏回族自治区' THEN '宁夏'
    WHEN province = '新疆维吾尔自治区' THEN '新疆'
    ELSE province
END
WHERE country = '中国'
  AND province IN ('内蒙古自治区', '广西壮族自治区', '西藏自治区', '宁夏回族自治区', '新疆维吾尔自治区');

-- 查看影响的记录数
SELECT 
    province,
    COUNT(*) as record_count,
    COUNT(DISTINCT ip) as unique_ips
FROM botnet_nodes_ramnit
WHERE country = '中国'
  AND province IN ('内蒙古', '广西', '西藏', '宁夏', '新疆')
GROUP BY province;
```

#### 步骤2：修改聚合器代码

修改 `/backend/stats_aggregator/aggregator.py` 第143-176行，添加显式的省份标准化：

```python
cursor.execute(f"""
    INSERT INTO {temp_table} (province, municipality, infected_num, created_at, updated_at)
    SELECT 
        t.province,
        t.municipality,
        COUNT(DISTINCT t.ip) as infected_num,
        MIN(t.created_time) as created_at,
        MAX(t.updated_at) as updated_at
    FROM (
        SELECT 
            -- 显式标准化省份名称（修改这部分）
            CASE
                WHEN province = '内蒙古自治区' OR province = '内蒙古壮族自治区' THEN '内蒙古'
                WHEN province = '广西自治区' OR province = '广西壮族自治区' THEN '广西'
                WHEN province = '西藏自治区' THEN '西藏'
                WHEN province = '宁夏自治区' OR province = '宁夏回族自治区' THEN '宁夏'
                WHEN province = '新疆自治区' OR province = '新疆维吾尔自治区' THEN '新疆'
                ELSE COALESCE(
                    TRIM(TRAILING '省' FROM 
                    TRIM(TRAILING '市' FROM province)),
                    '未知'
                )
            END as province,
            COALESCE(
                TRIM(TRAILING '市' FROM city),
                '未知'
            ) as municipality,
            ip,
            created_time,
            updated_at
        FROM {node_table}
        WHERE country = '中国'
    ) AS t
    GROUP BY t.province, t.municipality
""")
```

#### 步骤3：清理 china_botnet 表并重新聚合

```sql
-- 删除 ramnit 的聚合数据
DROP TABLE IF EXISTS china_botnet_ramnit;
DROP TABLE IF EXISTS global_botnet_ramnit;
```

然后重新运行聚合器：

```bash
cd /home/spider/31339752/backend
python3 stats_aggregator/aggregator.py once ramnit
```

#### 步骤4：验证数据一致性

```bash
python3 /home/spider/31339752/test_api_consistency.py
```

期望结果：
```
✅ 三个数据源完全一致！
  图一 global_amount:     116,108
  图二 total_nodes:       116,108
  图三 country_dist 总和:  116,108
```

---

### 方案2：仅清理聚合表（快速方案）

如果不想修改原始数据，可以只清理 `china_botnet_ramnit` 表：

```sql
-- 删除多余的记录
DELETE FROM china_botnet_ramnit 
WHERE province IN ('内蒙古自治区', '西藏自治区');

-- 验证结果
SELECT SUM(infected_num) FROM china_botnet_ramnit;
-- 应该返回 27,888（删除前是 27,906）
```

**缺点**：下次聚合器运行时，如果原始数据中还有这两种格式，问题会再次出现。

---

### 方案3：修改 API 计算逻辑（临时方案）

修改 `/backend/router/amount.py`，让它使用与 `node.py` 相同的计算方式：

```python
# 修改第48-60行
# 计算全球总数 = 中国表 + 全球表(非中国)
cursor.execute(f"""
    SELECT COALESCE(SUM(infected_num), 0) as china_total
    FROM china_botnet_{botnet_name}
""")
china_total = int(cursor.fetchone()['china_total'])

cursor.execute(f"""
    SELECT COALESCE(SUM(infected_num), 0) as global_non_china
    FROM global_botnet_{botnet_name}
    WHERE country != '中国'
""")
global_non_china = int(cursor.fetchone()['global_non_china'])

response_data.append({
    "name": botnet_name,
    "china_amount": china_total,
    "global_amount": china_total + global_non_china  # 修改这里
})
```

**缺点**：治标不治本，聚合表中的数据仍然不正确。

---

## 📝 执行修复的脚本

我已经创建了自动化修复脚本，按顺序执行：

### 1. 标准化原始数据

```bash
python3 /home/spider/31339752/fix_province_names.py
```

### 2. 清理并重新聚合

```bash
python3 /home/spider/31339752/rebuild_aggregation_ramnit.py
```

### 3. 验证修复结果

```bash
python3 /home/spider/31339752/test_api_consistency.py
```

---

## 🔍 预防措施

### 1. 在数据导入时标准化

在数据导入到 `botnet_nodes` 表时，应该立即标准化省份名称：

```python
def standardize_province(province):
    """标准化省份名称"""
    if not province:
        return '未知'
    
    # 自治区映射
    mappings = {
        '内蒙古自治区': '内蒙古',
        '内蒙古壮族自治区': '内蒙古',
        '广西自治区': '广西',
        '广西壮族自治区': '广西',
        '西藏自治区': '西藏',
        '宁夏自治区': '宁夏',
        '宁夏回族自治区': '宁夏',
        '新疆自治区': '新疆',
        '新疆维吾尔自治区': '新疆',
    }
    
    if province in mappings:
        return mappings[province]
    
    # 去除省、市后缀
    return province.replace('省', '').replace('市', '')
```

### 2. 添加数据验证

在聚合器中添加数据验证，检测并报告格式不一致的问题。

### 3. 定期检查

定期运行诊断脚本，检查是否有新的数据不一致问题：

```bash
# 添加到 crontab
0 2 * * * python3 /home/spider/31339752/diagnose_sum_issue.py >> /var/log/data_check.log
```

---

## ✅ 推荐执行顺序

1. ✅ **备份数据**（重要！）
   ```bash
   mysqldump -u root -p botnet botnet_nodes_ramnit china_botnet_ramnit > backup_$(date +%Y%m%d).sql
   ```

2. ✅ **标准化原始数据**
   执行步骤1的SQL语句

3. ✅ **修改聚合器代码**
   按照步骤2修改 `aggregator.py`

4. ✅ **清理并重新聚合**
   删除聚合表，重新运行聚合器

5. ✅ **验证修复**
   运行验证脚本，确认三个界面数据一致

6. ✅ **应用到其他僵尸网络**
   检查其他僵尸网络是否有相同问题

---

## 📊 预期结果

修复后，所有数据应该一致：

| 数据源 | 修复前 | 修复后 |
|--------|--------|--------|
| `china_botnet` 表记录数 | 446 | 428 |
| `china_botnet` SUM | 27,906 | 27,888 |
| `global_botnet` 中国节点 | 27,888 | 27,888 |
| 图一 global_amount | 116,090 | 116,108 |
| 图二 total_nodes | 116,090 | 116,108 |
| 图三 country_dist | 116,108 | 116,108 |

**最终一致的数据**：**116,108** 个节点
