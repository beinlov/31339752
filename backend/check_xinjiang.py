#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速检查新疆数据问题
"""
import pymysql
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_CONFIG

def check_xinjiang():
    """检查新疆数据"""
    conn = None
    cursor = None
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("=" * 60)
        print("新疆数据诊断")
        print("=" * 60)
        
        # 1. 检查原始节点表
        print("\n[1] 检查原始节点表 (botnet_nodes_ramnit)...")
        
        cursor.execute("""
            SELECT DISTINCT province, COUNT(*) as cnt 
            FROM botnet_nodes_ramnit 
            WHERE province LIKE '%新疆%'
            GROUP BY province
        """)
        results = cursor.fetchall()
        
        if results:
            print("  找到新疆相关数据:")
            for prov, cnt in results:
                print(f"    province = '{prov}': {cnt} 个节点")
        else:
            print("  ⚠️ 原始表中没有找到包含'新疆'的province数据")
            
            # 检查是否有其他可能的拼写
            cursor.execute("""
                SELECT DISTINCT province, COUNT(*) as cnt 
                FROM botnet_nodes_ramnit 
                GROUP BY province 
                ORDER BY cnt DESC
                LIMIT 10
            """)
            top_provinces = cursor.fetchall()
            print("\n  原始表中的省份分布 (前10):")
            for prov, cnt in top_provinces:
                print(f"    {prov}: {cnt} 个节点")
        
        # 2. 检查聚合表
        print("\n[2] 检查聚合表 (china_botnet_ramnit)...")
        
        cursor.execute("""
            SELECT DISTINCT province, SUM(infected_num) as total 
            FROM china_botnet_ramnit 
            WHERE province LIKE '%新疆%'
            GROUP BY province
        """)
        results = cursor.fetchall()
        
        if results:
            print("  找到新疆相关数据:")
            for prov, cnt in results:
                print(f"    province = '{prov}': {cnt} 个节点")
        else:
            print("  ⚠️ 聚合表中没有找到包含'新疆'的province数据")
            
            # 检查聚合表的所有省份
            cursor.execute("""
                SELECT DISTINCT province, SUM(infected_num) as total 
                FROM china_botnet_ramnit 
                GROUP BY province 
                ORDER BY total DESC
                LIMIT 10
            """)
            top_provinces = cursor.fetchall()
            print("\n  聚合表中的省份分布 (前10):")
            for prov, cnt in top_provinces:
                print(f"    {prov}: {cnt} 个节点")
        
        # 3. 测试API会返回什么
        print("\n[3] 模拟API返回数据...")
        cursor.execute("""
            SELECT province, SUM(infected_num) as total 
            FROM china_botnet_ramnit 
            GROUP BY province 
            ORDER BY total DESC
        """)
        all_provinces = cursor.fetchall()
        
        # 检查是否有新疆
        xinjiang_found = False
        for prov, cnt in all_provinces:
            if '新疆' in prov:
                xinjiang_found = True
                print(f"  ✓ API会返回: province='{prov}', amount={cnt}")
                break
        
        if not xinjiang_found:
            print("  ❌ API返回的数据中没有包含'新疆'的省份")
            print("     这就是地图上新疆显示为0的原因！")
        
        # 4. 给出修复建议
        print("\n" + "=" * 60)
        print("诊断结果和修复建议")
        print("=" * 60)
        
        if not xinjiang_found:
            print("\n❌ 问题确认: 聚合表中没有'新疆'数据")
            print("\n可能的原因:")
            print("1. 原始数据中province字段不是'新疆'或'新疆维吾尔自治区'")
            print("2. 聚合器在聚合时没有正确统一命名")
            print("3. 原始数据中根本没有新疆的节点")
            
            print("\n修复方法:")
            print("运行以下命令:")
            print("  python fix_region_names.py")
            print("\n该脚本会:")
            print("  1. 将 '新疆维吾尔自治区' 统一为 '新疆'")
            print("  2. 清空并重新聚合数据")
            print("  3. 验证修复结果")
        else:
            print("\n✓ 聚合表中有新疆数据")
            print("  如果地图仍显示为0，可能是前端匹配问题")
            print("  请检查浏览器控制台是否有匹配错误")
        
        print()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    check_xinjiang()
