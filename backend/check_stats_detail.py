"""详细检查统计表数据和字段"""
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
    china_table = f"china_botnet_{botnet_type}"
    
    # 检查表结构
    print(f"Table structure of {china_table}:")
    print("=" * 80)
    cursor.execute(f"DESCRIBE {china_table}")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col['Field']:20s} {col['Type']:20s} {col['Null']:5s} {col['Key']:5s}")
    
    print("\n" + "=" * 80)
    print(f"Sample data from {china_table}:")
    print("=" * 80)
    
    cursor.execute(f"""
        SELECT province, municipality, infected_num, communication_count
        FROM {china_table}
        WHERE infected_num > 0
        ORDER BY infected_num DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    
    if rows:
        for i, row in enumerate(rows, 1):
            print(f"{i}. province='{row['province']}', city='{row['municipality']}', infected_num={row['infected_num']}, comm_count={row['communication_count']}")
    else:
        print("No data with infected_num > 0")
    
    # 检查节点表的province数据编码
    print("\n" + "=" * 80)
    print(f"Province data from botnet_nodes_{botnet_type}:")
    print("=" * 80)
    
    node_table = f"botnet_nodes_{botnet_type}"
    cursor.execute(f"""
        SELECT province, city, COUNT(*) as count
        FROM {node_table}
        WHERE country = '中国' AND province IS NOT NULL AND province != ''
        GROUP BY province, city
        ORDER BY count DESC
        LIMIT 5
    """)
    
    node_rows = cursor.fetchall()
    if node_rows:
        for i, row in enumerate(node_rows, 1):
            # 打印原始字节
            province_bytes = row['province'].encode('utf-8') if row['province'] else b''
            city_bytes = row['city'].encode('utf-8') if row['city'] else b''
            print(f"{i}. province={row['province']} (bytes:{province_bytes}), city={row['city']} (bytes:{city_bytes}), count={row['count']}")
    
    print("\n" + "=" * 80)
    print("Checking if stats_aggregator needs to run...")
    print("=" * 80)
    
    # 检查统计表是否为空
    cursor.execute(f"SELECT SUM(infected_num) as total FROM {china_table}")
    total = cursor.fetchone()['total'] or 0
    
    cursor.execute(f"SELECT COUNT(*) as count FROM {node_table} WHERE country = '中国'")
    node_count = cursor.fetchone()['count']
    
    print(f"Stats table total: {total}")
    print(f"Node table count (China): {node_count}")
    
    if total == 0 and node_count > 0:
        print("\nWARNING: Stats table is empty but node table has data!")
        print("You need to run stats_aggregator to populate the stats tables.")
        print("Command: cd backend/stats_aggregator && python aggregator.py")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
