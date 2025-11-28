#!/usr/bin/env python3
"""
检查节点的完整分布情况
"""
import pymysql
from pymysql.cursors import DictCursor
from config import DB_CONFIG

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor(DictCursor)

botnet_type = 'ramnit'
table_name = f'botnet_nodes_{botnet_type}'

print("="*70)
print(f"检查 {botnet_type} 节点的完整分布")
print("="*70)

# 1. 总节点数
cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
total = cursor.fetchone()['total']
print(f"\n总节点数: {total}")

# 2. 状态分布
cursor.execute(f"""
    SELECT 
        status,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / {total}, 2) as percentage
    FROM {table_name}
    GROUP BY status
    ORDER BY count DESC
""")
print("\n节点状态分布:")
status_dist = cursor.fetchall()
for row in status_dist:
    status = row['status'] or '(NULL)'
    print(f"  {status:<15} {row['count']:>6} 个 ({row['percentage']:>5}%)")

# 3. 完整的国家分布（不限制数量）
cursor.execute(f"""
    SELECT 
        COALESCE(country, '未知') as country,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / {total}, 2) as percentage
    FROM {table_name}
    GROUP BY country
    ORDER BY count DESC
""")
print("\n节点地理分布（完整）:")
country_dist = cursor.fetchall()
print(f"  共有 {len(country_dist)} 个国家/地区")
print("\n  前20个国家:")
for i, row in enumerate(country_dist[:20], 1):
    print(f"  {i:>2}. {row['country']:<20} {row['count']:>6} 个 ({row['percentage']:>5}%)")

# 4. 当前接口返回的数据（限制前10个）
cursor.execute(f"""
    SELECT 
        COALESCE(country, '未知') as country,
        COUNT(*) as count
    FROM {table_name}
    GROUP BY country
    ORDER BY count DESC
    LIMIT 10
""")
print("\n当前 /node-stats 接口返回的数据（LIMIT 10）:")
api_result = cursor.fetchall()
api_total = sum(row['count'] for row in api_result)
print(f"  返回 {len(api_result)} 个国家，共 {api_total} 个节点")
print(f"  覆盖率: {api_total}/{total} = {api_total*100/total:.2f}%")
print(f"  缺失: {total - api_total} 个节点未在图表中显示")

# 5. 中国省份分布
cursor.execute(f"""
    SELECT 
        COALESCE(province, '未知') as province,
        COUNT(*) as count
    FROM {table_name}
    WHERE country = '中国'
    GROUP BY province
    ORDER BY count DESC
    LIMIT 10
""")
print("\n中国省份分布（前10）:")
for row in cursor.fetchall():
    print(f"  {row['province']:<20} {row['count']:>6} 个节点")

cursor.close()
conn.close()

print("\n" + "="*70)
print("问题总结:")
print("="*70)
print("""
1. 当前 /node-stats 接口使用 LIMIT 10，只返回前10个国家
2. 如果有超过10个国家，其他国家的节点不会显示在图表中
3. 前端如果使用分页数据绘图，只会显示当前页的节点（默认100-1000条）

建议解决方案:
1. 为图表创建专用的统计接口，返回所有国家/状态的完整分布
2. 或者增加参数控制是否限制数量，如 limit=None 表示不限制
3. 前端应该使用统计数据（statistics）而不是分页数据（nodes）绘制图表
""")
print("="*70)
