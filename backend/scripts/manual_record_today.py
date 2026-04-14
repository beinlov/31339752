"""
手动执行今日节点统计（用于测试或补录数据）
"""
import pymysql
from pymysql.cursors import DictCursor
from config import DB_CONFIG, ALLOWED_BOTNET_TYPES
from datetime import date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def record_today_counts():
    """统计并记录今日所有僵尸网络节点数量"""
    today = date.today()
    logger.info(f"统计日期: {today}")
    logger.info("=" * 60)
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        total_success = 0
        total_nodes = 0
        
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
                
                # 统计全球节点总数
                cursor.execute(f"SELECT COUNT(*) as total FROM {node_table}")
                result = cursor.fetchone()
                global_count = result['total'] if result else 0
                
                # 从global_botnet表读取中国节点数
                global_table = f"global_botnet_{botnet_type}"
                china_count = 0
                
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
                        china_count = int(result['infected_num'])
                
                # 写入或更新timeset表
                timeset_table = f"botnet_timeset_{botnet_type}"
                cursor.execute(f"""
                    INSERT INTO {timeset_table} (date, global_count, china_count)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        global_count = %s, 
                        china_count = %s,
                        updated_at = CURRENT_TIMESTAMP
                """, (today, global_count, china_count, global_count, china_count))
                
                conn.commit()
                logger.info(f"[成功] {botnet_type}: 全球 {global_count:,} 个节点, 中国 {china_count:,} 个节点")
                total_success += 1
                total_nodes += global_count
                
            except Exception as e:
                logger.error(f"[失败] {botnet_type}: {e}")
                conn.rollback()
        
        logger.info("=" * 60)
        logger.info(f"统计完成！成功: {total_success}/{len(ALLOWED_BOTNET_TYPES)}, 总节点数: {total_nodes:,}")
        
    except Exception as e:
        logger.error(f"数据库连接错误: {e}")
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    record_today_counts()
