"""
添加timeset表的active和cleaned字段
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


def add_timeset_fields():
    """为所有timeset表添加active和cleaned字段"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 获取所有timeset表
        cursor.execute("""
            SELECT TABLE_NAME as table_name
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND TABLE_NAME LIKE 'botnet_timeset_%'
        """)
        tables = cursor.fetchall()
        
        success_count = 0
        for table in tables:
            table_name = table['table_name']
            try:
                # 检查字段是否已存在
                cursor.execute(f"SHOW COLUMNS FROM {table_name}")
                columns = [col['Field'] for col in cursor.fetchall()]
                
                fields_to_add = []
                if 'china_active' not in columns:
                    fields_to_add.append("ADD COLUMN china_active INT DEFAULT 0")
                if 'global_active' not in columns:
                    fields_to_add.append("ADD COLUMN global_active INT DEFAULT 0")
                if 'china_cleaned' not in columns:
                    fields_to_add.append("ADD COLUMN china_cleaned INT DEFAULT 0")
                if 'global_cleaned' not in columns:
                    fields_to_add.append("ADD COLUMN global_cleaned INT DEFAULT 0")
                
                if fields_to_add:
                    alter_sql = f"ALTER TABLE {table_name} {', '.join(fields_to_add)}"
                    cursor.execute(alter_sql)
                    conn.commit()
                    logger.info(f"✓ {table_name}: 添加了 {len(fields_to_add)} 个字段")
                    success_count += 1
                else:
                    logger.info(f"○ {table_name}: 字段已存在，跳过")
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"✗ {table_name}: {e}")
                conn.rollback()
        
        logger.info(f"\n完成！成功处理 {success_count}/{len(tables)} 个表")
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
    success = add_timeset_fields()
    sys.exit(0 if success else 1)
