"""
直接查询并显示表字段，验证修复是否成功
"""
import pymysql
from config import DB_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def show_table_fields(table_name):
    """显示表的所有字段"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT 
                COLUMN_NAME,
                COLUMN_TYPE,
                IS_NULLABLE,
                COLUMN_COMMENT
            FROM information_schema.COLUMNS
            WHERE table_schema = DATABASE()
            AND table_name = %s
            ORDER BY ORDINAL_POSITION
        """, (table_name,))
        
        fields = cursor.fetchall()
        
        if not fields:
            logger.warning(f"表 {table_name} 不存在或没有字段")
            return
        
        logger.info(f"\n表: {table_name}")
        logger.info("-" * 80)
        for field in fields:
            logger.info(f"  {field[0]:<30} {field[1]:<20} {field[3]}")
        
    except Exception as e:
        logger.error(f"查询失败: {e}")
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("查询 utg_q_008 相关表的字段结构")
    logger.info("=" * 80)
    
    # 查询需要对比的表
    tables_to_check = [
        ("china_botnet_asruex", "china_botnet_utg_q_008"),
        ("global_botnet_asruex", "global_botnet_utg_q_008"),
        ("botnet_timeset_asruex", "botnet_timeset_utg_q_008")
    ]
    
    for ref_table, target_table in tables_to_check:
        logger.info("\n" + "=" * 80)
        show_table_fields(ref_table)
        show_table_fields(target_table)


if __name__ == "__main__":
    main()
