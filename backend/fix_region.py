import pymysql
from config import DB_CONFIG

conn = pymysql.connect(**DB_CONFIG)
cur = conn.cursor()

try:
    # Update rows where country contains HK characters
    sql = "UPDATE botnet_nodes_utg_q_008 SET country=0xE4B8ADE59BBD, province=0xE9A699E6B8AF WHERE country LIKE CONCAT('%', 0xE9A699E6B8AF, '%')"
    cur.execute(sql)
    updated = cur.rowcount
    conn.commit()
    print(f'Updated {updated} rows')
    
    # Verify
    cur.execute("SELECT COUNT(*) FROM botnet_nodes_utg_q_008 WHERE province=0xE9A699E6B8AF")
    count = cur.fetchone()[0]
    print(f'Total HK rows: {count}')
    
finally:
    cur.close()
    conn.close()
