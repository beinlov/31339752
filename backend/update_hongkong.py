import pymysql
from config import DB_CONFIG

conn = pymysql.connect(**DB_CONFIG)
cur = conn.cursor()

try:
    # Update Hong Kong data
    sql = "UPDATE botnet_nodes_utg_q_008 SET country='中国', province='香港' WHERE country LIKE '%香港%'"
    cur.execute(sql)
    updated = cur.rowcount
    conn.commit()
    print(f'Updated {updated} rows')
    
    # Verify
    cur.execute("SELECT COUNT(*) FROM botnet_nodes_utg_q_008 WHERE province='香港'")
    count = cur.fetchone()[0]
    print(f'Total rows with province=香港: {count}')
    
finally:
    cur.close()
    conn.close()
