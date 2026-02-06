#!/usr/bin/env python3
"""
验证所有僵尸网络的数据一致性
"""
import pymysql
import sys
sys.path.append('/home/spider/31339752/backend')
from config import DB_CONFIG, BOTNET_TYPES

print("=" * 120)
print("验证所有僵尸网络的数据一致性")
print("=" * 120)

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

results = []

for botnet_type in BOTNET_TYPES:
    node_table = f"botnet_nodes_{botnet_type}"
    china_table = f"china_botnet_{botnet_type}"
    global_table = f"global_botnet_{botnet_type}"
    
    # 检查节点表是否存在
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = %s AND table_name = %s
    """, (DB_CONFIG['database'], node_table))
    
    if cursor.fetchone()[0] == 0:
        continue
    
    # 检查聚合表是否存在
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = %s AND table_name = %s
    """, (DB_CONFIG['database'], china_table))
    
    if cursor.fetchone()[0] == 0:
        continue
    
    # 获取数据
    cursor.execute(f"SELECT COUNT(*) FROM {node_table}")
    node_count = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*), SUM(infected_num) FROM {china_table}")
    china_rows, china_sum = cursor.fetchone()
    china_sum = china_sum or 0
    
    cursor.execute(f"SELECT COUNT(*), SUM(infected_num) FROM {global_table}")
    global_rows, global_sum = cursor.fetchone()
    global_sum = global_sum or 0
    
    cursor.execute(f"SELECT SUM(infected_num) FROM {global_table} WHERE country = '中国'")
    china_in_global = cursor.fetchone()[0] or 0
    
    cursor.execute(f"SELECT SUM(infected_num) FROM {global_table} WHERE country != '中国'")
    non_china = cursor.fetchone()[0] or 0
    
    # 检查是否有未标准化的自治区记录
    cursor.execute(f"""
        SELECT COUNT(*) FROM {china_table}
        WHERE province LIKE '%自治区%'
    """)
    bad_province_count = cursor.fetchone()[0]
    
    # 检查是否有空字符串或NULL的country
    cursor.execute(f"""
        SELECT COUNT(*) FROM {global_table}
        WHERE country IS NULL OR country = ''
    """)
    bad_country_count = cursor.fetchone()[0]
    
    # 计算差异
    diff_china = china_sum - china_in_global
    total_nodes = china_sum + non_china
    
    # 判断状态
    status = "✅" if diff_china == 0 and bad_province_count == 0 and bad_country_count == 0 else "⚠️"
    
    results.append({
        'type': botnet_type,
        'status': status,
        'node_count': node_count,
        'china_rows': china_rows,
        'global_rows': global_rows,
        'china_sum': china_sum,
        'global_sum': global_sum,
        'china_in_global': china_in_global,
        'non_china': non_china,
        'total_nodes': total_nodes,
        'diff_china': diff_china,
        'bad_province': bad_province_count,
        'bad_country': bad_country_count
    })

cursor.close()
conn.close()

# 显示结果
print(f"\n{'类型':<15} | {'状态'} | {'节点数':>10} | {'china表':>8} | {'global表':>8} | {'一致性检查':<40}")
print("-" * 120)

for r in results:
    consistency = f"china={r['china_sum']:,} vs global中国={r['china_in_global']:,}"
    if r['diff_china'] != 0:
        consistency += f" ❌差异{r['diff_china']}"
    if r['bad_province'] > 0:
        consistency += f" ⚠️{r['bad_province']}条未标准化省份"
    if r['bad_country'] > 0:
        consistency += f" ⚠️{r['bad_country']}条空country"
    
    print(f"{r['type']:<15} | {r['status']}  | {r['node_count']:>10,} | {r['china_rows']:>8,} | {r['global_rows']:>8,} | {consistency}")

print("-" * 120)

# 统计
total_ok = sum(1 for r in results if r['status'] == "✅")
total_warning = sum(1 for r in results if r['status'] == "⚠️")

print(f"\n总计: {len(results)} 个僵尸网络")
print(f"  ✅ 数据一致: {total_ok} 个")
print(f"  ⚠️  需要检查: {total_warning} 个")

# 详细列出有问题的
if total_warning > 0:
    print(f"\n⚠️  需要检查的僵尸网络:")
    for r in results:
        if r['status'] == "⚠️":
            print(f"\n  {r['type']}:")
            if r['diff_china'] != 0:
                print(f"    - china表总和({r['china_sum']:,}) ≠ global表中国节点({r['china_in_global']:,}), 差异: {r['diff_china']}")
            if r['bad_province'] > 0:
                print(f"    - 有 {r['bad_province']} 条未标准化的省份记录")
            if r['bad_country'] > 0:
                print(f"    - 有 {r['bad_country']} 条空/NULL的country记录")
else:
    print(f"\n🎉 所有僵尸网络的数据都完全一致！")

print("\n" + "=" * 120)
