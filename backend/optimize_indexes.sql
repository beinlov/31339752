-- 数据库索引优化脚本
-- 用途：提升查询性能，减少锁等待
-- 使用方法：mysql -u root -p botnet < optimize_indexes.sql

USE botnet;

-- ============================================================
-- 1. 检查现有索引
-- ============================================================
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS COLUMNS
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'botnet'
    AND TABLE_NAME LIKE 'botnet_%'
GROUP BY TABLE_NAME, INDEX_NAME
ORDER BY TABLE_NAME, INDEX_NAME;

-- ============================================================
-- 2. 为各僵尸网络类型添加复合索引
-- ============================================================

-- Test僵尸网络
-- 节点表复合索引（如果已存在会显示警告，但不影响执行）
CREATE INDEX idx_ip_created_test 
    ON botnet_nodes_test(ip, created_time);

CREATE INDEX idx_location_china_test 
    ON botnet_nodes_test(country, province, city, is_china);

-- 通信记录表复合索引
CREATE INDEX idx_ip_comm_time_test 
    ON botnet_communications_test(ip, communication_time);

-- Ramnit僵尸网络（如果存在）
CREATE INDEX idx_ip_created_ramnit 
    ON botnet_nodes_ramnit(ip, created_time);

CREATE INDEX idx_location_china_ramnit 
    ON botnet_nodes_ramnit(country, province, city, is_china);

CREATE INDEX idx_ip_comm_time_ramnit 
    ON botnet_communications_ramnit(ip, communication_time);

-- 如果有其他僵尸网络类型，请仿照上述格式添加

-- ============================================================
-- 3. 优化MySQL配置（显示当前值）
-- ============================================================
SELECT '=== 当前MySQL配置 ===' AS '';

SELECT 'max_connections' AS Variable, @@max_connections AS Value
UNION ALL
SELECT 'innodb_buffer_pool_size', 
    CONCAT(ROUND(@@innodb_buffer_pool_size / 1024 / 1024 / 1024, 2), ' GB')
UNION ALL
SELECT 'innodb_lock_wait_timeout', @@innodb_lock_wait_timeout
UNION ALL
SELECT 'innodb_flush_log_at_trx_commit', @@innodb_flush_log_at_trx_commit
UNION ALL
SELECT 'query_cache_size', 
    CONCAT(ROUND(@@query_cache_size / 1024 / 1024, 2), ' MB');

-- ============================================================
-- 4. 检查表统计信息
-- ============================================================
SELECT '=== 表大小统计 ===' AS '';

SELECT 
    TABLE_NAME,
    ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) AS 'Size_MB',
    TABLE_ROWS,
    ROUND(DATA_LENGTH / TABLE_ROWS, 2) AS 'Avg_Row_Length'
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'botnet'
    AND TABLE_NAME LIKE 'botnet_%'
ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC;

-- ============================================================
-- 5. 分析表（更新统计信息）
-- ============================================================
SELECT '=== 正在分析表... ===' AS '';

ANALYZE TABLE botnet_nodes_test;
ANALYZE TABLE botnet_communications_test;

-- 如果有ramnit表
-- ANALYZE TABLE botnet_nodes_ramnit;
-- ANALYZE TABLE botnet_communications_ramnit;

-- ============================================================
-- 6. 优化表（整理碎片）
-- ============================================================
SELECT '=== 正在优化表... ===' AS '';

OPTIMIZE TABLE botnet_nodes_test;
OPTIMIZE TABLE botnet_communications_test;

-- 如果有ramnit表
-- OPTIMIZE TABLE botnet_nodes_ramnit;
-- OPTIMIZE TABLE botnet_communications_ramnit;

-- ============================================================
-- 完成
-- ============================================================
SELECT '=== 优化完成！ ===' AS '';
SELECT '建议重启后端服务以应用所有优化。' AS '';
