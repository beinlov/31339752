"""测试优化后的查询性能"""
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
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    botnet_type = 'asruex'
    table_name = f"botnet_nodes_{botnet_type}"
    
    print(f"Testing optimized queries on {table_name}...")
    print("=" * 60)
    
    # 测试优化后的count查询
    start = time.time()
    count_query = f"""
        SELECT COUNT(*) as total 
        FROM {table_name} n
        WHERE n.longitude IS NOT NULL AND n.latitude IS NOT NULL
    """
    cursor.execute(count_query)
    total = cursor.fetchone()['total']
    count_time = time.time() - start
    print(f"1. Count query: {total} rows (took {count_time:.3f}s)")
    
    # 测试主查询（前10条）
    start = time.time()
    main_query = f"""
        SELECT 
            COALESCE(CONCAT(n.id, ''), '') as id,
            COALESCE(n.ip, '') as ip,
            COALESCE(n.longitude, 0) as longitude,
            COALESCE(n.latitude, 0) as latitude,
            CASE 
                WHEN n.status = 'active' THEN 'active'
                ELSE 'inactive'
            END as status,
            COALESCE(n.last_seen, n.created_time, NOW()) as last_active,
            COALESCE(n.first_seen, n.created_time, NOW()) as active_time,
            %s as botnet_type,
            COALESCE(n.country, '') as country,
            COALESCE(n.province, '') as province,
            COALESCE(n.city, '') as city
        FROM {table_name} n
        WHERE n.longitude IS NOT NULL
        AND n.latitude IS NOT NULL
        LIMIT 10
    """
    cursor.execute(main_query, (botnet_type,))
    nodes = cursor.fetchall()
    main_time = time.time() - start
    print(f"2. Main query: {len(nodes)} rows (took {main_time:.3f}s)")
    
    # 测试状态统计查询
    start = time.time()
    status_query = f"""
        SELECT 
            COUNT(DISTINCT CASE WHEN status = 'active' THEN ip END) as active_count,
            COUNT(DISTINCT CASE WHEN status = 'inactive' THEN ip END) as inactive_count
        FROM {table_name}
    """
    cursor.execute(status_query)
    status_counts = cursor.fetchone()
    status_time = time.time() - start
    print(f"3. Status query: active={status_counts['active_count']}, inactive={status_counts['inactive_count']} (took {status_time:.3f}s)")
    
    # 测试国家分布查询
    start = time.time()
    country_query = f"""
        SELECT COALESCE(country, '未知') as country, COUNT(*) as count
        FROM {table_name}
        GROUP BY country
        ORDER BY count DESC
        LIMIT 10
    """
    cursor.execute(country_query)
    countries = cursor.fetchall()
    country_time = time.time() - start
    print(f"4. Country query: {len(countries)} countries (took {country_time:.3f}s)")
    
    total_time = count_time + main_time + status_time + country_time
    print("=" * 60)
    print(f"Total API call time: {total_time:.3f}s")
    
    if total_time < 5:
        print("OK: Query performance is acceptable (<5s)")
    else:
        print("WARNING: Query might timeout (>5s)")
    
    if nodes:
        print(f"\nSample node: IP={nodes[0]['ip']}, active_time={nodes[0]['active_time']}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
