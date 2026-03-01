#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证Bug1修复效果的脚本
1. 备份当前的china_botnet_test表数据
2. 重新运行聚合器
3. 对比修复前后的数据
"""
import pymysql
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DB_CONFIG
from stats_aggregator.aggregator import StatsAggregator

def backup_china_table():
    """备份china_botnet_test表"""
    print("=" * 80)
    print("步骤1: 备份china_botnet_test表")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 删除旧的备份表（如果存在）
    cursor.execute("DROP TABLE IF EXISTS china_botnet_test_backup")
    
    # 创建备份
    cursor.execute("""
        CREATE TABLE china_botnet_test_backup LIKE china_botnet_test
    """)
    
    cursor.execute("""
        INSERT INTO china_botnet_test_backup 
        SELECT * FROM china_botnet_test
    """)
    
    conn.commit()
    
    # 统计备份数据
    cursor.execute("SELECT COUNT(*), SUM(infected_num) FROM china_botnet_test_backup")
    count, total = cursor.fetchone()
    
    print(f"备份完成: {count} 条记录, 总节点数 {total}")
    
    cursor.close()
    conn.close()

def clear_china_table():
    """清空china_botnet_test表"""
    print("\n" + "=" * 80)
    print("步骤2: 清空china_botnet_test表")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM china_botnet_test")
    conn.commit()
    
    print("表已清空")
    
    cursor.close()
    conn.close()

def run_aggregation():
    """重新运行聚合"""
    print("\n" + "=" * 80)
    print("步骤3: 重新运行聚合器（只聚合test僵尸网络）")
    print("=" * 80)
    
    aggregator = StatsAggregator(DB_CONFIG)
    result = aggregator.aggregate_botnet_stats('test')
    
    print(f"\n聚合完成: {result}")
    
    return result

def compare_results():
    """对比修复前后的结果"""
    print("\n" + "=" * 80)
    print("步骤4: 对比修复前后的数据")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 修复前的数据
    cursor.execute("""
        SELECT COUNT(*) as count, SUM(infected_num) as total
        FROM china_botnet_test_backup
    """)
    old_count, old_total = cursor.fetchone()
    
    # 修复后的数据
    cursor.execute("""
        SELECT COUNT(*) as count, SUM(infected_num) as total
        FROM china_botnet_test
    """)
    new_count, new_total = cursor.fetchone()
    
    # global表的数据（作为参考）
    cursor.execute("""
        SELECT infected_num
        FROM global_botnet_test
        WHERE country = '中国'
    """)
    global_china = cursor.fetchone()
    global_count = global_china[0] if global_china else 0
    
    # 实际节点数（从nodes表）
    cursor.execute("""
        SELECT COUNT(DISTINCT ip)
        FROM botnet_nodes_test
        WHERE country = '中国'
    """)
    actual_count = cursor.fetchone()[0]
    
    print("\n对比结果:")
    print("-" * 80)
    print(f"{'项目':<30} | {'记录数':<10} | {'节点总数':<10} | {'备注'}")
    print("-" * 80)
    print(f"{'修复前 (china_botnet_test)':<30} | {old_count:<10} | {old_total:<10} | 有bug")
    print(f"{'修复后 (china_botnet_test)':<30} | {new_count:<10} | {new_total:<10} | 已修复")
    print(f"{'global_botnet_test (中国)':<30} | {'-':<10} | {global_count:<10} | 参考值")
    print(f"{'botnet_nodes_test (实际)':<30} | {'-':<10} | {actual_count:<10} | 实际值")
    print("-" * 80)
    
    # 分析差异
    print("\n差异分析:")
    print(f"修复前 vs global: {old_total - global_count:+d}")
    print(f"修复后 vs global: {new_total - global_count:+d}")
    print(f"修复后 vs 实际:   {new_total - actual_count:+d}")
    
    if new_total == global_count and new_total == actual_count:
        print("\n✓ 修复成功！china表、global表、实际节点数三者完全一致")
    else:
        print(f"\n✗ 数据仍不一致，需要进一步检查")
    
    # 查看内蒙古和西藏的数据
    print("\n" + "=" * 80)
    print("检查内蒙古和西藏的聚合情况")
    print("=" * 80)
    
    cursor.execute("""
        SELECT province, municipality, infected_num
        FROM china_botnet_test
        WHERE province LIKE '%内蒙古%' OR province LIKE '%西藏%'
        ORDER BY province, municipality
    """)
    
    special_regions = cursor.fetchall()
    if special_regions:
        print("\nchina_botnet_test 表中的内蒙古和西藏数据:")
        for province, city, count in special_regions:
            print(f"  {province} - {city}: {count} 个节点")
    else:
        print("\n未找到包含'内蒙古'或'西藏'的记录（这是正常的，因为自治区后缀已被去除）")
        
        # 查询"内蒙"开头的记录
        cursor.execute("""
            SELECT province, municipality, infected_num
            FROM china_botnet_test
            WHERE province LIKE '内蒙%' OR province = '西藏'
            ORDER BY province, municipality
        """)
        
        special_regions = cursor.fetchall()
        if special_regions:
            print("\n修复后的内蒙古和西藏数据:")
            for province, city, count in special_regions:
                print(f"  {province} - {city}: {count} 个节点")
    
    cursor.close()
    conn.close()

def main():
    print("\n" + "=" * 80)
    print("Bug1修复验证脚本")
    print("=" * 80)
    
    try:
        # 1. 备份当前数据
        backup_china_table()
        
        # 2. 清空表
        clear_china_table()
        
        # 3. 重新聚合
        run_aggregation()
        
        # 4. 对比结果
        compare_results()
        
        print("\n" + "=" * 80)
        print("验证完成！")
        print("=" * 80)
        print("\n提示: 如果修复成功，可以删除备份表 china_botnet_test_backup")
        print("      如果修复失败，可以从备份表恢复数据")
        
    except Exception as e:
        print(f"\n错误: {e}")
        print("\n如果出现问题，可以从备份表恢复数据:")
        print("  DELETE FROM china_botnet_test;")
        print("  INSERT INTO china_botnet_test SELECT * FROM china_botnet_test_backup;")

if __name__ == '__main__':
    main()
