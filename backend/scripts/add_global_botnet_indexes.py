"""
为global_botnet表添加索引以优化世界地图查询性能
"""
import pymysql
from pymysql.cursors import DictCursor
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_global_botnet_indexes():
    """为global_botnet表添加country索引"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 获取所有global_botnet表
        cursor.execute("""
            SELECT TABLE_NAME as table_name
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND TABLE_NAME LIKE 'global_botnet_%'
        """)
        tables = cursor.fetchall()
        
        logger.info(f"找到 {len(tables)} 个global_botnet表")
        
        for table in tables:
            table_name = table['table_name']
            logger.info(f"\n检查表: {table_name}")
            
            # 检查现有索引
            cursor.execute(f"SHOW INDEX FROM {table_name}")
            existing_indexes = cursor.fetchall()
            index_names = {idx['Key_name'] for idx in existing_indexes}
            
            logger.info(f"  现有索引: {', '.join(index_names)}")
            
            # 需要添加的索引
            indexes_to_add = []
            
            # 1. country索引（用于WHERE country = ? 和 GROUP BY country）
            if 'idx_country' not in index_names:
                indexes_to_add.append(
                    f"ALTER TABLE {table_name} ADD INDEX idx_country (country)"
                )
                logger.info(f"  ✓ 需要添加country索引")
            
            # 执行索引添加
            if indexes_to_add:
                for sql in indexes_to_add:
                    try:
                        logger.info(f"  执行: {sql}")
                        cursor.execute(sql)
                        conn.commit()
                        logger.info(f"  ✓ 索引添加成功")
                    except Exception as e:
                        logger.error(f"  ✗ 索引添加失败: {e}")
                        conn.rollback()
            else:
                logger.info(f"  ○ 所有必要的索引已存在")
        
        logger.info(f"\n索引检查和添加完成！")
        return True
        
    except Exception as e:
        logger.error(f"错误: {e}")
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    logger.info("开始为global_botnet表添加索引...\n")
    success = add_global_botnet_indexes()
    sys.exit(0 if success else 1)
