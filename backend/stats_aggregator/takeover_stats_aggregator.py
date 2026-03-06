#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
接管节点统计数据聚合器
每分钟聚合一次所有botnet_nodes表的统计数据
"""

import pymysql
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG
from database.takeover_stats_schema import TAKEOVER_STATS_TABLE_SCHEMA, TAKEOVER_STATS_DETAIL_TABLE_SCHEMA

# 配置日志
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'takeover_stats_aggregator.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TakeoverStatsAggregator:
    def __init__(self):
        self.db_config = DB_CONFIG
        
    def get_connection(self):
        """获取数据库连接"""
        try:
            conn = pymysql.connect(**self.db_config)
            return conn
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def ensure_tables_exist(self):
        """确保统计表存在"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 创建统计表
            cursor.execute(TAKEOVER_STATS_TABLE_SCHEMA)
            cursor.execute(TAKEOVER_STATS_DETAIL_TABLE_SCHEMA)
            
            conn.commit()
            logger.info("统计表结构检查完成")
            
        except Exception as e:
            logger.error(f"创建统计表失败: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_botnet_types(self) -> List[str]:
        """获取所有僵尸网络类型"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 查询所有僵尸网络类型
            cursor.execute("SELECT name FROM botnet_types WHERE name IS NOT NULL")
            results = cursor.fetchall()
            
            botnet_types = [row[0] for row in results]
            logger.info(f"发现 {len(botnet_types)} 个僵尸网络类型: {botnet_types}")
            
            return botnet_types
            
        except Exception as e:
            logger.error(f"获取僵尸网络类型失败: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_botnet_table_stats(self, botnet_type: str) -> Dict:
        """获取单个僵尸网络表的统计数据"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            table_name = f"botnet_nodes_{botnet_type}"
            
            # 检查表是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (self.db_config['database'], table_name))
            
            if cursor.fetchone()[0] == 0:
                logger.warning(f"表 {table_name} 不存在")
                return {
                    'total_nodes': 0,
                    'total_domestic_nodes': 0,
                    'total_foreign_nodes': 0,
                    'monthly_total_nodes': 0,
                    'monthly_domestic_nodes': 0,
                    'monthly_foreign_nodes': 0,
                    'cleaned_total_nodes': 0,
                    'cleaned_domestic_nodes': 0,
                    'cleaned_foreign_nodes': 0,
                    'monthly_cleaned_total_nodes': 0,
                    'monthly_cleaned_domestic_nodes': 0,
                    'monthly_cleaned_foreign_nodes': 0,
                    'suppression_total_count': 20,  # 写死为20
                    'monthly_suppression_count': 20  # 写死为20
                }
            
            # 计算30天前的时间
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            # 统计总体数据
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_nodes,
                    SUM(CASE WHEN is_china = 1 THEN 1 ELSE 0 END) as total_domestic_nodes,
                    SUM(CASE WHEN is_china = 0 THEN 1 ELSE 0 END) as total_foreign_nodes
                FROM {table_name}
            """)
            total_stats = cursor.fetchone()
            
            # 统计近30天数据（status=active）
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as monthly_total_nodes,
                    SUM(CASE WHEN is_china = 1 THEN 1 ELSE 0 END) as monthly_domestic_nodes,
                    SUM(CASE WHEN is_china = 0 THEN 1 ELSE 0 END) as monthly_foreign_nodes
                FROM {table_name}
                WHERE created_time >= %s AND status = 'active'
            """, (thirty_days_ago,))
            monthly_stats = cursor.fetchone()
            
            # 统计已清除节点数据（status=cleaned）
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as cleaned_total_nodes,
                    SUM(CASE WHEN is_china = 1 THEN 1 ELSE 0 END) as cleaned_domestic_nodes,
                    SUM(CASE WHEN is_china = 0 THEN 1 ELSE 0 END) as cleaned_foreign_nodes
                FROM {table_name}
                WHERE status = 'cleaned'
            """)
            cleaned_stats = cursor.fetchone()
            
            # 统计近30天已清除节点数据（status=cleaned）
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as monthly_cleaned_total_nodes,
                    SUM(CASE WHEN is_china = 1 THEN 1 ELSE 0 END) as monthly_cleaned_domestic_nodes,
                    SUM(CASE WHEN is_china = 0 THEN 1 ELSE 0 END) as monthly_cleaned_foreign_nodes
                FROM {table_name}
                WHERE created_time >= %s AND status = 'cleaned'
            """, (thirty_days_ago,))
            monthly_cleaned_stats = cursor.fetchone()
            
            return {
                'total_nodes': total_stats[0] or 0,
                'total_domestic_nodes': total_stats[1] or 0,
                'total_foreign_nodes': total_stats[2] or 0,
                'monthly_total_nodes': monthly_stats[0] or 0,
                'monthly_domestic_nodes': monthly_stats[1] or 0,
                'monthly_foreign_nodes': monthly_stats[2] or 0,
                'cleaned_total_nodes': cleaned_stats[0] or 0,
                'cleaned_domestic_nodes': cleaned_stats[1] or 0,
                'cleaned_foreign_nodes': cleaned_stats[2] or 0,
                'monthly_cleaned_total_nodes': monthly_cleaned_stats[0] or 0,
                'monthly_cleaned_domestic_nodes': monthly_cleaned_stats[1] or 0,
                'monthly_cleaned_foreign_nodes': monthly_cleaned_stats[2] or 0,
                'suppression_total_count': 20,  # 写死为20
                'monthly_suppression_count': 20  # 写死为20
            }
            
        except Exception as e:
            logger.error(f"获取表 {botnet_type} 统计数据失败: {e}")
            return {
                'total_nodes': 0,
                'total_domestic_nodes': 0,
                'total_foreign_nodes': 0,
                'monthly_total_nodes': 0,
                'monthly_domestic_nodes': 0,
                'monthly_foreign_nodes': 0,
                'cleaned_total_nodes': 0,
                'cleaned_domestic_nodes': 0,
                'cleaned_foreign_nodes': 0,
                'monthly_cleaned_total_nodes': 0,
                'monthly_cleaned_domestic_nodes': 0,
                'monthly_cleaned_foreign_nodes': 0,
                'suppression_total_count': 20,  # 写死为20
                'monthly_suppression_count': 20  # 写死为20
            }
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def aggregate_all_stats(self) -> Dict:
        """聚合所有僵尸网络的统计数据"""
        botnet_types = self.get_botnet_types()
        
        # 总体统计
        total_stats = {
            'total_nodes': 0,
            'total_domestic_nodes': 0,
            'total_foreign_nodes': 0,
            'monthly_total_nodes': 0,
            'monthly_domestic_nodes': 0,
            'monthly_foreign_nodes': 0,
            'cleaned_total_nodes': 0,
            'cleaned_domestic_nodes': 0,
            'cleaned_foreign_nodes': 0,
            'monthly_cleaned_total_nodes': 0,
            'monthly_cleaned_domestic_nodes': 0,
            'monthly_cleaned_foreign_nodes': 0,
            'suppression_total_count': 0,
            'monthly_suppression_count': 0
        }
        
        # 详细统计（按类型）
        detail_stats = {}
        
        for botnet_type in botnet_types:
            stats = self.get_botnet_table_stats(botnet_type)
            detail_stats[botnet_type] = stats
            
            # 累加到总体统计
            for key in total_stats:
                total_stats[key] += stats[key]
        
        logger.info(f"聚合完成 - 总节点数: {total_stats['total_nodes']}, "
                   f"国内: {total_stats['total_domestic_nodes']}, "
                   f"国外: {total_stats['total_foreign_nodes']}")
        
        return {
            'total': total_stats,
            'detail': detail_stats
        }
    
    def save_stats_to_db(self, stats_data: Dict):
        """保存统计数据到数据库"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 保存总体统计数据
            total_stats = stats_data['total']
            cursor.execute("""
                INSERT INTO takeover_stats (
                    total_nodes, total_domestic_nodes, total_foreign_nodes,
                    monthly_total_nodes, monthly_domestic_nodes, monthly_foreign_nodes,
                    cleaned_total_nodes, cleaned_domestic_nodes, cleaned_foreign_nodes,
                    monthly_cleaned_total_nodes, monthly_cleaned_domestic_nodes, monthly_cleaned_foreign_nodes,
                    suppression_total_count, monthly_suppression_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                total_stats['total_nodes'],
                total_stats['total_domestic_nodes'],
                total_stats['total_foreign_nodes'],
                total_stats['monthly_total_nodes'],
                total_stats['monthly_domestic_nodes'],
                total_stats['monthly_foreign_nodes'],
                total_stats['cleaned_total_nodes'],
                total_stats['cleaned_domestic_nodes'],
                total_stats['cleaned_foreign_nodes'],
                total_stats['monthly_cleaned_total_nodes'],
                total_stats['monthly_cleaned_domestic_nodes'],
                total_stats['monthly_cleaned_foreign_nodes'],
                total_stats['suppression_total_count'],
                total_stats['monthly_suppression_count']
            ))
            
            # 保存详细统计数据
            for botnet_type, detail_stats in stats_data['detail'].items():
                cursor.execute("""
                    INSERT INTO takeover_stats_detail (
                        botnet_type, total_nodes, total_domestic_nodes, total_foreign_nodes,
                        monthly_total_nodes, monthly_domestic_nodes, monthly_foreign_nodes,
                        cleaned_total_nodes, cleaned_domestic_nodes, cleaned_foreign_nodes,
                        monthly_cleaned_total_nodes, monthly_cleaned_domestic_nodes, monthly_cleaned_foreign_nodes,
                        suppression_total_count, monthly_suppression_count
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    botnet_type,
                    detail_stats['total_nodes'],
                    detail_stats['total_domestic_nodes'],
                    detail_stats['total_foreign_nodes'],
                    detail_stats['monthly_total_nodes'],
                    detail_stats['monthly_domestic_nodes'],
                    detail_stats['monthly_foreign_nodes'],
                    detail_stats['cleaned_total_nodes'],
                    detail_stats['cleaned_domestic_nodes'],
                    detail_stats['cleaned_foreign_nodes'],
                    detail_stats['monthly_cleaned_total_nodes'],
                    detail_stats['monthly_cleaned_domestic_nodes'],
                    detail_stats['monthly_cleaned_foreign_nodes'],
                    detail_stats['suppression_total_count'],
                    detail_stats['monthly_suppression_count']
                ))
            
            conn.commit()
            logger.info("统计数据保存成功")
            
        except Exception as e:
            logger.error(f"保存统计数据失败: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def cleanup_old_data(self, days_to_keep: int = 7):
        """清理旧的统计数据，只保留最近N天的数据"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # 清理总体统计表
            cursor.execute("""
                DELETE FROM takeover_stats 
                WHERE created_at < %s
            """, (cutoff_date,))
            total_deleted = cursor.rowcount
            
            # 清理详细统计表
            cursor.execute("""
                DELETE FROM takeover_stats_detail 
                WHERE created_at < %s
            """, (cutoff_date,))
            detail_deleted = cursor.rowcount
            
            conn.commit()
            logger.info(f"清理完成 - 总体统计删除: {total_deleted}, 详细统计删除: {detail_deleted}")
            
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def run_once(self):
        """执行一次统计聚合"""
        try:
            logger.info("开始执行接管节点统计聚合")
            
            # 确保表存在
            self.ensure_tables_exist()
            
            # 聚合统计数据
            stats_data = self.aggregate_all_stats()
            
            # 保存到数据库
            self.save_stats_to_db(stats_data)
            
            # 清理旧数据（保留7天）
            self.cleanup_old_data(7)
            
            logger.info("接管节点统计聚合完成")
            
        except Exception as e:
            logger.error(f"统计聚合执行失败: {e}")
            raise
    
    def run_continuous(self, interval_seconds: int = 60):
        """持续运行，每隔指定秒数执行一次"""
        logger.info(f"开始持续运行，间隔 {interval_seconds} 秒")
        
        while True:
            try:
                self.run_once()
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                logger.info("收到中断信号，停止运行")
                break
            except Exception as e:
                logger.error(f"运行出错: {e}")
                time.sleep(interval_seconds)  # 出错后也要等待，避免频繁重试

def main():
    """主函数"""
    aggregator = TakeoverStatsAggregator()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # 执行一次
        aggregator.run_once()
    else:
        # 持续运行（每分钟一次）
        aggregator.run_continuous(60)

if __name__ == "__main__":
    main()
