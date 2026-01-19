"""
创建所有僵尸网络的时间序列表（botnet_timeset_BOTNETNAME）
每个表包含：date（日期）和 count（节点数量）两个字段
"""
import pymysql
from config import DB_CONFIG, ALLOWED_BOTNET_TYPES
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_timeset_table(botnet_type):
    """为指定僵尸网络创建时间序列表"""
    table_name = f"botnet_timeset_{botnet_type}"
    
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        date DATE NOT NULL UNIQUE COMMENT '日期',
        count INT NOT NULL DEFAULT 0 COMMENT '节点数量',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        INDEX idx_date (date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='{botnet_type}僵尸网络每日节点数量统计表';
    """
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute(create_table_sql)
        conn.commit()
        
        logger.info(f"✓ 成功创建表: {table_name}")
        return True
        
    except Exception as e:
        logger.error(f"✗ 创建表 {table_name} 失败: {e}")
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def create_all_timeset_tables():
    """为所有允许的僵尸网络类型创建时间序列表"""
    logger.info("开始创建僵尸网络时间序列表...")
    logger.info(f"僵尸网络类型列表: {ALLOWED_BOTNET_TYPES}")
    
    success_count = 0
    fail_count = 0
    
    for botnet_type in ALLOWED_BOTNET_TYPES:
        if create_timeset_table(botnet_type):
            success_count += 1
        else:
            fail_count += 1
    
    logger.info(f"\n创建完成！成功: {success_count}, 失败: {fail_count}")
    return success_count, fail_count


if __name__ == "__main__":
    create_all_timeset_tables()
