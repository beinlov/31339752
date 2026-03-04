import pymysql
import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from config import DB_CONFIG

def check_tables():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查botnet_types表
        print("=" * 60)
        print("检查 botnet_types 表中的僵网类型")
        print("=" * 60)
        cursor.execute("SELECT name, display_name FROM botnet_types ORDER BY created_at")
        botnets = cursor.fetchall()
        for name, display_name in botnets:
            print(f"  - {name}: {display_name}")
        
        # 检查是否有utg-q-008
        cursor.execute("SELECT COUNT(*) FROM botnet_types WHERE name = 'utg-q-008'")
        utg_exists = cursor.fetchone()[0]
        print(f"\nutg-q-008 在 botnet_types 中: {'存在' if utg_exists else '不存在'}")
        
        # 检查节点表
        print("\n" + "=" * 60)
        print("检查节点数据表")
        print("=" * 60)
        cursor.execute("SHOW TABLES LIKE 'botnet_nodes_%'")
        node_tables = cursor.fetchall()
        for (table,) in node_tables:
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} 个节点")
        
        # 检查utg-q-008的节点表
        cursor.execute("SHOW TABLES LIKE 'botnet_nodes_utg-q-008'")
        utg_table_exists = cursor.fetchone()
        print(f"\nbotnet_nodes_utg-q-008 表: {'存在' if utg_table_exists else '不存在'}")
        
        # 检查server_management表中的utg-q-008
        print("\n" + "=" * 60)
        print("检查 server_management 表中的 utg-q-008")
        print("=" * 60)
        cursor.execute("SELECT id, ip, location, Botnet_Name FROM server_management WHERE Botnet_Name = 'utg-q-008'")
        servers = cursor.fetchall()
        if servers:
            for server_id, ip, location, botnet_name in servers:
                print(f"  ID: {server_id}, IP: {ip}, Location: {location}, Botnet: {botnet_name}")
        else:
            print("  未找到 utg-q-008 的C2服务器记录")
        
        conn.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_tables()
