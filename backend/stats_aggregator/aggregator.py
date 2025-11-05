#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计数据聚合器
自动定时从 botnet_nodes_{type} 聚合统计到 china_botnet_{type} 和 global_botnet_{type}
"""
import pymysql
import sys
import os
import time
import logging
from collections import defaultdict
from datetime import datetime

# 添加父目录到路径以便导入config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DB_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), '..', 'stats_aggregator.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StatsAggregator:
    """统计数据聚合器"""
    
    # 支持的僵尸网络类型
    BOTNET_TYPES = ['asruex', 'mozi', 'andromeda', 'moobot', 'ramnit', 'leethozer']
    
    def __init__(self, db_config):
        """
        初始化聚合器
        
        Args:
            db_config: 数据库配置
        """
        self.db_config = db_config
        
    def aggregate_botnet_stats(self, botnet_type):
        """
        从 botnet_nodes_{type} 聚合统计到 
        china_botnet_{type} 和 global_botnet_{type}
        
        Args:
            botnet_type: 僵尸网络类型
            
        Returns:
            dict: 统计信息 {'china_rows': int, 'global_rows': int}
        """
        conn = None
        cursor = None
        
        try:
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor()
            
            node_table = f"botnet_nodes_{botnet_type}"
            china_table = f"china_botnet_{botnet_type}"
            global_table = f"global_botnet_{botnet_type}"
            
            logger.info(f"[{botnet_type}] 开始聚合统计数据...")
            
            # 检查节点表是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (self.db_config['database'], node_table))
            
            if cursor.fetchone()[0] == 0:
                logger.warning(f"[{botnet_type}] 节点表 {node_table} 不存在，跳过")
                return {'china_rows': 0, 'global_rows': 0, 'skipped': True}
            
            # 检查节点表是否有数据
            cursor.execute(f"SELECT COUNT(*) FROM {node_table}")
            node_count = cursor.fetchone()[0]
            
            if node_count == 0:
                logger.info(f"[{botnet_type}] 节点表为空，跳过聚合")
                return {'china_rows': 0, 'global_rows': 0, 'node_count': 0}
            
            logger.info(f"[{botnet_type}] 节点表共有 {node_count} 条记录")
            
            # 确保统计表存在
            self._ensure_stats_tables_exist(cursor, botnet_type)
            
            # 1. 清空旧的统计数据（全量聚合）
            cursor.execute(f"DELETE FROM {china_table}")
            cursor.execute(f"DELETE FROM {global_table}")
            
            # 2. 聚合中国地区统计（按省市分组）
            # 注意: created_at 和 updated_at 使用每个分组中最早和最晚的时间
            cursor.execute(f"""
                INSERT INTO {china_table} (province, municipality, infected_num, created_at, updated_at)
                SELECT 
                    COALESCE(TRIM(TRAILING '省' FROM province), '未知') as province,
                    CASE 
                        WHEN city IN ('北京', '天津', '上海', '重庆') THEN city
                        WHEN city IS NOT NULL THEN TRIM(TRAILING '市' FROM city)
                        ELSE '未知'
                    END as municipality,
                    COUNT(*) as infected_num,
                    MIN(created_at) as created_at,
                    MAX(updated_at) as updated_at
                FROM {node_table}
                WHERE country = '中国'
                GROUP BY 
                    COALESCE(TRIM(TRAILING '省' FROM province), '未知'),
                    CASE 
                        WHEN city IN ('北京', '天津', '上海', '重庆') THEN city
                        WHEN city IS NOT NULL THEN TRIM(TRAILING '市' FROM city)
                        ELSE '未知'
                    END
            """)
            china_rows = cursor.rowcount
            
            # 3. 聚合全球统计（按国家分组）
            # 注意: created_at 和 updated_at 使用每个分组中最早和最晚的时间
            cursor.execute(f"""
                INSERT INTO {global_table} (country, infected_num, created_at, updated_at)
                SELECT 
                    COALESCE(country, '未知') as country,
                    COUNT(*) as infected_num,
                    MIN(created_at) as created_at,
                    MAX(updated_at) as updated_at
                FROM {node_table}
                GROUP BY country
            """)
            global_rows = cursor.rowcount
            
            conn.commit()
            
            logger.info(f"✅ [{botnet_type}] 聚合完成：节点 {node_count} → 中国统计 {china_rows} 条，全球统计 {global_rows} 条")
            
            return {
                'china_rows': china_rows,
                'global_rows': global_rows,
                'node_count': node_count,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ [{botnet_type}] 聚合失败: {e}")
            if conn:
                conn.rollback()
            return {'success': False, 'error': str(e)}
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
                
    def _ensure_stats_tables_exist(self, cursor, botnet_type):
        """
        确保统计表存在
        
        时间字段说明:
        - created_at: 该地区/国家第一个节点的创建时间(来自原始表的MIN(created_at))
        - updated_at: 该地区/国家最新节点的更新时间(来自原始表的MAX(updated_at))
        """
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
        
    def aggregate_all(self):
        """聚合所有僵尸网络的统计数据"""
        logger.info("=" * 60)
        logger.info("开始全量聚合统计数据")
        logger.info("=" * 60)
        
        start_time = time.time()
        results = {}
        
        for botnet_type in self.BOTNET_TYPES:
            result = self.aggregate_botnet_stats(botnet_type)
            results[botnet_type] = result
            
        elapsed = time.time() - start_time
        
        # 统计总结
        total_china = sum(r.get('china_rows', 0) for r in results.values())
        total_global = sum(r.get('global_rows', 0) for r in results.values())
        success_count = sum(1 for r in results.values() if r.get('success', False))
        
        logger.info("=" * 60)
        logger.info(f"聚合完成！耗时: {elapsed:.2f}秒")
        logger.info(f"成功: {success_count}/{len(self.BOTNET_TYPES)}")
        logger.info(f"总计: 中国统计 {total_china} 条，全球统计 {total_global} 条")
        logger.info("=" * 60)
        
        return results


def run_once():
    """运行一次聚合（用于测试或手动执行）"""
    logger.info("执行单次聚合...")
    aggregator = StatsAggregator(DB_CONFIG)
    
    if len(sys.argv) > 2 and sys.argv[2]:
        # 指定了僵尸网络类型
        botnet_type = sys.argv[2]
        if botnet_type in StatsAggregator.BOTNET_TYPES:
            result = aggregator.aggregate_botnet_stats(botnet_type)
            logger.info(f"结果: {result}")
        else:
            logger.error(f"不支持的僵尸网络类型: {botnet_type}")
            logger.info(f"支持的类型: {', '.join(StatsAggregator.BOTNET_TYPES)}")
    else:
        # 聚合所有类型
        aggregator.aggregate_all()


def run_daemon(interval_minutes=30):
    """
    守护进程模式，定时聚合
    
    Args:
        interval_minutes: 聚合间隔（分钟）
    """
    logger.info("=" * 60)
    logger.info("统计聚合器启动（守护进程模式）")
    logger.info(f"聚合间隔: {interval_minutes} 分钟")
    logger.info(f"监控的僵尸网络: {', '.join(StatsAggregator.BOTNET_TYPES)}")
    logger.info("=" * 60)
    
    aggregator = StatsAggregator(DB_CONFIG)
    
    # 立即执行一次
    logger.info("执行首次聚合...")
    aggregator.aggregate_all()
    
    # 定时循环
    interval_seconds = interval_minutes * 60
    
    try:
        while True:
            next_run = datetime.now().timestamp() + interval_seconds
            next_run_time = datetime.fromtimestamp(next_run).strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info(f"\n⏰ 下次聚合时间: {next_run_time} (等待 {interval_minutes} 分钟)")
            time.sleep(interval_seconds)
            
            # 执行聚合
            aggregator.aggregate_all()
            
    except KeyboardInterrupt:
        logger.info("\n收到中断信号，正在退出...")
        logger.info("统计聚合器已停止")
    except Exception as e:
        logger.error(f"守护进程异常: {e}")
        raise


def main():
    """主函数"""
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == "once":
            # 单次执行模式
            run_once()
            
        elif mode == "daemon":
            # 守护进程模式
            interval = 30  # 默认30分钟
            if len(sys.argv) > 2:
                try:
                    interval = int(sys.argv[2])
                except ValueError:
                    logger.warning(f"无效的间隔时间，使用默认值: {interval}分钟")
            
            run_daemon(interval_minutes=interval)
            
        else:
            print("用法:")
            print("  python aggregator.py once [botnet_type]  # 执行一次聚合")
            print("  python aggregator.py daemon [minutes]    # 守护进程模式（默认30分钟）")
            print("\n示例:")
            print("  python aggregator.py once               # 聚合所有僵尸网络")
            print("  python aggregator.py once mozi          # 只聚合 mozi")
            print("  python aggregator.py daemon 30          # 每30分钟聚合一次")
            print("  python aggregator.py daemon 5           # 每5分钟聚合一次")
    else:
        # 默认：守护进程模式，30分钟间隔
        run_daemon(interval_minutes=30)


if __name__ == "__main__":
    main()



