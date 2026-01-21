#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查特定IP在节点表和通信表中的详细情况
"""
import pymysql
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DB_CONFIG

def check_ip_details(ip, botnet_type='test'):
    """检查IP的详细信息"""
    print("=" * 80)
    print(f"检查IP {ip} 在 {botnet_type} 僵尸网络中的详细情况")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    node_table = f"botnet_nodes_{botnet_type}"
    comm_table = f"botnet_communications_{botnet_type}"
    
    # 1. 检查节点表
    print(f"\n1. 检查 {node_table} 表:")
    cursor.execute(f"""
        SELECT id, ip, country, province, city, status, 
               created_time, updated_at, first_seen, last_seen
        FROM {node_table}
        WHERE ip = %s
    """, (ip,))
    
    node_records = cursor.fetchall()
    if node_records:
        print(f"   找到 {len(node_records)} 条节点记录:")
        for row in node_records:
            print(f"   ID={row[0]}")
            print(f"   IP={row[1]}")
            print(f"   位置={row[2]}/{row[3]}/{row[4]}")
            print(f"   状态={row[5]}")
            print(f"   创建时间={row[6]}")
            print(f"   更新时间={row[7]}")
            print(f"   首次发现={row[8]}")
            print(f"   最后发现={row[9]}")
            print()
    else:
        print(f"   [WARNING] IP {ip} 不存在于 {node_table} 表")
        print(f"   这意味着该IP不应该出现在节点列表中！")
    
    # 2. 检查通信表
    print(f"\n2. 检查 {comm_table} 表:")
    
    # 先检查表是否存在
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = %s AND table_name = %s
    """, (DB_CONFIG['database'], comm_table))
    
    table_exists = cursor.fetchone()[0] > 0
    
    if not table_exists:
        print(f"   [ERROR] {comm_table} 表不存在!")
        print(f"   这是正常的，说明该僵尸网络类型还没有创建通信记录表")
    else:
        cursor.execute(f"""
            SELECT id, node_id, ip, communication_time, event_type, status
            FROM {comm_table}
            WHERE ip = %s
            ORDER BY communication_time DESC
        """, (ip,))
        
        comm_records = cursor.fetchall()
        if comm_records:
            print(f"   找到 {len(comm_records)} 条通信记录:")
            for i, row in enumerate(comm_records[:5], 1):
                print(f"   [{i}] ID={row[0]}, NodeID={row[1]}, 时间={row[3]}, 事件={row[4]}")
            if len(comm_records) > 5:
                print(f"   ... 还有 {len(comm_records)-5} 条记录")
        else:
            print(f"   [INFO] IP {ip} 在 {comm_table} 表中没有通信记录")
            print(f"   这是正常的，因为并非所有节点都有通信记录")
    
    # 3. 分析情况
    print("\n" + "=" * 80)
    print("分析结论:")
    print("=" * 80)
    
    if node_records and not comm_records:
        print(f"""
[正常情况] IP {ip} 存在于节点表，但没有通信记录

这是完全正常的，原因可能是：
1. 该节点刚被发现，还没有产生通信行为
2. 该节点只在网络中存在，但没有产生需要记录的通信事件
3. 通信记录数据尚未被收集或导入

建议：
- 前端应该正常显示"暂无通信记录"
- 这不是bug，是数据的真实情况
        """)
    elif not node_records:
        print(f"""
[异常情况] IP {ip} 不存在于节点表

这是异常的！如果该IP出现在前端的节点列表中，说明：
1. 前端展示的数据与数据库不一致
2. 可能是缓存问题
3. 或者前端从错误的数据源读取了数据

需要进一步检查：
- 前端调用的API接口
- 返回的数据来源
        """)
    elif node_records and comm_records:
        print(f"""
[正常情况] IP {ip} 既有节点记录，又有通信记录

节点记录: {len(node_records)} 条
通信记录: {len(comm_records)} 条

这是完全正常的情况，通信记录弹窗应该能正常显示数据。
        """)
    
    # 4. 统计所有没有通信记录的节点
    print("\n" + "=" * 80)
    print(f"统计 {botnet_type} 僵尸网络中没有通信记录的节点数量:")
    print("=" * 80)
    
    if table_exists:
        # 查询所有节点总数
        cursor.execute(f"SELECT COUNT(DISTINCT ip) FROM {node_table}")
        total_nodes = cursor.fetchone()[0]
        
        # 查询有通信记录的节点数
        cursor.execute(f"SELECT COUNT(DISTINCT ip) FROM {comm_table}")
        nodes_with_comm = cursor.fetchone()[0]
        
        # 查询节点表中但通信表中没有的IP
        cursor.execute(f"""
            SELECT n.ip, n.country, n.province, n.city
            FROM {node_table} n
            LEFT JOIN {comm_table} c ON n.ip = c.ip
            WHERE c.ip IS NULL
            LIMIT 10
        """)
        
        nodes_without_comm = cursor.fetchall()
        nodes_without_comm_count = total_nodes - nodes_with_comm
        
        print(f"\n节点总数: {total_nodes}")
        print(f"有通信记录的节点: {nodes_with_comm}")
        print(f"没有通信记录的节点: {nodes_without_comm_count}")
        print(f"覆盖率: {nodes_with_comm/total_nodes*100:.2f}%")
        
        if nodes_without_comm:
            print(f"\n没有通信记录的节点示例（前10个）:")
            for row in nodes_without_comm:
                print(f"   {row[0]} - {row[1]}/{row[2]}/{row[3]}")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    ip = sys.argv[1] if len(sys.argv) > 1 else '139.13.159.86'
    botnet_type = sys.argv[2] if len(sys.argv) > 2 else 'test'
    
    check_ip_details(ip, botnet_type)
