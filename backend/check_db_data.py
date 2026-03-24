import pymysql
from config import DB_CONFIG

conn = None
cursor = None

try:
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    table_name = "botnet_communications_utg_q_008"
    
    print("\n" + "="*80)
    print(f"Querying table: {table_name}")
    print("="*80 + "\n")
    
    query = """
        SELECT 
            DATE_FORMAT(communication_time, '%Y-%m-%d %H:%i:%s') as time,
            ip,
            country,
            province,
            city,
            status,
            unit,
            industry
        FROM botnet_communications_utg_q_008
        ORDER BY communication_time DESC
        LIMIT 5
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"Found {len(results)} records\n")
    
    for i, row in enumerate(results, 1):
        print(f"Record {i}:")
        print(f"  time: {row['time']}")
        print(f"  ip: {row['ip']}")
        print(f"  country: {row['country']}")
        print(f"  province: {row['province']}")
        print(f"  city: {row['city']}")
        print(f"  status: {row['status']}")
        print(f"  unit: {row['unit']}")
        print(f"  industry: {row['industry']}")
        print()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
