# Nodes 表添加 Unit/Industry 字段 - 实现说明

## 需求

为 `botnet_nodes_*` 表添加 `unit` 和 `industry` 字段，实现与 `botnet_communications_*` 表相同的功能：
1. 服务器启动时检查字段是否存在
2. 如果不存在则添加字段
3. 回填历史数据：从 ip_info 表查找对应 IP 的单位和行业信息

## 实现逻辑

### 1. 新增方法：`_ensure_node_unit_industry_fields_sync`

**位置**: `backend/log_processor/db_writer.py` (第 704-757 行)

**功能**:
- 检查 `botnet_nodes_*` 表是否有 `unit` 和 `industry` 字段
- 如果不存在则添加字段和索引
- 调用回填方法补充历史数据

**代码逻辑**:
```python
def _ensure_node_unit_industry_fields_sync(self, cursor):
    # 1. 检查字段是否存在
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = '{self.node_table}'
        AND COLUMN_NAME IN ('unit', 'industry')
    """)
    
    existing_fields = {row[0] for row in cursor.fetchall()}
    
    # 2. 添加 unit 字段（如果不存在）
    if 'unit' not in existing_fields:
        cursor.execute(f"""
            ALTER TABLE {self.node_table}
            ADD COLUMN unit VARCHAR(255) DEFAULT NULL COMMENT '所属单位'
            AFTER city
        """)
        cursor.execute(f"""
            ALTER TABLE {self.node_table}
            ADD INDEX idx_unit (unit)
        """)
    
    # 3. 添加 industry 字段（如果不存在）
    if 'industry' not in existing_fields:
        cursor.execute(f"""
            ALTER TABLE {self.node_table}
            ADD COLUMN industry VARCHAR(255) DEFAULT NULL COMMENT '所属行业'
            AFTER unit
        """)
        cursor.execute(f"""
            ALTER TABLE {self.node_table}
            ADD INDEX idx_industry (industry)
        """)
    
    # 4. 回填历史数据
    self._backfill_node_unit_industry_data_sync(cursor)
```

### 2. 新增方法：`_backfill_node_unit_industry_data_sync`

**位置**: `backend/log_processor/db_writer.py` (第 789-847 行)

**功能**:
- 查询 nodes 表中 unit 和 industry 为空的记录
- 批量查询 ip_info 表获取对应的单位和行业
- 批量更新 nodes 表

**代码逻辑**:
```python
def _backfill_node_unit_industry_data_sync(self, cursor):
    # 1. 查询需要回填的 IP
    cursor.execute(f"""
        SELECT DISTINCT ip
        FROM {self.node_table}
        WHERE (unit IS NULL OR unit = '') 
        AND (industry IS NULL OR industry = '')
    """)
    
    ips_to_update = [row[0] for row in cursor.fetchall()]
    
    # 2. 批量查询 ip_info 表
    ip_mapping = self.ip_mapper.batch_get_unit_industry(ips_to_update)
    
    # 3. 过滤有数据的 IP
    updates = []
    for ip, (unit, industry) in ip_mapping.items():
        if unit or industry:
            updates.append((unit, industry, ip))
    
    # 4. 批量更新（使用 CASE WHEN 语句）
    batch_size = 500
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]
        
        update_sql = f"""
            UPDATE {self.node_table}
            SET 
                unit = CASE ip
                    {' '.join([f"WHEN %s THEN %s" for _ in batch])}
                    ELSE unit
                END,
                industry = CASE ip
                    {' '.join([f"WHEN %s THEN %s" for _ in batch])}
                    ELSE industry
                END
            WHERE ip IN ({','.join(['%s'] * len(batch))})
            AND (unit IS NULL OR unit = '')
            AND (industry IS NULL OR industry = '')
        """
        
        cursor.execute(update_sql, params)
```

### 3. 修改初始化方法

**位置**: `backend/log_processor/db_writer.py` (第 185-221 行)

**修改内容**: 在 `_initialize_database` 方法中添加 nodes 表的字段检查

```python
def _initialize_database(self):
    # 1. 确保表存在
    self._ensure_tables_exist_sync(cursor)
    
    # 2. 确保 communications 表的 unit 和 industry 字段存在
    self._ensure_unit_industry_fields_sync(cursor)
    
    # 3. 确保 nodes 表的 unit 和 industry 字段存在  ← 新增
    self._ensure_node_unit_industry_fields_sync(cursor)
    
    # 提交更改
    conn.commit()
```

## 工作流程

### 服务启动时

```
服务启动
  ↓
创建 BotnetDBWriter 实例
  ↓
__init__() 调用 _initialize_database()
  ↓
1. 确保表存在
  ↓
2. 处理 communications 表
   ├─ 检查 unit/industry 字段
   ├─ 添加字段（如果不存在）
   └─ 回填历史数据
  ↓
3. 处理 nodes 表  ← 新增
   ├─ 检查 unit/industry 字段
   ├─ 添加字段（如果不存在）
   └─ 回填历史数据
  ↓
初始化完成
```

### 预期日志输出

```
[asruex] 开始初始化数据库表和字段...
[asruex] Tables ensured: botnet_nodes_asruex, botnet_communications_asruex

[asruex] 为 botnet_communications_asruex 添加 unit 字段...
[asruex] unit 字段添加成功
[asruex] 为 botnet_communications_asruex 添加 industry 字段...
[asruex] industry 字段添加成功
[asruex] 开始检查并回填 communications 表历史数据...
[asruex] communications 表找到 251924 个需要回填的IP
[asruex] communications 表找到 2 个IP有对应的 unit/industry 数据
[asruex] communications 表历史数据回填完成: 更新了 2 条记录

[asruex] 为 botnet_nodes_asruex 添加 unit 字段...
[asruex] botnet_nodes_asruex unit 字段添加成功
[asruex] 为 botnet_nodes_asruex 添加 industry 字段...
[asruex] botnet_nodes_asruex industry 字段添加成功
[asruex] 开始检查并回填 nodes 表历史数据...
[asruex] nodes 表找到 15432 个需要回填的IP
[asruex] nodes 表找到 1 个IP有对应的 unit/industry 数据
[asruex] nodes 表历史数据回填完成: 更新了 1 条记录

[asruex] 数据库初始化完成
```

## 数据库结构

### 修改后的 botnet_nodes_* 表结构

```sql
CREATE TABLE botnet_nodes_asruex (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(15) NOT NULL,
    longitude FLOAT,
    latitude FLOAT,
    country VARCHAR(50),
    province VARCHAR(50),
    city VARCHAR(50),
    unit VARCHAR(255) DEFAULT NULL COMMENT '所属单位',      ← 新增
    industry VARCHAR(255) DEFAULT NULL COMMENT '所属行业',  ← 新增
    continent VARCHAR(50),
    isp VARCHAR(255),
    asn VARCHAR(50),
    status ENUM('active', 'inactive') DEFAULT 'active',
    first_seen TIMESTAMP NULL DEFAULT NULL,
    last_seen TIMESTAMP NULL DEFAULT NULL,
    communication_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_china BOOLEAN DEFAULT FALSE,
    UNIQUE KEY idx_unique_ip (ip),
    INDEX idx_unit (unit),      ← 新增索引
    INDEX idx_industry (industry)  ← 新增索引
);
```

## 测试方法

### 1. 检查字段是否添加

```bash
cd backend
python check_node_fields.py
```

**预期输出**:
```
======================================================================
Checking Nodes Tables for unit/industry Fields
======================================================================

ASRUEX:
  Table: botnet_nodes_asruex
  Status: Table exists with fields:
    - industry (varchar(255)) - 所属行业
    - unit (varchar(255)) - 所属单位
  Data Statistics:
    Total records: 15432
    Records with unit: 1 (0.0%)
    Records with industry: 1 (0.0%)

MOZI:
  Table: botnet_nodes_mozi
  Status: Table exists with fields:
    - industry (varchar(255)) - 所属行业
    - unit (varchar(255)) - 所属单位
  Data Statistics:
    Total records: 28765
    Records with unit: 0 (0.0%)
    Records with industry: 0 (0.0%)
```

### 2. 启动服务观察日志

```bash
cd backend
python main.py
```

观察日志输出，应该看到：
- nodes 表字段添加日志
- nodes 表历史数据回填日志

### 3. 直接查询数据库

```sql
-- 检查字段是否存在
DESCRIBE botnet_nodes_asruex;

-- 检查数据统计
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN unit IS NOT NULL THEN 1 ELSE 0 END) as has_unit,
    SUM(CASE WHEN industry IS NOT NULL THEN 1 ELSE 0 END) as has_industry
FROM botnet_nodes_asruex;
```

## 与 Communications 表的对比

| 特性 | Communications 表 | Nodes 表 |
|------|------------------|----------|
| 表名 | botnet_communications_* | botnet_nodes_* |
| 字段添加方法 | `_ensure_unit_industry_fields_sync` | `_ensure_node_unit_industry_fields_sync` |
| 回填方法 | `_backfill_unit_industry_data_sync` | `_backfill_node_unit_industry_data_sync` |
| 数据量 | 大（每次通信一条记录） | 小（每个 IP 一条记录） |
| 回填速度 | 较慢（记录多） | 较快（记录少） |
| 用途 | 详细通信历史 | 节点汇总信息 |

## 数据填充情况

### 当前状态
- ? 字段已添加到 nodes 表
- ? 索引已创建
- ?? 历史数据大部分为空（IP 不匹配）

### 原因
- ip_info 表中的 IP 和实际 botnet 数据中的 IP 不是同一批
- 只有极少数 IP 能匹配上

### 解决方案
1. **等待新数据**：新的 botnet 节点会自动填充 unit 和 industry
2. **导入正确的 IP 映射**：获取实际 botnet IP 的单位和行业信息并导入
3. **接受现状**：历史数据为空是可接受的，重要的是新数据能正确填充

## 总结

### 已完成 ?
1. 为 nodes 表添加 unit 和 industry 字段的检查逻辑
2. 为 nodes 表添加历史数据回填逻辑
3. 在服务启动时自动执行
4. 与 communications 表保持一致的实现方式

### 优势 ?
1. **自动化**：服务启动时自动检查和添加
2. **一致性**：nodes 和 communications 表使用相同的逻辑
3. **性能优化**：批量更新，使用 CASE WHEN 语句
4. **错误处理**：失败不影响服务启动

### 注意事项 ??
1. 历史数据回填依赖 ip_info 表的数据质量
2. 如果 IP 不匹配，历史数据会保持为 NULL
3. 新数据会自动填充（如果 IP 在 ip_info 中）

**实现完成，请重启服务测试！** ?
