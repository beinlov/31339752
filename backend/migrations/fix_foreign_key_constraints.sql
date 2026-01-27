-- ============================================================
-- 数据库优化脚本：修复外键约束问题
-- ============================================================
-- 目的：将通信记录表的外键约束从 ON DELETE CASCADE 改为 ON DELETE RESTRICT
-- 原因：防止误删节点导致大量通信历史记录丢失
-- 执行前提：确保所有botnet_communications表都已存在
-- 执行方式：mysql -u root -p botnet < fix_foreign_key_constraints.sql
-- ============================================================

USE botnet;

-- ============================================================
-- Step 1: 检查现有外键约束
-- ============================================================
SELECT 
    TABLE_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    DELETE_RULE,
    UPDATE_RULE
FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS
WHERE TABLE_SCHEMA = 'botnet'
  AND TABLE_NAME LIKE 'botnet_communications_%'
ORDER BY TABLE_NAME;

-- ============================================================
-- Step 2: 为每个僵尸网络类型修复外键约束
-- ============================================================

-- 2.1 asruex
-- 检查外键是否存在
SELECT CONSTRAINT_NAME 
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'botnet' 
  AND TABLE_NAME = 'botnet_communications_asruex'
  AND REFERENCED_TABLE_NAME = 'botnet_nodes_asruex';

-- 删除旧的外键（如果存在）
SET @fk_name = (
    SELECT CONSTRAINT_NAME 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'botnet' 
      AND TABLE_NAME = 'botnet_communications_asruex'
      AND REFERENCED_TABLE_NAME = 'botnet_nodes_asruex'
    LIMIT 1
);

SET @drop_fk_sql = IF(@fk_name IS NOT NULL,
    CONCAT('ALTER TABLE botnet_communications_asruex DROP FOREIGN KEY ', @fk_name),
    'SELECT "No FK to drop for asruex"');
PREPARE stmt FROM @drop_fk_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加新的外键（RESTRICT）
ALTER TABLE botnet_communications_asruex
ADD CONSTRAINT fk_node_asruex 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_asruex(id) ON DELETE RESTRICT;

-- 添加必要的索引（如果不存在）
ALTER TABLE botnet_communications_asruex ADD INDEX idx_node_id (node_id);


-- 2.2 mozi
SET @fk_name = (
    SELECT CONSTRAINT_NAME 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'botnet' 
      AND TABLE_NAME = 'botnet_communications_mozi'
      AND REFERENCED_TABLE_NAME = 'botnet_nodes_mozi'
    LIMIT 1
);

SET @drop_fk_sql = IF(@fk_name IS NOT NULL,
    CONCAT('ALTER TABLE botnet_communications_mozi DROP FOREIGN KEY ', @fk_name),
    'SELECT "No FK to drop for mozi"');
PREPARE stmt FROM @drop_fk_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

ALTER TABLE botnet_communications_mozi
ADD CONSTRAINT fk_node_mozi 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_mozi(id) ON DELETE RESTRICT;

ALTER TABLE botnet_communications_mozi ADD INDEX idx_node_id (node_id);


-- 2.3 andromeda
SET @fk_name = (
    SELECT CONSTRAINT_NAME 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'botnet' 
      AND TABLE_NAME = 'botnet_communications_andromeda'
      AND REFERENCED_TABLE_NAME = 'botnet_nodes_andromeda'
    LIMIT 1
);

SET @drop_fk_sql = IF(@fk_name IS NOT NULL,
    CONCAT('ALTER TABLE botnet_communications_andromeda DROP FOREIGN KEY ', @fk_name),
    'SELECT "No FK to drop for andromeda"');
PREPARE stmt FROM @drop_fk_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

ALTER TABLE botnet_communications_andromeda
ADD CONSTRAINT fk_node_andromeda 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_andromeda(id) ON DELETE RESTRICT;

ALTER TABLE botnet_communications_andromeda ADD INDEX idx_node_id (node_id);


-- 2.4 moobot
SET @fk_name = (
    SELECT CONSTRAINT_NAME 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'botnet' 
      AND TABLE_NAME = 'botnet_communications_moobot'
      AND REFERENCED_TABLE_NAME = 'botnet_nodes_moobot'
    LIMIT 1
);

SET @drop_fk_sql = IF(@fk_name IS NOT NULL,
    CONCAT('ALTER TABLE botnet_communications_moobot DROP FOREIGN KEY ', @fk_name),
    'SELECT "No FK to drop for moobot"');
PREPARE stmt FROM @drop_fk_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

ALTER TABLE botnet_communications_moobot
ADD CONSTRAINT fk_node_moobot 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_moobot(id) ON DELETE RESTRICT;

ALTER TABLE botnet_communications_moobot ADD INDEX idx_node_id (node_id);


-- 2.5 ramnit
SET @fk_name = (
    SELECT CONSTRAINT_NAME 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'botnet' 
      AND TABLE_NAME = 'botnet_communications_ramnit'
      AND REFERENCED_TABLE_NAME = 'botnet_nodes_ramnit'
    LIMIT 1
);

SET @drop_fk_sql = IF(@fk_name IS NOT NULL,
    CONCAT('ALTER TABLE botnet_communications_ramnit DROP FOREIGN KEY ', @fk_name),
    'SELECT "No FK to drop for ramnit"');
PREPARE stmt FROM @drop_fk_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

ALTER TABLE botnet_communications_ramnit
ADD CONSTRAINT fk_node_ramnit 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_ramnit(id) ON DELETE RESTRICT;

ALTER TABLE botnet_communications_ramnit ADD INDEX idx_node_id (node_id);


-- 2.6 leethozer
SET @fk_name = (
    SELECT CONSTRAINT_NAME 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'botnet' 
      AND TABLE_NAME = 'botnet_communications_leethozer'
      AND REFERENCED_TABLE_NAME = 'botnet_nodes_leethozer'
    LIMIT 1
);

SET @drop_fk_sql = IF(@fk_name IS NOT NULL,
    CONCAT('ALTER TABLE botnet_communications_leethozer DROP FOREIGN KEY ', @fk_name),
    'SELECT "No FK to drop for leethozer"');
PREPARE stmt FROM @drop_fk_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

ALTER TABLE botnet_communications_leethozer
ADD CONSTRAINT fk_node_leethozer 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_leethozer(id) ON DELETE RESTRICT;

ALTER TABLE botnet_communications_leethozer ADD INDEX idx_node_id (node_id);


-- 2.7 test
SET @fk_name = (
    SELECT CONSTRAINT_NAME 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'botnet' 
      AND TABLE_NAME = 'botnet_communications_test'
      AND REFERENCED_TABLE_NAME = 'botnet_nodes_test'
    LIMIT 1
);

SET @drop_fk_sql = IF(@fk_name IS NOT NULL,
    CONCAT('ALTER TABLE botnet_communications_test DROP FOREIGN KEY ', @fk_name),
    'SELECT "No FK to drop for test"');
PREPARE stmt FROM @drop_fk_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

ALTER TABLE botnet_communications_test
ADD CONSTRAINT fk_node_test 
FOREIGN KEY (node_id) REFERENCES botnet_nodes_test(id) ON DELETE RESTRICT;

ALTER TABLE botnet_communications_test ADD INDEX idx_node_id (node_id);


-- ============================================================
-- Step 3: 验证修改结果
-- ============================================================
SELECT 
    '外键约束修改完成' AS status,
    TABLE_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    DELETE_RULE,
    UPDATE_RULE
FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS
WHERE TABLE_SCHEMA = 'botnet'
  AND TABLE_NAME LIKE 'botnet_communications_%'
ORDER BY TABLE_NAME;

-- ============================================================
-- Step 4: 优化建议（可选执行）
-- ============================================================
-- 如果通信记录表索引过多，可以删除冗余索引

-- 示例：删除冗余的复合索引（如果idx_unique_communication已存在）
-- ALTER TABLE botnet_communications_test DROP INDEX idx_composite;
-- 注意：只有当idx_composite (ip, communication_time) 和 
-- idx_unique_communication (ip, communication_time) 完全相同时才能删除

SELECT 
    '优化建议：检查并删除冗余索引' AS suggestion,
    TABLE_NAME,
    INDEX_NAME,
    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS columns
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = 'botnet'
  AND TABLE_NAME LIKE 'botnet_communications_%'
GROUP BY TABLE_NAME, INDEX_NAME
HAVING COUNT(*) > 1
ORDER BY TABLE_NAME, INDEX_NAME;
