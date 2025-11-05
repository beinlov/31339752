#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计聚合器测试脚本
用于快速测试聚合功能是否正常
"""
import pymysql
from config import DB_CONFIG
from stats_aggregator.aggregator import StatsAggregator

def print_separator(char='=', length=60):
    print(char * length)

def test_database_connection():
    """测试数据库连接"""
    print_separator()
    print("测试 1: 数据库连接")
    print_separator()
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        
        cursor.execute("SELECT DATABASE()")
        database = cursor.fetchone()[0]
        
        print(f"✅ 数据库连接成功")
        print(f"   MySQL 版本: {version}")
        print(f"   当前数据库: {database}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_node_tables():
    """检查节点表"""
    print_separator()
    print("测试 2: 检查节点表")
    print_separator()
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        botnet_types = ['asruex', 'mozi', 'andromeda', 'moobot', 'ramnit', 'leethozer']
        
        for botnet_type in botnet_types:
            table_name = f"botnet_nodes_{botnet_type}"
            
            # 检查表是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (DB_CONFIG['database'], table_name))
            
            if cursor.fetchone()[0] > 0:
                # 统计记录数
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                
                if count > 0:
                    print(f"✅ {table_name:25s} - {count:6d} 条记录")
                else:
                    print(f"⚠️  {table_name:25s} - 表为空")
            else:
                print(f"❌ {table_name:25s} - 表不存在")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 检查节点表失败: {e}")
        return False

def test_aggregation():
    """测试聚合功能"""
    print_separator()
    print("测试 3: 执行聚合测试")
    print_separator()
    
    try:
        aggregator = StatsAggregator(DB_CONFIG)
        
        # 测试聚合一个类型
        print("\n正在聚合 mozi 数据...")
        result = aggregator.aggregate_botnet_stats('mozi')
        
        if result.get('success'):
            print(f"✅ 聚合成功")
            print(f"   节点数: {result.get('node_count', 0)}")
            print(f"   中国统计: {result.get('china_rows', 0)} 条")
            print(f"   全球统计: {result.get('global_rows', 0)} 条")
        elif result.get('skipped'):
            print(f"⚠️  跳过（表不存在）")
        else:
            print(f"❌ 聚合失败: {result.get('error', '未知错误')}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 测试聚合功能失败: {e}")
        return False

def test_stats_tables():
    """检查统计表"""
    print_separator()
    print("测试 4: 检查统计表")
    print_separator()
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查 mozi 的统计表
        china_table = "china_botnet_mozi"
        global_table = "global_botnet_mozi"
        
        # 中国统计表
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], china_table))
        
        if cursor.fetchone()[0] > 0:
            cursor.execute(f"SELECT COUNT(*) FROM {china_table}")
            count = cursor.fetchone()[0]
            print(f"✅ {china_table:25s} - {count:6d} 条记录")
            
            if count > 0:
                cursor.execute(f"""
                    SELECT province, municipality, infected_num 
                    FROM {china_table} 
                    ORDER BY infected_num DESC 
                    LIMIT 5
                """)
                print(f"\n   Top 5 省市:")
                for province, city, num in cursor.fetchall():
                    print(f"     {province} - {city}: {num}")
        else:
            print(f"❌ {china_table} - 表不存在")
        
        print()
        
        # 全球统计表
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], global_table))
        
        if cursor.fetchone()[0] > 0:
            cursor.execute(f"SELECT COUNT(*) FROM {global_table}")
            count = cursor.fetchone()[0]
            print(f"✅ {global_table:25s} - {count:6d} 条记录")
            
            if count > 0:
                cursor.execute(f"""
                    SELECT country, infected_num 
                    FROM {global_table} 
                    ORDER BY infected_num DESC 
                    LIMIT 5
                """)
                print(f"\n   Top 5 国家:")
                for country, num in cursor.fetchall():
                    print(f"     {country}: {num}")
        else:
            print(f"❌ {global_table} - 表不存在")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 检查统计表失败: {e}")
        return False

def main():
    """主函数"""
    print("\n")
    print_separator('=', 60)
    print("  统计聚合器功能测试")
    print_separator('=', 60)
    print()
    
    results = []
    
    # 测试1: 数据库连接
    results.append(("数据库连接", test_database_connection()))
    print()
    
    if not results[-1][1]:
        print("\n❌ 数据库连接失败，终止测试")
        print("请检查 backend/config.py 中的数据库配置")
        return
    
    # 测试2: 节点表
    results.append(("节点表检查", test_node_tables()))
    print()
    
    # 测试3: 聚合功能
    results.append(("聚合功能", test_aggregation()))
    print()
    
    # 测试4: 统计表
    results.append(("统计表检查", test_stats_tables()))
    print()
    
    # 总结
    print_separator('=', 60)
    print("测试总结")
    print_separator('=', 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print()
    print(f"总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！统计聚合器工作正常。")
        print("\n下一步:")
        print("  1. 启动聚合器守护进程:")
        print("     cd backend")
        print("     python stats_aggregator/aggregator.py daemon 30")
        print()
        print("  2. 或使用启动脚本:")
        print("     Windows: start_aggregator.bat")
        print("     Linux:   ./start_aggregator.sh")
    else:
        print("\n⚠️ 部分测试失败，请检查：")
        print("  1. 数据库配置是否正确（backend/config.py）")
        print("  2. 节点表是否存在且有数据")
        print("  3. 日志处理器是否正常运行")
    
    print()

if __name__ == "__main__":
    main()



