"""
更新timeset表结构：
1. 将count字段重命名为global_count
2. 添加china_count字段
"""
import pymysql
from config import DB_CONFIG, ALLOWED_BOTNET_TYPES
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_timeset_schema():
    """更新所有timeset表的结构"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        for botnet_type in ALLOWED_BOTNET_TYPES:
            try:
                timeset_table = f"botnet_timeset_{botnet_type}"
                
                # 检查表是否存在
                cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_name = %s
                """, (timeset_table,))
                
                if cursor.fetchone()[0] == 0:
                    logger.warning(f"[跳过] {timeset_table}: 表不存在")
                    continue
                
                # 检查是否已经有global_count字段
                cursor.execute(f"""
                    SELECT COUNT(*) as count
                    FROM information_schema.columns
                    WHERE table_schema = DATABASE()
                    AND table_name = %s
                    AND column_name = 'global_count'
                """, (timeset_table,))
                
                has_global_count = cursor.fetchone()[0] > 0
                
                if not has_global_count:
                    # 重命名count为global_count
                    logger.info(f"[修改] {timeset_table}: 重命名 count -> global_count")
                    cursor.execute(f"""
                        ALTER TABLE {timeset_table}
                        CHANGE COLUMN count global_count INT NOT NULL DEFAULT 0 COMMENT '全球节点数量'
                    """)
                    conn.commit()
                else:
                    logger.info(f"[已存在] {timeset_table}: global_count字段已存在")
                
                # 检查是否已经有china_count字段
                cursor.execute(f"""
                    SELECT COUNT(*) as count
                    FROM information_schema.columns
                    WHERE table_schema = DATABASE()
                    AND table_name = %s
                    AND column_name = 'china_count'
                """, (timeset_table,))
                
                has_china_count = cursor.fetchone()[0] > 0
                
                if not has_china_count:
                    # 添加china_count字段
                    logger.info(f"[添加] {timeset_table}: 添加 china_count 字段")
                    cursor.execute(f"""
                        ALTER TABLE {timeset_table}
                        ADD COLUMN china_count INT NOT NULL DEFAULT 0 COMMENT '中国节点数量'
                        AFTER global_count
                    """)
                    conn.commit()
                else:
                    logger.info(f"[已存在] {timeset_table}: china_count字段已存在")
                
                logger.info(f"[成功] {timeset_table}: 表结构更新完成")
                
            except Exception as e:
                logger.error(f"[失败] {botnet_type}: {e}")
                conn.rollback()
        
        logger.info("=" * 60)
        logger.info("所有表结构更新完成！")
        
    except Exception as e:
        logger.error(f"数据库连接错误: {e}")
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    update_timeset_schema()
