#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建接管节点统计数据表
直接执行SQL创建表结构
"""

import pymysql
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 统计表SQL
TAKEOVER_STATS_SQL = """
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

# 详细统计表SQL
TAKEOVER_STATS_DETAIL_SQL = """
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

def create_tables():
    """创建统计表"""
    conn = None
    cursor = None
    try:
        logger.info("连接数据库...")
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        logger.info("创建 takeover_stats 表...")
        cursor.execute(TAKEOVER_STATS_SQL)
        logger.info("✓ takeover_stats 表创建成功")
        
        logger.info("创建 takeover_stats_detail 表...")
        cursor.execute(TAKEOVER_STATS_DETAIL_SQL)
        logger.info("✓ takeover_stats_detail 表创建成功")
        
        conn.commit()
        logger.info("✓ 所有表创建完成")
        
        return True
        
    except Exception as e:
        logger.error(f"创建表失败: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def verify_tables():
    """验证表是否创建成功"""
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查表是否存在
        tables = ['takeover_stats', 'takeover_stats_detail']
        for table in tables:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (DB_CONFIG['database'], table))
            
            if cursor.fetchone()[0] > 0:
                logger.info(f"✓ 表 {table} 存在")
            else:
                logger.error(f"✗ 表 {table} 不存在")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"验证表失败: {e}")
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("创建接管节点统计数据表")
    logger.info("=" * 50)
    
    # 创建表
    if not create_tables():
        logger.error("表创建失败")
        return False
    
    # 验证表
    if not verify_tables():
        logger.error("表验证失败")
        return False
    
    logger.info("=" * 50)
    logger.info("✓ 接管节点统计数据表创建完成")
    logger.info("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
