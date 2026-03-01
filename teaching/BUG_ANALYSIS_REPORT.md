# test僵尸网络Bug分析报告

## Bug 1: 节点数不一致

### 问题描述
- `global_botnet_test` 表显示中国有 **28674** 个节点
- 前端界面显示 test 僵尸网络在中国有 **28695** 个节点
- **差异：21个节点**

### 根本原因

**省份名称处理逻辑不完整**

在 `stats_aggregator/aggregator.py` 的聚合逻辑中（第153-161行），对省份名称的清理逻辑如下：

```sql
COALESCE(
    TRIM(TRAILING '省' FROM 
    TRIM(TRAILING '市' FROM 
    REPLACE(REPLACE(REPLACE(
        province, 
        '壮族自治区', ''), 
        '回族自治区', ''), 
        '维吾尔自治区', '')
    )), 
    '未知'
) as province
```

**问题**：这个逻辑只删除了特定的民族自治区名称，但**没有删除通用的"自治区"后缀**。

### 受影响的省份

原始数据中的省份名称包含完整后缀：
- `内蒙古自治区`（265个节点）
- `西藏自治区`（35个节点）
- `广西壮族自治区`（349个节点，被正确处理）
- `新疆维吾尔自治区`（290个节点，被正确处理）
- `宁夏回族自治区`（113个节点，被正确处理）

### 多出的21个节点详情

在 `china_botnet_test` 表中多出的9条记录（共21个节点）：

| 省份 | 城市 | 节点数 | 备注 |
|------|------|--------|------|
| 内蒙古 | 赤峰 | 1 | 部分数据被错误地记录为"内蒙古" |
| 内蒙古 | 乌海 | 2 | |
| 内蒙古 | 通辽 | 2 | |
| 内蒙古 | 呼和浩特 | 6 | |
| 内蒙古 | 包头 | 2 | |
| 内蒙古 | 兴安盟 | 2 | |
| 内蒙古 | 呼伦贝尔 | 3 | |
| 西藏 | 山南 | 1 | 部分数据被错误地记录为"西藏" |
| 西藏 | 拉萨 | 2 | |
| **总计** | | **21** | |

### 数据验证

从 `botnet_nodes_test` 表实际统计：
- 中国节点数（DISTINCT IP）：**28674**
- 手动按省市分组聚合：**28674**

从聚合表统计：
- `global_botnet_test` 中国节点：**28674**（正确）
- `china_botnet_test` 总节点：**28695**（错误，多了21个）

### 数据流向分析

```
botnet_nodes_test (原始数据)
    ↓
    ├─→ global_botnet_test (聚合逻辑A) → 28674 ✓ 正确
    │   
    └─→ china_botnet_test (聚合逻辑B) → 28695 ✗ 错误
         ↓
         前端 API: /api/node-stats/test
         ↓
         前端显示：country_distribution['中国'] = 28695
```

**关键问题**：`/api/node-stats/{botnet_type}` 接口（`router/node.py` 第255-352行）返回的中国节点数来自 `china_botnet_test` 表的聚合（第282-291行），而不是 `global_botnet_test` 表，导致前端显示的数字与全球表不一致。

### 修复方案

#### 方案1：修复聚合逻辑（推荐）

修改 `stats_aggregator/aggregator.py` 第153-161行的省份处理逻辑，添加对"自治区"后缀的处理：

```sql
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
) as province
```

同时修改 `stats_aggregator/incremental_aggregator.py` 第166行和第205行的对应逻辑。

#### 方案2：统一数据源（临时方案）

修改 `/api/node-stats/{botnet_type}` 接口，让中国节点数直接从 `global_botnet_test` 表读取：

```python
# 从全球表获取中国节点数
cursor.execute(f"""
    SELECT infected_num
    FROM {global_table}
    WHERE country = '中国'
""")
china_result = cursor.fetchone()
china_total = int(china_result['infected_num']) if china_result else 0
```

**推荐使用方案1**，因为方案2只是隐藏问题，不解决根本原因。

---

## Bug 2: 有多条通信记录的IP显示"暂无通信记录"

### 问题描述
- 用户在测试数据中加入了重复IP的多条节点通信信息
- 但在后台管理系统查看节点通信记录时，显示"暂无通信记录"（如图所示：IP 73.35.170.55 显示共0条记录）

### 根本原因

**测试IP不存在于数据库中**

从测试结果来看：
- `botnet_communications_test` 表存在
- 表中有 **294,500** 条通信记录
- 唯一IP数：**289,169**
- 有多条记录的IP示例：`97.19.218.217` (4条), `236.55.198.147` (3条) 等
- **但 IP `73.35.170.55` 的记录数为 0**

### 验证测试

测试查询结果：
```
IP 73.35.170.55 的通信记录总数: 0
```

表中存在的IP示例：
```
1.1.123.7
1.1.130.119
1.1.15.52
...
```

### 结论

**这不是代码bug，而是数据问题**：
1. 用户测试时使用的IP (`73.35.170.55`) 实际上并未成功插入到 `botnet_communications_test` 表中
2. 查询接口逻辑正确（`router/node.py` 第364-479行）
3. 前端调用逻辑正确（`fronted/src/components/CommunicationModal.js` 第385行）

### 可能的原因

1. **数据插入失败**：测试数据没有成功写入数据库
2. **IP格式不匹配**：插入的IP格式与查询的不一致（如有空格、引号等）
3. **表名错误**：数据插入到了错误的表中（如 `botnet_communications_ramnit` 而不是 `botnet_communications_test`）
4. **botnet_type参数错误**：前端查询时使用的 `botnet_type` 参数不是 `test`

### 验证步骤

1. **检查前端请求参数**：
   - 打开浏览器开发者工具 → Network 标签
   - 点击节点查看通信记录
   - 查看请求URL，确认 `botnet_type` 和 `ip` 参数是否正确

2. **直接查询数据库**：
   ```sql
   -- 查询该IP是否存在
   SELECT * FROM botnet_communications_test WHERE ip = '73.35.170.55';
   
   -- 查询包含该IP的记录（模糊匹配）
   SELECT * FROM botnet_communications_test WHERE ip LIKE '%73.35.170.55%';
   
   -- 查看表中有多条记录的IP
   SELECT ip, COUNT(*) as count
   FROM botnet_communications_test
   GROUP BY ip
   HAVING count > 1
   ORDER BY count DESC
   LIMIT 10;
   ```

3. **使用其他已存在的IP测试**：
   使用 `97.19.218.217`（有4条记录）测试功能是否正常

### 修复建议

1. **确认测试数据**：重新插入测试数据，确保IP正确
2. **添加日志**：在数据插入时添加日志，确认数据是否成功写入
3. **API测试**：使用已知存在的IP测试通信记录查询功能

---

## 两个问题是否一致？

**答：不一致，是两个完全不同的问题**

| 对比项 | Bug 1 | Bug 2 |
|--------|-------|-------|
| 问题类型 | 代码逻辑错误 | 数据问题 |
| 根本原因 | 省份名称处理逻辑不完整，缺少"自治区"后缀处理 | 测试IP不存在于数据库中 |
| 影响范围 | 所有包含"内蒙古自治区"和"西藏自治区"数据的僵尸网络 | 仅影响特定IP的查询 |
| 修复方式 | 修改聚合器代码 | 确认测试数据是否正确插入 |
| 严重程度 | 中等（数据统计不准确） | 低（仅影响个别测试数据） |

---

## 测试脚本

已创建以下测试脚本用于验证和调试：

1. **`backend/debugging/test_bugs.py`**: 综合测试两个bug
2. **`backend/debugging/analyze_bug1.py`**: 深入分析Bug1的详细原因
3. **`backend/debugging/check_province_names.py`**: 检查省份名称原始数据

运行方式：
```bash
python backend/debugging/test_bugs.py
python backend/debugging/analyze_bug1.py
python backend/debugging/check_province_names.py
```

---

## 建议

1. **立即修复Bug1**：这是一个实际的代码bug，会影响数据准确性
2. **验证Bug2**：确认测试数据是否正确插入，使用已存在的IP测试功能
3. **添加测试用例**：为聚合器添加单元测试，覆盖所有省份名称格式
4. **数据一致性检查**：定期运行脚本检查各表数据一致性

---

**报告生成时间**: 2026-01-19
**测试环境**: test僵尸网络
**影响版本**: 当前版本
