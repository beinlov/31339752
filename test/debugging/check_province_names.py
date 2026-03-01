#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查botnet_nodes_test表中的省份名称
"""
import pymysql
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DB_CONFIG

def check_province_names():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 查询所有不同的省份名称
    cursor.execute("""
        SELECT DISTINCT province, COUNT(DISTINCT ip) as count
        FROM botnet_nodes_test
        WHERE country = '中国'
        GROUP BY province
        ORDER BY count DESC
    """)
    
    provinces = cursor.fetchall()
    
    print("=" * 80)
    print(f"botnet_nodes_test 表中的所有省份名称 (共{len(provinces)}个):")
    print("=" * 80)
    
    for province, count in provinces:
        print(f"{province:30s} : {count:6d} 个节点")
    
    # 专门查看内蒙古和西藏
    print("\n" + "=" * 80)
    print("内蒙古相关的数据:")
    print("=" * 80)
    
    cursor.execute("""
        SELECT province, city, COUNT(DISTINCT ip) as count
        FROM botnet_nodes_test
        WHERE country = '中国' AND province LIKE '%内蒙古%'
        GROUP BY province, city
        ORDER BY count DESC
    """)
    
    inner_mongolia = cursor.fetchall()
    for province, city, count in inner_mongolia:
        print(f"省份='{province}', 城市='{city}', 节点数={count}")
    
    print("\n" + "=" * 80)
    print("西藏相关的数据:")
    print("=" * 80)
    
    cursor.execute("""
        SELECT province, city, COUNT(DISTINCT ip) as count
        FROM botnet_nodes_test
        WHERE country = '中国' AND province LIKE '%西藏%'
        GROUP BY province, city
        ORDER BY count DESC
    """)
    
    tibet = cursor.fetchall()
    for province, city, count in tibet:
        print(f"省份='{province}', 城市='{city}', 节点数={count}")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    check_province_names()
