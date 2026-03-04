"""
验证cleaned状态同步结果
检查botnet_communications表中cleaned状态的记录数量
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


def verify_sync(botnet_type='mozi'):
    """验证同步结果"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        nodes_table = f"botnet_nodes_{botnet_type}"
        communications_table = f"botnet_communications_{botnet_type}"
        
        # 统计nodes表中cleaned节点数量
        cursor.execute(f"""
            SELECT COUNT(DISTINCT ip) as count 
            FROM {nodes_table} 
            WHERE status = 'cleaned'
        """)
        nodes_cleaned_count = cursor.fetchone()['count']
        logger.info(f"✓ {nodes_table} 表中status为cleaned的节点数: {nodes_cleaned_count}")
        
        # 统计communications表中cleaned记录数量
        cursor.execute(f"""
            SELECT COUNT(*) as count 
            FROM {communications_table} 
            WHERE status = 'cleaned'
        """)
        comm_cleaned_count = cursor.fetchone()['count']
        logger.info(f"✓ {communications_table} 表中status为cleaned的记录数: {comm_cleaned_count}")
        
        # 抽样检查几个IP
        cursor.execute(f"""
            SELECT ip 
            FROM {nodes_table} 
            WHERE status = 'cleaned' 
            LIMIT 5
        """)
        sample_ips = [row['ip'] for row in cursor.fetchall()]
        
        logger.info(f"\n抽样检查 {len(sample_ips)} 个IP的最新通信记录:")
        for ip in sample_ips:
            cursor.execute(f"""
                SELECT ip, status, communication_time 
                FROM {communications_table} 
                WHERE ip = %s 
                ORDER BY communication_time DESC 
                LIMIT 1
            """, (ip,))
            result = cursor.fetchone()
            if result:
                status_icon = "✓" if result['status'] == 'cleaned' else "✗"
                logger.info(f"  {status_icon} IP {ip}: status={result['status']}, time={result['communication_time']}")
            else:
                logger.warning(f"  ✗ IP {ip}: 未找到通信记录")
        
        logger.info(f"\n验证完成！")
        return True
        
    except Exception as e:
        logger.error(f"验证失败: {e}")
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    botnet_type = sys.argv[1] if len(sys.argv) > 1 else 'mozi'
    logger.info(f"验证 {botnet_type} 的cleaned状态同步结果...\n")
    success = verify_sync(botnet_type)
    sys.exit(0 if success else 1)
