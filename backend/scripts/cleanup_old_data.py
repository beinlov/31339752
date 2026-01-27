#!/usr/bin/env python3
"""
自动清理旧数据脚本
保留指定天数的数据，删除更早的通信记录
"""
import pymysql
import logging
from datetime import datetime
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG, BOTNET_CONFIG

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
RETENTION_DAYS = 180  # 保留天数（默认180天）
BATCH_SIZE = 10000    # 每批删除数量（避免锁表）

def cleanup_communications(botnet_type: str, dry_run: bool = False):
    """清理指定僵尸网络的旧通信记录"""
    table_name = f"botnet_communications_{botnet_type}"
    
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute(f"""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = '{table_name}'
        """)
        if cursor.fetchone()[0] == 0:
            logger.info(f"[{botnet_type}] 表 {table_name} 不存在，跳过")
            return
        
        # 1. 检查要删除的记录数
        cursor.execute(f"""
            SELECT COUNT(*) FROM {table_name}
            WHERE communication_time < DATE_SUB(NOW(), INTERVAL {RETENTION_DAYS} DAY)
        """)
        total_to_delete = cursor.fetchone()[0]
        
        if total_to_delete == 0:
            logger.info(f"[{botnet_type}] 没有需要清理的数据")
            return
        
        logger.info(f"[{botnet_type}] 发现 {total_to_delete} 条需要清理的记录")
        
        if dry_run:
            logger.info(f"[{botnet_type}] 试运行模式，不执行删除")
            return
        
        # 2. 分批删除
        deleted_total = 0
        while True:
            cursor.execute(f"""
                DELETE FROM {table_name}
                WHERE communication_time < DATE_SUB(NOW(), INTERVAL {RETENTION_DAYS} DAY)
                LIMIT {BATCH_SIZE}
            """)
            deleted = cursor.rowcount
            conn.commit()
            
            if deleted == 0:
                break
            
            deleted_total += deleted
            logger.info(f"[{botnet_type}] 已删除 {deleted_total}/{total_to_delete} 条记录 ({deleted_total*100/total_to_delete:.1f}%)")
            
        logger.info(f"[{botnet_type}] 清理完成，共删除 {deleted_total} 条记录")
        
        # 3. 优化表（可选，释放空间）
        if deleted_total > 0:
            logger.info(f"[{botnet_type}] 优化表...")
            cursor.execute(f"OPTIMIZE TABLE {table_name}")
            logger.info(f"[{botnet_type}] 表优化完成")
        
    except Exception as e:
        logger.error(f"[{botnet_type}] 清理失败: {e}", exc_info=True)
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='清理僵尸网络旧数据')
    parser.add_argument('--dry-run', action='store_true', help='试运行模式（不实际删除）')
    parser.add_argument('--days', type=int, default=180, help='保留天数（默认180天）')
    parser.add_argument('--botnet', type=str, help='指定僵尸网络类型（默认全部）')
    args = parser.parse_args()
    
    global RETENTION_DAYS
    RETENTION_DAYS = args.days
    
    logger.info(f"========== 数据清理开始 ==========")
    logger.info(f"保留期: {RETENTION_DAYS}天")
    logger.info(f"模式: {'试运行' if args.dry_run else '正式清理'}")
    
    # 遍历所有僵尸网络类型
    botnet_types = [args.botnet] if args.botnet else BOTNET_CONFIG.keys()
    
    for botnet_type in botnet_types:
        if botnet_type not in BOTNET_CONFIG:
            logger.warning(f"未知的僵尸网络类型: {botnet_type}")
            continue
            
        if not BOTNET_CONFIG[botnet_type].get('enabled', True):
            logger.info(f"[{botnet_type}] 未启用，跳过")
            continue
        
        logger.info(f"\n处理 {botnet_type}...")
        cleanup_communications(botnet_type, dry_run=args.dry_run)
    
    logger.info(f"\n========== 数据清理完成 ==========")

if __name__ == '__main__':
    main()
