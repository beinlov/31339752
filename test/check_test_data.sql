-- 检查test僵尸网络的数据存储位置
-- 使用方法：mysql -u root -p botnet < check_test_data.sql

USE botnet;

-- 1. 检查test通信记录表是否存在
SELECT '=== 1. 检查表是否存在 ===' as '';
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    CREATE_TIME,
    UPDATE_TIME,
    DATA_LENGTH,
    INDEX_LENGTH
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'botnet' 
  AND TABLE_NAME LIKE '%test%'
ORDER BY TABLE_NAME;

-- 2. 检查botnet_communications_test表的最新数据
SELECT '\n=== 2. 检查最新通信记录 (最近10条) ===' as '';
SELECT 
    id,
    ip,
    communication_time,
    received_at,
    country,
    province,
    city,
    event_type,
    is_china
FROM botnet_communications_test
ORDER BY id DESC
LIMIT 10;

-- 3. 统计最近1小时的数据量
SELECT '\n=== 3. 最近1小时的数据量 ===' as '';
SELECT 
    COUNT(*) as total_count,
    COUNT(DISTINCT ip) as unique_ips,
    MIN(received_at) as earliest_time,
    MAX(received_at) as latest_time
FROM botnet_communications_test
WHERE received_at > NOW() - INTERVAL 1 HOUR;

-- 4. 统计今天的数据量
SELECT '\n=== 4. 今天的数据量 ===' as '';
SELECT 
    COUNT(*) as total_count,
    COUNT(DISTINCT ip) as unique_ips,
    MIN(received_at) as earliest_time,
    MAX(received_at) as latest_time
FROM botnet_communications_test
WHERE DATE(received_at) = CURDATE();

-- 5. 检查botnet_nodes_test表
SELECT '\n=== 5. 检查节点表最新数据 ===' as '';
SELECT 
    id,
    ip,
    first_seen,
    last_seen,
    total_communications,
    country,
    province,
    city
FROM botnet_nodes_test
ORDER BY last_seen DESC
LIMIT 10;

-- 6. 按时间段统计数据分布
SELECT '\n=== 6. 按小时统计数据分布 ===' as '';
SELECT 
    DATE_FORMAT(received_at, '%Y-%m-%d %H:00') as hour,
    COUNT(*) as count,
    COUNT(DISTINCT ip) as unique_ips
FROM botnet_communications_test
WHERE received_at > NOW() - INTERVAL 24 HOUR
GROUP BY DATE_FORMAT(received_at, '%Y-%m-%d %H:00')
ORDER BY hour DESC
LIMIT 24;

-- 7. 检查所有僵尸网络类型的通信记录表
SELECT '\n=== 7. 所有僵尸网络通信表的记录数 ===' as '';
SELECT 
    'asruex' as botnet_type,
    COUNT(*) as total_records,
    MAX(received_at) as last_update
FROM botnet_communications_asruex
UNION ALL
SELECT 
    'mozi' as botnet_type,
    COUNT(*) as total_records,
    MAX(received_at) as last_update
FROM botnet_communications_mozi
UNION ALL
SELECT 
    'andromeda' as botnet_type,
    COUNT(*) as total_records,
    MAX(received_at) as last_update
FROM botnet_communications_andromeda
UNION ALL
SELECT 
    'moobot' as botnet_type,
    COUNT(*) as total_records,
    MAX(received_at) as last_update
FROM botnet_communications_moobot
UNION ALL
SELECT 
    'ramnit' as botnet_type,
    COUNT(*) as total_records,
    MAX(received_at) as last_update
FROM botnet_communications_ramnit
UNION ALL
SELECT 
    'leethozer' as botnet_type,
    COUNT(*) as total_records,
    MAX(received_at) as last_update
FROM botnet_communications_leethozer
UNION ALL
SELECT 
    'test' as botnet_type,
    COUNT(*) as total_records,
    MAX(received_at) as last_update
FROM botnet_communications_test
ORDER BY botnet_type;

-- 8. 检查表结构
SELECT '\n=== 8. botnet_communications_test 表结构 ===' as '';
DESCRIBE botnet_communications_test;
