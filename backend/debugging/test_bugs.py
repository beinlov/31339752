#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试两个bug的脚本
1. global_botnet_test 和 china_botnet_test 的节点数不一致问题
2. 通信记录查询问题
"""
import pymysql
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DB_CONFIG

def test_bug1_node_count():
    """测试Bug1：节点数不一致"""
    print("=" * 80)
    print("测试Bug1：global_botnet_test vs china_botnet_test 节点数")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 1. 查询 global_botnet_test 中中国的节点数
    cursor.execute("""
        SELECT country, infected_num 
        FROM global_botnet_test 
        WHERE country = '中国'
    """)
    global_result = cursor.fetchone()
    global_china_count = global_result[1] if global_result else 0
    
    print(f"\n1. global_botnet_test 表中中国节点数: {global_china_count}")
    
    # 2. 查询 china_botnet_test 表的总节点数
    cursor.execute("""
        SELECT SUM(infected_num) as total
        FROM china_botnet_test
    """)
    china_result = cursor.fetchone()
    china_total_count = china_result[0] if china_result else 0
    
    print(f"2. china_botnet_test 表总节点数: {china_total_count}")
    
    # 3. 查看差异详情
    diff = china_total_count - global_china_count
    print(f"\n差异: {diff} 个节点 (china_botnet_test - global_botnet_test)")
    
    # 4. 检查 botnet_nodes_test 表中国节点的实际数量（去重IP）
    cursor.execute("""
        SELECT COUNT(DISTINCT ip) as unique_ips
        FROM botnet_nodes_test
        WHERE country = '中国'
    """)
    nodes_result = cursor.fetchone()
    nodes_china_count = nodes_result[0] if nodes_result else 0
    
    print(f"3. botnet_nodes_test 表中国节点数 (DISTINCT IP): {nodes_china_count}")
    
    # 5. 检查聚合逻辑是否有问题
    cursor.execute("""
        SELECT 
            COALESCE(TRIM(TRAILING '省' FROM province), '未知') as province,
            CASE 
                WHEN city IN ('北京', '天津', '上海', '重庆') THEN city
                WHEN city IS NOT NULL THEN TRIM(TRAILING '市' FROM city)
                ELSE '未知'
            END as municipality,
            COUNT(DISTINCT ip) as count
        FROM botnet_nodes_test
        WHERE country = '中国'
        GROUP BY province, municipality
    """)
    manual_aggregation = cursor.fetchall()
    manual_total = sum(row[2] for row in manual_aggregation)
    
    print(f"4. 手动聚合中国节点数 (按省市分组): {manual_total}")
    
    # 6. 查看china_botnet_test表的详细数据
    cursor.execute("""
        SELECT province, municipality, infected_num
        FROM china_botnet_test
        ORDER BY infected_num DESC
        LIMIT 5
    """)
    china_top5 = cursor.fetchall()
    
    print("\n5. china_botnet_test 表前5条记录:")
    for row in china_top5:
        print(f"   {row[0]} - {row[1]}: {row[2]} 个节点")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print(f"结论: {'数据一致' if diff == 0 else f'数据不一致，差异{diff}个节点'}")
    print("=" * 80 + "\n")
    
    return {
        'global_china': global_china_count,
        'china_total': china_total_count,
        'nodes_actual': nodes_china_count,
        'manual_aggregation': manual_total,
        'difference': diff
    }


def test_bug2_communication_records(test_ip='73.35.170.55'):
    """测试Bug2：通信记录查询问题"""
    print("=" * 80)
    print(f"测试Bug2：IP {test_ip} 的通信记录查询")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 1. 检查表是否存在
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = %s AND table_name = 'botnet_communications_test'
    """, (DB_CONFIG['database'],))
    
    table_exists = cursor.fetchone()[0] > 0
    
    if not table_exists:
        print("\n[ERROR] botnet_communications_test 表不存在!")
        cursor.close()
        conn.close()
        return
    
    print("\n[OK] botnet_communications_test 表存在")
    
    # 2. 查询该IP的通信记录总数
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM botnet_communications_test
        WHERE ip = %s
    """, (test_ip,))
    
    total_count = cursor.fetchone()[0]
    print(f"\n1. IP {test_ip} 的通信记录总数: {total_count}")
    
    if total_count == 0:
        # 查询表中所有唯一IP
        cursor.execute("""
            SELECT DISTINCT ip 
            FROM botnet_communications_test 
            LIMIT 10
        """)
        sample_ips = cursor.fetchall()
        
        print(f"\n2. 表中存在的IP示例 (前10个):")
        for row in sample_ips:
            print(f"   - {row[0]}")
        
        # 检查IP格式是否有问题（可能有空格或其他字符）
        cursor.execute("""
            SELECT DISTINCT ip, LENGTH(ip), HEX(ip)
            FROM botnet_communications_test 
            WHERE ip LIKE %s
            LIMIT 5
        """, (f'%{test_ip}%',))
        
        similar_ips = cursor.fetchall()
        if similar_ips:
            print(f"\n3. 包含 '{test_ip}' 的IP (可能格式有问题):")
            for row in similar_ips:
                print(f"   - IP: '{row[0]}', 长度: {row[1]}, HEX: {row[2]}")
    else:
        # 查询详细记录
        cursor.execute("""
            SELECT id, ip, communication_time, event_type
            FROM botnet_communications_test
            WHERE ip = %s
            ORDER BY communication_time DESC
            LIMIT 5
        """, (test_ip,))
        
        records = cursor.fetchall()
        print(f"\n2. 最近5条通信记录:")
        for row in records:
            print(f"   ID: {row[0]}, IP: {row[1]}, 时间: {row[2]}, 事件: {row[3]}")
    
    # 3. 检查表的总记录数
    cursor.execute("SELECT COUNT(*) FROM botnet_communications_test")
    total_records = cursor.fetchone()[0]
    
    print(f"\n3. botnet_communications_test 表总记录数: {total_records}")
    
    # 4. 统计有多少个不同IP
    cursor.execute("SELECT COUNT(DISTINCT ip) FROM botnet_communications_test")
    unique_ips = cursor.fetchone()[0]
    
    print(f"4. 表中唯一IP数: {unique_ips}")
    
    # 5. 查找有多条记录的IP
    cursor.execute("""
        SELECT ip, COUNT(*) as count
        FROM botnet_communications_test
        GROUP BY ip
        HAVING count > 1
        ORDER BY count DESC
        LIMIT 10
    """)
    
    multi_record_ips = cursor.fetchall()
    if multi_record_ips:
        print(f"\n5. 有多条通信记录的IP (前10个):")
        for row in multi_record_ips:
            print(f"   - {row[0]}: {row[1]} 条记录")
    else:
        print("\n5. 没有找到有多条记录的IP")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80 + "\n")


if __name__ == '__main__':
    # 测试Bug1
    bug1_result = test_bug1_node_count()
    
    # 测试Bug2 - 使用默认IP或从命令行参数获取
    test_ip = sys.argv[1] if len(sys.argv) > 1 else '73.35.170.55'
    
    test_bug2_communication_records(test_ip)
    
    print("\n" + "=" * 80)
    print("测试总结:")
    print("=" * 80)
    print(f"Bug1: global表中国节点={bug1_result['global_china']}, " 
          f"china表总节点={bug1_result['china_total']}, "
          f"差异={bug1_result['difference']}")
    print("\nBug2: 查看上面的详细输出")
    print("=" * 80)
