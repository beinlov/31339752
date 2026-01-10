-- ============================================================
-- 僵尸网络接管集成平台 - 数据库初始化脚本
-- ============================================================

USE botnet;

-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 创建用户表
CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` varchar(20) DEFAULT '访客',
  `status` varchar(20) DEFAULT '离线',
  `last_login` datetime DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认管理员账户（密码: admin）
INSERT IGNORE INTO `users` (`username`, `password`, `role`, `status`) 
VALUES ('admin', '21232f297a57a5a743894a0e4a801fc3', '管理员', '在线');

-- 创建僵尸网络类型表
CREATE TABLE IF NOT EXISTS `botnet_types` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `display_name` varchar(100) NOT NULL,
  `description` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入僵尸网络类型
INSERT IGNORE INTO `botnet_types` (`name`, `display_name`, `description`) VALUES
('asruex', 'Asruex', 'Asruex僵尸网络'),
('mozi', 'Mozi', 'Mozi僵尸网络'),
('andromeda', 'Andromeda', 'Andromeda僵尸网络'),
('moobot', 'Moobot', 'Moobot僵尸网络'),
('ramnit', 'Ramnit', 'Ramnit僵尸网络'),
('leethozer', 'Leethozer', 'Leethozer僵尸网络');

-- 注意：botnet_nodes_* 表会由log_processor自动创建
-- 注意：china_botnet_* 和 global_botnet_* 表会由stats_aggregator自动创建

-- 创建用户事件日志表（如果需要）
CREATE TABLE IF NOT EXISTS `user_events` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `event_type` varchar(50) NOT NULL,
  `description` text,
  `ip_address` varchar(45) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_username` (`username`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建异常报告表（如果需要）
CREATE TABLE IF NOT EXISTS `anomaly_reports` (
  `id` int NOT NULL AUTO_INCREMENT,
  `botnet_type` varchar(50) NOT NULL,
  `anomaly_type` varchar(100) NOT NULL,
  `description` text,
  `status` varchar(20) DEFAULT 'pending',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_botnet_type` (`botnet_type`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 完成
SELECT 'Database initialization completed successfully!' AS message;


