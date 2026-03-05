"""
修复 utg_q_008 的数据库表结构，使其与其他僵网一致
"""
import pymysql
from config import DB_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_china_botnet_table():
    """修复 china_botnet_utg_q_008 表，添加 communication_count 字段"""
    table_name = "china_botnet_utg_q_008"
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = %s
        """, (table_name,))
        
        if cursor.fetchone()[0] == 0:
            logger.warning(f"[跳过] {table_name}: 表不存在")
            return False
        
        # 检查 communication_count 字段是否存在
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
            AND table_name = %s
            AND column_name = 'communication_count'
        """, (table_name,))
        
        if cursor.fetchone()[0] > 0:
            logger.info(f"[已存在] {table_name}: communication_count 字段已存在")
            return True
        
        # 添加 communication_count 字段
        logger.info(f"[修改] {table_name}: 添加 communication_count 字段")
        cursor.execute(f"""
            ALTER TABLE {table_name}
            ADD COLUMN communication_count INT DEFAULT 0 COMMENT '通信总次数'
            AFTER infected_num
        """)
        
        # 添加索引
        cursor.execute(f"""
            ALTER TABLE {table_name}
            ADD INDEX idx_communication_count (communication_count)
        """)
        
        conn.commit()
        logger.info(f"[成功] {table_name}: communication_count 字段添加完成")
        return True
        
    except Exception as e:
        logger.error(f"[失败] {table_name}: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def fix_global_botnet_table():
    """修复 global_botnet_utg_q_008 表"""
    table_name = "global_botnet_utg_q_008"
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = %s
        """, (table_name,))
        
        if cursor.fetchone()[0] == 0:
            logger.warning(f"[跳过] {table_name}: 表不存在")
            return False
        
        # 1. 检查并添加 communication_count 字段
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
            AND table_name = %s
            AND column_name = 'communication_count'
        """, (table_name,))
        
        if cursor.fetchone()[0] == 0:
            logger.info(f"[修改] {table_name}: 添加 communication_count 字段")
            cursor.execute(f"""
                ALTER TABLE {table_name}
                ADD COLUMN communication_count INT DEFAULT 0 COMMENT '通信总次数'
                AFTER infected_num
            """)
            
            cursor.execute(f"""
                ALTER TABLE {table_name}
                ADD INDEX idx_communication_count (communication_count)
            """)
            conn.commit()
        else:
            logger.info(f"[已存在] {table_name}: communication_count 字段已存在")
        
        # 2. 检查并修改 country 字段类型
        cursor.execute("""
            SELECT COLUMN_TYPE
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
            AND table_name = %s
            AND column_name = 'country'
        """, (table_name,))
        
        result = cursor.fetchone()
        if result and result[0] != 'varchar(100)':
            logger.info(f"[修改] {table_name}: 修改 country 字段类型 {result[0]} -> varchar(100)")
            cursor.execute(f"""
                ALTER TABLE {table_name}
                MODIFY COLUMN country VARCHAR(100) NOT NULL
            """)
            conn.commit()
        else:
            logger.info(f"[已正确] {table_name}: country 字段类型已是 varchar(100)")
        
        logger.info(f"[成功] {table_name}: 表结构修复完成")
        return True
        
    except Exception as e:
        logger.error(f"[失败] {table_name}: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def fix_timeset_table():
    """修复 botnet_timeset_utg_q_008 表，添加缺失的字段"""
    table_name = "botnet_timeset_utg_q_008"
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = %s
        """, (table_name,))
        
        if cursor.fetchone()[0] == 0:
            logger.warning(f"[跳过] {table_name}: 表不存在")
            return False
        
        # 获取参考表的所有字段
        ref_table = "botnet_timeset_asruex"
        cursor.execute(f"""
            SELECT COLUMN_NAME
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
            AND table_name = %s
            ORDER BY ORDINAL_POSITION
        """, (ref_table,))
        
        ref_columns = [row[0] for row in cursor.fetchall()]
        
        # 获取目标表的所有字段
        cursor.execute(f"""
            SELECT COLUMN_NAME
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
            AND table_name = %s
            ORDER BY ORDINAL_POSITION
        """, (table_name,))
        
        target_columns = [row[0] for row in cursor.fetchall()]
        
        # 找出缺失的字段
        missing_columns = set(ref_columns) - set(target_columns)
        
        if not missing_columns:
            logger.info(f"[完整] {table_name}: 所有字段都已存在")
            return True
        
        logger.info(f"[发现] {table_name}: 缺少字段 {', '.join(missing_columns)}")
        
        # 添加缺失的字段
        # 注意：这里我们需要根据参考表的字段定义来添加
        field_definitions = {
            'global_active': "INT NOT NULL DEFAULT 0 COMMENT '全球活跃节点数量'",
            'china_active': "INT NOT NULL DEFAULT 0 COMMENT '中国活跃节点数量'",
            'global_cleaned': "INT NOT NULL DEFAULT 0 COMMENT '全球已清除节点数量'",
            'china_cleaned': "INT NOT NULL DEFAULT 0 COMMENT '中国已清除节点数量'",
            'global_count_active': "INT NOT NULL DEFAULT 0 COMMENT '全球节点数量（仅活跃）'",
            'china_count_active': "INT NOT NULL DEFAULT 0 COMMENT '中国节点数量（仅活跃）'"
        }
        
        for column in missing_columns:
            if column in field_definitions:
                logger.info(f"[添加] {table_name}: 添加字段 {column}")
                cursor.execute(f"""
                    ALTER TABLE {table_name}
                    ADD COLUMN {column} {field_definitions[column]}
                """)
                conn.commit()
        
        logger.info(f"[成功] {table_name}: 表结构修复完成")
        return True
        
    except Exception as e:
        logger.error(f"[失败] {table_name}: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("开始修复 utg_q_008 的数据库表结构")
    logger.info("=" * 80)
    
    results = []
    
    # 修复 china_botnet 表
    logger.info("\n1. 修复 china_botnet_utg_q_008 表...")
    results.append(("china_botnet", fix_china_botnet_table()))
    
    # 修复 global_botnet 表
    logger.info("\n2. 修复 global_botnet_utg_q_008 表...")
    results.append(("global_botnet", fix_global_botnet_table()))
    
    # 修复 timeset 表
    logger.info("\n3. 修复 botnet_timeset_utg_q_008 表...")
    results.append(("timeset", fix_timeset_table()))
    
    # 输出总结
    logger.info("\n" + "=" * 80)
    logger.info("修复完成！")
    success_count = sum(1 for _, success in results if success)
    logger.info(f"成功: {success_count}/{len(results)}")
    for table_type, success in results:
        status = "✓" if success else "✗"
        logger.info(f"  {status} {table_type}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
