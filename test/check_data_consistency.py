#!/usr/bin/env python3
import pymysql
import sys

# 从配置文件中读取数据库配置
sys.path.append('/home/spider/31339752/backend')
from config import DB_CONFIG

def check_data():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    botnet_type = 'asruex'
    
    print("=" * 80)
    print("数据一致性检查")
    print("=" * 80)
    
    # 1. 检查中国表总和
    cursor.execute(f"SELECT SUM(infected_num) as total FROM china_botnet_{botnet_type}")
    china_total = cursor.fetchone()[0] or 0
    print(f"\n1. china_botnet_{botnet_type} 表总和: {china_total}")
    
    # 2. 检查全球表总和
    cursor.execute(f"SELECT SUM(infected_num) as total FROM global_botnet_{botnet_type}")
    global_total = cursor.fetchone()[0] or 0
    print(f"2. global_botnet_{botnet_type} 表总和: {global_total}")
    
    # 3. 检查全球表中中国节点数量
    cursor.execute(f"SELECT SUM(infected_num) as total FROM global_botnet_{botnet_type} WHERE country = '中国'")
    china_in_global = cursor.fetchone()[0] or 0
    print(f"3. global_botnet_{botnet_type} 表中中国节点: {china_in_global}")
    
    # 4. 检查全球表中非中国节点数量
    cursor.execute(f"SELECT SUM(infected_num) as total FROM global_botnet_{botnet_type} WHERE country != '中国'")
    non_china_in_global = cursor.fetchone()[0] or 0
    print(f"4. global_botnet_{botnet_type} 表中非中国节点: {non_china_in_global}")
    
    print("\n" + "=" * 80)
    print("计算结果对比:")
    print("=" * 80)
    
    # amount.py 的计算方式 (图一 - 展示处置平台)
    amount_py_global = global_total
    print(f"\namount.py (图一) 返回的 global_amount: {amount_py_global}")
    
    # node.py 的计算方式 (图二、图三 - 后台管理系统)
    node_py_total = china_total + non_china_in_global
    print(f"node.py (图二、图三) 返回的 total_nodes: {node_py_total}")
    
    print(f"\n差异: {amount_py_global - node_py_total} 个节点")
    
    # 5. 检查 country_distribution 的计算
    cursor.execute(f"""
        SELECT country, SUM(infected_num) as count 
        FROM global_botnet_{botnet_type} 
        GROUP BY country 
        ORDER BY count DESC
    """)
    country_stats = cursor.fetchall()
    
    print("\n" + "=" * 80)
    print("国家分布统计 (从 global_botnet 表):")
    print("=" * 80)
    total_from_distribution = 0
    for country, count in country_stats[:10]:
        print(f"{country}: {count}")
        total_from_distribution += count
    
    print(f"\n从 country_distribution 汇总的总数: {total_from_distribution}")
    
    # 6. node.py 的 country_distribution 计算方式
    print("\n" + "=" * 80)
    print("node.py 中的 country_distribution 计算:")
    print("=" * 80)
    country_distribution = {}
    country_distribution['中国'] = china_total
    for country, count in country_stats:
        if country and country != '中国':
            country_distribution[country] = int(count)
    
    node_py_distribution_total = sum(country_distribution.values())
    print(f"country_distribution 中所有国家的总和: {node_py_distribution_total}")
    
    print("\n" + "=" * 80)
    print("结论:")
    print("=" * 80)
    print(f"1. 图一显示的全球数量 (116,090) = global_botnet 表总和 = {global_total}")
    print(f"2. 图二显示的总节点数 (116,090) = china_botnet 表 + global_botnet 表(非中国) = {node_py_total}")
    print(f"3. 图三显示的总节点数应该来自 country_distribution 的总和 = {node_py_distribution_total}")
    
    if node_py_distribution_total != node_py_total:
        print(f"\n⚠️ 发现问题: country_distribution 总和({node_py_distribution_total}) != total_nodes({node_py_total})")
        print(f"差异: {node_py_distribution_total - node_py_total} 个节点")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    check_data()
