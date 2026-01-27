#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深入分析Bug1：找出china_botnet_test表多出21个节点的原因
"""
import pymysql
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DB_CONFIG

def analyze_china_table_duplicates():
    """分析china_botnet_test表是否有重复统计的问题"""
    print("=" * 80)
    print("分析 china_botnet_test 表的重复统计问题")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 1. 查看china_botnet_test表的所有记录
    cursor.execute("""
        SELECT province, municipality, infected_num
        FROM china_botnet_test
        ORDER BY province, municipality
    """)
    
    china_records = cursor.fetchall()
    total_from_table = sum(row[2] for row in china_records)
    
    print(f"\nchina_botnet_test 表总记录数: {len(china_records)}")
    print(f"表中 infected_num 总和: {total_from_table}")
    
    # 2. 手动聚合botnet_nodes_test表，复现聚合逻辑
    print("\n" + "=" * 80)
    print("复现聚合逻辑，查找问题所在")
    print("=" * 80)
    
    # 使用聚合器的同样逻辑
    cursor.execute("""
        SELECT 
            COALESCE(
                TRIM(TRAILING '省' FROM 
                TRIM(TRAILING '市' FROM 
                REPLACE(REPLACE(REPLACE(
                    province, 
                    '壮族自治区', ''), 
                    '回族自治区', ''), 
                    '维吾尔自治区', '')
                )), 
                '未知'
            ) as clean_province,
            COALESCE(
                TRIM(TRAILING '市' FROM city),
                '未知'
            ) as clean_municipality,
            COUNT(DISTINCT ip) as node_count
        FROM botnet_nodes_test
        WHERE country = '中国'
        GROUP BY clean_province, clean_municipality
        ORDER BY clean_province, clean_municipality
    """)
    
    manual_aggregation = cursor.fetchall()
    manual_total = sum(row[2] for row in manual_aggregation)
    
    print(f"\n手动聚合结果:")
    print(f"总记录数: {len(manual_aggregation)}")
    print(f"总节点数: {manual_total}")
    
    # 3. 对比两个结果集，找出差异
    print("\n" + "=" * 80)
    print("对比表中数据和手动聚合结果")
    print("=" * 80)
    
    # 创建字典方便对比
    table_dict = {(row[0], row[1]): row[2] for row in china_records}
    manual_dict = {(row[0], row[1]): row[2] for row in manual_aggregation}
    
    # 找出只在表中存在的记录
    only_in_table = set(table_dict.keys()) - set(manual_dict.keys())
    if only_in_table:
        print(f"\n只在china_botnet_test表中存在的记录 ({len(only_in_table)}条):")
        for key in only_in_table:
            print(f"  {key[0]} - {key[1]}: {table_dict[key]} 个节点")
    
    # 找出只在手动聚合中存在的记录
    only_in_manual = set(manual_dict.keys()) - set(table_dict.keys())
    if only_in_manual:
        print(f"\n只在手动聚合中存在的记录 ({len(only_in_manual)}条):")
        for key in only_in_manual:
            print(f"  {key[0]} - {key[1]}: {manual_dict[key]} 个节点")
    
    # 找出数值不同的记录
    common_keys = set(table_dict.keys()) & set(manual_dict.keys())
    differences = []
    for key in common_keys:
        if table_dict[key] != manual_dict[key]:
            differences.append((key, table_dict[key], manual_dict[key]))
    
    if differences:
        print(f"\n数值不同的记录 ({len(differences)}条):")
        for key, table_val, manual_val in differences:
            print(f"  {key[0]} - {key[1]}: 表={table_val}, 实际={manual_val}, 差异={table_val - manual_val}")
    
    # 4. 检查是否有IP被重复计数
    print("\n" + "=" * 80)
    print("检查增量聚合逻辑的问题")
    print("=" * 80)
    
    # 使用增量聚合器的逻辑（注意：使用不同的省市处理规则）
    cursor.execute("""
        SELECT 
            COALESCE(TRIM(TRAILING '省' FROM province), '未知') as province,
            CASE 
                WHEN city IN ('北京', '天津', '上海', '重庆') THEN city
                WHEN city IS NOT NULL THEN TRIM(TRAILING '市' FROM city)
                ELSE '未知'
            END as municipality,
            COUNT(DISTINCT ip) as node_count
        FROM botnet_nodes_test
        WHERE country = '中国'
        GROUP BY province, municipality
    """)
    
    incremental_aggregation = cursor.fetchall()
    incremental_total = sum(row[2] for row in incremental_aggregation)
    
    print(f"\n使用增量聚合器逻辑:")
    print(f"总记录数: {len(incremental_aggregation)}")
    print(f"总节点数: {incremental_total}")
    
    # 5. 检查province和city字段的原始值
    print("\n" + "=" * 80)
    print("检查原始数据中的特殊情况")
    print("=" * 80)
    
    cursor.execute("""
        SELECT DISTINCT province, city, COUNT(DISTINCT ip) as count
        FROM botnet_nodes_test
        WHERE country = '中国' AND (
            province LIKE '%台湾%' OR 
            province LIKE '%香港%' OR 
            province LIKE '%澳门%' OR
            city LIKE '%台湾%' OR
            city LIKE '%香港%' OR
            city LIKE '%澳门%'
        )
        GROUP BY province, city
    """)
    
    special_cases = cursor.fetchall()
    if special_cases:
        print("\n特殊地区的原始数据:")
        for row in special_cases:
            print(f"  省份='{row[0]}', 城市='{row[1]}', 节点数={row[2]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print(f"结论: 表中总节点={total_from_table}, 实际总节点={manual_total}, " 
          f"差异={total_from_table - manual_total}")
    print("=" * 80 + "\n")

if __name__ == '__main__':
    analyze_china_table_duplicates()
