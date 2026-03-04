"""
检查并添加数据库索引以优化查询性能
特别针对china_botnet表的province和municipality字段
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


def check_and_add_indexes():
    """检查并添加必要的索引"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 获取所有china_botnet表
        cursor.execute("""
            SELECT TABLE_NAME as table_name
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND TABLE_NAME LIKE 'china_botnet_%'
        """)
        tables = cursor.fetchall()
        
        logger.info(f"找到 {len(tables)} 个china_botnet表")
        
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
            
            # 1. province索引（用于WHERE province = ?）
            if 'idx_province' not in index_names:
                indexes_to_add.append(
                    f"ALTER TABLE {table_name} ADD INDEX idx_province (province)"
                )
                logger.info(f"  ✓ 需要添加province索引")
            
            # 2. municipality索引（用于GROUP BY municipality）
            if 'idx_municipality' not in index_names:
                indexes_to_add.append(
                    f"ALTER TABLE {table_name} ADD INDEX idx_municipality (municipality)"
                )
                logger.info(f"  ✓ 需要添加municipality索引")
            
            # 3. 组合索引 province + municipality（最优化查询）
            if 'idx_province_municipality' not in index_names:
                indexes_to_add.append(
                    f"ALTER TABLE {table_name} ADD INDEX idx_province_municipality (province, municipality)"
                )
                logger.info(f"  ✓ 需要添加province+municipality组合索引")
            
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
    logger.info("开始检查和添加数据库索引...\n")
    success = check_and_add_indexes()
    sys.exit(0 if success else 1)
