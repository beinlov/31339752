#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查IP在不同表中的存在情况
"""
import pymysql
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DB_CONFIG

def check_ip(ip='97.19.218.217'):
    """检查IP在各个表中的情况"""
    print("=" * 80)
    print(f"检查IP {ip} 在各表中的存在情况")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 1. 检查在botnet_nodes_test表中
    print("\n1. 检查 botnet_nodes_test 表:")
    cursor.execute("""
        SELECT id, ip, country, province, city, status, created_time
        FROM botnet_nodes_test
        WHERE ip = %s
    """, (ip,))
    
    nodes = cursor.fetchall()
    if nodes:
        print(f"   找到 {len(nodes)} 条记录:")
        for row in nodes:
            print(f"   ID={row[0]}, IP={row[1]}, 位置={row[2]}/{row[3]}/{row[4]}, 状态={row[5]}")
    else:
        print(f"   [X] IP {ip} 不存在于 botnet_nodes_test 表")
    
    # 2. 检查在botnet_communications_test表中
    print("\n2. 检查 botnet_communications_test 表:")
    cursor.execute("""
        SELECT id, node_id, ip, communication_time, event_type
        FROM botnet_communications_test
        WHERE ip = %s
        ORDER BY communication_time DESC
    """, (ip,))
    
    comms = cursor.fetchall()
    if comms:
        print(f"   找到 {len(comms)} 条通信记录:")
        for row in comms[:5]:  # 只显示前5条
            print(f"   ID={row[0]}, NodeID={row[1]}, IP={row[2]}, 时间={row[3]}, 事件={row[4]}")
        if len(comms) > 5:
            print(f"   ... 还有 {len(comms)-5} 条记录")
    else:
        print(f"   [X] IP {ip} 不存在于 botnet_communications_test 表")
    
    # 3. 分析原因
    print("\n" + "=" * 80)
    print("原因分析:")
    print("=" * 80)
    
    if not nodes and comms:
        print(f"""
[WARNING] IP {ip} 只存在于通信表，不存在于节点表！

这说明：
1. 通信记录是独立插入的测试数据，没有对应的节点记录
2. 前端的节点列表是从 botnet_nodes_test 表查询的
3. 因此该IP无法在节点列表中搜索到

解决方案：
- 如果要测试通信记录功能，需要使用既存在于节点表又存在于通信表的IP
- 或者先插入节点数据，再插入通信数据
        """)
    elif nodes and comms:
        print(f"[OK] IP {ip} 同时存在于节点表和通信表，应该可以正常查询")
        print(f"     节点记录: {len(nodes)} 条")
        print(f"     通信记录: {len(comms)} 条")
    elif nodes and not comms:
        print(f"[INFO] IP {ip} 只存在于节点表，没有通信记录")
    else:
        print(f"[ERROR] IP {ip} 在两个表中都不存在")
    
    # 4. 找一个同时存在于两个表的IP用于测试
    print("\n" + "=" * 80)
    print("查找同时存在于两个表的IP（用于测试）:")
    print("=" * 80)
    
    cursor.execute("""
        SELECT n.ip, COUNT(c.id) as comm_count
        FROM botnet_nodes_test n
        INNER JOIN botnet_communications_test c ON n.ip = c.ip
        GROUP BY n.ip
        HAVING comm_count > 1
        ORDER BY comm_count DESC
        LIMIT 10
    """)
    
    valid_ips = cursor.fetchall()
    if valid_ips:
        print("\n可用于测试的IP（有节点记录且有多条通信记录）:")
        for ip_addr, count in valid_ips:
            print(f"   {ip_addr} - {count} 条通信记录")
    else:
        print("没有找到同时存在于两个表且有多条通信记录的IP")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    ip = sys.argv[1] if len(sys.argv) > 1 else '97.19.218.217'
    check_ip(ip)
