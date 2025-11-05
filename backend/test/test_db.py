#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库连接和表结构
"""
import pymysql
from config import DB_CONFIG

try:
    print("正在连接数据库...")
    print(f"配置: {DB_CONFIG}")
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("✅ 数据库连接成功！")
    
    # 查询所有表
    cursor.execute("SHOW TABLES")
    tables = [t[0] for t in cursor.fetchall()]
    
    print(f"\n数据库中的表 (共 {len(tables)} 个):")
    for table in sorted(tables):
        print(f"  - {table}")
    
    # 检查关键表
    required_patterns = ['botnet_nodes_', 'china_botnet_']
    
    print("\n检查关键表:")
    for pattern in required_patterns:
        matching_tables = [t for t in tables if pattern in t]
        print(f"\n  包含 '{pattern}' 的表 ({len(matching_tables)} 个):")
        for table in matching_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"    - {table}: {count} 条记录")
    
    cursor.close()
    conn.close()
    
    print("\n✅ 测试完成！")
    
except pymysql.Error as e:
    print(f"\n❌ 数据库错误: {e}")
    print(f"   错误代码: {e.args[0]}")
    print(f"   错误信息: {e.args[1]}")
except Exception as e:
    print(f"\n❌ 其他错误: {e}")



