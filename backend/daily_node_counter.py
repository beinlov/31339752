"""
每日定时任务：每天上午8点统计各僵尸网络节点数量并写入timeset表
"""
import pymysql
from pymysql.cursors import DictCursor
from config import DB_CONFIG, ALLOWED_BOTNET_TYPES
from datetime import datetime, date
import logging
import schedule
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def count_and_record_nodes():
    """统计所有僵尸网络的节点数量并记录到timeset表"""
    today = date.today()
    logger.info(f"开始统计 {today} 的节点数量...")
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
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
                    logger.warning(f"节点表 {node_table} 不存在，跳过")
                    continue
                
                # 统计节点总数
                cursor.execute(f"SELECT COUNT(*) as total FROM {node_table}")
                result = cursor.fetchone()
                total_count = result['total'] if result else 0
                
                # 写入或更新timeset表
                timeset_table = f"botnet_timeset_{botnet_type}"
                cursor.execute(f"""
                    INSERT INTO {timeset_table} (date, count)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE count = %s, updated_at = CURRENT_TIMESTAMP
                """, (today, total_count, total_count))
                
                conn.commit()
                logger.info(f"✓ {botnet_type}: {total_count} 个节点")
                
            except Exception as e:
                logger.error(f"✗ 处理 {botnet_type} 时出错: {e}")
                conn.rollback()
        
        logger.info("节点统计完成！")
        
    except Exception as e:
        logger.error(f"数据库连接错误: {e}")
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def run_daily_task():
    """运行每日任务"""
    logger.info("=" * 60)
    logger.info("执行每日节点统计任务")
    count_and_record_nodes()
    logger.info("=" * 60)


def start_scheduler():
    """启动定时任务调度器"""
    # 每天上午8点执行
    schedule.every().day.at("08:00").do(run_daily_task)
    
    logger.info("定时任务调度器已启动")
    logger.info("每日统计时间: 上午 08:00")
    logger.info("按 Ctrl+C 停止...")
    
    # 立即执行一次（用于测试）
    logger.info("\n立即执行一次任务（测试）...")
    run_daily_task()
    
    # 持续运行
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次


if __name__ == "__main__":
    try:
        start_scheduler()
    except KeyboardInterrupt:
        logger.info("\n定时任务已停止")
