#!/usr/bin/env python3
"""重建 Ramnit 聚合表"""
import pymysql
import sys
import os
sys.path.append('/home/spider/31339752/backend')
from config import DB_CONFIG

# 导入聚合器
sys.path.append('/home/spider/31339752/backend/stats_aggregator')
from aggregator import StatsAggregator

print("=" * 80)
print("重建 Ramnit 聚合表")
print("=" * 80)

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

# 步骤1：删除旧的聚合表
print("\n【步骤1】删除旧的聚合表...")
cursor.execute("DROP TABLE IF EXISTS china_botnet_ramnit")
print("  ✅ 删除 china_botnet_ramnit")

cursor.execute("DROP TABLE IF EXISTS global_botnet_ramnit")
print("  ✅ 删除 global_botnet_ramnit")

conn.commit()
cursor.close()
conn.close()

# 步骤2：重新运行聚合器
print("\n【步骤2】重新运行聚合器...")
print("-" * 80)

aggregator = StatsAggregator(DB_CONFIG)
result = aggregator.aggregate_botnet_stats('ramnit')

print("-" * 80)

if result.get('success'):
    print(f"\n✅ 聚合成功！")
    print(f"  - 中国统计记录: {result.get('china_rows', 0):,} 条")
    print(f"  - 全球统计记录: {result.get('global_rows', 0):,} 条")
    print(f"  - 原始节点数: {result.get('node_count', 0):,} 个")
else:
    print(f"\n❌ 聚合失败: {result.get('error', '未知错误')}")
    sys.exit(1)

# 步骤3：验证结果
print("\n【步骤3】验证聚合结果...")
conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*), SUM(infected_num) FROM china_botnet_ramnit")
china_count, china_sum = cursor.fetchone()

cursor.execute("SELECT COUNT(*), SUM(infected_num) FROM global_botnet_ramnit")
global_count, global_sum = cursor.fetchone()

cursor.execute("SELECT SUM(infected_num) FROM global_botnet_ramnit WHERE country = '中国'")
china_in_global = cursor.fetchone()[0] or 0

cursor.execute("SELECT SUM(infected_num) FROM global_botnet_ramnit WHERE country != '中国'")
non_china_in_global = cursor.fetchone()[0] or 0

print(f"\nchina_botnet_ramnit:")
print(f"  记录数: {china_count:,}")
print(f"  节点总和: {china_sum:,}")

print(f"\nglobal_botnet_ramnit:")
print(f"  记录数: {global_count:,}")
print(f"  节点总和: {global_sum:,}")
print(f"  └─ 中国节点: {china_in_global:,}")
print(f"  └─ 非中国节点: {non_china_in_global:,}")

# 关键检查：china_botnet 和 global_botnet 中的中国节点是否一致
print(f"\n【关键检查】数据一致性验证:")
if china_sum == china_in_global:
    print(f"  ✅ china_botnet 总和 ({china_sum:,}) = global_botnet 中国节点 ({china_in_global:,})")
else:
    print(f"  ❌ 不一致！")
    print(f"     china_botnet 总和: {china_sum:,}")
    print(f"     global_botnet 中国节点: {china_in_global:,}")
    print(f"     差异: {abs(china_sum - china_in_global):,}")

# 计算全球总数
total_nodes = china_sum + non_china_in_global
print(f"\n【计算结果】")
print(f"  全球总节点数 = china_botnet + global_botnet(非中国)")
print(f"               = {china_sum:,} + {non_china_in_global:,}")
print(f"               = {total_nodes:,}")

# 检查是否还有多余的自治区记录
print(f"\n【最终检查】是否还有未标准化的自治区记录...")
cursor.execute("""
    SELECT province, municipality, infected_num
    FROM china_botnet_ramnit
    WHERE province LIKE '%自治区%'
    ORDER BY province, municipality
""")

remaining = cursor.fetchall()
if remaining:
    print(f"  ⚠️  警告：还有 {len(remaining)} 条未标准化的记录：")
    for prov, muni, num in remaining[:10]:
        print(f"    - ({prov}, {muni}): {num} 个节点")
    if len(remaining) > 10:
        print(f"    ... 还有 {len(remaining) - 10} 条")
else:
    print(f"  ✅ 所有记录已正确标准化！")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("✅ 步骤4完成：聚合表已重建")
print("=" * 80)
