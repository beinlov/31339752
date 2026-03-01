#!/usr/bin/env python3
"""
分析 Ramnit 僵尸网络的数据不一致问题
"""
import pymysql
import sys
sys.path.append('/home/spider/31339752/backend')
from config import DB_CONFIG

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

print('=' * 100)
print('🎯 Ramnit 僵尸网络数据分析')
print('=' * 100)

# 1. 基础数据统计
cursor.execute('SELECT SUM(infected_num) FROM china_botnet_ramnit')
china_total = cursor.fetchone()[0] or 0

cursor.execute('SELECT SUM(infected_num) FROM global_botnet_ramnit')
global_total = cursor.fetchone()[0] or 0

cursor.execute("SELECT SUM(infected_num) FROM global_botnet_ramnit WHERE country = %s", ('中国',))
china_in_global = cursor.fetchone()[0] or 0

cursor.execute("SELECT SUM(infected_num) FROM global_botnet_ramnit WHERE country != %s", ('中国',))
non_china = cursor.fetchone()[0] or 0

print(f'\n📊 数据库原始数据:')
print(f'  china_botnet_ramnit 总和:       {china_total:,}')
print(f'  global_botnet_ramnit 总和:      {global_total:,}')
print(f'  global 表中的中国节点:          {china_in_global:,}')
print(f'  global 表中的非中国节点:        {non_china:,}')

# 2. 获取国家分布
cursor.execute("""
    SELECT country, SUM(infected_num) as total
    FROM global_botnet_ramnit
    GROUP BY country
    ORDER BY total DESC
    LIMIT 10
""")
country_dist = cursor.fetchall()

print(f'\n🌍 国家分布 Top 10 (来自 global_botnet_ramnit):')
for country, count in country_dist:
    print(f'  {country}: {count:,}')

# 3. 模拟三个接口的计算逻辑
print('\n' + '=' * 100)
print('📈 三个接口的计算逻辑模拟:')
print('=' * 100)

# 图一：amount.py 的计算
amount_china = china_total
amount_global = global_total
print(f'\n【图一】展示处置平台 - /api/botnet-distribution (amount.py)')
print(f'  china_amount  = china_botnet 表总和 = {amount_china:,}')
print(f'  global_amount = global_botnet 表总和 = {amount_global:,}')
print(f'  ⚠️  注意: global_amount 包含了中国节点！')

# 图二：node.py 的 total_nodes 计算
node_total = china_total + non_china
print(f'\n【图二】后台管理系统受控节点监控 - /api/node-stats/ramnit (node.py)')
print(f'  total_nodes = china_botnet + global_botnet(非中国)')
print(f'              = {china_total:,} + {non_china:,}')
print(f'              = {node_total:,}')
print(f'  ✅ 这个计算避免了重复计算中国节点')

# 图三：node.py 的 country_distribution 总和
# node.py 的逻辑：
# country_distribution['中国'] = china_total
# for country in global_stats:
#     if country != '中国':
#         country_distribution[country] = count

cursor.execute("""
    SELECT SUM(infected_num) as total
    FROM global_botnet_ramnit
    WHERE country != %s
""", ('中国',))
global_non_china_sum = cursor.fetchone()[0] or 0

country_dist_total = china_total + global_non_china_sum

print(f'\n【图三】后台管理系统受控节点分布 - /api/node-stats/ramnit country_distribution')
print(f'  country_distribution = {{')
print(f'    "中国": {china_total:,},  # 来自 china_botnet 表')
print(f'    "其他国家": {global_non_china_sum:,},  # 来自 global_botnet 表(非中国)')
print(f'  }}')
print(f'  总和 = {country_dist_total:,}')

# 4. 对比分析
print('\n' + '=' * 100)
print('🔍 数据差异分析:')
print('=' * 100)

print(f'\n图一显示的数字:')
print(f'  全国数量 (china_amount):  {amount_china:,}')
print(f'  全球数量 (global_amount): {amount_global:,}')

print(f'\n图二显示的数字:')
print(f'  总节点数 (total_nodes):   {node_total:,}')

print(f'\n图三显示的数字:')
print(f'  总节点数 (country_dist):  {country_dist_total:,}')

print(f'\n' + '-' * 100)

# 验证用户报告的问题
if amount_global == 116090 and node_total == 116090:
    print(f'\n✅ 验证: 图一的 global_amount ({amount_global:,}) = 图二的 total_nodes ({node_total:,})')
else:
    print(f'\n⚠️  图一和图二的数据不同:')
    print(f'   图一 global_amount: {amount_global:,}')
    print(f'   图二 total_nodes:   {node_total:,}')
    print(f'   差异: {abs(amount_global - node_total):,}')

if country_dist_total == 116108:
    print(f'\n❌ 验证: 图三的 country_distribution 总和 = {country_dist_total:,}')
    print(f'   与图一、图二的 116,090 相差 {country_dist_total - 116090} 个节点')
else:
    print(f'\n图三 country_distribution 总和: {country_dist_total:,}')

# 5. 查找数据差异的根源
print('\n' + '=' * 100)
print('🔎 查找 18 个节点差异的根源:')
print('=' * 100)

# 检查 china_botnet 和 global_botnet 中的中国节点是否一致
diff_china = china_total - china_in_global
print(f'\nchina_botnet_ramnit 总和:     {china_total:,}')
print(f'global_botnet_ramnit 中国节点: {china_in_global:,}')
print(f'差异:                          {diff_china:,}')

if diff_china != 0:
    print(f'\n⚠️  发现问题: china_botnet 表与 global_botnet 表中的中国节点数量不一致！')
    print(f'   这就是导致图二和图三数据不一致的根本原因！')
    print(f'\n解释:')
    print(f'   - 图二 total_nodes = china_botnet({china_total:,}) + global_botnet非中国({non_china:,}) = {node_total:,}')
    print(f'   - 图三 country_dist = china_botnet({china_total:,}) + global_botnet非中国({global_non_china_sum:,}) = {country_dist_total:,}')
    print(f'   - 由于 global_botnet 中的中国节点({china_in_global:,}) ≠ china_botnet 总和({china_total:,})')
    print(f'   - 导致两个计算结果相差 {abs(diff_china):,} 个节点')
else:
    print(f'\n✅ china_botnet 表与 global_botnet 表中的中国节点数量一致')

# 6. 结论和建议
print('\n' + '=' * 100)
print('📋 结论和建议:')
print('=' * 100)

print(f'\n1️⃣  数据不一致的根本原因:')
print(f'   china_botnet_ramnit 表与 global_botnet_ramnit 表中的中国节点数量不一致')
print(f'   - china_botnet_ramnit: {china_total:,}')
print(f'   - global_botnet 中国节点: {china_in_global:,}')
print(f'   - 差异: {abs(diff_china):,} 个节点')

print(f'\n2️⃣  哪个数据是正确的:')
print(f'   ✅ node.py 的 total_nodes = {node_total:,} 是正确的计算方式')
print(f'   ✅ 但由于底层数据不一致，导致 country_distribution 总和偏差')

print(f'\n3️⃣  修复建议:')
print(f'   方案1: 修复数据同步问题，确保 china_botnet 和 global_botnet 中的中国节点一致')
print(f'   方案2: 修改计算逻辑，统一使用一个表作为数据源')
print(f'   方案3: 在 node.py 中添加数据校验，发现不一致时记录告警')

cursor.close()
conn.close()
