# 接管节点统计数据表结构定义

TAKEOVER_STATS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS takeover_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- 总体统计数据
    total_nodes INT NOT NULL DEFAULT 0 COMMENT '已接管节点总数',
    total_domestic_nodes INT NOT NULL DEFAULT 0 COMMENT '已接管国内节点总数',
    total_foreign_nodes INT NOT NULL DEFAULT 0 COMMENT '已接管国外节点总数',
    
    -- 近30天统计数据
    monthly_total_nodes INT NOT NULL DEFAULT 0 COMMENT '近一个月接管节点总数',
    monthly_domestic_nodes INT NOT NULL DEFAULT 0 COMMENT '近一个月接管国内节点数',
    monthly_foreign_nodes INT NOT NULL DEFAULT 0 COMMENT '近一个月接管国外节点数',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '统计时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='接管节点统计数据表';
"""

# 详细统计表（按僵尸网络类型分类）
TAKEOVER_STATS_DETAIL_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS takeover_stats_detail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- 僵尸网络信息
    botnet_type VARCHAR(50) NOT NULL COMMENT '僵尸网络类型',
    
    -- 总体统计数据
    total_nodes INT NOT NULL DEFAULT 0 COMMENT '该类型已接管节点总数',
    total_domestic_nodes INT NOT NULL DEFAULT 0 COMMENT '该类型已接管国内节点总数',
    total_foreign_nodes INT NOT NULL DEFAULT 0 COMMENT '该类型已接管国外节点总数',
    
    -- 近30天统计数据
    monthly_total_nodes INT NOT NULL DEFAULT 0 COMMENT '该类型近一个月接管节点总数',
    monthly_domestic_nodes INT NOT NULL DEFAULT 0 COMMENT '该类型近一个月接管国内节点数',
    monthly_foreign_nodes INT NOT NULL DEFAULT 0 COMMENT '该类型近一个月接管国外节点数',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '统计时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_botnet_type (botnet_type),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at),
    UNIQUE KEY unique_botnet_time (botnet_type, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='接管节点详细统计数据表（按僵尸网络类型）';
"""
