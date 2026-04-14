"""
为过去7天添加历史数据（用于测试和初始化）
"""
import pymysql
from pymysql.cursors import DictCursor
from config import DB_CONFIG, ALLOWED_BOTNET_TYPES
from datetime import date, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_historical_data():
    """为过去7天添加模拟的历史数据"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        today = date.today()
        
        for botnet_type in ALLOWED_BOTNET_TYPES:
            try:
                # 检查节点表是否存在
                node_table = f"botnet_nodes_{botnet_type}"
                cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_name = %s
                """, (node_table,))
                
                if cursor.fetchone()['count'] == 0:
                    logger.warning(f"[跳过] {botnet_type}: 节点表不存在")
                    continue
                
                # 获取当前全球节点总数
                cursor.execute(f"SELECT COUNT(*) as total FROM {node_table}")
                current_global_count = cursor.fetchone()['total']
                
                if current_global_count == 0:
                    logger.warning(f"[跳过] {botnet_type}: 没有节点数据")
                    continue
                
                # 获取当前中国节点数
                global_table = f"global_botnet_{botnet_type}"
                current_china_count = 0
                
                cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_name = %s
                """, (global_table,))
                
                if cursor.fetchone()['count'] > 0:
                    cursor.execute(f"""
                        SELECT infected_num 
                        FROM {global_table} 
                        WHERE country = '中国'
                    """)
                    result = cursor.fetchone()
                    if result and result['infected_num']:
                        current_china_count = int(result['infected_num'])
                
                timeset_table = f"botnet_timeset_{botnet_type}"
                
                # 为过去7天添加数据（模拟增长趋势）
                for days_ago in range(7, 0, -1):
                    target_date = today - timedelta(days=days_ago)
                    
                    # 模拟历史数据：当前数量的 70%-95% 之间
                    import random
                    ratio = 0.70 + (days_ago / 7) * 0.25  # 从70%逐渐增长到95%
                    historical_global_count = int(current_global_count * ratio)
                    historical_china_count = int(current_china_count * ratio)
                    
                    cursor.execute(f"""
                        INSERT INTO {timeset_table} (date, global_count, china_count)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                            global_count = %s,
                            china_count = %s
                    """, (target_date, historical_global_count, historical_china_count, 
                          historical_global_count, historical_china_count))
                
                conn.commit()
                logger.info(f"[成功] {botnet_type}: 已添加过去7天的历史数据")
                
            except Exception as e:
                logger.error(f"[失败] {botnet_type}: {e}")
                conn.rollback()
        
        logger.info("=" * 60)
        logger.info("历史数据添加完成！")
        
    except Exception as e:
        logger.error(f"数据库连接错误: {e}")
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    add_historical_data()
