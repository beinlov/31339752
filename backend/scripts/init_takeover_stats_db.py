#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
接管节点统计数据库初始化脚本
创建统计表并执行初始数据聚合
"""

import sys
import os
from pathlib import Path
import pymysql
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.database import DB_CONFIG
from database.takeover_stats_schema import TAKEOVER_STATS_TABLE_SCHEMA, TAKEOVER_STATS_DETAIL_TABLE_SCHEMA
from stats_aggregator.takeover_stats_aggregator import TakeoverStatsAggregator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """初始化数据库表结构"""
    conn = None
    cursor = None
    try:
        logger.info("开始初始化接管节点统计数据库...")
        
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 创建统计表
        logger.info("创建统计表...")
        cursor.execute(TAKEOVER_STATS_TABLE_SCHEMA)
        logger.info("✓ takeover_stats 表创建成功")
        
        cursor.execute(TAKEOVER_STATS_DETAIL_TABLE_SCHEMA)
        logger.info("✓ takeover_stats_detail 表创建成功")
        
        conn.commit()
        logger.info("数据库表结构初始化完成")
        
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def run_initial_aggregation():
    """执行初始数据聚合"""
    try:
        logger.info("开始执行初始数据聚合...")
        
        aggregator = TakeoverStatsAggregator()
        aggregator.run_once()
        
        logger.info("✓ 初始数据聚合完成")
        return True
        
    except Exception as e:
        logger.error(f"初始数据聚合失败: {e}")
        return False

def check_botnet_tables():
    """检查僵尸网络表是否存在"""
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查botnet_types表
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = 'botnet_types'
        """, (DB_CONFIG['database'],))
        
        if cursor.fetchone()[0] == 0:
            logger.warning("botnet_types 表不存在，需要先创建基础表结构")
            return False
        
        # 获取僵尸网络类型
        cursor.execute("SELECT name FROM botnet_types")
        botnet_types = [row[0] for row in cursor.fetchall()]
        
        if not botnet_types:
            logger.warning("botnet_types 表中没有数据")
            return False
        
        logger.info(f"发现 {len(botnet_types)} 个僵尸网络类型: {botnet_types}")
        
        # 检查对应的节点表
        existing_tables = []
        missing_tables = []
        
        for botnet_type in botnet_types:
            table_name = f"botnet_nodes_{botnet_type}"
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (DB_CONFIG['database'], table_name))
            
            if cursor.fetchone()[0] > 0:
                existing_tables.append(table_name)
            else:
                missing_tables.append(table_name)
        
        if existing_tables:
            logger.info(f"存在的节点表: {existing_tables}")
        
        if missing_tables:
            logger.warning(f"缺失的节点表: {missing_tables}")
        
        return len(existing_tables) > 0
        
    except Exception as e:
        logger.error(f"检查僵尸网络表失败: {e}")
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def verify_installation():
    """验证安装是否成功"""
    conn = None
    cursor = None
    try:
        logger.info("验证安装...")
        
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查统计表是否存在
        tables_to_check = ['takeover_stats', 'takeover_stats_detail']
        for table_name in tables_to_check:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (DB_CONFIG['database'], table_name))
            
            if cursor.fetchone()[0] == 0:
                logger.error(f"表 {table_name} 不存在")
                return False
            else:
                logger.info(f"✓ 表 {table_name} 存在")
        
        # 检查是否有初始数据
        cursor.execute("SELECT COUNT(*) FROM takeover_stats")
        stats_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM takeover_stats_detail")
        detail_count = cursor.fetchone()[0]
        
        logger.info(f"✓ takeover_stats 表有 {stats_count} 条记录")
        logger.info(f"✓ takeover_stats_detail 表有 {detail_count} 条记录")
        
        if stats_count > 0 and detail_count > 0:
            logger.info("✓ 验证成功，系统已正确初始化")
            return True
        else:
            logger.warning("表结构存在但缺少初始数据")
            return False
        
    except Exception as e:
        logger.error(f"验证失败: {e}")
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("接管节点统计系统初始化")
    logger.info("=" * 60)
    
    # 检查僵尸网络基础表
    if not check_botnet_tables():
        logger.error("缺少必要的僵尸网络基础表，请先确保系统基础数据完整")
        return False
    
    # 初始化数据库表结构
    if not init_database():
        logger.error("数据库初始化失败")
        return False
    
    # 执行初始数据聚合
    if not run_initial_aggregation():
        logger.error("初始数据聚合失败")
        return False
    
    # 验证安装
    if not verify_installation():
        logger.error("安装验证失败")
        return False
    
    logger.info("=" * 60)
    logger.info("✓ 接管节点统计系统初始化完成！")
    logger.info("=" * 60)
    logger.info("")
    logger.info("下一步操作:")
    logger.info("1. 启动定时聚合服务:")
    logger.info("   python scripts/start_takeover_stats_aggregator.py start")
    logger.info("")
    logger.info("2. 或设置Windows定时任务:")
    logger.info("   以管理员权限运行 scripts/setup_windows_task.bat")
    logger.info("")
    logger.info("3. 测试API接口:")
    logger.info("   访问 http://localhost:8000/api/takeover-stats/latest")
    logger.info("")
    logger.info("4. 查看API文档:")
    logger.info("   docs/TAKEOVER_STATS_API_GUIDE.md")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
