#!/usr/bin/env python3
"""
更新所有僵尸网络的active_num和cleaned_num统计
基于botnet_nodes_*表中的status字段重新计算统计数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from pymysql.cursors import DictCursor
import logging
from config import DB_CONFIG

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_statistics_for_botnet(botnet_type):
    """为指定的僵尸网络类型更新统计数据"""
    conn = None
    cursor = None
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        node_table = f"botnet_nodes_{botnet_type}"
        china_table = f"china_botnet_{botnet_type}"
        global_table = f"global_botnet_{botnet_type}"
        
        logger.info(f"开始更新 {botnet_type} 的统计数据...")
        
        # 检查节点表是否存在
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], node_table))
        
        if cursor.fetchone()['count'] == 0:
            logger.warning(f"节点表 {node_table} 不存在，跳过")
            return False
        
        # 检查节点表是否有数据
        cursor.execute(f"SELECT COUNT(*) as count FROM {node_table}")
        node_count = cursor.fetchone()['count']
        
        if node_count == 0:
            logger.info(f"节点表 {node_table} 为空，跳过")
            return False
        
        logger.info(f"节点表 {node_table} 共有 {node_count} 条记录")
        
        # 1. 更新中国统计表
        logger.info(f"更新中国统计表 {china_table}...")
        
        # 清空现有数据
        cursor.execute(f"DELETE FROM {china_table}")
        logger.info(f"清空了 {china_table} 表")
        
        # 重新聚合中国数据
        cursor.execute(f"""
            INSERT INTO {china_table} (province, municipality, infected_num, active_num, cleaned_num, created_at, updated_at)
            SELECT 
                t.province,
                t.municipality,
                COUNT(DISTINCT t.ip) as infected_num,
                COUNT(DISTINCT CASE WHEN t.status = 'active' THEN t.ip END) as active_num,
                COUNT(DISTINCT CASE WHEN t.status = 'cleaned' THEN t.ip END) as cleaned_num,
                MIN(t.created_time) as created_at,
                MAX(t.updated_at) as updated_at
            FROM (
                SELECT 
                    -- 标准化省份名称
                    CASE
                        WHEN province IN ('内蒙古自治区', '内蒙古壮族自治区') THEN '内蒙古'
                        WHEN province IN ('广西自治区', '广西壮族自治区') THEN '广西'
                        WHEN province = '西藏自治区' THEN '西藏'
                        WHEN province IN ('宁夏自治区', '宁夏回族自治区') THEN '宁夏'
                        WHEN province IN ('新疆自治区', '新疆维吾尔自治区') THEN '新疆'
                        ELSE COALESCE(
                            TRIM(TRAILING '省' FROM 
                            TRIM(TRAILING '市' FROM province)),
                            '未知'
                        )
                    END as province,
                    COALESCE(
                        TRIM(TRAILING '市' FROM city),
                        '未知'
                    ) as municipality,
                    ip,
                    status,
                    created_time,
                    updated_at
                FROM {node_table}
                WHERE country = '中国'
            ) AS t
            GROUP BY t.province, t.municipality
        """)
        china_rows = cursor.rowcount
        logger.info(f"插入了 {china_rows} 条中国统计记录")
        
        # 2. 更新全球统计表
        logger.info(f"更新全球统计表 {global_table}...")
        
        # 清空现有数据
        cursor.execute(f"DELETE FROM {global_table}")
        logger.info(f"清空了 {global_table} 表")
        
        # 重新聚合全球数据
        cursor.execute(f"""
            INSERT INTO {global_table} (country, infected_num, active_num, cleaned_num, created_at, updated_at)
            SELECT 
                CASE
                    WHEN country = '中国台湾' THEN '台湾'
                    WHEN country = '中国香港' THEN '香港'
                    WHEN country = '中国澳门' THEN '澳门'
                    WHEN country IS NOT NULL THEN country
                    ELSE '未知'
                END as country,
                COUNT(DISTINCT ip) as infected_num,
                COUNT(DISTINCT CASE WHEN status = 'active' THEN ip END) as active_num,
                COUNT(DISTINCT CASE WHEN status = 'cleaned' THEN ip END) as cleaned_num,
                MIN(created_time) as created_at,
                MAX(updated_at) as updated_at
            FROM {node_table}
            GROUP BY 1
        """)
        global_rows = cursor.rowcount
        logger.info(f"插入了 {global_rows} 条全球统计记录")
        
        conn.commit()
        
        # 验证结果
        cursor.execute(f"""
            SELECT 
                SUM(infected_num) as total_infected,
                SUM(active_num) as total_active,
                SUM(cleaned_num) as total_cleaned
            FROM {china_table}
        """)
        china_stats = cursor.fetchone()
        
        cursor.execute(f"""
            SELECT 
                SUM(infected_num) as total_infected,
                SUM(active_num) as total_active,
                SUM(cleaned_num) as total_cleaned
            FROM {global_table}
        """)
        global_stats = cursor.fetchone()
        
        logger.info(f"[{botnet_type}] 统计完成:")
        logger.info(f"  中国: 感染 {china_stats['total_infected']}, 活跃 {china_stats['total_active']}, 已清理 {china_stats['total_cleaned']}")
        logger.info(f"  全球: 感染 {global_stats['total_infected']}, 活跃 {global_stats['total_active']}, 已清理 {global_stats['total_cleaned']}")
        
        return True
        
    except Exception as e:
        logger.error(f"更新 {botnet_type} 统计数据失败: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """主函数：更新所有僵尸网络的统计数据"""
    conn = None
    cursor = None
    
    try:
        # 获取所有僵尸网络类型
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        cursor.execute("SELECT name FROM botnet_types ORDER BY created_at")
        botnet_types = [row['name'] for row in cursor.fetchall()]
        
        logger.info(f"找到 {len(botnet_types)} 个僵尸网络类型: {botnet_types}")
        
        success_count = 0
        for botnet_type in botnet_types:
            if update_statistics_for_botnet(botnet_type):
                success_count += 1
        
        logger.info(f"统计更新完成: {success_count}/{len(botnet_types)} 个僵尸网络类型成功更新")
        
    except Exception as e:
        logger.error(f"获取僵尸网络类型失败: {e}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
