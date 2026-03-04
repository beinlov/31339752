import pymysql
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from config import DB_CONFIG

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

print("=" * 70)
print("botnet_types 表中的所有记录:")
print("=" * 70)
cursor.execute("SELECT name, display_name, table_name FROM botnet_types ORDER BY name")
for name, display, table in cursor.fetchall():
    print(f"  name: {name:20} | display: {display:25} | table: {table}")

print("\n" + "=" * 70)
print("所有节点表:")
print("=" * 70)
cursor.execute("SHOW TABLES LIKE 'botnet_nodes_%'")
for (table,) in cursor.fetchall():
    cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
    count = cursor.fetchone()[0]
    print(f"  {table:40} | {count:10} nodes")

print("\n" + "=" * 70)
print("server_management 中的 utg-q-008:")
print("=" * 70)
cursor.execute("SELECT id, ip, location, Botnet_Name FROM server_management WHERE Botnet_Name LIKE '%utg%'")
for row in cursor.fetchall():
    print(f"  ID: {row[0]}, IP: {row[1]}, Location: {row[2]}, Botnet: {row[3]}")

conn.close()
