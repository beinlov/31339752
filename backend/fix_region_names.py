#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键修复地区名称不统一问题
直接更新数据库中的旧数据，然后重新聚合
"""
import pymysql
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_CONFIG

def fix_region_names():
    """修复数据库中的地区名称"""
    conn = None
    cursor = None
    
    try:
        print("=" * 60)
        print("开始修复地区名称...")
        print("=" * 60)
        
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. 修复botnet_nodes表中的province字段
        print("\n[1/5] 检查并诊断问题数据...")
        
        # 获取所有节点表
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_name LIKE 'botnet_nodes_%%'
        """, (DB_CONFIG['database'],))
        
        node_tables = [row[0] for row in cursor.fetchall()]
        
        for table in node_tables:
            print(f"\n  检查表: {table}")
            
            # 检查NULL或空字符串的province
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE province IS NULL OR province = ''")
            null_province_count = cursor.fetchone()[0]
            if null_province_count > 0:
                print(f"    ⚠️ 发现 {null_province_count} 个节点的province为空")
                
                # 显示示例数据
                cursor.execute(f"SELECT ip, country, city FROM {table} WHERE province IS NULL OR province = '' LIMIT 3")
                samples = cursor.fetchall()
                for ip, country, city in samples:
                    print(f"       示例: IP={ip}, country={country}, city={city}")
            
            # 检查包含"中国"前缀的province
            cursor.execute(f"SELECT DISTINCT province, COUNT(*) as cnt FROM {table} WHERE province LIKE '中国%%' GROUP BY province")
            china_prefix = cursor.fetchall()
            if china_prefix:
                print(f"    ⚠️ 发现province包含'中国'前缀:")
                for prov, cnt in china_prefix:
                    print(f"       {prov}: {cnt} 个节点")
            
            # 检查包含"中国"前缀的country
            cursor.execute(f"SELECT DISTINCT country, COUNT(*) as cnt FROM {table} WHERE country LIKE '中国%%' AND country != '中国' GROUP BY country")
            china_country = cursor.fetchall()
            if china_country:
                print(f"    ⚠️ 发现country包含'中国'前缀:")
                for country, cnt in china_country:
                    print(f"       {country}: {cnt} 个节点")
            
            # 检查不规范的省份名称
            cursor.execute(f"""
                SELECT DISTINCT province, COUNT(*) as cnt 
                FROM {table} 
                WHERE province LIKE '%%自治区' OR province LIKE '%%省' OR province LIKE '%%市'
                GROUP BY province
            """)
            irregular = cursor.fetchall()
            if irregular:
                print(f"    ⚠️ 发现不规范的省份名称:")
                for prov, cnt in irregular:
                    print(f"       {prov}: {cnt} 个节点")
            
            # 特别检查新疆数据
            cursor.execute(f"""
                SELECT DISTINCT province, COUNT(*) as cnt 
                FROM {table} 
                WHERE province LIKE '%%新疆%%'
                GROUP BY province
            """)
            xinjiang_data = cursor.fetchall()
            if xinjiang_data:
                print(f"    ℹ️ 新疆相关数据:")
                for prov, cnt in xinjiang_data:
                    print(f"       {prov}: {cnt} 个节点")
        
        print("\n[2/5] 修复原始节点表中的数据...")
        
        for table in node_tables:
            print(f"\n  处理表: {table}")
            
            # 1. 先处理province中包含"中国"前缀的情况
            cursor.execute(f"""
                UPDATE {table} 
                SET province = REPLACE(province, '中国', '') 
                WHERE province LIKE '中国%%'
            """)
            if cursor.rowcount > 0:
                print(f"    ✓ 移除province中的'中国'前缀: {cursor.rowcount} 行")
            
            # 2. 统一省份名称
            updates = [
                ("UPDATE {table} SET province = REPLACE(province, '壮族自治区', '') WHERE province LIKE '%%壮族自治区'", "广西壮族自治区"),
                ("UPDATE {table} SET province = REPLACE(province, '回族自治区', '') WHERE province LIKE '%%回族自治区'", "宁夏回族自治区"),
                ("UPDATE {table} SET province = REPLACE(province, '维吾尔自治区', '') WHERE province LIKE '%%维吾尔自治区'", "新疆维吾尔自治区"),
                ("UPDATE {table} SET province = REPLACE(province, '自治区', '') WHERE province LIKE '%%自治区' AND province NOT IN ('广西', '宁夏', '新疆', '内蒙古', '西藏')", "其他自治区"),
                ("UPDATE {table} SET province = REPLACE(province, '省', '') WHERE province LIKE '%%省'", "XX省"),
                ("UPDATE {table} SET province = REPLACE(province, '市', '') WHERE province IN ('北京市', '天津市', '上海市', '重庆市')", "直辖市"),
            ]
            
            for update_sql, desc in updates:
                sql = update_sql.format(table=table)
                cursor.execute(sql)
                affected = cursor.rowcount
                if affected > 0:
                    print(f"    ✓ 更新 {desc}: {affected} 行")
            
            # 3. 处理NULL或空字符串的province
            cursor.execute(f"""
                UPDATE {table} 
                SET province = '未知' 
                WHERE province IS NULL OR province = ''
            """)
            if cursor.rowcount > 0:
                print(f"    ✓ 填充空province为'未知': {cursor.rowcount} 行")
            
            # 4. 统一国家名称
            try:
                cursor.execute(f"UPDATE {table} SET country = '台湾' WHERE country = '中国台湾' OR country LIKE '%%台湾%%'")
                if cursor.rowcount > 0:
                    print(f"    ✓ 统一台湾命名: {cursor.rowcount} 行")
                    
                cursor.execute(f"UPDATE {table} SET country = '香港' WHERE country = '中国香港' OR country LIKE '%%香港%%'")
                if cursor.rowcount > 0:
                    print(f"    ✓ 统一香港命名: {cursor.rowcount} 行")
                    
                cursor.execute(f"UPDATE {table} SET country = '澳门' WHERE country = '中国澳门' OR country LIKE '%%澳门%%'")
                if cursor.rowcount > 0:
                    print(f"    ✓ 统一澳门命名: {cursor.rowcount} 行")
                
                # 处理NULL或空字符串的country
                cursor.execute(f"""
                    UPDATE {table} 
                    SET country = '未知' 
                    WHERE country IS NULL OR country = ''
                """)
                if cursor.rowcount > 0:
                    print(f"    ✓ 填充空country为'未知': {cursor.rowcount} 行")
            except Exception as e:
                pass  # 如果没有country字段，忽略错误
        
        conn.commit()
        print("  ✓ 原始数据修复完成")
        
        # 2. 清空聚合表
        print("\n[3/5] 清空旧的聚合表...")
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND (table_name LIKE 'china_botnet_%%' OR table_name LIKE 'global_botnet_%%')
            AND table_name NOT LIKE '%%_template'
        """, (DB_CONFIG['database'],))
        
        agg_tables = [row[0] for row in cursor.fetchall()]
        
        for table in agg_tables:
            print(f"  清空表: {table}")
            cursor.execute(f"DELETE FROM {table}")
            print(f"    ✓ 已清空 {cursor.rowcount} 行")
        
        conn.commit()
        print("  ✓ 聚合表清空完成")
        
        # 3. 重新运行聚合器
        print("\n[4/5] 重新聚合数据...")
        print("  正在启动聚合器...")
        
        # 导入并运行聚合器
        from stats_aggregator.aggregator import StatsAggregator
        
        aggregator = StatsAggregator(DB_CONFIG)
        botnet_types = ['ramnit']  # 添加你的僵尸网络类型
        
        for botnet_type in botnet_types:
            print(f"  聚合 {botnet_type}...")
            result = aggregator.aggregate_botnet_stats(botnet_type)
            print(f"    ✓ 中国表: {result['china_rows']} 行")
            print(f"    ✓ 全球表: {result['global_rows']} 行")
        
        print("  ✓ 数据聚合完成")
        
        # 4. 验证修复结果
        print("\n[5/5] 验证修复结果...")
        
        for botnet_type in botnet_types:
            china_table = f"china_botnet_{botnet_type}"
            global_table = f"global_botnet_{botnet_type}"
            
            # 检查省份名称
            cursor.execute(f"""
                SELECT DISTINCT province 
                FROM {china_table} 
                WHERE province LIKE '%自治区%' OR province LIKE '%省%'
            """)
            problematic_provinces = cursor.fetchall()
            
            if problematic_provinces:
                print(f"  ⚠️ {botnet_type} 中仍有未规范的省份名:")
                for row in problematic_provinces:
                    print(f"      - {row[0]}")
            else:
                print(f"  ✓ {botnet_type} 省份名称已规范化")
            
            # 检查国家名称
            cursor.execute(f"""
                SELECT DISTINCT country 
                FROM {global_table} 
                WHERE country LIKE '中国%'
            """)
            problematic_countries = cursor.fetchall()
            
            if problematic_countries:
                print(f"  ⚠️ {botnet_type} 中仍有未规范的国家名:")
                for row in problematic_countries:
                    print(f"      - {row[0]}")
            else:
                print(f"  ✓ {botnet_type} 国家名称已规范化")
            
            # 显示省份列表和数量
            cursor.execute(f"""
                SELECT province, SUM(infected_num) as total 
                FROM {china_table} 
                GROUP BY province 
                ORDER BY total DESC
            """)
            provinces = cursor.fetchall()
            print(f"\n  {botnet_type} 省份分布 ({len(provinces)} 个):")
            for i, (prov, cnt) in enumerate(provinces[:10]):
                print(f"    {i+1}. {prov}: {cnt} 个节点")
            if len(provinces) > 10:
                print(f"    ... 还有 {len(provinces)-10} 个省份")
            
            # 特别检查是否有"未知"省份
            cursor.execute(f"SELECT SUM(infected_num) FROM {china_table} WHERE province = '未知'")
            unknown_count = cursor.fetchone()[0] or 0
            if unknown_count > 0:
                print(f"\n  ⚠️ 有 {unknown_count} 个节点的省份为'未知'")
                print(f"     这些可能是原始数据中province字段为空的节点")
            
            # 检查国家列表
            cursor.execute(f"""
                SELECT country, SUM(infected_num) as total 
                FROM {global_table} 
                GROUP BY country 
                ORDER BY total DESC 
                LIMIT 10
            """)
            countries = cursor.fetchall()
            print(f"\n  {botnet_type} 国家分布 (前10):")
            for i, (country, cnt) in enumerate(countries):
                print(f"    {i+1}. {country}: {cnt} 个节点")
        
        print("\n" + "=" * 60)
        print("✅ 地区名称修复完成！")
        print("=" * 60)
        print("\n后续步骤：")
        print("1. 重新构建前端: cd fronted && npm run build")
        print("2. 重启服务")
        print("3. 清除浏览器缓存后访问")
        print()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    return True

if __name__ == "__main__":
    success = fix_region_names()
    sys.exit(0 if success else 1)
