#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库状态和表结构 - 修复编码问题
"""

import pymysql
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG

def check_database_connection():
    """检查数据库连接"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        print("[OK] 数据库连接成功")
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        return False

def check_tables_exist():
    """检查统计表是否存在"""
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        tables = ['takeover_stats', 'takeover_stats_detail']
        for table in tables:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (DB_CONFIG['database'], table))
            
            if cursor.fetchone()[0] > 0:
                print(f"[OK] 表 {table} 存在")
                
                # 检查表中的数据量
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  - 数据条数: {count}")
                
                if count > 0:
                    # 显示最新的一条记录
                    cursor.execute(f"SELECT created_at FROM {table} ORDER BY created_at DESC LIMIT 1")
                    latest = cursor.fetchone()
                    if latest:
                        print(f"  - 最新记录时间: {latest[0]}")
            else:
                print(f"[ERROR] 表 {table} 不存在")
                return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 检查表失败: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def check_table_structure():
    """检查表结构"""
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n检查 takeover_stats 表结构:")
        cursor.execute("DESCRIBE takeover_stats")
        columns = cursor.fetchall()
        
        expected_new_columns = [
            'cleaned_total_nodes', 'cleaned_domestic_nodes', 'cleaned_foreign_nodes',
            'monthly_cleaned_total_nodes', 'monthly_cleaned_domestic_nodes', 'monthly_cleaned_foreign_nodes',
            'suppression_total_count', 'monthly_suppression_count'
        ]
        
        existing_columns = [col[0] for col in columns]
        
        for col in expected_new_columns:
            if col in existing_columns:
                print(f"[OK] 字段 {col} 存在")
            else:
                print(f"[ERROR] 字段 {col} 不存在")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 检查表结构失败: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def test_simple_query():
    """测试简单查询"""
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n测试简单查询:")
        cursor.execute("SELECT COUNT(*) FROM takeover_stats")
        count = cursor.fetchone()[0]
        print(f"[OK] takeover_stats 表查询成功，共 {count} 条记录")
        
        if count > 0:
            cursor.execute("""
                SELECT 
                    total_nodes, cleaned_total_nodes, suppression_total_count,
                    created_at
                FROM takeover_stats 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                print(f"[OK] 最新记录查询成功")
                print(f"  - 总节点数: {result[0]}")
                print(f"  - 已清除节点数: {result[1]}")
                print(f"  - 抑制阻断次数: {result[2]}")
                print(f"  - 创建时间: {result[3]}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 查询测试失败: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """主函数"""
    print("=" * 60)
    print("数据库状态检查")
    print("=" * 60)
    
    results = []
    
    # 检查数据库连接
    results.append(check_database_connection())
    
    # 检查表是否存在
    results.append(check_tables_exist())
    
    # 检查表结构
    results.append(check_table_structure())
    
    # 测试简单查询
    results.append(test_simple_query())
    
    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("[OK] 数据库状态正常")
        return True
    else:
        print("[ERROR] 数据库存在问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
