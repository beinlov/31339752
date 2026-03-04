"""
同步cleaned状态到通信记录表
将botnet_nodes表中status为cleaned的节点，在botnet_communications表中对应IP的最新记录也设置为cleaned
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


def sync_cleaned_status(botnet_type='mozi'):
    """
    同步cleaned状态到通信记录表
    
    Args:
        botnet_type: 僵尸网络类型，默认为mozi
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        nodes_table = f"botnet_nodes_{botnet_type}"
        communications_table = f"botnet_communications_{botnet_type}"
        
        # 检查表是否存在
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = %s
        """, (nodes_table,))
        
        if cursor.fetchone()['count'] == 0:
            logger.error(f"表 {nodes_table} 不存在")
            return False
        
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = %s
        """, (communications_table,))
        
        if cursor.fetchone()['count'] == 0:
            logger.error(f"表 {communications_table} 不存在")
            return False
        
        # 查询nodes表中status为cleaned的节点IP
        logger.info(f"查询 {nodes_table} 表中status为cleaned的节点...")
        cursor.execute(f"""
            SELECT DISTINCT ip 
            FROM {nodes_table} 
            WHERE status = 'cleaned'
        """)
        cleaned_nodes = cursor.fetchall()
        
        if not cleaned_nodes:
            logger.info(f"没有找到status为cleaned的节点")
            return True
        
        logger.info(f"找到 {len(cleaned_nodes)} 个cleaned节点")
        
        # 为每个cleaned节点更新communications表中的最新记录
        updated_count = 0
        for node in cleaned_nodes:
            ip = node['ip']
            
            # 更新该IP的最新通信记录状态为cleaned
            # 使用子查询找到最新的记录ID，然后更新
            update_sql = f"""
                UPDATE {communications_table}
                SET status = 'cleaned'
                WHERE ip = %s
                AND id = (
                    SELECT id FROM (
                        SELECT id 
                        FROM {communications_table} 
                        WHERE ip = %s 
                        ORDER BY communication_time DESC 
                        LIMIT 1
                    ) as latest
                )
            """
            
            cursor.execute(update_sql, (ip, ip))
            
            if cursor.rowcount > 0:
                updated_count += 1
                logger.info(f"✓ 更新IP {ip} 的最新通信记录状态为cleaned")
        
        conn.commit()
        logger.info(f"\n完成！成功更新 {updated_count}/{len(cleaned_nodes)} 个IP的通信记录")
        return True
        
    except Exception as e:
        logger.error(f"同步失败: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    # 可以指定僵尸网络类型，默认为mozi
    botnet_type = sys.argv[1] if len(sys.argv) > 1 else 'mozi'
    logger.info(f"开始同步 {botnet_type} 的cleaned状态...")
    success = sync_cleaned_status(botnet_type)
    sys.exit(0 if success else 1)
