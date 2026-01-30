#!/usr/bin/env python3
"""
用简单的方法找出多余的记录
"""
import pymysql
import sys
sys.path.append('/home/spider/31339752/backend')
from config import DB_CONFIG

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

# 统一字符集
cursor.execute("SET NAMES utf8mb4")

botnet_type = 'ramnit'
node_table = f"botnet_nodes_{botnet_type}"
china_table = f"china_botnet_{botnet_type}"

print("=" * 100)
print("🔍 用简单方法找出数据不一致的原因")
print("=" * 100)

# 1. 查看 china_botnet 表的所有记录
print("\n【步骤1】获取 china_botnet_ramnit 表的所有记录...")
cursor.execute(f"""
    SELECT 
        province,
        municipality,
        infected_num
    FROM {china_table}
    ORDER BY province, municipality
""")

china_records = {}  # {(province, municipality): infected_num}
china_sum = 0
for prov, muni, num in cursor.fetchall():
    china_records[(prov, muni)] = num
    china_sum += num

print(f"china_botnet 表: {len(china_records)} 条记录, 节点总和 = {china_sum:,}")

# 2. 模拟聚合器查询，获取应该有的记录
print("\n【步骤2】模拟聚合器查询，获取应该有的记录...")
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
    ORDER BY t.province, t.municipality
""")

expected_records = {}  # {(province, municipality): infected_num}
expected_sum = 0
for prov, muni, num in cursor.fetchall():
    expected_records[(prov, muni)] = num
    expected_sum += num

print(f"应该有的记录: {len(expected_records)} 条记录, 节点总和 = {expected_sum:,}")

# 3. 对比找出差异
print("\n" + "=" * 100)
print("📊 对比分析")
print("=" * 100)

# 3.1 找出多余的记录（在china_botnet中有，但不应该有）
extra_records = []
for key in china_records:
    if key not in expected_records:
        extra_records.append((key, china_records[key]))

if extra_records:
    print(f"\n🔥 找到 {len(extra_records)} 条多余的记录：")
    print("\n" + "-" * 80)
    print(f"{'省份':20} | {'城市':20} | {'节点数':>8}")
    print("-" * 80)
    
    extra_sum = 0
    for (prov, muni), num in extra_records:
        extra_sum += num
        print(f"{prov:20} | {muni:20} | {num:>8}")
    
    print("-" * 80)
    print(f"多余记录的节点数总和: {extra_sum:,}")
    
    if extra_sum == 18:
        print(f"\n✅ 完美！这 {len(extra_records)} 条记录的节点数总和正好是 18！")
else:
    print("\n✅ 没有多余的记录")

# 3.2 找出缺失的记录（应该有但china_botnet中没有）
missing_records = []
for key in expected_records:
    if key not in china_records:
        missing_records.append((key, expected_records[key]))

if missing_records:
    print(f"\n⚠️  找到 {len(missing_records)} 条缺失的记录：")
    print("\n" + "-" * 80)
    print(f"{'省份':20} | {'城市':20} | {'节点数':>8}")
    print("-" * 80)
    
    missing_sum = 0
    for (prov, muni), num in missing_records[:20]:  # 只显示前20个
        missing_sum += num
        print(f"{prov:20} | {muni:20} | {num:>8}")
    
    if len(missing_records) > 20:
        print(f"... 还有 {len(missing_records) - 20} 条缺失记录")
    
    print("-" * 80)
    print(f"缺失记录的节点数总和: {missing_sum:,}")
else:
    print("\n✅ 没有缺失的记录")

# 3.3 找出节点数不一致的记录
mismatch_records = []
for key in china_records:
    if key in expected_records:
        if china_records[key] != expected_records[key]:
            mismatch_records.append((key, china_records[key], expected_records[key]))

if mismatch_records:
    print(f"\n⚠️  找到 {len(mismatch_records)} 条节点数不一致的记录：")
    print("\n" + "-" * 100)
    print(f"{'省份':20} | {'城市':20} | {'表中值':>8} | {'应该值':>8} | {'差异':>8}")
    print("-" * 100)
    
    mismatch_sum = 0
    for (prov, muni), china_val, expected_val in mismatch_records[:20]:
        diff = china_val - expected_val
        mismatch_sum += diff
        print(f"{prov:20} | {muni:20} | {china_val:>8} | {expected_val:>8} | {diff:>8}")
    
    if len(mismatch_records) > 20:
        print(f"... 还有 {len(mismatch_records) - 20} 条不一致记录")
    
    print("-" * 100)
    print(f"不一致记录的差异总和: {mismatch_sum:,}")
else:
    print("\n✅ 所有记录的节点数都一致")

# 4. 总结
print("\n" + "=" * 100)
print("📋 总结")
print("=" * 100)

print(f"""
china_botnet_ramnit 表:
  记录数: {len(china_records):,}
  节点总和: {china_sum:,}

应该有的记录:
  记录数: {len(expected_records):,}
  节点总和: {expected_sum:,}

差异:
  多余记录: {len(extra_records):,} 条 (节点数: {sum(num for _, num in extra_records):,})
  缺失记录: {len(missing_records):,} 条 (节点数: {sum(num for _, num in missing_records):,})
  不一致记录: {len(mismatch_records):,} 条 (差异: {sum(c-e for _, c, e in mismatch_records):,})
  
  总差异: {china_sum - expected_sum:,} 个节点

结论:
""")

if len(extra_records) > 0 and sum(num for _, num in extra_records) == 18:
    print(f"  ✅ 找到了！有 {len(extra_records)} 条多余的记录，包含 18 个节点")
    print(f"     这些记录是历史遗留数据或聚合器错误创建的")
elif len(mismatch_records) > 0 and sum(c-e for _, c, e in mismatch_records) == 18:
    print(f"  ✅ 找到了！有 {len(mismatch_records)} 条记录的节点数不正确")
    print(f"     总共多计数了 18 个节点")
else:
    print(f"  需要进一步分析...")

cursor.close()
conn.close()
