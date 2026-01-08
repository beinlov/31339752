"""快速检查迁移进度"""
import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'botnet',
    'charset': 'utf8mb4'
}

BOTNET_TYPES = ['asruex', 'mozi', 'andromeda', 'moobot', 'ramnit', 'leethozer']

try:
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("迁移进度检查")
    print("=" * 80)
    
    for botnet_type in BOTNET_TYPES:
        node_table = f"botnet_nodes_{botnet_type}"
        comm_table = f"botnet_communications_{botnet_type}"
        
        # 检查通信记录表是否存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], comm_table))
        
        comm_table_exists = cursor.fetchone()[0] > 0
        
        # 检查新字段
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s 
              AND COLUMN_NAME IN ('first_seen', 'last_seen', 'communication_count')
        """, (DB_CONFIG['database'], node_table))
        
        new_fields = [row[0] for row in cursor.fetchall()]
        
        # 统计数据
        cursor.execute(f"SELECT COUNT(*) FROM {node_table}")
        node_count = cursor.fetchone()[0]
        
        if comm_table_exists:
            cursor.execute(f"SELECT COUNT(*) FROM {comm_table}")
            comm_count = cursor.fetchone()[0]
        else:
            comm_count = 0
        
        status = "DONE" if (comm_table_exists and len(new_fields) == 3) else "PENDING"
        
        print(f"\n{botnet_type}:")
        print(f"  状态: {status}")
        print(f"  通信表存在: {'是' if comm_table_exists else '否'}")
        print(f"  新字段: {', '.join(new_fields) if new_fields else '无'}")
        print(f"  节点数: {node_count}")
        print(f"  通信记录数: {comm_count}")
    
    print("\n" + "=" * 80)
    
except Exception as e:
    print(f"错误: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
