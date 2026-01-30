#!/usr/bin/env python3
"""标准化省份名称"""
import pymysql
import sys
sys.path.append('/home/spider/31339752/backend')
from config import DB_CONFIG

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

print("=" * 80)
print("标准化 botnet_nodes_ramnit 表中的省份名称")
print("=" * 80)

# 查看修改前的数据
print("\n【修改前】查看受影响的数据...")
cursor.execute("""
    SELECT province, COUNT(*) as cnt, COUNT(DISTINCT ip) as unique_ips
    FROM botnet_nodes_ramnit
    WHERE country = '中国'
      AND province IN ('内蒙古自治区', '西藏自治区')
    GROUP BY province
""")

before_data = cursor.fetchall()
print("\n省份名称格式:")
for province, cnt, ips in before_data:
    print(f"  {province:20} | {cnt:>4} 条记录 | {ips:>4} 个唯一IP")

# 执行标准化
print("\n【执行标准化】更新省份名称...")
cursor.execute("""
    UPDATE botnet_nodes_ramnit
    SET province = CASE
        WHEN province = '内蒙古自治区' THEN '内蒙古'
        WHEN province = '西藏自治区' THEN '西藏'
        ELSE province
    END
    WHERE country = '中国'
      AND province IN ('内蒙古自治区', '西藏自治区')
""")

affected_rows = cursor.rowcount
conn.commit()

print(f"✅ 成功更新 {affected_rows} 条记录")

# 验证修改后的数据
print("\n【修改后】验证数据...")
cursor.execute("""
    SELECT province, COUNT(*) as cnt, COUNT(DISTINCT ip) as unique_ips
    FROM botnet_nodes_ramnit
    WHERE country = '中国'
      AND province IN ('内蒙古', '西藏')
    GROUP BY province
""")

after_data = cursor.fetchall()
print("\n省份名称格式:")
for province, cnt, ips in after_data:
    print(f"  {province:20} | {cnt:>4} 条记录 | {ips:>4} 个唯一IP")

# 检查是否还有未标准化的数据
print("\n【最终检查】是否还有未标准化的省份名称...")
cursor.execute("""
    SELECT DISTINCT province
    FROM botnet_nodes_ramnit
    WHERE country = '中国'
      AND (province LIKE '%自治区%' OR province LIKE '%壮族%' OR province LIKE '%回族%' OR province LIKE '%维吾尔%')
    ORDER BY province
""")

remaining = cursor.fetchall()
if remaining:
    print(f"⚠️  还有 {len(remaining)} 个未标准化的省份:")
    for (province,) in remaining:
        print(f"  - {province}")
else:
    print("✅ 所有省份名称已标准化！")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("✅ 步骤2完成：原始数据已标准化")
print("=" * 80)
