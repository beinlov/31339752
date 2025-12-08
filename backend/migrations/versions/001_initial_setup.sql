-- ============================================================
-- Migration: 001_initial_setup
-- Description: 初始化数据库基础结构和配置
-- Author: System
-- Date: 2024-12-08
-- ============================================================

-- 迁移前检查
SELECT '开始执行迁移 001: 初始化数据库...' as status;

-- ============================================================
-- 创建僵尸网络类型表
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
-- 插入初始僵尸网络类型
-- ============================================================

INSERT INTO botnet_types (name, display_name, description) VALUES
    ('ramnit', 'Ramnit', 'Ramnit 僵尸网络'),
    ('mozi', 'Mozi', 'Mozi 僵尸网络'),
    ('moobot', 'Moobot', 'Moobot 僵尸网络'),
    ('asruex', 'AsrueX', 'AsrueX 僵尸网络'),
    ('andromeda', 'Andromeda', 'Andromeda 僵尸网络'),
    ('leethozer', 'LeetHozer', 'LeetHozer 僵尸网络')
ON DUPLICATE KEY UPDATE 
    display_name = VALUES(display_name),
    description = VALUES(description);

-- ============================================================
-- 验证迁移结果
-- ============================================================

SELECT COUNT(*) as created_botnet_types 
FROM botnet_types;

SELECT '迁移 001 执行完成！' as status;

-- ============================================================
-- 回滚脚本（手动执行时使用）
-- ============================================================
-- DROP TABLE IF EXISTS botnet_types;
