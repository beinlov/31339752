"""检查统计表数据"""
import pymysql

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
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    botnet_type = 'ramnit'
    
    # 检查china_botnet表
    china_table = f"china_botnet_{botnet_type}"
    print(f"Checking {china_table}...")
    print("=" * 80)
    
    cursor.execute(f"SELECT * FROM {china_table} LIMIT 10")
    rows = cursor.fetchall()
    
    if rows:
        print(f"Found {len(rows)} rows")
        print(f"\nColumns: {list(rows[0].keys())}")
        print(f"\nFirst few rows:")
        for i, row in enumerate(rows[:5], 1):
            print(f"{i}. province={row.get('province')}, city={row.get('city')}, count={row.get('count')}, communication_count={row.get('communication_count')}")
    else:
        print("No data found!")
    
    print("\n" + "=" * 80)
    
    # 检查global_botnet表
    global_table = f"global_botnet_{botnet_type}"
    print(f"\nChecking {global_table}...")
    print("=" * 80)
    
    cursor.execute(f"SELECT * FROM {global_table} LIMIT 10")
    rows = cursor.fetchall()
    
    if rows:
        print(f"Found {len(rows)} rows")
        print(f"\nColumns: {list(rows[0].keys())}")
        print(f"\nFirst few rows:")
        for i, row in enumerate(rows[:5], 1):
            print(f"{i}. country={row.get('country')}, count={row.get('count')}, communication_count={row.get('communication_count')}")
    else:
        print("No data found!")
    
    print("\n" + "=" * 80)
    
    # 检查节点表的省份数据
    node_table = f"botnet_nodes_{botnet_type}"
    print(f"\nChecking province/city in {node_table}...")
    print("=" * 80)
    
    cursor.execute(f"""
        SELECT province, city, COUNT(*) as count
        FROM {node_table}
        WHERE country = '中国'
        GROUP BY province, city
        ORDER BY count DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    
    if rows:
        print(f"Top 10 province/city combinations:")
        for i, row in enumerate(rows, 1):
            print(f"{i}. {row['province']} - {row['city']}: {row['count']}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
