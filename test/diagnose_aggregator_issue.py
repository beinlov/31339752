#!/usr/bin/env python3
"""
诊断聚合器数据不一致的具体原因
"""
import pymysql
import sys
sys.path.append('/home/spider/31339752/backend')
from config import DB_CONFIG

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

botnet_type = 'ramnit'
node_table = f"botnet_nodes_{botnet_type}"

print("=" * 100)
print("🔬 诊断聚合器数据不一致问题")
print("=" * 100)

# 1. 简单统计（对应 global_botnet 的逻辑）
print("\n【测试1】简单统计（global_botnet 的逻辑）")
print("-" * 100)
cursor.execute(f"""
    SELECT COUNT(DISTINCT ip) 
    FROM {node_table} 
    WHERE country = '中国'
""")
simple_count = cursor.fetchone()[0]
print(f"结果: {simple_count:,} 个去重IP")
print(f"对应: global_botnet_ramnit 表中的中国节点数 = 27,888")

# 2. 使用中国统计的复杂逻辑
print("\n【测试2】复杂统计（china_botnet 的逻辑 - 使用子查询）")
print("-" * 100)
cursor.execute(f"""
    SELECT COUNT(DISTINCT t.ip)
    FROM (
        SELECT 
            COALESCE(
                TRIM(TRAILING '省' FROM 
                TRIM(TRAILING '市' FROM 
                TRIM(TRAILING '自治区' FROM 
                REPLACE(REPLACE(REPLACE(
                    province, 
                    '壮族自治区', '自治区'), 
                    '回族自治区', '自治区'), 
                    '维吾尔自治区', '自治区')
                ))), 
                '未知'
            ) as province,
            COALESCE(
                TRIM(TRAILING '市' FROM city),
                '未知'
            ) as municipality,
            ip
        FROM {node_table}
        WHERE country = '中国'
    ) AS t
""")
complex_count = cursor.fetchone()[0]
print(f"结果: {complex_count:,} 个去重IP")
print(f"对应: china_botnet_ramnit 表的总节点数 = 27,906")

diff = abs(simple_count - complex_count)
print(f"\n💡 差异: {diff:,} 个节点")

# 3. 验证这是否就是我们要找的18个节点
if diff == 18:
    print(f"✅ 验证成功！这正是导致数据不一致的 18 个节点！")
else:
    print(f"⚠️  差异不是18个，而是 {diff} 个，需要进一步调查")

# 4. 查找具体是哪些节点造成的差异
print("\n" + "=" * 100)
print("🔎 查找造成差异的具体节点")
print("=" * 100)

# 方法：找出在子查询处理后会被"丢失"或"重复计数"的IP
# 先看看子查询前后，GROUP BY 的结果是否一致

# 4.1 不使用子查询，直接统计每个省市组合的IP数
print("\n【测试3】不使用子查询，查看原始数据的分布")
cursor.execute(f"""
    SELECT 
        province,
        city,
        COUNT(DISTINCT ip) as ip_count
    FROM {node_table}
    WHERE country = '中国'
    GROUP BY province, city
    ORDER BY ip_count DESC
    LIMIT 10
""")
print("\n原始数据 Top 10 省市组合:")
original_dist = cursor.fetchall()
for province, city, count in original_dist:
    print(f"  省: {province or 'NULL':20} | 市: {city or 'NULL':20} | IP数: {count:,}")

# 4.2 使用子查询后，查看标准化后的分布
print("\n【测试4】使用子查询标准化后的分布")
cursor.execute(f"""
    SELECT 
        province,
        municipality,
        COUNT(DISTINCT ip) as ip_count
    FROM (
        SELECT 
            COALESCE(
                TRIM(TRAILING '省' FROM 
                TRIM(TRAILING '市' FROM 
                TRIM(TRAILING '自治区' FROM 
                REPLACE(REPLACE(REPLACE(
                    province, 
                    '壮族自治区', '自治区'), 
                    '回族自治区', '自治区'), 
                    '维吾尔自治区', '自治区')
                ))), 
                '未知'
            ) as province,
            COALESCE(
                TRIM(TRAILING '市' FROM city),
                '未知'
            ) as municipality,
            ip
        FROM {node_table}
        WHERE country = '中国'
    ) AS t
    GROUP BY province, municipality
    ORDER BY ip_count DESC
    LIMIT 10
""")
print("\n标准化后的数据 Top 10 省市组合:")
normalized_dist = cursor.fetchall()
for province, city, count in normalized_dist:
    print(f"  省: {province:20} | 市: {city:20} | IP数: {count:,}")

# 5. 查找可能导致差异的特殊情况
print("\n" + "=" * 100)
print("🔍 查找可能导致差异的特殊数据")
print("=" * 100)

# 5.1 查找 province 或 city 为 NULL 的节点
print("\n【测试5】province 或 city 为 NULL 的节点")
cursor.execute(f"""
    SELECT 
        COUNT(DISTINCT ip) as ip_count,
        COUNT(*) as total_records
    FROM {node_table}
    WHERE country = '中国' AND (province IS NULL OR city IS NULL)
""")
null_result = cursor.fetchone()
print(f"IP数: {null_result[0]:,}, 记录数: {null_result[1]:,}")

# 5.2 查找 province 或 city 为空字符串的节点
print("\n【测试6】province 或 city 为空字符串的节点")
cursor.execute(f"""
    SELECT 
        COUNT(DISTINCT ip) as ip_count,
        COUNT(*) as total_records
    FROM {node_table}
    WHERE country = '中国' AND (province = '' OR city = '')
""")
empty_result = cursor.fetchone()
print(f"IP数: {empty_result[0]:,}, 记录数: {empty_result[1]:,}")

# 5.3 查找同一个IP在多个省市出现的情况（这会导致去重后数量不同）
print("\n【测试7】同一个IP出现在多个省市的情况")
cursor.execute(f"""
    SELECT 
        ip,
        COUNT(DISTINCT province) as province_count,
        COUNT(DISTINCT city) as city_count,
        GROUP_CONCAT(DISTINCT province ORDER BY province SEPARATOR ', ') as provinces,
        GROUP_CONCAT(DISTINCT city ORDER BY city SEPARATOR ', ') as cities
    FROM {node_table}
    WHERE country = '中国'
    GROUP BY ip
    HAVING province_count > 1 OR city_count > 1
    LIMIT 20
""")
multi_location_ips = cursor.fetchall()
if multi_location_ips:
    print(f"\n找到 {len(multi_location_ips)} 个IP出现在多个位置（显示前20个）:")
    for ip, prov_cnt, city_cnt, provs, cities in multi_location_ips:
        print(f"  IP: {ip}")
        print(f"    省份({prov_cnt}个): {provs}")
        print(f"    城市({city_cnt}个): {cities}")
        print()
else:
    print("✅ 没有IP出现在多个位置")

# 6. 最关键的测试：找出在两种统计方式下数量不同的原因
print("\n" + "=" * 100)
print("🎯 找出 18 个差异节点的具体原因")
print("=" * 100)

# 思路：如果简单统计是27888，复杂统计是27906，说明复杂统计多了18个
# 这可能是因为：
# 1. 某些IP在原始数据中出现多次，经过GROUP BY后被正确计数
# 2. 子查询的标准化逻辑导致某些分组合并，从而正确统计了IP数量

print("\n【测试8】检查是否是 GROUP BY 导致的统计差异")
print("统计每个IP在原始数据中出现的次数...")

cursor.execute(f"""
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT ip) as unique_ips
    FROM {node_table}
    WHERE country = '中国'
""")
record_stats = cursor.fetchone()
print(f"总记录数: {record_stats[0]:,}")
print(f"唯一IP数: {record_stats[1]:,}")
print(f"平均每个IP的记录数: {record_stats[0] / record_stats[1]:.2f}")

# 查找有多条记录的IP
cursor.execute(f"""
    SELECT 
        ip,
        COUNT(*) as record_count,
        GROUP_CONCAT(DISTINCT province ORDER BY province SEPARATOR ' | ') as provinces,
        GROUP_CONCAT(DISTINCT city ORDER BY city SEPARATOR ' | ') as cities
    FROM {node_table}
    WHERE country = '中国'
    GROUP BY ip
    HAVING COUNT(*) > 1
    ORDER BY record_count DESC
    LIMIT 20
""")
duplicate_ips = cursor.fetchall()
if duplicate_ips:
    print(f"\n找到 {len(duplicate_ips)} 个有多条记录的IP（显示前20个）:")
    for ip, count, provs, cities in duplicate_ips:
        print(f"  {ip}: {count} 条记录")
        print(f"    省份: {provs}")
        print(f"    城市: {cities}")
else:
    print("\n✅ 所有IP都只有一条记录")

print("\n" + "=" * 100)
print("📊 总结")
print("=" * 100)
print(f"\n简单统计（global_botnet逻辑）: {simple_count:,} 个IP")
print(f"复杂统计（china_botnet逻辑）:  {complex_count:,} 个IP")
print(f"差异:                          {diff:,} 个IP")

print("\n可能的原因:")
if diff > 0:
    if complex_count > simple_count:
        print("  ✓ 复杂统计（china_botnet）的结果更大")
        print("  ✓ 这说明子查询的处理逻辑导致了不同的统计结果")
        print("  ✓ 可能是因为子查询在处理前进行了数据转换，影响了后续的 COUNT(DISTINCT ip)")
    else:
        print("  ✓ 简单统计（global_botnet）的结果更大")
        print("  ✓ 这说明子查询可能过滤掉了一些数据")

cursor.close()
conn.close()
