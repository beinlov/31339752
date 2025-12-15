-- ================================================================
-- 为僵尸网络节点表添加唯一索引
-- 目的：从数据库层面防止IP重复插入，根治数据重复问题
-- 
-- 重要提示：
-- 1. 执行前必须先去重数据（运行 deduplicate_nodes.py --execute）
-- 2. 如果表中已有重复数据，添加索引会失败
-- 3. 建议在低峰期执行，避免影响服务
-- 4. 建议先备份数据库
-- ================================================================

USE botnet_monitor;

-- ----------------------------------------------------------------
-- 检查是否已存在唯一索引（可选）
-- ----------------------------------------------------------------

SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    NON_UNIQUE
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'botnet_monitor'
  AND TABLE_NAME LIKE 'botnet_nodes_%'
  AND COLUMN_NAME = 'ip'
ORDER BY TABLE_NAME;

-- 如果上面的查询显示已存在 NON_UNIQUE=0 的索引，说明已经有唯一索引了

-- ----------------------------------------------------------------
-- 为每个僵尸网络表添加IP唯一索引
-- ----------------------------------------------------------------

-- 1. ramnit（主要问题僵尸网络）
ALTER TABLE botnet_nodes_ramnit 
ADD UNIQUE INDEX idx_unique_ip (ip);

-- 2. asruex
ALTER TABLE botnet_nodes_asruex 
ADD UNIQUE INDEX idx_unique_ip (ip);

-- 3. mozi
ALTER TABLE botnet_nodes_mozi 
ADD UNIQUE INDEX idx_unique_ip (ip);

-- 4. andromeda
ALTER TABLE botnet_nodes_andromeda 
ADD UNIQUE INDEX idx_unique_ip (ip);

-- 5. moobot
ALTER TABLE botnet_nodes_moobot 
ADD UNIQUE INDEX idx_unique_ip (ip);

-- 6. leethozer
ALTER TABLE botnet_nodes_leethozer 
ADD UNIQUE INDEX idx_unique_ip (ip);

-- ----------------------------------------------------------------
-- 验证唯一索引是否创建成功
-- ----------------------------------------------------------------

SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    NON_UNIQUE,
    INDEX_TYPE
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'botnet_monitor'
  AND TABLE_NAME LIKE 'botnet_nodes_%'
  AND COLUMN_NAME = 'ip'
ORDER BY TABLE_NAME;

-- 期望结果：
-- - INDEX_NAME = 'idx_unique_ip'
-- - NON_UNIQUE = 0（表示唯一索引）
-- - INDEX_TYPE = 'BTREE'

-- ----------------------------------------------------------------
-- 测试唯一索引是否生效
-- ----------------------------------------------------------------

-- 测试重复插入是否会自动更新（应该成功）
INSERT INTO botnet_nodes_ramnit 
(ip, longitude, latitude, country, province, city, continent, isp, asn, status, active_time, is_china, created_time, updated_at)
VALUES 
('999.999.999.999', 0, 0, 'Test', 'Test', 'Test', 'Test', 'Test', 'Test', 'active', NOW(), 0, NOW(), NOW())
ON DUPLICATE KEY UPDATE
    country = VALUES(country),
    updated_at = NOW();

-- 再次插入相同IP（应该更新而不是插入新记录）
INSERT INTO botnet_nodes_ramnit 
(ip, longitude, latitude, country, province, city, continent, isp, asn, status, active_time, is_china, created_time, updated_at)
VALUES 
('999.999.999.999', 0, 0, 'Test2', 'Test2', 'Test2', 'Test2', 'Test2', 'Test2', 'active', NOW(), 0, NOW(), NOW())
ON DUPLICATE KEY UPDATE
    country = VALUES(country),
    updated_at = NOW();

-- 检查是否只有一条记录
SELECT COUNT(*) as count, ip FROM botnet_nodes_ramnit WHERE ip = '999.999.999.999' GROUP BY ip;
-- 期望结果：count = 1（只有一条记录）

-- 清理测试数据
DELETE FROM botnet_nodes_ramnit WHERE ip = '999.999.999.999';

-- ----------------------------------------------------------------
-- 性能优化建议（可选）
-- ----------------------------------------------------------------

-- 如果表数据量很大，可以考虑：
-- 1. 在创建索引时使用 ALGORITHM=INPLACE, LOCK=NONE（MySQL 5.6+）
-- ALTER TABLE botnet_nodes_ramnit 
-- ADD UNIQUE INDEX idx_unique_ip (ip)
-- ALGORITHM=INPLACE, LOCK=NONE;

-- 2. 查看索引大小
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    ROUND(SUM(stat_value * @@innodb_page_size) / 1024 / 1024, 2) AS size_mb
FROM mysql.innodb_index_stats
WHERE database_name = 'botnet_monitor'
  AND table_name LIKE 'botnet_nodes_%'
  AND index_name = 'idx_unique_ip'
GROUP BY TABLE_NAME, INDEX_NAME;

-- ----------------------------------------------------------------
-- 故障排查
-- ----------------------------------------------------------------

-- 如果添加索引失败，检查重复数据：
-- SELECT ip, COUNT(*) as count 
-- FROM botnet_nodes_ramnit 
-- GROUP BY ip 
-- HAVING count > 1 
-- ORDER BY count DESC 
-- LIMIT 10;

-- 如果有重复，先去重：
-- cd d:\workspace\botnet\backend\scripts
-- python deduplicate_nodes.py --execute

-- ----------------------------------------------------------------
-- 完成
-- ================================================================

SELECT '✅ 唯一索引添加完成！' AS status;
SELECT '⚠️  请重新运行聚合器：python rebuild_aggregation.py' AS reminder;
