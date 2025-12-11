"""
增量聚合器
只聚合新增或更新的数据，避免重复处理
"""
import pymysql
import sys
import os
import time
import logging
from datetime import datetime, timedelta

# 添加父目录到路径以便导入config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DB_CONFIG

logger = logging.getLogger(__name__)


class IncrementalStatsAggregator:
    """增量统计数据聚合器"""
    
    BOTNET_TYPES = ['asruex', 'mozi', 'andromeda', 'moobot', 'ramnit', 'leethozer']
    
    def __init__(self, db_config):
        self.db_config = db_config
        
    def get_last_aggregation_time(self, botnet_type):
        """获取上次聚合时间"""
        try:
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 从聚合状态表获取上次聚合时间
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aggregation_status (
                    botnet_type VARCHAR(50) PRIMARY KEY,
                    last_aggregated_at TIMESTAMP NULL,
                    last_max_updated_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            cursor.execute("""
                SELECT last_max_updated_at FROM aggregation_status 
                WHERE botnet_type = %s
            """, (botnet_type,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and result[0]:
                return result[0]
            else:
                # 首次聚合，返回很早的时间
                return datetime(2020, 1, 1)
                
        except Exception as e:
            logger.error(f"获取上次聚合时间失败: {e}")
            return datetime(2020, 1, 1)
    
    def update_aggregation_status(self, botnet_type, max_updated_at):
        """更新聚合状态"""
        try:
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO aggregation_status (botnet_type, last_aggregated_at, last_max_updated_at)
                VALUES (%s, NOW(), %s)
                ON DUPLICATE KEY UPDATE
                    last_aggregated_at = NOW(),
                    last_max_updated_at = VALUES(last_max_updated_at)
            """, (botnet_type, max_updated_at))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"更新聚合状态失败: {e}")
    
    def incremental_aggregate_botnet_stats(self, botnet_type):
        """
        增量聚合僵尸网络统计数据
        只处理自上次聚合以来新增或更新的数据
        """
        conn = None
        cursor = None
        
        try:
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor()
            
            node_table = f"botnet_nodes_{botnet_type}"
            china_table = f"china_botnet_{botnet_type}"
            global_table = f"global_botnet_{botnet_type}"
            
            # 获取上次聚合时间
            last_aggregated = self.get_last_aggregation_time(botnet_type)
            
            logger.info(f"[{botnet_type}] 开始增量聚合（自 {last_aggregated} 以来的数据）...")
            
            # 检查是否有新数据
            cursor.execute(f"""
                SELECT COUNT(*), MAX(updated_at) 
                FROM {node_table} 
                WHERE updated_at > %s
            """, (last_aggregated,))
            
            new_count, max_updated_at = cursor.fetchone()
            
            if new_count == 0:
                logger.info(f"[{botnet_type}] 没有新数据需要聚合")
                return {'china_rows': 0, 'global_rows': 0, 'new_nodes': 0, 'skipped': True}
            
            logger.info(f"[{botnet_type}] 发现 {new_count} 条新数据")
            
            # 确保统计表存在
            self._ensure_stats_tables_exist(cursor, botnet_type)
            
            # 获取受影响的地区和国家
            affected_locations = self._get_affected_locations(cursor, node_table, last_aggregated)
            affected_countries = self._get_affected_countries(cursor, node_table, last_aggregated)
            
            logger.info(f"[{botnet_type}] 需要更新 {len(affected_locations)} 个地区，{len(affected_countries)} 个国家")
            
            # 重新聚合受影响的地区
            china_rows = self._update_china_stats(cursor, node_table, china_table, affected_locations)
            
            # 重新聚合受影响的国家
            global_rows = self._update_global_stats(cursor, node_table, global_table, affected_countries)
            
            # 更新聚合状态
            self.update_aggregation_status(botnet_type, max_updated_at)
            
            conn.commit()
            
            logger.info(f"✅ [{botnet_type}] 增量聚合完成：处理 {new_count} 条新数据 → 更新中国统计 {china_rows} 条，全球统计 {global_rows} 条")
            
            return {
                'china_rows': china_rows,
                'global_rows': global_rows,
                'new_nodes': new_count,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ [{botnet_type}] 增量聚合失败: {e}")
            if conn:
                conn.rollback()
            return {'success': False, 'error': str(e)}
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def _get_affected_locations(self, cursor, node_table, since_time):
        """获取受影响的省市组合"""
        cursor.execute(f"""
            SELECT DISTINCT
                COALESCE(TRIM(TRAILING '省' FROM province), '未知') as province,
                CASE 
                    WHEN city IN ('北京', '天津', '上海', '重庆') THEN city
                    WHEN city IS NOT NULL THEN TRIM(TRAILING '市' FROM city)
                    ELSE '未知'
                END as municipality
            FROM {node_table}
            WHERE country = '中国' AND updated_at > %s
        """, (since_time,))
        
        return cursor.fetchall()
    
    def _get_affected_countries(self, cursor, node_table, since_time):
        """获取受影响的国家"""
        cursor.execute(f"""
            SELECT DISTINCT COALESCE(country, '未知') as country
            FROM {node_table}
            WHERE updated_at > %s
        """, (since_time,))
        
        return [row[0] for row in cursor.fetchall()]
    
    def _update_china_stats(self, cursor, node_table, china_table, affected_locations):
        """更新受影响地区的中国统计"""
        updated_count = 0
        
        for province, municipality in affected_locations:
            # 注意：节点表使用 created_time，但统计表使用 created_at
            # 按IP去重统计节点数量，避免重复计数
            cursor.execute(f"""
                INSERT INTO {china_table} (province, municipality, infected_num, created_at, updated_at)
                SELECT 
                    %s as province,
                    %s as municipality,
                    COUNT(DISTINCT ip) as infected_num,
                    MIN(created_time) as created_at,
                    MAX(updated_at) as updated_at
                FROM {node_table}
                WHERE country = '中国' 
                    AND COALESCE(TRIM(TRAILING '省' FROM province), '未知') = %s
                    AND CASE 
                        WHEN city IN ('北京', '天津', '上海', '重庆') THEN city
                        WHEN city IS NOT NULL THEN TRIM(TRAILING '市' FROM city)
                        ELSE '未知'
                    END = %s
                ON DUPLICATE KEY UPDATE
                    infected_num = VALUES(infected_num),
                    created_at = VALUES(created_at),
                    updated_at = VALUES(updated_at)
            """, (province, municipality, province, municipality))
            
            if cursor.rowcount > 0:
                updated_count += 1
        
        return updated_count
    
    def _update_global_stats(self, cursor, node_table, global_table, affected_countries):
        """更新受影响国家的全球统计"""
        updated_count = 0
        
        for country in affected_countries:
            # 注意：节点表使用 created_time，但统计表使用 created_at
            # 按IP去重统计节点数量，避免重复计数
            cursor.execute(f"""
                INSERT INTO {global_table} (country, infected_num, created_at, updated_at)
                SELECT 
                    %s as country,
                    COUNT(DISTINCT ip) as infected_num,
                    MIN(created_time) as created_at,
                    MAX(updated_at) as updated_at
                FROM {node_table}
                WHERE COALESCE(country, '未知') = %s
                ON DUPLICATE KEY UPDATE
                    infected_num = VALUES(infected_num),
                    created_at = VALUES(created_at),
                    updated_at = VALUES(updated_at)
            """, (country, country))
            
            if cursor.rowcount > 0:
                updated_count += 1
        
        return updated_count
    
    def _ensure_stats_tables_exist(self, cursor, botnet_type):
        """确保统计表存在"""
        china_table = f"china_botnet_{botnet_type}"
        global_table = f"global_botnet_{botnet_type}"
        
        # 创建中国统计表
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {china_table} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                province VARCHAR(50) NOT NULL,
                municipality VARCHAR(50) NOT NULL,
                infected_num INT DEFAULT 0 COMMENT '感染数量',
                created_at TIMESTAMP NULL DEFAULT NULL COMMENT '该地区第一个节点的创建时间',
                updated_at TIMESTAMP NULL DEFAULT NULL COMMENT '该地区最新节点的更新时间',
                UNIQUE KEY idx_location (province, municipality),
                INDEX idx_province (province),
                INDEX idx_infected_num (infected_num),
                INDEX idx_created_at (created_at),
                INDEX idx_updated_at (updated_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
            COMMENT='中国地区僵尸网络统计表(按省市)'
        """)
        
        # 创建全球统计表
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {global_table} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                country VARCHAR(50) NOT NULL,
                infected_num INT DEFAULT 0 COMMENT '感染数量',
                created_at TIMESTAMP NULL DEFAULT NULL COMMENT '该国家第一个节点的创建时间',
                updated_at TIMESTAMP NULL DEFAULT NULL COMMENT '该国家最新节点的更新时间',
                UNIQUE KEY idx_country (country),
                INDEX idx_infected_num (infected_num),
                INDEX idx_created_at (created_at),
                INDEX idx_updated_at (updated_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
            COMMENT='全球僵尸网络统计表(按国家)'
        """)


def main():
    """主函数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    aggregator = IncrementalStatsAggregator(DB_CONFIG)
    
    if len(sys.argv) > 1:
        botnet_type = sys.argv[1]
        if botnet_type in aggregator.BOTNET_TYPES:
            result = aggregator.incremental_aggregate_botnet_stats(botnet_type)
            logger.info(f"结果: {result}")
        else:
            logger.error(f"不支持的僵尸网络类型: {botnet_type}")
    else:
        # 聚合所有类型
        for botnet_type in aggregator.BOTNET_TYPES:
            aggregator.incremental_aggregate_botnet_stats(botnet_type)


if __name__ == "__main__":
    main()
