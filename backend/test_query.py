"""测试SQL查询"""
import pymysql
import time

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'botnet',
    'charset': 'utf8mb4'
}

try:
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    botnet_type = 'asruex'
    table_name = f"botnet_nodes_{botnet_type}"
    
    print(f"Testing query on {table_name}...")
    
    # 测试简单查询
    start = time.time()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"Total rows: {count} (took {time.time()-start:.2f}s)")
    
    # 测试带字段的查询
    start = time.time()
    query = f"""
        SELECT 
            id, ip, 
            first_seen, 
            last_seen, 
            created_time
        FROM {table_name}
        WHERE longitude IS NOT NULL
        AND latitude IS NOT NULL
        LIMIT 5
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    print(f"Sample query: {len(rows)} rows (took {time.time()-start:.2f}s)")
    
    if rows:
        print(f"First row: {rows[0]}")
    
    print("\nQuery test completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
