-- ============================================================
-- 僵尸网络平台数据库迁移脚本
-- 从单表设计迁移到双表设计（节点表 + 通信记录表）
-- ============================================================
-- 
-- 使用说明：
-- 1. 备份现有数据库
-- 2. 替换 {type} 为具体的僵尸网络类型（如 asruex, mozi, ramnit 等）
-- 3. 在测试环境先执行验证
-- 4. 生产环境执行前再次备份
--
-- 注意：本脚本需要为每个僵尸网络类型分别执行
-- ============================================================

USE botnet;

-- ============================================================
-- Step 1: 创建通信记录表
-- ============================================================

CREATE TABLE IF NOT EXISTS botnet_communications_{type} (
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
    INDEX idx_composite (ip, communication_time)
    
    -- 外键约束（可选，建议在数据完整性要求高时启用）
    -- FOREIGN KEY (node_id) REFERENCES botnet_nodes_{type}(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
COMMENT='僵尸网络节点通信记录表（每次通信一条记录）';

SELECT CONCAT('✓ 通信记录表 botnet_communications_{type} 创建完成') AS Status;

-- ============================================================
-- Step 2: 修改节点表结构
-- ============================================================

-- 2.1 检查字段是否存在，如果存在则重命名
SET @db_name = DATABASE();

-- 重命名 active_time 为 first_seen
SET @column_exists = (SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = @db_name 
    AND TABLE_NAME = 'botnet_nodes_{type}' 
    AND COLUMN_NAME = 'active_time');

SET @sql = IF(@column_exists > 0,
    'ALTER TABLE botnet_nodes_{type} CHANGE COLUMN active_time first_seen TIMESTAMP NULL DEFAULT NULL COMMENT ''首次发现时间（日志时间）''',
    'SELECT ''字段 active_time 不存在，跳过'' AS Notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 重命名 updated_at 为 last_seen（临时名称，后面会改回来）
SET @column_exists = (SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = @db_name 
    AND TABLE_NAME = 'botnet_nodes_{type}' 
    AND COLUMN_NAME = 'updated_at');

SET @sql = IF(@column_exists > 0,
    'ALTER TABLE botnet_nodes_{type} CHANGE COLUMN updated_at last_seen TIMESTAMP NULL DEFAULT NULL COMMENT ''最后一次通信时间（日志时间）''',
    'SELECT ''字段 updated_at 不存在，跳过'' AS Notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2.2 添加 updated_at 字段（记录更新时间）
SET @column_exists = (SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = @db_name 
    AND TABLE_NAME = 'botnet_nodes_{type}' 
    AND COLUMN_NAME = 'updated_at');

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE botnet_nodes_{type} ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT ''记录更新时间'' AFTER last_seen',
    'SELECT ''字段 updated_at 已存在，修改定义'' AS Notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 如果updated_at已存在，修改其定义
ALTER TABLE botnet_nodes_{type} 
    MODIFY COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP 
    COMMENT '记录更新时间';

-- 2.3 添加通信次数字段
SET @column_exists = (SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = @db_name 
    AND TABLE_NAME = 'botnet_nodes_{type}' 
    AND COLUMN_NAME = 'communication_count');

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE botnet_nodes_{type} ADD COLUMN communication_count INT DEFAULT 0 COMMENT ''通信次数'' AFTER is_china',
    'SELECT ''字段 communication_count 已存在'' AS Notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2.4 添加索引
SET @index_exists = (SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = @db_name 
    AND TABLE_NAME = 'botnet_nodes_{type}' 
    AND INDEX_NAME = 'idx_first_seen');

SET @sql = IF(@index_exists = 0,
    'ALTER TABLE botnet_nodes_{type} ADD INDEX idx_first_seen (first_seen)',
    'SELECT ''索引 idx_first_seen 已存在'' AS Notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @index_exists = (SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = @db_name 
    AND TABLE_NAME = 'botnet_nodes_{type}' 
    AND INDEX_NAME = 'idx_last_seen');

SET @sql = IF(@index_exists = 0,
    'ALTER TABLE botnet_nodes_{type} ADD INDEX idx_last_seen (last_seen)',
    'SELECT ''索引 idx_last_seen 已存在'' AS Notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @index_exists = (SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = @db_name 
    AND TABLE_NAME = 'botnet_nodes_{type}' 
    AND INDEX_NAME = 'idx_communication_count');

SET @sql = IF(@index_exists = 0,
    'ALTER TABLE botnet_nodes_{type} ADD INDEX idx_communication_count (communication_count)',
    'SELECT ''索引 idx_communication_count 已存在'' AS Notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2.5 更新表注释
ALTER TABLE botnet_nodes_{type} 
    COMMENT='僵尸网络节点基本信息表（每个IP一条记录）';

SELECT CONCAT('✓ 节点表 botnet_nodes_{type} 结构修改完成') AS Status;

-- ============================================================
-- Step 3: 迁移历史数据
-- ============================================================

-- 3.1 迁移第一次通信记录（使用 first_seen）
INSERT INTO botnet_communications_{type} 
    (node_id, ip, communication_time, received_at, longitude, latitude, 
     country, province, city, continent, isp, asn, status, is_china)
SELECT 
    id, 
    ip, 
    COALESCE(first_seen, created_time) as communication_time,
    created_time as received_at,
    longitude, 
    latitude,
    country, 
    province, 
    city, 
    continent, 
    isp, 
    asn, 
    status, 
    is_china
FROM botnet_nodes_{type}
WHERE first_seen IS NOT NULL OR created_time IS NOT NULL;

SELECT CONCAT('✓ 已迁移 ', ROW_COUNT(), ' 条第一次通信记录') AS Status;

-- 3.2 迁移最后一次通信记录（使用 last_seen，如果与 first_seen 不同）
INSERT INTO botnet_communications_{type} 
    (node_id, ip, communication_time, received_at, longitude, latitude, 
     country, province, city, continent, isp, asn, status, is_china)
SELECT 
    id, 
    ip, 
    last_seen as communication_time,
    created_time as received_at,
    longitude, 
    latitude,
    country, 
    province, 
    city, 
    continent, 
    isp, 
    asn, 
    status, 
    is_china
FROM botnet_nodes_{type}
WHERE last_seen IS NOT NULL 
  AND (first_seen IS NULL OR last_seen != first_seen)
  AND last_seen > COALESCE(first_seen, '1970-01-01');

SELECT CONCAT('✓ 已迁移 ', ROW_COUNT(), ' 条最后一次通信记录') AS Status;

-- 3.3 更新节点表的通信次数
UPDATE botnet_nodes_{type} n
SET communication_count = (
    SELECT COUNT(*) 
    FROM botnet_communications_{type} c 
    WHERE c.node_id = n.id
);

SELECT CONCAT('✓ 已更新节点通信次数统计') AS Status;

-- ============================================================
-- Step 4: 更新统计表结构（可选）
-- ============================================================

-- 4.1 中国统计表添加通信次数
SET @column_exists = (SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = @db_name 
    AND TABLE_NAME = 'china_botnet_{type}' 
    AND COLUMN_NAME = 'communication_count');

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE china_botnet_{type} ADD COLUMN communication_count INT DEFAULT 0 COMMENT ''通信总次数'' AFTER infected_num',
    'SELECT ''字段 communication_count 已存在于 china_botnet_{type}'' AS Notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4.2 全球统计表添加通信次数
SET @column_exists = (SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = @db_name 
    AND TABLE_NAME = 'global_botnet_{type}' 
    AND COLUMN_NAME = 'communication_count');

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE global_botnet_{type} ADD COLUMN communication_count INT DEFAULT 0 COMMENT ''通信总次数'' AFTER infected_num',
    'SELECT ''字段 communication_count 已存在于 global_botnet_{type}'' AS Notice');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT CONCAT('✓ 统计表结构更新完成') AS Status;

-- ============================================================
-- Step 5: 数据验证
-- ============================================================

-- 验证节点数量
SELECT 
    '节点表记录数' as TableName,
    COUNT(*) as RecordCount 
FROM botnet_nodes_{type}
UNION ALL
SELECT 
    '通信记录表记录数' as TableName,
    COUNT(*) as RecordCount 
FROM botnet_communications_{type}
UNION ALL
SELECT 
    '节点表中有通信记录的数量' as TableName,
    COUNT(*) as RecordCount 
FROM botnet_nodes_{type} 
WHERE communication_count > 0;

-- 验证数据一致性
SELECT 
    n.ip,
    n.communication_count as node_count,
    COUNT(c.id) as actual_count,
    CASE 
        WHEN n.communication_count = COUNT(c.id) THEN 'OK'
        ELSE 'MISMATCH'
    END as status
FROM botnet_nodes_{type} n
LEFT JOIN botnet_communications_{type} c ON n.id = c.node_id
GROUP BY n.id, n.ip, n.communication_count
HAVING status = 'MISMATCH'
LIMIT 10;

-- ============================================================
-- Step 6: 性能优化（可选）
-- ============================================================

-- 分析表以优化查询性能
ANALYZE TABLE botnet_nodes_{type};
ANALYZE TABLE botnet_communications_{type};

SELECT CONCAT('✓ 表分析完成，优化查询性能') AS Status;

-- ============================================================
-- 迁移完成
-- ============================================================

SELECT '
========================================
数据库迁移完成！
========================================

请验证以下内容：
1. 节点表和通信记录表的数据量是否正确
2. 通信次数统计是否准确
3. 执行测试查询验证性能

下一步：
1. 修改后端代码（db_writer.py）
2. 在测试环境部署并测试
3. 准备生产环境部署计划

' AS Message;
