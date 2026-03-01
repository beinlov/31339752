#!/usr/bin/env python3
"""验证所有僵尸网络表的结构"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pymysql
from config import DB_CONFIG

def verify_tables():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 获取所有僵尸网络类型
        cursor.execute("SELECT name, display_name FROM botnet_types")
        botnets = cursor.fetchall()
        
        print(f"数据库中共有 {len(botnets)} 个僵尸网络类型\n")
        
        for bot in botnets:
            name = bot['name']
            display_name = bot.get('display_name', name)
            print(f"僵尸网络: {name} ({display_name})")
            
            # 检查4个表
            tables = [
                f'china_botnet_{name}',
                f'global_botnet_{name}',
                f'botnet_nodes_{name}',
                f'botnet_communications_{name}'
            ]
            
            all_exist = True
            for table in tables:
                cursor.execute("""
                    SELECT COUNT(*) as cnt
                    FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = %s
                """, (DB_CONFIG['database'], table))
                
                exists = cursor.fetchone()['cnt'] > 0
                status = "[OK]" if exists else "[MISSING]"
                print(f"  {status} {table}")
                if not exists:
                    all_exist = False
            
            if all_exist:
                print(f"  状态: 完整\n")
            else:
                print(f"  状态: 不完整\n")
        
        # 统计总体情况
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND (table_name LIKE 'botnet_nodes_%' 
                 OR table_name LIKE 'botnet_communications_%'
                 OR table_name LIKE 'china_botnet_%'
                 OR table_name LIKE 'global_botnet_%')
            ORDER BY table_name
        """, (DB_CONFIG['database'],))
        
        all_tables = cursor.fetchall()
        print(f"\n数据库中共有 {len(all_tables)} 个僵尸网络相关表:")
        for table in all_tables:
            print(f"  - {table['table_name']}")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    verify_tables()
