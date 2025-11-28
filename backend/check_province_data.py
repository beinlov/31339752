#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中province字段的实际值
"""
import pymysql
import sys
import os

# 从环境变量或配置文件读取数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'botnet_db'),
    'charset': 'utf8mb4'
}

def check_province_data():
    """检查province字段的实际值"""
    print("=" * 60)
    print("检查数据库中的province字段")
    print("=" * 60)
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查china_botnet_ramnit表
        print("\n[1] china_botnet_ramnit 表中的province字段（前20条）:")
        cursor.execute("""
            SELECT province, infected_num 
            FROM china_botnet_ramnit 
            ORDER BY infected_num DESC 
            LIMIT 20
        """)
        results = cursor.fetchall()
        
        for province, count in results:
            print(f"  {province}: {count} 个节点")
        
        # 特别检查新疆
        print("\n[2] 新疆相关数据:")
        cursor.execute("""
            SELECT province, infected_num 
            FROM china_botnet_ramnit 
            WHERE province LIKE '%新疆%'
        """)
        xinjiang = cursor.fetchall()
        if xinjiang:
            for province, count in xinjiang:
                print(f"  ✓ 找到: {province}: {count}")
        else:
            print("  ❌ 没有找到新疆数据")
        
        # 特别检查广西
        print("\n[3] 广西相关数据:")
        cursor.execute("""
            SELECT province, infected_num 
            FROM china_botnet_ramnit 
            WHERE province LIKE '%广西%'
        """)
        guangxi = cursor.fetchall()
        if guangxi:
            for province, count in guangxi:
                print(f"  ✓ 找到: {province}: {count}")
        else:
            print("  ❌ 没有找到广西数据")
        
        # 检查原始表
        print("\n[4] botnet_nodes_ramnit 原始表中的province字段（样本）:")
        cursor.execute("""
            SELECT DISTINCT province 
            FROM botnet_nodes_ramnit 
            WHERE province IS NOT NULL 
            LIMIT 10
        """)
        raw_provinces = cursor.fetchall()
        for (province,) in raw_provinces:
            print(f"  - {province}")
        
        # 检查是否有带城市名的province
        print("\n[5] 检查是否有包含城市名的province字段:")
        cursor.execute("""
            SELECT DISTINCT province 
            FROM botnet_nodes_ramnit 
            WHERE province LIKE '%市' AND province NOT IN ('北京市', '天津市', '上海市', '重庆市')
            LIMIT 10
        """)
        city_provinces = cursor.fetchall()
        if city_provinces:
            print("  ⚠️ 发现包含城市名的province:")
            for (province,) in city_provinces:
                print(f"     - {province}")
        else:
            print("  ✓ 没有发现包含城市名的province")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("检查完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    check_province_data()
