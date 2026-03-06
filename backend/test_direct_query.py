#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接测试 SQL 查询，模拟 main.py 的完整逻辑"""
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
    
    # 完全模拟 main.py 的 SQL 查询
    query = f"""
        SELECT 
            DATE_FORMAT(communication_time, '%Y-%m-%d %H:%i:%s') as time,
            ip,
            COALESCE(country, '未知') as country,
            status
        FROM {table_name}
        ORDER BY communication_time DESC
        LIMIT 20
    """
    
    print("=" * 70)
    print("执行的 SQL 查询:")
    print("=" * 70)
    print(query)
    print()
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print("=" * 70)
    print(f"查询结果（共 {len(results)} 条）:")
    print("=" * 70)
    
    for i, row in enumerate(results, 1):
        print(f"\n记录 {i}:")
        for key, value in row.items():
            print(f"  {key}: {value}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("结论：如果上面有 status 字段，说明 SQL 是正确的")
    print("      如果 API 没有返回 status，说明是 FastAPI 的问题")
    print("=" * 70)
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
