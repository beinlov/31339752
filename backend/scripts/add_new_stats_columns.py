#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为接管节点统计表添加新的统计字段
包括已清除节点统计和抑制阻断策略统计
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

# 添加新字段的SQL - 分别执行每个字段
ADD_COLUMNS_SQL = [
    # 总体统计表新增字段
    "ALTER TABLE takeover_stats ADD COLUMN cleaned_total_nodes INT NOT NULL DEFAULT 0 COMMENT '已清除节点总数'",
    "ALTER TABLE takeover_stats ADD COLUMN cleaned_domestic_nodes INT NOT NULL DEFAULT 0 COMMENT '已清除国内节点总数'",
    "ALTER TABLE takeover_stats ADD COLUMN cleaned_foreign_nodes INT NOT NULL DEFAULT 0 COMMENT '已清除国外节点总数'",
    "ALTER TABLE takeover_stats ADD COLUMN monthly_cleaned_total_nodes INT NOT NULL DEFAULT 0 COMMENT '近一个月清除节点总数'",
    "ALTER TABLE takeover_stats ADD COLUMN monthly_cleaned_domestic_nodes INT NOT NULL DEFAULT 0 COMMENT '近一个月清除国内节点数'",
    "ALTER TABLE takeover_stats ADD COLUMN monthly_cleaned_foreign_nodes INT NOT NULL DEFAULT 0 COMMENT '近一个月清除国外节点数'",
    "ALTER TABLE takeover_stats ADD COLUMN suppression_total_count INT NOT NULL DEFAULT 0 COMMENT '已使用抑制阻断策略总次数'",
    "ALTER TABLE takeover_stats ADD COLUMN monthly_suppression_count INT NOT NULL DEFAULT 0 COMMENT '近一个月使用抑制阻断策略次数'",
    
    # 详细统计表新增字段
    "ALTER TABLE takeover_stats_detail ADD COLUMN cleaned_total_nodes INT NOT NULL DEFAULT 0 COMMENT '该类型已清除节点总数'",
    "ALTER TABLE takeover_stats_detail ADD COLUMN cleaned_domestic_nodes INT NOT NULL DEFAULT 0 COMMENT '该类型已清除国内节点总数'",
    "ALTER TABLE takeover_stats_detail ADD COLUMN cleaned_foreign_nodes INT NOT NULL DEFAULT 0 COMMENT '该类型已清除国外节点总数'",
    "ALTER TABLE takeover_stats_detail ADD COLUMN monthly_cleaned_total_nodes INT NOT NULL DEFAULT 0 COMMENT '该类型近一个月清除节点总数'",
    "ALTER TABLE takeover_stats_detail ADD COLUMN monthly_cleaned_domestic_nodes INT NOT NULL DEFAULT 0 COMMENT '该类型近一个月清除国内节点数'",
    "ALTER TABLE takeover_stats_detail ADD COLUMN monthly_cleaned_foreign_nodes INT NOT NULL DEFAULT 0 COMMENT '该类型近一个月清除国外节点数'",
    "ALTER TABLE takeover_stats_detail ADD COLUMN suppression_total_count INT NOT NULL DEFAULT 0 COMMENT '该类型已使用抑制阻断策略总次数'",
    "ALTER TABLE takeover_stats_detail ADD COLUMN monthly_suppression_count INT NOT NULL DEFAULT 0 COMMENT '该类型近一个月使用抑制阻断策略次数'"
]

def add_new_columns():
    """添加新的统计字段"""
    conn = None
    cursor = None
    try:
        logger.info("连接数据库...")
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        for i, sql in enumerate(ADD_COLUMNS_SQL, 1):
            logger.info(f"执行第 {i} 个ALTER语句...")
            try:
                cursor.execute(sql)
                logger.info(f"✓ 第 {i} 个ALTER语句执行成功")
            except pymysql.Error as e:
                if "Duplicate column name" in str(e):
                    logger.info(f"✓ 第 {i} 个ALTER语句 - 字段已存在，跳过")
                else:
                    raise e
        
        conn.commit()
        logger.info("✓ 所有新字段添加完成")
        
        return True
        
    except Exception as e:
        logger.error(f"添加新字段失败: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def verify_new_columns():
    """验证新字段是否添加成功"""
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查总体统计表的新字段
        cursor.execute("DESCRIBE takeover_stats")
        columns = [row[0] for row in cursor.fetchall()]
        
        expected_columns = [
            'cleaned_total_nodes', 'cleaned_domestic_nodes', 'cleaned_foreign_nodes',
            'monthly_cleaned_total_nodes', 'monthly_cleaned_domestic_nodes', 'monthly_cleaned_foreign_nodes',
            'suppression_total_count', 'monthly_suppression_count'
        ]
        
        missing_columns = []
        for col in expected_columns:
            if col in columns:
                logger.info(f"✓ takeover_stats.{col} 存在")
            else:
                missing_columns.append(col)
                logger.error(f"✗ takeover_stats.{col} 不存在")
        
        # 检查详细统计表的新字段
        cursor.execute("DESCRIBE takeover_stats_detail")
        detail_columns = [row[0] for row in cursor.fetchall()]
        
        detail_missing_columns = []
        for col in expected_columns:
            if col in detail_columns:
                logger.info(f"✓ takeover_stats_detail.{col} 存在")
            else:
                detail_missing_columns.append(col)
                logger.error(f"✗ takeover_stats_detail.{col} 不存在")
        
        return len(missing_columns) == 0 and len(detail_missing_columns) == 0
        
    except Exception as e:
        logger.error(f"验证新字段失败: {e}")
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("为接管节点统计表添加新的统计字段")
    logger.info("=" * 60)
    
    # 添加新字段
    if not add_new_columns():
        logger.error("添加新字段失败")
        return False
    
    # 验证新字段
    if not verify_new_columns():
        logger.error("验证新字段失败")
        return False
    
    logger.info("=" * 60)
    logger.info("✓ 新统计字段添加完成")
    logger.info("=" * 60)
    logger.info("")
    logger.info("新增字段包括:")
    logger.info("- 已清除节点统计 (cleaned_*)")
    logger.info("- 近一个月清除节点统计 (monthly_cleaned_*)")
    logger.info("- 抑制阻断策略统计 (suppression_*)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
