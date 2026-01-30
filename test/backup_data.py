#!/usr/bin/env python3
"""备份关键数据"""
import pymysql
import json
import sys
from datetime import datetime
sys.path.append('/home/spider/31339752/backend')
from config import DB_CONFIG

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

backup_file = f"/home/spider/31339752/backup_ramnit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

print("=" * 80)
print("备份 Ramnit 数据...")
print("=" * 80)

backup_data = {}

# 备份受影响的记录
print("\n1. 备份将被修改的 botnet_nodes_ramnit 记录...")
cursor.execute("""
    SELECT id, ip, province, city, country, created_time, updated_at
    FROM botnet_nodes_ramnit
    WHERE country = '中国'
      AND province IN ('内蒙古自治区', '西藏自治区')
""")
backup_data['nodes_to_update'] = [
    {
        'id': row[0], 'ip': row[1], 'province': row[2], 'city': row[3],
        'country': row[4], 'created_time': str(row[5]), 'updated_at': str(row[6])
    }
    for row in cursor.fetchall()
]
print(f"   备份了 {len(backup_data['nodes_to_update'])} 条节点记录")

# 备份将被删除的聚合记录
print("\n2. 备份将被删除的 china_botnet_ramnit 记录...")
cursor.execute("""
    SELECT id, province, municipality, infected_num, created_at, updated_at
    FROM china_botnet_ramnit
    WHERE province IN ('内蒙古自治区', '西藏自治区')
""")
backup_data['aggregation_to_delete'] = [
    {
        'id': row[0], 'province': row[1], 'municipality': row[2],
        'infected_num': row[3], 'created_at': str(row[4]), 'updated_at': str(row[5])
    }
    for row in cursor.fetchall()
]
print(f"   备份了 {len(backup_data['aggregation_to_delete'])} 条聚合记录")

# 保存备份
with open(backup_file, 'w', encoding='utf-8') as f:
    json.dump(backup_data, f, ensure_ascii=False, indent=2)

print(f"\n✅ 备份完成！文件保存在: {backup_file}")
print(f"   节点记录: {len(backup_data['nodes_to_update'])} 条")
print(f"   聚合记录: {len(backup_data['aggregation_to_delete'])} 条")

cursor.close()
conn.close()
