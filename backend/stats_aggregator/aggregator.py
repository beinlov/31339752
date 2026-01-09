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
from config import DB_CONFIG, BOTNET_TYPES, get_enabled_botnet_types, STATS_AGGREGATOR_LOG_FILE

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(STATS_AGGREGATOR_LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StatsAggregator:
    """统计数据聚合器"""
    
    # 支持的僵尸网络类型（从统一配置导入）
    BOTNET_TYPES = BOTNET_TYPES
    
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
            # 设置连接和查询超时（5分钟，大数据量需要更长时间）
            config = self.db_config.copy()
            config['connect_timeout'] = 300
            config['read_timeout'] = 300
            config['write_timeout'] = 300
            
            conn = pymysql.connect(**config)
            cursor = conn.cursor()
            
            # 设置会话级别的查询超时（5分钟）
            cursor.execute("SET SESSION max_execution_time = 300000")
            
            # 优化MySQL设置以加快聚合
            cursor.execute("SET SESSION sort_buffer_size = 268435456")  # 256MB
            cursor.execute("SET SESSION tmp_table_size = 536870912")    # 512MB
            cursor.execute("SET SESSION max_heap_table_size = 536870912")  # 512MB
            
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
            
            # 检查country字段的索引
            cursor.execute(f"""
                SHOW INDEX FROM {node_table} WHERE Column_name = 'country'
            """)
            if not cursor.fetchone():
                logger.warning(f"[{botnet_type}] 警告：{node_table} 缺少 country 索引，聚合可能很慢！")
                logger.info(f"[{botnet_type}] 建议执行： CREATE INDEX idx_country ON {node_table}(country)")
            
            # 确保统计表存在
            self._ensure_stats_tables_exist(cursor, botnet_type)
            
            # 1. 优化聚合：使用临时表 + 分离INSERT/UPDATE（提升100倍性能）
            overall_start = time.time()
            logger.info(f"[{botnet_type}] 聚合中国地区统计...")
            
            # Step 1.1: 创建临时表存储聚合结果
            temp_table = f"temp_china_{botnet_type}"
            cursor.execute(f"DROP TEMPORARY TABLE IF EXISTS {temp_table}")
            cursor.execute(f"""
                CREATE TEMPORARY TABLE {temp_table} (
                    province VARCHAR(100),
                    municipality VARCHAR(100),
                    infected_num INT,
                    created_at DATETIME,
                    updated_at DATETIME,
                    PRIMARY KEY (province, municipality)
                )
            """)
            
            # Step 1.2: 聚合到临时表（优化：简化字符串操作）
            start_time = time.time()
            logger.info(f"[{botnet_type}] 开始聚合到临时表（这可能需要几秒钟）...")
            
            cursor.execute(f"""
                INSERT INTO {temp_table} (province, municipality, infected_num, created_at, updated_at)
                SELECT 
                    COALESCE(
                        TRIM(TRAILING '省' FROM 
                        TRIM(TRAILING '市' FROM 
                        REPLACE(REPLACE(REPLACE(
                            province, 
                            '壮族自治区', ''), 
                            '回族自治区', ''), 
                            '维吾尔自治区', '')
                        )), 
                        '未知'
                    ) as province,
                    COALESCE(
                        TRIM(TRAILING '市' FROM city),
                        '未知'
                    ) as municipality,
                    COUNT(DISTINCT ip) as infected_num,
                    MIN(created_time) as created_at,
                    MAX(updated_at) as updated_at
                FROM {node_table}
                WHERE country = '中国'
                GROUP BY province, city
            """)
            temp_count = cursor.rowcount
            elapsed = time.time() - start_time
            logger.info(f"[{botnet_type}] 临时表聚合完成: {temp_count} 条记录, 耗时 {elapsed:.2f}秒")
            
            # Step 1.3: 查询已存在的记录（优化：使用JOIN代替IN）
            start_time = time.time()
            cursor.execute(f"""
                SELECT c.province, c.municipality
                FROM {china_table} c
                INNER JOIN {temp_table} t ON c.province = t.province AND c.municipality = t.municipality
            """)
            existing_keys = {f"{row[0]}|{row[1]}" for row in cursor.fetchall()}
            elapsed = time.time() - start_time
            logger.info(f"[{botnet_type}] 已存在记录: {len(existing_keys)} 条, 耗时 {elapsed:.2f}秒")
            
            # Step 1.4: 插入新记录（纯INSERT，快）
            if temp_count > len(existing_keys):
                cursor.execute(f"""
                    INSERT INTO {china_table} (province, municipality, infected_num, created_at, updated_at)
                    SELECT t.province, t.municipality, t.infected_num, t.created_at, t.updated_at
                    FROM {temp_table} t
                    LEFT JOIN {china_table} c ON t.province = c.province AND t.municipality = c.municipality
                    WHERE c.province IS NULL
                """)
                insert_count = cursor.rowcount
                logger.info(f"[{botnet_type}] 插入新记录: {insert_count} 条")
            
            # Step 1.5: 更新已存在记录（纯UPDATE，快）
            if existing_keys:
                cursor.execute(f"""
                    UPDATE {china_table} c
                    INNER JOIN {temp_table} t ON c.province = t.province AND c.municipality = t.municipality
                    SET c.infected_num = t.infected_num,
                        c.created_at = t.created_at,
                        c.updated_at = t.updated_at
                """)
                update_count = cursor.rowcount
                logger.info(f"[{botnet_type}] 更新记录: {update_count} 条")
            
            # 2. 优化全球统计聚合（使用临时表）
            logger.info(f"[{botnet_type}] 聚合全球统计...")
            
            # Step 2.1: 创建临时表
            temp_global_table = f"temp_global_{botnet_type}"
            cursor.execute(f"DROP TEMPORARY TABLE IF EXISTS {temp_global_table}")
            cursor.execute(f"""
                CREATE TEMPORARY TABLE {temp_global_table} (
                    country VARCHAR(100) PRIMARY KEY,
                    infected_num INT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            """)
            
            # Step 2.2: 聚合到临时表
            cursor.execute(f"""
                INSERT INTO {temp_global_table} (country, infected_num, created_at, updated_at)
                SELECT 
                    CASE
                        WHEN country = '中国台湾' THEN '台湾'
                        WHEN country = '中国香港' THEN '香港'
                        WHEN country = '中国澳门' THEN '澳门'
                        WHEN country IS NOT NULL THEN country
                        ELSE '未知'
                    END as country,
                    COUNT(DISTINCT ip) as infected_num,
                    MIN(created_time) as created_at,
                    MAX(updated_at) as updated_at
                FROM {node_table}
                GROUP BY 1
            """)
            temp_global_count = cursor.rowcount
            logger.info(f"[{botnet_type}] 临时表聚合完成: {temp_global_count} 个国家")
            
            # Step 2.3: 查询已存在的国家
            cursor.execute(f"""
                SELECT country FROM {global_table}
                WHERE country IN (SELECT country FROM {temp_global_table})
            """)
            existing_countries = {row[0] for row in cursor.fetchall()}
            
            # Step 2.4: 插入新国家
            if temp_global_count > len(existing_countries):
                cursor.execute(f"""
                    INSERT INTO {global_table} (country, infected_num, created_at, updated_at)
                    SELECT t.country, t.infected_num, t.created_at, t.updated_at
                    FROM {temp_global_table} t
                    LEFT JOIN {global_table} g ON t.country = g.country
                    WHERE g.country IS NULL
                """)
                logger.info(f"[{botnet_type}] 插入新国家: {cursor.rowcount} 个")
            
            # Step 2.5: 更新已存在国家
            if existing_countries:
                cursor.execute(f"""
                    UPDATE {global_table} g
                    INNER JOIN {temp_global_table} t ON g.country = t.country
                    SET g.infected_num = t.infected_num,
                        g.created_at = t.created_at,
                        g.updated_at = t.updated_at
                """)
                logger.info(f"[{botnet_type}] 更新国家: {cursor.rowcount} 个")
            
            conn.commit()
            
            # 查询实际的记录数（不依赖 cursor.rowcount）
            cursor.execute(f"SELECT COUNT(*) as count FROM {china_table}")
            china_rows = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) as count FROM {global_table}")
            global_rows = cursor.fetchone()[0]
            
            total_elapsed = time.time() - overall_start
            logger.info(f"[{botnet_type}] 聚合完成：节点 {node_count} -> 中国统计 {temp_count} 条，全球统计 {temp_global_count} 条，总耗时 {total_elapsed:.2f}秒")
            
            return {
                'china_rows': china_rows,
                'global_rows': global_rows,
                'node_count': node_count,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"[{botnet_type}] 聚合失败: {e}")
            # 安全地进行rollback，避免连接已断开时再次出错
            if conn:
                try:
                    conn.rollback()
                except Exception as rollback_error:
                    logger.warning(f"[{botnet_type}] Rollback失败（可能连接已断开）: {rollback_error}")
            return {'success': False, 'error': str(e)}
            
        finally:
            # 安全地关闭资源
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if conn:
                try:
                    conn.close()
                except:
                    pass
                
    def _ensure_stats_tables_exist(self, cursor, botnet_type):
        """
        确保统计表存在
        
        时间字段说明:
        - created_at: 该地区/国家第一个节点的创建时间(来自节点表的MIN(created_time))
        - updated_at: 该地区/国家最新节点的更新时间(来自节点表的MAX(updated_at))
        
        注意：统计表使用 created_at，但节点表使用 created_time
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
        
    def aggregate_all(self, max_retries=3):
        """聚合所有僵尸网络的统计数据（支持重试）"""
        logger.info("=" * 60)
        logger.info("开始全量聚合统计数据")
        logger.info("=" * 60)
        
        start_time = time.time()
        results = {}
        
        for botnet_type in self.BOTNET_TYPES:
            retry_count = 0
            while retry_count < max_retries:
                result = self.aggregate_botnet_stats(botnet_type)
                
                # 如果成功或跳过，跳出重试循环
                if result.get('success') or result.get('skipped'):
                    results[botnet_type] = result
                    break
                
                # 失败则重试
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 5 * retry_count  # 递增等待时间
                    logger.warning(f"[{botnet_type}] 聚合失败，{wait_time}秒后重试 ({retry_count}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    logger.error(f"[{botnet_type}] 聚合失败，已达到最大重试次数")
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
            
            logger.info(f"\n下次聚合时间: {next_run_time} (等待 {interval_minutes} 分钟)")
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



