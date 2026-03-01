#!/usr/bin/env python3
"""
批量修复所有僵尸网络的数据不一致问题
"""
import pymysql
import sys
import os
sys.path.append('/home/spider/31339752/backend')
from config import DB_CONFIG, BOTNET_TYPES

# 导入聚合器
sys.path.append('/home/spider/31339752/backend/stats_aggregator')
from aggregator import StatsAggregator

# 已经修复的类型
FIXED_TYPES = ['ramnit']

# 需要修复的类型
TO_FIX = [bt for bt in BOTNET_TYPES if bt not in FIXED_TYPES]

print("=" * 100)
print("批量修复所有僵尸网络")
print("=" * 100)
print(f"\n待修复的僵尸网络类型: {', '.join(TO_FIX)}")
print(f"已修复的类型: {', '.join(FIXED_TYPES)}")

# 统计信息
results = {
    'success': [],
    'failed': [],
    'skipped': []
}

for botnet_type in TO_FIX:
    print("\n" + "=" * 100)
    print(f"🔧 修复 {botnet_type}")
    print("=" * 100)
    
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        node_table = f"botnet_nodes_{botnet_type}"
        china_table = f"china_botnet_{botnet_type}"
        global_table = f"global_botnet_{botnet_type}"
        
        # 步骤1: 检查节点表是否存在
        print(f"\n【步骤1】检查节点表是否存在...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], node_table))
        
        if cursor.fetchone()[0] == 0:
            print(f"  ⚠️  节点表 {node_table} 不存在，跳过")
            results['skipped'].append(botnet_type)
            cursor.close()
            conn.close()
            continue
        
        # 检查节点数量
        cursor.execute(f"SELECT COUNT(*) FROM {node_table}")
        node_count = cursor.fetchone()[0]
        print(f"  ✅ 节点表存在，共有 {node_count:,} 条记录")
        
        if node_count == 0:
            print(f"  ⚠️  节点表为空，跳过")
            results['skipped'].append(botnet_type)
            cursor.close()
            conn.close()
            continue
        
        # 步骤2: 检查并修复空字符串 country
        print(f"\n【步骤2】检查并修复空字符串 country...")
        cursor.execute(f"""
            SELECT COUNT(*) FROM {node_table} WHERE country = ''
        """)
        empty_country_count = cursor.fetchone()[0]
        
        if empty_country_count > 0:
            print(f"  ⚠️  发现 {empty_country_count:,} 条空字符串 country 记录")
            cursor.execute(f"""
                UPDATE {node_table}
                SET country = '未知'
                WHERE country = ''
            """)
            conn.commit()
            print(f"  ✅ 已修复 {cursor.rowcount:,} 条记录")
        else:
            print(f"  ✅ 没有空字符串 country 记录")
        
        # 步骤3: 删除旧的聚合表
        print(f"\n【步骤3】删除旧的聚合表...")
        cursor.execute(f"DROP TABLE IF EXISTS {china_table}")
        print(f"  ✅ 删除 {china_table}")
        
        cursor.execute(f"DROP TABLE IF EXISTS {global_table}")
        print(f"  ✅ 删除 {global_table}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # 步骤4: 重新聚合
        print(f"\n【步骤4】重新运行聚合器...")
        print("-" * 100)
        
        aggregator = StatsAggregator(DB_CONFIG)
        result = aggregator.aggregate_botnet_stats(botnet_type)
        
        print("-" * 100)
        
        if result.get('success'):
            print(f"\n✅ {botnet_type} 聚合成功！")
            print(f"  - 中国统计记录: {result.get('china_rows', 0):,} 条")
            print(f"  - 全球统计记录: {result.get('global_rows', 0):,} 条")
            print(f"  - 原始节点数: {result.get('node_count', 0):,} 个")
            results['success'].append(botnet_type)
            
            # 步骤5: 验证数据一致性
            print(f"\n【步骤5】验证数据一致性...")
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT SUM(infected_num) FROM {china_table}")
            china_sum = cursor.fetchone()[0] or 0
            
            cursor.execute(f"SELECT SUM(infected_num) FROM {global_table} WHERE country = '中国'")
            china_in_global = cursor.fetchone()[0] or 0
            
            if china_sum == china_in_global:
                print(f"  ✅ 数据一致: china_botnet ({china_sum:,}) = global_botnet中国节点 ({china_in_global:,})")
            else:
                print(f"  ⚠️  数据不一致:")
                print(f"     china_botnet: {china_sum:,}")
                print(f"     global_botnet中国节点: {china_in_global:,}")
                print(f"     差异: {abs(china_sum - china_in_global):,}")
            
            cursor.close()
            conn.close()
        else:
            print(f"\n❌ {botnet_type} 聚合失败: {result.get('error', '未知错误')}")
            results['failed'].append(botnet_type)
    
    except Exception as e:
        print(f"\n❌ {botnet_type} 修复失败: {e}")
        results['failed'].append(botnet_type)
        if conn:
            try:
                conn.close()
            except:
                pass

# 最终总结
print("\n" + "=" * 100)
print("📊 修复总结")
print("=" * 100)

print(f"\n✅ 成功修复: {len(results['success'])} 个")
for bt in results['success']:
    print(f"  - {bt}")

if results['skipped']:
    print(f"\n⏭️  跳过: {len(results['skipped'])} 个")
    for bt in results['skipped']:
        print(f"  - {bt} (节点表不存在或为空)")

if results['failed']:
    print(f"\n❌ 失败: {len(results['failed'])} 个")
    for bt in results['failed']:
        print(f"  - {bt}")

print("\n" + "=" * 100)
print("✅ 批量修复完成！")
print("=" * 100)
