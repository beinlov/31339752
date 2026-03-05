"""
修复其他僵网（除 utg_q_008 外）的 china_botnet 和 global_botnet 表结构
添加缺失的 communication_count 字段，修改 country 字段类型
"""
import pymysql
from config import DB_CONFIG, ALLOWED_BOTNET_TYPES
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_china_botnet_tables():
    """为所有僵网（除 utg_q_008）的 china_botnet 表添加 communication_count 字段"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        for botnet_type in ALLOWED_BOTNET_TYPES:
            if botnet_type == 'utg_q_008':
                continue  # 跳过 utg_q_008，它已经是正确的
            
            table_name = f"china_botnet_{botnet_type}"
            
            # 检查表是否存在
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = %s
            """, (table_name,))
            
            if cursor.fetchone()[0] == 0:
                logger.warning(f"[跳过] {table_name}: 表不存在")
                continue
            
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
                continue
            
            # 添加 communication_count 字段
            logger.info(f"[添加] {table_name}: 添加 communication_count 字段")
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
        
    except Exception as e:
        logger.error(f"修复 china_botnet 表失败: {e}")
        if 'conn' in locals():
            conn.rollback()
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def fix_global_botnet_tables():
    """为所有僵网（除 utg_q_008）的 global_botnet 表添加 communication_count 字段和修改 country 字段类型"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        for botnet_type in ALLOWED_BOTNET_TYPES:
            if botnet_type == 'utg_q_008':
                continue  # 跳过 utg_q_008，它已经是正确的
            
            table_name = f"global_botnet_{botnet_type}"
            
            # 检查表是否存在
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = %s
            """, (table_name,))
            
            if cursor.fetchone()[0] == 0:
                logger.warning(f"[跳过] {table_name}: 表不存在")
                continue
            
            # 1. 检查并添加 communication_count 字段
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                AND table_name = %s
                AND column_name = 'communication_count'
            """, (table_name,))
            
            if cursor.fetchone()[0] == 0:
                logger.info(f"[添加] {table_name}: 添加 communication_count 字段")
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
        
    except Exception as e:
        logger.error(f"修复 global_botnet 表失败: {e}")
        if 'conn' in locals():
            conn.rollback()
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("开始修复其他僵网的数据库表结构（使其与 utg_q_008 和标准定义一致）")
    logger.info("=" * 80)
    
    logger.info("\n1. 修复 china_botnet 表...")
    fix_china_botnet_tables()
    
    logger.info("\n2. 修复 global_botnet 表...")
    fix_global_botnet_tables()
    
    logger.info("\n" + "=" * 80)
    logger.info("所有表结构修复完成！")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
