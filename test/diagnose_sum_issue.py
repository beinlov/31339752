#!/usr/bin/env python3
"""
诊断 china_botnet 表的 SUM(infected_num) 为什么比实际IP数多
"""
import pymysql
import sys
sys.path.append('/home/spider/31339752/backend')
from config import DB_CONFIG

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

botnet_type = 'ramnit'
node_table = f"botnet_nodes_{botnet_type}"
china_table = f"china_botnet_{botnet_type}"

print("=" * 100)
print("🔬 诊断 china_botnet 表的 SUM 计算问题")
print("=" * 100)

# 1. 查看 china_botnet 表的总和
print("\n【测试1】china_botnet_ramnit 表的统计")
print("-" * 100)
cursor.execute(f"SELECT SUM(infected_num) FROM {china_table}")
china_sum = cursor.fetchone()[0] or 0
print(f"SUM(infected_num) = {china_sum:,}")

cursor.execute(f"SELECT COUNT(*) FROM {china_table}")
china_rows = cursor.fetchone()[0]
print(f"总记录数 = {china_rows:,}")

# 2. 从 botnet_nodes 统计实际的唯一IP数
print("\n【测试2】从 botnet_nodes_ramnit 统计实际的中国唯一IP数")
print("-" * 100)
cursor.execute(f"""
    SELECT COUNT(DISTINCT ip) 
    FROM {node_table} 
    WHERE country = '中国'
""")
actual_unique_ips = cursor.fetchone()[0]
print(f"COUNT(DISTINCT ip) = {actual_unique_ips:,}")

diff = china_sum - actual_unique_ips
print(f"\n💡 差异: {diff:,} 个")
print(f"   china_botnet SUM(infected_num) = {china_sum:,}")
print(f"   实际唯一IP数                  = {actual_unique_ips:,}")

if diff == 18:
    print(f"\n✅ 找到了！这就是 18 个节点差异的根源！")
else:
    print(f"\n差异是 {diff} 个，不是预期的 18 个")

# 3. 验证聚合器的逻辑
print("\n" + "=" * 100)
print("🔍 验证聚合器的统计逻辑")
print("=" * 100)

print("\n聚合器使用的查询逻辑:")
print("""
SELECT 
    province, municipality,
    COUNT(DISTINCT ip) as infected_num
FROM (...)
GROUP BY province, municipality
""")

# 4. 模拟聚合器的查询
print("\n【测试3】模拟聚合器的查询，查看每个省市组合的统计")
cursor.execute(f"""
    SELECT 
        t.province,
        t.municipality,
        COUNT(DISTINCT t.ip) as infected_num
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
    GROUP BY t.province, t.municipality
""")

results = cursor.fetchall()
total_from_groupby = sum(row[2] for row in results)

print(f"GROUP BY 后的记录数: {len(results):,}")
print(f"SUM(COUNT(DISTINCT ip)): {total_from_groupby:,}")

print(f"\n对比:")
print(f"  china_botnet 表 SUM(infected_num) = {china_sum:,}")
print(f"  模拟查询 SUM(COUNT DISTINCT)      = {total_from_groupby:,}")

if china_sum == total_from_groupby:
    print(f"\n✅ 一致！china_botnet 表的数据与聚合器逻辑一致")
else:
    print(f"\n⚠️  不一致！差异 = {abs(china_sum - total_from_groupby):,}")

# 5. 关键发现：检查是否有IP被重复计数
print("\n" + "=" * 100)
print("🎯 关键发现：检查是否有IP在多个分组中被计数")
print("=" * 100)

# 思路：如果某个IP在原始数据中的 province 或 city 有多个不同的值
# 经过子查询标准化后，可能会被归入不同的 (province, municipality) 组合
# 从而在 GROUP BY 后被计数多次

print("\n【测试4】查找在原始数据中有多个 province 或 city 值的IP")
cursor.execute(f"""
    SELECT 
        ip,
        COUNT(DISTINCT province) as province_count,
        COUNT(DISTINCT city) as city_count,
        GROUP_CONCAT(DISTINCT province ORDER BY province SEPARATOR ' | ') as provinces,
        GROUP_CONCAT(DISTINCT city ORDER BY city SEPARATOR ' | ') as cities,
        COUNT(*) as record_count
    FROM {node_table}
    WHERE country = '中国'
    GROUP BY ip
    HAVING province_count > 1 OR city_count > 1
    LIMIT 30
""")

multi_location = cursor.fetchall()
if multi_location:
    print(f"\n⚠️  找到 {len(multi_location)} 个IP有多个位置信息！")
    for ip, prov_cnt, city_cnt, provs, cities, rec_cnt in multi_location[:10]:
        print(f"\n  IP: {ip} ({rec_cnt} 条记录)")
        print(f"    省份({prov_cnt}个): {provs}")
        print(f"    城市({city_cnt}个): {cities}")
        
        # 查看这个IP在标准化后会被分到哪些组合
        cursor.execute(f"""
            SELECT DISTINCT
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
                ) as municipality
            FROM {node_table}
            WHERE country = '中国' AND ip = %s
        """, (ip,))
        
        normalized = cursor.fetchall()
        print(f"    标准化后的组合({len(normalized)}个):")
        for prov, muni in normalized:
            print(f"      ({prov}, {muni})")
else:
    print("\n✅ 没有IP有多个位置信息")

# 6. 另一种可能：检查聚合表中是否有重复的 (province, municipality) 组合
print("\n【测试5】检查 china_botnet 表中是否有重复的 (province, municipality)")
cursor.execute(f"""
    SELECT province, municipality, COUNT(*) as cnt
    FROM {china_table}
    GROUP BY province, municipality
    HAVING cnt > 1
""")
duplicates = cursor.fetchall()
if duplicates:
    print(f"\n⚠️  找到 {len(duplicates)} 个重复的组合！")
    for prov, muni, cnt in duplicates:
        print(f"  ({prov}, {muni}): {cnt} 次")
else:
    print("\n✅ 没有重复的 (province, municipality) 组合")

# 7. 最终验证：对比每个IP在两种方式下的计数次数
print("\n" + "=" * 100)
print("📊 最终验证：找出被重复计数的IP")
print("=" * 100)

# 创建临时表存储每个IP在 GROUP BY 后出现的次数
cursor.execute(f"""
    CREATE TEMPORARY TABLE IF NOT EXISTS temp_ip_count AS
    SELECT 
        ip,
        COUNT(*) as group_count
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
    GROUP BY ip, province, municipality
""")

# 查找出现在多个分组中的IP
cursor.execute("""
    SELECT ip, SUM(group_count) as total_appearances
    FROM temp_ip_count
    GROUP BY ip
    HAVING COUNT(*) > 1
    ORDER BY total_appearances DESC
    LIMIT 20
""")

repeated_ips = cursor.fetchall()
if repeated_ips:
    print(f"\n🔥 找到了！有 {len(repeated_ips)} 个IP在多个分组中出现（显示前20个）:")
    total_extra = 0
    for ip, appearances in repeated_ips:
        extra = appearances - 1
        total_extra += extra
        print(f"  {ip}: 出现在 {appearances} 个分组中（多计数 {extra} 次）")
    
    print(f"\n总共多计数: {total_extra:,} 次")
    if total_extra == diff:
        print(f"✅ 完美匹配！这就是导致 {diff} 个节点差异的原因！")
else:
    print("\n未找到被重复计数的IP")

cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_ip_count")

print("\n" + "=" * 100)
print("📋 结论")
print("=" * 100)
print(f"""
china_botnet_ramnit 表的统计方式:
  1. 按 (province, municipality) 分组
  2. 每组计算 COUNT(DISTINCT ip)
  3. 最后 SUM(infected_num)

如果某个IP的原始数据中 province 或 city 字段有多个不同值,
经过标准化处理后,可能会被归入多个不同的 (province, municipality) 组合,
从而在 SUM 时被重复计数。

实际唯一IP数:     {actual_unique_ips:,}
china_botnet SUM:  {china_sum:,}
差异:              {diff:,}

这就是导致三个界面数据不一致的根本原因！
""")

cursor.close()
conn.close()
