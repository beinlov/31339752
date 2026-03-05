"""
检查 utg_q_008 与其他僵网的数据库表结构是否一致
"""
import pymysql
from config import DB_CONFIG, ALLOWED_BOTNET_TYPES
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_table_structure(cursor, table_name):
    """获取表的字段结构"""
    cursor.execute(f"""
        SELECT 
            COLUMN_NAME,
            COLUMN_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            COLUMN_COMMENT
        FROM information_schema.COLUMNS
        WHERE table_schema = DATABASE()
        AND table_name = %s
        ORDER BY ORDINAL_POSITION
    """, (table_name,))
    
    return cursor.fetchall()


def compare_structures(ref_structure, target_structure, ref_name, target_name):
    """比较两个表的结构并输出差异"""
    ref_dict = {row[0]: row for row in ref_structure}
    target_dict = {row[0]: row for row in target_structure}
    
    differences = []
    
    # 检查缺少的字段
    missing_fields = set(ref_dict.keys()) - set(target_dict.keys())
    if missing_fields:
        differences.append(f"  缺少的字段: {', '.join(missing_fields)}")
    
    # 检查多余的字段
    extra_fields = set(target_dict.keys()) - set(ref_dict.keys())
    if extra_fields:
        differences.append(f"  多余的字段: {', '.join(extra_fields)}")
    
    # 检查字段类型差异
    for field in set(ref_dict.keys()) & set(target_dict.keys()):
        ref_type = ref_dict[field][1]
        target_type = target_dict[field][1]
        if ref_type != target_type:
            differences.append(f"  字段类型不同 [{field}]: {ref_name}={ref_type}, {target_name}={target_type}")
    
    return differences


def check_all_table_structures():
    """检查所有表结构"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 定义要检查的表类型
        table_types = [
            ('botnet_nodes', 'nodes'),
            ('botnet_communications', 'communications'),
            ('china_botnet', 'china_botnet'),
            ('global_botnet', 'global_botnet'),
            ('botnet_timeset', 'timeset')
        ]
        
        # 使用第一个非 utg_q_008 的僵网作为参考
        reference_botnet = None
        for bt in ALLOWED_BOTNET_TYPES:
            if bt != 'utg_q_008':
                reference_botnet = bt
                break
        
        if not reference_botnet:
            logger.error("没有找到参考僵网类型")
            return
        
        logger.info("=" * 80)
        logger.info(f"检查 utg_q_008 与 {reference_botnet} 的表结构差异")
        logger.info("=" * 80)
        
        has_differences = False
        
        for table_prefix, table_desc in table_types:
            ref_table = f"{table_prefix}_{reference_botnet}"
            target_table = f"{table_prefix}_utg_q_008"
            
            # 检查参考表是否存在
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = %s
            """, (ref_table,))
            
            if cursor.fetchone()[0] == 0:
                logger.warning(f"[跳过] {table_desc}: 参考表 {ref_table} 不存在")
                continue
            
            # 检查目标表是否存在
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = %s
            """, (target_table,))
            
            if cursor.fetchone()[0] == 0:
                logger.warning(f"[跳过] {table_desc}: 目标表 {target_table} 不存在")
                continue
            
            # 获取表结构
            ref_structure = get_table_structure(cursor, ref_table)
            target_structure = get_table_structure(cursor, target_table)
            
            # 比较结构
            differences = compare_structures(
                ref_structure, 
                target_structure, 
                ref_table, 
                target_table
            )
            
            if differences:
                has_differences = True
                logger.warning(f"\n[差异] {table_desc} 表:")
                logger.warning(f"  参考表: {ref_table}")
                logger.warning(f"  目标表: {target_table}")
                for diff in differences:
                    logger.warning(diff)
            else:
                logger.info(f"[一致] {table_desc} 表结构一致")
        
        logger.info("=" * 80)
        if not has_differences:
            logger.info("✓ 所有表结构检查完成，utg_q_008 与其他僵网表结构一致")
        else:
            logger.warning("⚠ 发现表结构差异，请查看上面的详细信息")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"检查过程出错: {e}")
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    check_all_table_structures()
