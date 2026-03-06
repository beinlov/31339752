#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试后端 API 返回的数据格式"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pymysql
from pymysql.cursors import DictCursor
from config import DB_CONFIG

try:
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(DictCursor)
    
    botnet_type = 'utg_q_008'
    table_name = f"botnet_communications_{botnet_type}"
    
    cursor.execute(
        f"""
        SELECT
            DATE_FORMAT(communication_time, '%Y-%m-%d %H:%i:%s') as time,
            ip,
            COALESCE(country, '未知') as country,
            status
        FROM {table_name}
        ORDER BY communication_time DESC
        LIMIT 5
        """
    )
    
    results = cursor.fetchall()
    
    print("=" * 70)
    print("API 返回的数据格式测试（模拟 /api/active-botnet-communications）")
    print("=" * 70)
    print()
    
    for i, row in enumerate(results, 1):
        print(f"记录 {i}:")
        print(f"  time: {row['time']}")
        print(f"  ip: {row['ip']}")
        print(f"  country: {row['country']}")
        print(f"  status: '{row['status']}' (类型: {type(row['status']).__name__})")
        print(f"  status == 'active': {row['status'] == 'active'}")
        print(f"  status == 'cleaned': {row['status'] == 'cleaned'}")
        print()
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"错误: {e}")
