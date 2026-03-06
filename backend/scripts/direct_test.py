#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试统计功能
"""

import pymysql
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG

def test_direct_query():
    """直接测试数据库查询"""
    conn = None
    cursor = None
    try:
        print("测试直接数据库查询...")
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询最新的统计数据
        cursor.execute("""
            SELECT 
                total_nodes,
                total_domestic_nodes,
                total_foreign_nodes,
                cleaned_total_nodes,
                cleaned_domestic_nodes,
                cleaned_foreign_nodes,
                suppression_total_count,
                monthly_suppression_count,
                created_at
            FROM takeover_stats 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        
        if result:
            print("[OK] 查询成功")
            print(f"总节点数: {result['total_nodes']}")
            print(f"国内节点数: {result['total_domestic_nodes']}")
            print(f"国外节点数: {result['total_foreign_nodes']}")
            print(f"已清除总节点: {result['cleaned_total_nodes']}")
            print(f"已清除国内节点: {result['cleaned_domestic_nodes']}")
            print(f"已清除国外节点: {result['cleaned_foreign_nodes']}")
            print(f"抑制阻断策略总次数: {result['suppression_total_count']}")
            print(f"近一个月抑制阻断次数: {result['monthly_suppression_count']}")
            print(f"创建时间: {result['created_at']}")
            return True
        else:
            print("[ERROR] 没有查询到数据")
            return False
            
    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def test_api_import():
    """测试API模块导入"""
    try:
        print("\n测试API模块导入...")
        from router.takeover_stats_api import router
        print("[OK] API模块导入成功")
        return True
    except Exception as e:
        print(f"[ERROR] API模块导入失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("直接测试统计功能")
    print("=" * 50)
    
    results = []
    
    # 测试直接数据库查询
    results.append(test_direct_query())
    
    # 测试API模块导入
    results.append(test_api_import())
    
    print("\n" + "=" * 50)
    print("测试结果")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("[OK] 基础功能测试通过")
        return True
    else:
        print("[ERROR] 基础功能测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
