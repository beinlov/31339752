"""
简化版每日定时任务：不依赖schedule库
使用Windows任务计划程序或cron来调度
"""
import pymysql
from pymysql.cursors import DictCursor
from config import DB_CONFIG, ALLOWED_BOTNET_TYPES
from datetime import date
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def count_and_record_nodes():
    """统计所有僵尸网络的节点数量并记录到timeset表"""
    today = date.today()
    logger.info(f"开始统计 {today} 的节点数量...")
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        success_count = 0
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
                
                # 从global_botnet表读取全球统计（包括总数、active、cleaned）
                global_table = f"global_botnet_{botnet_type}"
                global_count = 0
                global_active = 0
                global_cleaned = 0
                
                cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_name = %s
                """, (global_table,))
                
                if cursor.fetchone()['count'] > 0:
                    # 统计全球总数、active和cleaned节点数
                    cursor.execute(f"""
                        SELECT 
                            COALESCE(SUM(infected_num), 0) as total_count,
                            COALESCE(SUM(active_num), 0) as total_active,
                            COALESCE(SUM(cleaned_num), 0) as total_cleaned
                        FROM {global_table}
                    """)
                    result = cursor.fetchone()
                    if result:
                        global_count = int(result['total_count'])
                        global_active = int(result['total_active'])
                        global_cleaned = int(result['total_cleaned'])
                else:
                    logger.warning(f"[警告] {botnet_type}: global_botnet表不存在")
                
                # 从china_botnet表读取中国统计（包括总数、active、cleaned）
                china_table = f"china_botnet_{botnet_type}"
                china_count = 0
                china_active = 0
                china_cleaned = 0
                
                cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_name = %s
                """, (china_table,))
                
                if cursor.fetchone()['count'] > 0:
                    # 统计中国总数、active和cleaned节点数
                    cursor.execute(f"""
                        SELECT 
                            COALESCE(SUM(infected_num), 0) as total_count,
                            COALESCE(SUM(active_num), 0) as total_active,
                            COALESCE(SUM(cleaned_num), 0) as total_cleaned
                        FROM {china_table}
                    """)
                    result = cursor.fetchone()
                    if result:
                        china_count = int(result['total_count'])
                        china_active = int(result['total_active'])
                        china_cleaned = int(result['total_cleaned'])
                else:
                    logger.warning(f"[警告] {botnet_type}: china_botnet表不存在")
                
                # 写入或更新timeset表（包括所有6个字段）
                timeset_table = f"botnet_timeset_{botnet_type}"
                cursor.execute(f"""
                    INSERT INTO {timeset_table} (date, global_count, china_count, global_active, china_active, global_cleaned, china_cleaned)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        global_count = %s,
                        china_count = %s,
                        global_active = %s,
                        china_active = %s,
                        global_cleaned = %s,
                        china_cleaned = %s,
                        updated_at = CURRENT_TIMESTAMP
                """, (today, global_count, china_count, global_active, china_active, global_cleaned, china_cleaned,
                      global_count, china_count, global_active, china_active, global_cleaned, china_cleaned))
                
                conn.commit()
                logger.info(f"[成功] {botnet_type}: 全球总数 {global_count:,}, 全球活跃 {global_active:,}, 全球清理 {global_cleaned:,}, 中国总数 {china_count:,}, 中国活跃 {china_active:,}, 中国清理 {china_cleaned:,}")
                success_count += 1
                total_nodes += global_active
                
            except Exception as e:
                logger.error(f"[失败] {botnet_type}: {e}")
                conn.rollback()
        
        logger.info("=" * 60)
        logger.info(f"统计完成！成功: {success_count}/{len(ALLOWED_BOTNET_TYPES)}, 总节点数: {total_nodes:,}")
        return True
        
    except Exception as e:
        logger.error(f"数据库连接错误: {e}")
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    success = count_and_record_nodes()
    sys.exit(0 if success else 1)
