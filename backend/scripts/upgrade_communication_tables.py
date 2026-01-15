#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库升级脚本 - 为通信记录表添加唯一约束并优化索引

功能：
1. 为botnet_communications_{type}表添加唯一约束 (ip, communication_time)
2. 删除冗余索引，保留核心索引
3. 清理重复数据（可选）

警告：此脚本会修改生产数据库结构，请先备份数据库！
"""

import sys
import os
import pymysql
import logging
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG, get_enabled_botnet_types

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backup_reminder():
    """备份提醒"""
    print("=" * 80)
    print("⚠️  重要提醒：数据库结构升级")
    print("=" * 80)
    print("此脚本将修改以下内容：")
    print("1. 为通信记录表添加唯一约束 UNIQUE(ip, communication_time)")
    print("2. 删除冗余索引（idx_node_id, idx_ip, idx_received_at, idx_is_china）")
    print("3. 可选：清理重复数据")
    print()
    print("⚠️  请确保已经备份数据库！")
    print("   mysqldump -u root -p botnet > botnet_backup_$(date +%Y%m%d_%H%M%S).sql")
    print("=" * 80)
    print()
    
    response = input("是否已完成备份并继续？(yes/no): ").strip().lower()
    return response in ['yes', 'y']


def check_duplicates(conn, table_name):
    """检查重复数据"""
    cursor = conn.cursor()
    
    logger.info(f"[{table_name}] 检查重复数据...")
    
    cursor.execute(f"""
        SELECT ip, communication_time, COUNT(*) as count
        FROM {table_name}
        GROUP BY ip, communication_time
        HAVING count > 1
        LIMIT 10
    """)
    
    duplicates = cursor.fetchall()
    
    if duplicates:
        logger.warning(f"[{table_name}] 发现 {len(duplicates)} 组重复数据（显示前10组）：")
        for dup in duplicates:
            logger.warning(f"  IP: {dup[0]}, Time: {dup[1]}, Count: {dup[2]}")
        
        # 统计总重复数
        cursor.execute(f"""
            SELECT SUM(count - 1) as total_duplicates
            FROM (
                SELECT COUNT(*) as count
                FROM {table_name}
                GROUP BY ip, communication_time
                HAVING count > 1
            ) AS dups
        """)
        total_dups = cursor.fetchone()[0] or 0
        logger.warning(f"[{table_name}] 总共有 {total_dups} 条重复记录需要清理")
        
        return total_dups
    else:
        logger.info(f"[{table_name}] 没有发现重复数据")
        return 0


def clean_duplicates(conn, table_name):
    """清理重复数据（保留ID最小的记录）"""
    cursor = conn.cursor()
    
    logger.info(f"[{table_name}] 清理重复数据...")
    
    # 删除重复记录（保留id最小的）
    cursor.execute(f"""
        DELETE t1 FROM {table_name} t1
        INNER JOIN {table_name} t2
        WHERE t1.ip = t2.ip
          AND t1.communication_time = t2.communication_time
          AND t1.id > t2.id
    """)
    
    deleted_count = cursor.rowcount
    conn.commit()
    
    logger.info(f"[{table_name}] 已删除 {deleted_count} 条重复记录")
    return deleted_count


def upgrade_table(conn, botnet_type):
    """升级单个表"""
    table_name = f"botnet_communications_{botnet_type}"
    cursor = conn.cursor()
    
    try:
        # 检查表是否存在
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = '{table_name}'
        """)
        
        if cursor.fetchone()[0] == 0:
            logger.warning(f"[{botnet_type}] 表 {table_name} 不存在，跳过")
            return False
        
        logger.info(f"[{botnet_type}] 开始升级表 {table_name}")
        
        # 1. 检查重复数据
        dup_count = check_duplicates(conn, table_name)
        
        if dup_count > 0:
            response = input(f"发现 {dup_count} 条重复数据，是否清理？(yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                clean_duplicates(conn, table_name)
            else:
                logger.warning(f"[{botnet_type}] 跳过清理重复数据，无法添加唯一约束")
                return False
        
        # 2. 检查并添加唯一约束
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
              AND table_name = '{table_name}'
              AND index_name = 'idx_unique_communication'
        """)
        
        if cursor.fetchone()[0] == 0:
            logger.info(f"[{botnet_type}] 添加唯一约束...")
            cursor.execute(f"""
                ALTER TABLE {table_name}
                ADD UNIQUE KEY idx_unique_communication (ip, communication_time)
            """)
            logger.info(f"[{botnet_type}] ✓ 唯一约束已添加")
        else:
            logger.info(f"[{botnet_type}] 唯一约束已存在，跳过")
        
        # 3. 删除冗余索引
        redundant_indexes = ['idx_node_id', 'idx_ip', 'idx_received_at', 'idx_is_china', 'idx_composite']
        
        for index_name in redundant_indexes:
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                  AND table_name = '{table_name}'
                  AND index_name = '{index_name}'
            """)
            
            if cursor.fetchone()[0] > 0:
                logger.info(f"[{botnet_type}] 删除冗余索引 {index_name}...")
                cursor.execute(f"ALTER TABLE {table_name} DROP INDEX {index_name}")
                logger.info(f"[{botnet_type}] ✓ 索引已删除")
        
        conn.commit()
        logger.info(f"[{botnet_type}] ✓ 表升级完成")
        return True
        
    except Exception as e:
        logger.error(f"[{botnet_type}] 升级失败: {e}")
        conn.rollback()
        return False


def main():
    """主函数"""
    logger.info("数据库升级脚本启动")
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 备份提醒
    if not backup_reminder():
        logger.info("用户取消操作")
        return
    
    # 连接数据库
    try:
        conn = pymysql.connect(**DB_CONFIG)
        logger.info("数据库连接成功")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return
    
    try:
        # 获取启用的僵尸网络类型
        botnet_types = get_enabled_botnet_types()
        logger.info(f"将升级 {len(botnet_types)} 个僵尸网络类型的表")
        
        success_count = 0
        fail_count = 0
        
        for botnet_type in botnet_types:
            if upgrade_table(conn, botnet_type):
                success_count += 1
            else:
                fail_count += 1
        
        logger.info("=" * 80)
        logger.info(f"升级完成！成功: {success_count}, 失败: {fail_count}")
        logger.info(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
    finally:
        conn.close()
        logger.info("数据库连接已关闭")


if __name__ == '__main__':
    main()
