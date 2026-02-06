#!/usr/bin/env python3
"""
找出 china_botnet 表中多余的18条记录
"""
import pymysql
import sys
sys.path.append('/home/spider/31339752/backend')
from config import DB_CONFIG

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

# 统一字符集设置
cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_general_ci")
cursor.execute("SET collation_connection = 'utf8mb4_general_ci'")

botnet_type = 'ramnit'
node_table = f"botnet_nodes_{botnet_type}"
china_table = f"china_botnet_{botnet_type}"

print("=" * 100)
print("🔍 找出 china_botnet_ramnit 表中多余的18条记录")
print("=" * 100)

# 1. 创建临时表存储应该有的记录
print("\n【步骤1】创建临时表，存储应该有的记录...")
cursor.execute(f"DROP TEMPORARY TABLE IF EXISTS temp_expected_china")
cursor.execute(f"""
    CREATE TEMPORARY TABLE temp_expected_china AS
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

cursor.execute("SELECT COUNT(*) FROM temp_expected_china")
expected_count = cursor.fetchone()[0]
print(f"应该有的记录数: {expected_count:,}")

# 2. 查找在 china_botnet 表中存在，但不应该存在的记录
print(f"\n【步骤2】查找 china_botnet 表中多余的记录...")
cursor.execute(f"""
    SELECT 
        c.id,
        c.province,
        c.municipality,
        c.infected_num,
        c.created_at,
        c.updated_at
    FROM {china_table} c
    LEFT JOIN temp_expected_china e 
        ON c.province = e.province AND c.municipality = e.municipality
    WHERE e.province IS NULL
    ORDER BY c.id
""")

extra_records = cursor.fetchall()
if extra_records:
    print(f"\n🔥 找到 {len(extra_records)} 条多余的记录：")
    print("\n" + "-" * 100)
    print(f"{'ID':>6} | {'省份':20} | {'城市':20} | {'节点数':>8} | 创建时间 | 更新时间")
    print("-" * 100)
    
    extra_sum = 0
    for record in extra_records:
        id, prov, muni, num, created, updated = record
        extra_sum += num
        created_str = created.strftime('%Y-%m-%d %H:%M:%S') if created else 'NULL'
        updated_str = updated.strftime('%Y-%m-%d %H:%M:%S') if updated else 'NULL'
        print(f"{id:>6} | {prov:20} | {muni:20} | {num:>8} | {created_str} | {updated_str}")
    
    print("-" * 100)
    print(f"多余记录的节点数总和: {extra_sum:,}")
    
    if extra_sum == 18:
        print(f"\n✅ 完美匹配！这 {len(extra_records)} 条记录的节点数总和正好是 18！")
    else:
        print(f"\n⚠️  节点数总和 ({extra_sum}) 不等于差异 (18)")
else:
    print("\n未找到多余的记录")

# 3. 反向检查：查找应该有但实际没有的记录
print(f"\n【步骤3】查找应该有但在 china_botnet 表中缺失的记录...")
cursor.execute(f"""
    SELECT 
        e.province,
        e.municipality,
        e.infected_num
    FROM temp_expected_china e
    LEFT JOIN {china_table} c 
        ON e.province = c.province AND e.municipality = c.municipality
    WHERE c.province IS NULL
    ORDER BY e.infected_num DESC
    LIMIT 20
""")

missing_records = cursor.fetchall()
if missing_records:
    print(f"\n⚠️  找到 {len(missing_records)} 条缺失的记录（显示前20个）：")
    print("\n" + "-" * 80)
    print(f"{'省份':20} | {'城市':20} | {'节点数':>8}")
    print("-" * 80)
    
    missing_sum = 0
    for prov, muni, num in missing_records:
        missing_sum += num
        print(f"{prov:20} | {muni:20} | {num:>8}")
    
    print("-" * 80)
    print(f"缺失记录的节点数总和: {missing_sum:,}")
else:
    print("\n✅ 没有缺失的记录")

# 4. 检查这些多余记录对应的原始数据
if extra_records:
    print("\n" + "=" * 100)
    print("🔬 检查多余记录对应的原始数据")
    print("=" * 100)
    
    for id, prov, muni, num, _, _ in extra_records[:5]:  # 只检查前5个
        print(f"\n检查: ({prov}, {muni}) - {num} 个节点")
        print("-" * 100)
        
        # 查找原始数据
        cursor.execute(f"""
            SELECT COUNT(*), COUNT(DISTINCT ip)
            FROM {node_table}
            WHERE country = '中国'
                AND COALESCE(
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
                ) = %s
                AND COALESCE(
                    TRIM(TRAILING '市' FROM city),
                    '未知'
                ) = %s
        """, (prov, muni))
        
        count, distinct_ip = cursor.fetchone()
        print(f"  原始数据: {count} 条记录, {distinct_ip} 个唯一IP")
        
        if distinct_ip == 0:
            print(f"  ⚠️  原始数据中没有对应的记录！这是一条孤立的记录！")
        elif distinct_ip != num:
            print(f"  ⚠️  节点数不匹配：表中 {num}, 实际 {distinct_ip}")

# 5. 总结
print("\n" + "=" * 100)
print("📊 总结")
print("=" * 100)

cursor.execute(f"SELECT COUNT(*), SUM(infected_num) FROM {china_table}")
actual_count, actual_sum = cursor.fetchone()

cursor.execute("SELECT COUNT(*), SUM(infected_num) FROM temp_expected_china")
expected_count_final, expected_sum = cursor.fetchone()

print(f"""
china_botnet_ramnit 表:
  记录数: {actual_count:,}
  节点数总和: {actual_sum:,}

应该有的记录:
  记录数: {expected_count_final:,}
  节点数总和: {expected_sum:,}

差异:
  多余记录: {actual_count - expected_count_final:,} 条
  多余节点: {actual_sum - expected_sum:,} 个

结论:
  china_botnet 表中有 {actual_count - expected_count_final} 条不应该存在的记录,
  这些记录包含 {actual_sum - expected_sum} 个节点,
  导致 SUM(infected_num) 比实际的唯一IP数多了 {actual_sum - expected_sum} 个。
  
  这就是三个界面数据不一致的根本原因！
""")

cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_expected_china")
cursor.close()
conn.close()
