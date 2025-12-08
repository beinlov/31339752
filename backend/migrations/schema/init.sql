-- ============================================================
-- 初始数据库结构
-- 这是完整的数据库结构，用于全新部署
-- 如果是已有数据库，请使用 versions/ 中的增量迁移脚本
-- ============================================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS botnet DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE botnet;

-- ============================================================
-- 核心表：僵尸网络类型
-- ============================================================

CREATE TABLE IF NOT EXISTS botnet_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL COMMENT '僵尸网络类型名称',
    display_name VARCHAR(100) COMMENT '显示名称',
    description TEXT COMMENT '描述信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    status ENUM('active', 'inactive') DEFAULT 'active' COMMENT '状态',
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='僵尸网络类型表';

-- ============================================================
-- 注意：节点表、统计表是动态创建的
-- ============================================================
-- 
-- 每个僵尸网络类型会自动创建以下表：
-- 1. botnet_nodes_{type}      - 节点原始数据表
-- 2. china_botnet_{type}      - 中国地区统计表
-- 3. global_botnet_{type}     - 全球统计表
--
-- 这些表由代码动态创建，不在此初始化
-- 表结构参考：backend/router/botnet.py
-- ============================================================

-- ============================================================
-- 迁移管理表
-- ============================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    version VARCHAR(50) UNIQUE NOT NULL COMMENT '迁移版本号',
    description VARCHAR(255) COMMENT '迁移描述',
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '执行时间',
    execution_time_ms INT COMMENT '执行耗时(毫秒)',
    INDEX idx_version (version),
    INDEX idx_executed_at (executed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据库迁移记录表';

-- ============================================================
-- 用户表（如果有权限管理功能）
-- ============================================================

-- CREATE TABLE IF NOT EXISTS users (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     username VARCHAR(50) UNIQUE NOT NULL,
--     password_hash VARCHAR(255) NOT NULL,
--     role ENUM('admin', 'user') DEFAULT 'user',
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     INDEX idx_username (username)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 插入默认管理员（密码：admin，实际使用时应该加密）
-- INSERT INTO users (username, password_hash, role) 
-- VALUES ('admin', 'hashed_password_here', 'admin')
-- ON DUPLICATE KEY UPDATE username=username;

-- ============================================================
-- 初始化完成
-- ============================================================

SELECT 'Database initialization completed successfully!' as status;
