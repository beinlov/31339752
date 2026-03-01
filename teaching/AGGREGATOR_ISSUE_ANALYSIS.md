# 聚合器数据不一致问题分析报告

## 🎯 问题定位

在 `/backend/stats_aggregator/aggregator.py` 中发现了导致 `china_botnet` 和 `global_botnet` 表中中国节点数据不一致的根本原因。

---

## 🔍 聚合器代码分析

### 中国统计聚合逻辑（第143-176行）

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
            COALESCE(
                TRIM(TRAILING '省' FROM 
                TRIM(TRAILING '市' FROM 
                TRIM(TRAILING '自治区' FROM 
                REPLACE(REPLACE(REPLACE(
                    province, 
                    '壮族自治区', '自治区'), 
                    '回族自治区', '自治区'), 
                    '维吾尔自治区', '自治区')
                ))), 
                '未知'
            ) as province,
            COALESCE(
                TRIM(TRAILING '市' FROM city),
                '未知'
            ) as municipality,
            ip,
            created_time,
            updated_at
        FROM {node_table}
        WHERE country = '中国'  ⬅️ 【关键】只统计 country = '中国' 的数据
    ) AS t
    GROUP BY t.province, t.municipality
""")
```

**关键点**：
1. ✅ 使用 `WHERE country = '中国'` 过滤
2. ✅ 对省份和城市名称进行了**标准化处理**（去除后缀）
3. ✅ 使用 `COUNT(DISTINCT ip)` 去重
4. ✅ 在子查询中处理字段后再聚合

---

### 全球统计聚合逻辑（第232-247行）

```python
cursor.execute(f"""
    INSERT INTO {temp_global_table} (country, infected_num, created_at, updated_at)
    SELECT 
        CASE
            WHEN country = '中国台湾' THEN '台湾'
            WHEN country = '中国香港' THEN '香港'
            WHEN country = '中国澳门' THEN '澳门'
            WHEN country IS NOT NULL THEN country
            ELSE '未知'
        END as country,
        COUNT(DISTINCT ip) as infected_num,  ⬅️ 【问题】直接在主查询中去重
        MIN(created_time) as created_at,
        MAX(updated_at) as updated_at
    FROM {node_table}  ⬅️ 【关键】统计所有国家，包括中国
    GROUP BY 1
""")
```

**关键点**：
1. ⚠️ **没有使用子查询**，直接在主查询中进行 `COUNT(DISTINCT ip)`
2. ⚠️ 统计了所有国家的数据，包括中国
3. ⚠️ 对国家名称做了简单的 CASE 处理，但没有更复杂的标准化

---

## 🚨 根本原因

### 原因1：数据处理逻辑不一致

**中国统计**使用了**两层查询**：
1. 内层子查询：标准化省份和城市名称，过滤 `country = '中国'`
2. 外层聚合：对标准化后的数据进行 `GROUP BY` 和 `COUNT(DISTINCT ip)`

**全球统计**使用了**单层查询**：
1. 直接对原始数据进行聚合，没有子查询进行数据清洗

这导致：
- 中国统计可能会过滤掉一些**省份或城市字段为NULL或异常值**的数据
- 全球统计会统计所有 `country = '中国'` 的数据，包括那些被中国统计过滤掉的数据

### 原因2：字段处理差异

**中国统计的字段处理**：
```python
COALESCE(
    TRIM(TRAILING '省' FROM 
    TRIM(TRAILING '市' FROM 
    TRIM(TRAILING '自治区' FROM ...))),
    '未知'
)
```

**全球统计的字段处理**：
```python
CASE
    WHEN country IS NOT NULL THEN country
    ELSE '未知'
END
```

中国统计进行了更复杂的字符串处理，可能导致部分数据在处理过程中被归类到不同的分组。

---

## 🔬 验证假设

让我们验证是否存在这种数据差异：

### 检查1：查询 botnet_nodes_ramnit 中 country='中国' 的总数

```sql
-- 简单统计（对应 global_botnet 的逻辑）
SELECT COUNT(DISTINCT ip) 
FROM botnet_nodes_ramnit 
WHERE country = '中国';
```

### 检查2：使用中国统计的逻辑查询

```sql
-- 使用中国统计的复杂逻辑（对应 china_botnet 的逻辑）
SELECT COUNT(DISTINCT ip)
FROM (
    SELECT 
        COALESCE(
            TRIM(TRAILING '省' FROM 
            TRIM(TRAILING '市' FROM 
            TRIM(TRAILING '自治区' FROM 
            REPLACE(REPLACE(REPLACE(
                province, 
                '壮族自治区', '自治区'), 
                '回族自治区', '自治区'), 
                '维吾尔自治区', '自治区')
            ))), 
            '未知'
        ) as province,
        COALESCE(
            TRIM(TRAILING '市' FROM city),
            '未知'
        ) as municipality,
        ip
    FROM botnet_nodes_ramnit
    WHERE country = '中国'
) AS t
GROUP BY province, municipality;
```

**预期结果**：
- 简单统计应该返回 **27,888** 个（与 global_botnet 一致）
- 复杂统计应该返回 **27,906** 个（与 china_botnet 一致）
- 差异应该是 **18** 个节点

---

## 💡 可能的数据差异场景

### 场景1：省份/城市字段为空或异常

某些节点可能：
- `country = '中国'`
- `province` 为 NULL 或空字符串
- `city` 为 NULL 或空字符串

**在中国统计中**：
- 子查询会将这些节点的 `province` 和 `city` 都设为 `'未知'`
- 然后按 `('未知', '未知')` 分组统计

**在全球统计中**：
- 直接统计所有 `country = '中国'` 的节点，不关心省份/城市

**结果**：两者统计的节点总数可能不同

### 场景2：字符串处理导致分组变化

某些节点可能有特殊的省份名称格式，例如：
- `province = '北京市'`（带"市"后缀）
- `province = '上海市'`（带"市"后缀）

**在中国统计中**：
- 经过 `TRIM(TRAILING '市' FROM ...)` 处理后变成 `'北京'` 和 `'上海'`

如果在处理过程中某些边界情况导致 `province` 或 `city` 变成空字符串或NULL，这些记录可能会：
- 在子查询中被过滤掉
- 或者被归入到 `'未知'` 分组

### 场景3：GROUP BY 聚合差异

**中国统计**使用了子查询 + GROUP BY：
```sql
FROM (...) AS t
GROUP BY t.province, t.municipality
```

**全球统计**直接 GROUP BY：
```sql
FROM botnet_nodes_ramnit
GROUP BY country
```

如果某些节点在子查询处理后导致 `province` 或 `municipality` 字段发生变化，可能会影响最终的统计结果。

---

## 🔧 修复方案

### 方案1：统一数据处理逻辑（推荐）

**目标**：让 `global_botnet` 中的中国节点数量与 `china_botnet` 完全一致

**修改 aggregator.py 第232-247行**：

```python
# 修改前（当前逻辑）
cursor.execute(f"""
    INSERT INTO {temp_global_table} (country, infected_num, created_at, updated_at)
    SELECT 
        CASE
            WHEN country = '中国台湾' THEN '台湾'
            WHEN country = '中国香港' THEN '香港'
            WHEN country = '中国澳门' THEN '澳门'
            WHEN country IS NOT NULL THEN country
            ELSE '未知'
        END as country,
        COUNT(DISTINCT ip) as infected_num,
        MIN(created_time) as created_at,
        MAX(updated_at) as updated_at
    FROM {node_table}
    GROUP BY 1
""")

# 修改后（使用子查询确保数据一致性）
cursor.execute(f"""
    INSERT INTO {temp_global_table} (country, infected_num, created_at, updated_at)
    SELECT 
        country,
        COUNT(DISTINCT ip) as infected_num,
        MIN(created_time) as created_at,
        MAX(updated_at) as updated_at
    FROM (
        SELECT 
            CASE
                WHEN country = '中国台湾' THEN '台湾'
                WHEN country = '中国香港' THEN '香港'
                WHEN country = '中国澳门' THEN '澳门'
                WHEN country IS NOT NULL THEN country
                ELSE '未知'
            END as country,
            ip,
            created_time,
            updated_at
        FROM {node_table}
        WHERE country IS NOT NULL  -- 过滤 NULL 值，与中国统计保持一致
    ) AS t
    GROUP BY country
""")
```

### 方案2：在全球统计中使用 china_botnet 的数据

**目标**：确保 `global_botnet` 表中的中国数据与 `china_botnet` 完全一致

**修改思路**：
1. 先统计所有国家（排除中国）
2. 从 `china_botnet` 表汇总中国的总数，插入到 `global_botnet`

**修改 aggregator.py**：

```python
# 第一步：统计非中国国家
cursor.execute(f"""
    INSERT INTO {temp_global_table} (country, infected_num, created_at, updated_at)
    SELECT 
        CASE
            WHEN country = '中国台湾' THEN '台湾'
            WHEN country = '中国香港' THEN '香港'
            WHEN country = '中国澳门' THEN '澳门'
            WHEN country IS NOT NULL THEN country
            ELSE '未知'
        END as country,
        COUNT(DISTINCT ip) as infected_num,
        MIN(created_time) as created_at,
        MAX(updated_at) as updated_at
    FROM {node_table}
    WHERE country != '中国'  -- 排除中国
    GROUP BY 1
""")

# 第二步：从 china_botnet 表汇总中国数据
cursor.execute(f"""
    INSERT INTO {temp_global_table} (country, infected_num, created_at, updated_at)
    SELECT 
        '中国' as country,
        SUM(infected_num) as infected_num,
        MIN(created_at) as created_at,
        MAX(updated_at) as updated_at
    FROM {china_table}
""")
```

**优点**：
- ✅ 确保 `global_botnet` 中的中国数据与 `china_botnet` 完全一致
- ✅ 避免了重复计算和数据不一致

**缺点**：
- ⚠️ 需要先执行中国统计，再执行全球统计（顺序依赖）

---

## 📝 立即执行的诊断脚本

创建一个脚本来验证数据差异的具体原因：

```python
#!/usr/bin/env python3
import pymysql
import sys
sys.path.append('/home/spider/31339752/backend')
from config import DB_CONFIG

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

botnet_type = 'ramnit'
node_table = f"botnet_nodes_{botnet_type}"

print("=" * 80)
print("验证数据差异的具体原因")
print("=" * 80)

# 1. 简单统计（对应 global_botnet 的逻辑）
cursor.execute(f"""
    SELECT COUNT(DISTINCT ip) 
    FROM {node_table} 
    WHERE country = '中国'
""")
simple_count = cursor.fetchone()[0]
print(f"\n1. 简单统计（global_botnet 逻辑）: {simple_count:,} 个节点")

# 2. 使用中国统计的复杂逻辑
cursor.execute(f"""
    SELECT COUNT(DISTINCT t.ip)
    FROM (
        SELECT 
            COALESCE(
                TRIM(TRAILING '省' FROM 
                TRIM(TRAILING '市' FROM 
                TRIM(TRAILING '自治区' FROM 
                REPLACE(REPLACE(REPLACE(
                    province, 
                    '壮族自治区', '自治区'), 
                    '回族自治区', '自治区'), 
                    '维吾尔自治区', '自治区')
                ))), 
                '未知'
            ) as province,
            COALESCE(
                TRIM(TRAILING '市' FROM city),
                '未知'
            ) as municipality,
            ip
        FROM {node_table}
        WHERE country = '中国'
    ) AS t
""")
complex_count = cursor.fetchone()[0]
print(f"2. 复杂统计（china_botnet 逻辑）: {complex_count:,} 个节点")

print(f"\n差异: {abs(simple_count - complex_count):,} 个节点")

# 3. 查找差异的具体数据
if simple_count != complex_count:
    print(f"\n" + "=" * 80)
    print("查找被过滤掉的 {abs(simple_count - complex_count)} 个节点...")
    print("=" * 80)
    
    # 查找在简单统计中有，但在复杂统计中没有的IP
    cursor.execute(f"""
        SELECT ip, province, city, created_time, updated_at
        FROM {node_table}
        WHERE country = '中国'
            AND ip NOT IN (
                SELECT DISTINCT ip
                FROM (
                    SELECT 
                        ip,
                        COALESCE(
                            TRIM(TRAILING '省' FROM 
                            TRIM(TRAILING '市' FROM 
                            TRIM(TRAILING '自治区' FROM 
                            REPLACE(REPLACE(REPLACE(
                                province, 
                                '壮族自治区', '自治区'), 
                                '回族自治区', '自治区'), 
                                '维吾尔自治区', '自治区')
                            ))), 
                            '未知'
                        ) as province,
                        COALESCE(
                            TRIM(TRAILING '市' FROM city),
                            '未知'
                        ) as municipality
                    FROM {node_table}
                    WHERE country = '中国'
                ) AS t
            )
        LIMIT 20
    """)
    
    diff_nodes = cursor.fetchall()
    if diff_nodes:
        print(f"\n找到 {len(diff_nodes)} 个差异节点（显示前20个）：")
        for ip, province, city, created, updated in diff_nodes:
            print(f"  IP: {ip}, Province: {province}, City: {city}")
    else:
        print("\n未找到明显差异的节点，可能是 GROUP BY 导致的统计差异")

cursor.close()
conn.close()
```

---

## 🎯 推荐的修复步骤

1. ✅ **先运行诊断脚本**，确认数据差异的具体原因
2. ✅ **选择修复方案**（推荐方案2）
3. ✅ **修改 aggregator.py**
4. ✅ **重新运行聚合器**
5. ✅ **验证数据一致性**

---

## 📌 总结

**问题根源**：
- `china_botnet` 使用了复杂的子查询和字段标准化逻辑
- `global_botnet` 使用了简单的直接聚合逻辑
- 两者对于中国节点的统计结果不一致（差18个节点）

**推荐方案**：
- 方案2：在全球统计中使用 `china_botnet` 的数据，确保数据源统一

**预期效果**：
- 修复后，`global_botnet_ramnit` 表中的中国节点将变成 27,906 个
- `global_amount` 将从 116,090 增加到 116,108
- 三个界面的数据将完全一致
