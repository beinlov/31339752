# 数据库表结构修改方案

## 需求变更说明

### 旧逻辑
- C2端：进行去重，只传输唯一的节点IP
- 平台端：
  - 只记录每个节点IP的三个时间点
  - `active_time`: 节点激活时间（日志中的第一次通信时间）
  - `created_time`: 首次写入数据库的时间
  - `updated_at`: 最新一次响应时间（日志中的时间）
  - 使用 `UNIQUE KEY idx_unique_ip (ip)` 保证每个IP只有一条记录
  - 使用 `ON DUPLICATE KEY UPDATE` 更新现有记录

### 新逻辑
- C2端：不进行去重，传输所有通信日志
- 平台端：记录节点的**全部通信信息**，每次通信都作为一条独立记录

---

## 当前表结构分析

### 1. botnet_nodes_{type} 表（节点表）

```sql
CREATE TABLE botnet_nodes_{type} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(15) NOT NULL,
    longitude FLOAT,
    latitude FLOAT,
    country VARCHAR(50),
    province VARCHAR(50),
    city VARCHAR(50),
    continent VARCHAR(50),
    isp VARCHAR(255),
    asn VARCHAR(50),
    status ENUM('active', 'inactive') DEFAULT 'active',
    active_time TIMESTAMP NULL DEFAULT NULL COMMENT '节点激活时间（日志中的时间）',
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '节点首次写入数据库的时间',
    updated_at TIMESTAMP NULL DEFAULT NULL COMMENT '节点最新一次响应时间（日志中的时间）',
    is_china BOOLEAN DEFAULT FALSE,
    INDEX idx_ip (ip),
    INDEX idx_location (country, province, city),
    INDEX idx_status (status),
    INDEX idx_active_time (active_time),
    INDEX idx_created_time (created_time),
    INDEX idx_updated_at (updated_at),
    INDEX idx_is_china (is_china),
    UNIQUE KEY idx_unique_ip (ip)  -- 关键约束：每个IP只有一条记录
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
COMMENT='僵尸网络节点原始数据表'
```

**问题**：
1. `UNIQUE KEY idx_unique_ip (ip)` 限制了每个IP只能有一条记录
2. 无法存储同一节点的多次通信记录
3. 只能保存第一次和最后一次的时间，中间的通信记录全部丢失

---

## 推荐方案：双表设计

### 方案概述
将原来的单表拆分为两张表：
1. **节点表** (`botnet_nodes_{type}`)：存储节点的基本信息和汇总统计
2. **通信记录表** (`botnet_communications_{type}`)：存储所有通信记录

### 优势
✅ 数据完整性：保存全部通信历史  
✅ 查询性能：节点表用于快速统计，通信表用于详细分析  
✅ 向后兼容：现有的统计查询不需要大改  
✅ 可扩展性：方便后续添加通信相关的字段（如事件类型、载荷等）  
✅ 存储优化：节点的静态信息不重复存储  

---

## 新表结构设计

### 表1: botnet_nodes_{type} (节点信息表)

```sql
CREATE TABLE botnet_nodes_{type} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(15) NOT NULL COMMENT '节点IP地址',
    
    -- 地理位置信息（最新）
    longitude FLOAT COMMENT '经度',
    latitude FLOAT COMMENT '纬度',
    country VARCHAR(50) COMMENT '国家',
    province VARCHAR(50) COMMENT '省份',
    city VARCHAR(50) COMMENT '城市',
    continent VARCHAR(50) COMMENT '洲',
    
    -- 网络信息（最新）
    isp VARCHAR(255) COMMENT 'ISP运营商',
    asn VARCHAR(50) COMMENT 'AS号',
    
    -- 状态信息
    status ENUM('active', 'inactive') DEFAULT 'active' COMMENT '节点状态',
    is_china BOOLEAN DEFAULT FALSE COMMENT '是否为中国节点',
    
    -- 统计信息
    first_seen TIMESTAMP NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
    last_seen TIMESTAMP NULL DEFAULT NULL COMMENT '最后一次通信时间（日志时间）',
    communication_count INT DEFAULT 0 COMMENT '通信次数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
    
    -- 索引
    UNIQUE KEY idx_unique_ip (ip),
    INDEX idx_location (country, province, city),
    INDEX idx_status (status),
    INDEX idx_first_seen (first_seen),
    INDEX idx_last_seen (last_seen),
    INDEX idx_is_china (is_china),
    INDEX idx_communication_count (communication_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
COMMENT='僵尸网络节点基本信息表（每个IP一条记录）';
```

**字段说明**：
- `first_seen`: 该节点首次通信的时间（来自日志）
- `last_seen`: 该节点最后一次通信的时间（来自日志）
- `communication_count`: 该节点的通信总次数
- `created_at`: 该记录首次写入数据库的时间
- `updated_at`: 该记录最后更新的时间

### 表2: botnet_communications_{type} (通信记录表)

```sql
CREATE TABLE botnet_communications_{type} (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    node_id INT NOT NULL COMMENT '关联的节点ID',
    ip VARCHAR(15) NOT NULL COMMENT '节点IP（冗余字段，便于查询）',
    
    -- 通信时间信息
    communication_time TIMESTAMP NOT NULL COMMENT '通信发生时间（日志中的时间）',
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '平台接收时间',
    
    -- 地理位置信息（快照，记录通信时的位置）
    longitude FLOAT COMMENT '经度',
    latitude FLOAT COMMENT '纬度',
    country VARCHAR(50) COMMENT '国家',
    province VARCHAR(50) COMMENT '省份',
    city VARCHAR(50) COMMENT '城市',
    continent VARCHAR(50) COMMENT '洲',
    
    -- 网络信息（快照）
    isp VARCHAR(255) COMMENT 'ISP运营商',
    asn VARCHAR(50) COMMENT 'AS号',
    
    -- 通信详情（可扩展）
    event_type VARCHAR(50) COMMENT '事件类型',
    status VARCHAR(50) DEFAULT 'active' COMMENT '通信状态',
    
    -- 其他信息
    is_china BOOLEAN DEFAULT FALSE COMMENT '是否为中国节点',
    
    -- 索引
    INDEX idx_node_id (node_id),
    INDEX idx_ip (ip),
    INDEX idx_communication_time (communication_time),
    INDEX idx_received_at (received_at),
    INDEX idx_location (country, province, city),
    INDEX idx_is_china (is_china),
    INDEX idx_composite (ip, communication_time),
    
    -- 外键约束（可选）
    FOREIGN KEY (node_id) REFERENCES botnet_nodes_{type}(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
COMMENT='僵尸网络节点通信记录表（每次通信一条记录）';
```

**字段说明**：
- `node_id`: 关联到节点表的外键
- `ip`: 冗余字段，方便直接按IP查询，避免JOIN
- `communication_time`: 日志中记录的通信发生时间
- `received_at`: 平台接收并记录该通信的时间
- 地理和网络信息：快照数据，记录该次通信时的节点位置信息

---

## 数据迁移步骤

### Step 1: 创建新表

```sql
-- 创建通信记录表
CREATE TABLE botnet_communications_{type} (
    -- 完整建表语句见上方
);
```

### Step 2: 修改现有节点表

```sql
-- 重命名旧的时间字段
ALTER TABLE botnet_nodes_{type} 
    CHANGE COLUMN active_time first_seen TIMESTAMP NULL DEFAULT NULL 
    COMMENT '首次发现时间（日志时间）';

ALTER TABLE botnet_nodes_{type} 
    CHANGE COLUMN updated_at last_seen TIMESTAMP NULL DEFAULT NULL 
    COMMENT '最后一次通信时间（日志时间）';

-- 移除自动更新时间戳（因为需要手动从日志时间设置）
ALTER TABLE botnet_nodes_{type}
    MODIFY COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    COMMENT '记录更新时间';

-- 添加通信次数字段
ALTER TABLE botnet_nodes_{type}
    ADD COLUMN communication_count INT DEFAULT 0 COMMENT '通信次数'
    AFTER is_china;

-- 添加索引
ALTER TABLE botnet_nodes_{type}
    ADD INDEX idx_communication_count (communication_count);

-- 更新表注释
ALTER TABLE botnet_nodes_{type} COMMENT='僵尸网络节点基本信息表（每个IP一条记录）';
```

### Step 3: 迁移历史数据

```sql
-- 为每个现有节点创建一条通信记录（使用active_time作为通信时间）
INSERT INTO botnet_communications_{type} 
    (node_id, ip, communication_time, received_at, longitude, latitude, 
     country, province, city, continent, isp, asn, status, is_china)
SELECT 
    id, ip, first_seen, created_time, longitude, latitude,
    country, province, city, continent, isp, asn, status, is_china
FROM botnet_nodes_{type}
WHERE first_seen IS NOT NULL;

-- 如果last_seen不同于first_seen，再创建一条记录
INSERT INTO botnet_communications_{type} 
    (node_id, ip, communication_time, received_at, longitude, latitude, 
     country, province, city, continent, isp, asn, status, is_china)
SELECT 
    id, ip, last_seen, created_time, longitude, latitude,
    country, province, city, continent, isp, asn, status, is_china
FROM botnet_nodes_{type}
WHERE last_seen IS NOT NULL AND last_seen != first_seen;

-- 更新节点表的通信次数
UPDATE botnet_nodes_{type} n
SET communication_count = (
    SELECT COUNT(*) 
    FROM botnet_communications_{type} c 
    WHERE c.node_id = n.id
);
```

---

## 代码修改要点

### 1. db_writer.py 修改

#### 修改点 A: 表结构创建逻辑
位置：`_ensure_tables_exist()` 方法

修改：
- 创建新的通信记录表
- 修改节点表的字段定义

#### 修改点 B: 数据插入逻辑
位置：`_insert_nodes()` 方法

**旧逻辑**：
```python
# 使用 INSERT ... ON DUPLICATE KEY UPDATE
# 如果IP存在则更新，否则插入
```

**新逻辑**：
```python
# 1. 先插入或更新节点表（维护节点的汇总信息）
# 2. 然后插入通信记录表（每次通信都是新记录，不去重）
```

#### 修改点 C: 去重逻辑
位置：`add_node()` 方法

**需要移除**：
```python
# 生成记录唯一标识（用于去重）
record_key = f"{log_data['ip']}|{log_data['timestamp']}|{log_data.get('event_type', '')}"

# 检查是否已处理过（应用层去重）
if record_key in self.processed_records:
    self.duplicate_count += 1
    return False
```

**新逻辑**：
- 移除应用层去重
- 所有记录都应该被处理和存储

### 2. 查询接口修改

#### node.py 修改
位置：`get_node_details()` 接口

需要考虑：
- 是否只返回节点表（汇总信息）
- 还是需要新增接口返回通信记录详情

建议：
1. 保持现有接口返回节点表数据（向后兼容）
2. 新增 `/node-communications` 接口返回通信记录详情

```python
@router.get("/node-communications")
async def get_node_communications(
    botnet_type: str,
    ip: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=100, le=10000)
):
    """获取节点的通信记录详情"""
    # 查询 botnet_communications_{type} 表
    pass
```

---

## 性能优化建议

### 1. 分区策略（可选）
对于通信记录表，数据量会快速增长，建议使用时间分区：

```sql
CREATE TABLE botnet_communications_{type} (
    -- 字段定义
) 
PARTITION BY RANGE (TO_DAYS(communication_time)) (
    PARTITION p202401 VALUES LESS THAN (TO_DAYS('2024-02-01')),
    PARTITION p202402 VALUES LESS THAN (TO_DAYS('2024-03-01')),
    -- 每月一个分区
    PARTITION pmax VALUES LESS THAN MAXVALUE
);
```

### 2. 归档策略
定期将旧的通信记录归档到历史表：

```sql
-- 创建归档表（结构相同）
CREATE TABLE botnet_communications_{type}_archive LIKE botnet_communications_{type};

-- 定期归档（例如：归档3个月前的数据）
INSERT INTO botnet_communications_{type}_archive
SELECT * FROM botnet_communications_{type}
WHERE communication_time < DATE_SUB(NOW(), INTERVAL 3 MONTH);

DELETE FROM botnet_communications_{type}
WHERE communication_time < DATE_SUB(NOW(), INTERVAL 3 MONTH);
```

### 3. 索引优化
根据实际查询需求，可能需要添加组合索引：

```sql
-- 按IP和时间范围查询
CREATE INDEX idx_ip_time ON botnet_communications_{type}(ip, communication_time);

-- 按地区和时间查询
CREATE INDEX idx_location_time ON botnet_communications_{type}(country, province, communication_time);
```

---

## 统计表的影响

### china_botnet_{type} 和 global_botnet_{type} 表

这两个统计表目前记录的是：
- `infected_num`: 该地区/国家的节点数量（unique IP）
- `created_at`: 该地区第一个节点的创建时间
- `updated_at`: 该地区最新节点的更新时间

**建议修改**：
```sql
ALTER TABLE china_botnet_{type}
    ADD COLUMN communication_count INT DEFAULT 0 COMMENT '通信总次数';

ALTER TABLE global_botnet_{type}
    ADD COLUMN communication_count INT DEFAULT 0 COMMENT '通信总次数';
```

这样可以同时统计：
- 节点数量（unique IP count）
- 通信次数（communication count）

---

## 回滚方案

如果需要回滚到旧的单表设计：

```sql
-- 1. 从通信记录表恢复数据到节点表
UPDATE botnet_nodes_{type} n
JOIN (
    SELECT node_id, 
           MIN(communication_time) as first_time,
           MAX(communication_time) as last_time
    FROM botnet_communications_{type}
    GROUP BY node_id
) c ON n.id = c.node_id
SET n.first_seen = c.first_time,
    n.last_seen = c.last_time;

-- 2. 删除通信记录表
DROP TABLE botnet_communications_{type};

-- 3. 恢复旧的字段名
ALTER TABLE botnet_nodes_{type}
    CHANGE COLUMN first_seen active_time TIMESTAMP NULL DEFAULT NULL;

ALTER TABLE botnet_nodes_{type}
    CHANGE COLUMN last_seen updated_at TIMESTAMP NULL DEFAULT NULL;
```

---

## 总结

### 修改内容
1. ✅ 新建通信记录表 `botnet_communications_{type}`
2. ✅ 修改节点表字段：`active_time` → `first_seen`, `updated_at` → `last_seen`
3. ✅ 添加 `communication_count` 字段
4. ✅ 移除应用层和数据库层的去重逻辑
5. ✅ 修改数据插入代码：双表插入
6. ✅ 新增通信记录查询接口

### 优势
- 📊 **完整记录**：保存所有通信历史
- 🚀 **性能优化**：节点表小而快，通信表可分区
- 🔄 **向后兼容**：现有接口可继续使用
- 📈 **可扩展**：方便添加通信详情字段
- 💾 **存储优化**：静态信息不重复

### 风险评估
- ⚠️ 存储空间增加（需要监控）
- ⚠️ 代码改动较大（需要充分测试）
- ⚠️ 查询逻辑需要调整（但可向后兼容）

---

## 下一步行动

1. **审查方案**：团队review这个设计
2. **测试环境验证**：在测试环境创建表并测试
3. **编写迁移脚本**：准备完整的SQL迁移脚本
4. **修改代码**：修改 `db_writer.py` 和相关接口
5. **性能测试**：验证插入和查询性能
6. **生产部署**：分步骤部署到生产环境
