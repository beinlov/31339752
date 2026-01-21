#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证修复详情
"""
import pymysql
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DB_CONFIG

def verify_fix_details(botnet_type='test'):
    """验证修复的详细情况"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    comm_table = f"botnet_communications_{botnet_type}"
    
    print("=" * 80)
    print(f"验证修复详情 - {botnet_type} 僵尸网络")
    print("=" * 80)
    
    # 检查补偿记录
    cursor.execute(f"""
        SELECT COUNT(*) FROM {comm_table}
        WHERE event_type = 'data_补偿'
    """)
    compensated_count = cursor.fetchone()[0]
    
    print(f"\n1. 补偿记录统计:")
    print(f"   补偿的通信记录数: {compensated_count:,}")
    
    if compensated_count > 0:
        # 查看补偿记录的时间分布
        cursor.execute(f"""
            SELECT DATE(communication_time) as date, COUNT(*) as count
            FROM {comm_table}
            WHERE event_type = 'data_补偿'
            GROUP BY DATE(communication_time)
            ORDER BY count DESC
            LIMIT 10
        """)
        
        time_dist = cursor.fetchall()
        print(f"\n2. 补偿记录的时间分布:")
        for date, count in time_dist:
            print(f"   {date}: {count:,} 条")
        
        # 查看补偿记录示例
        cursor.execute(f"""
            SELECT id, ip, communication_time, event_type
            FROM {comm_table}
            WHERE event_type = 'data_补偿'
            ORDER BY id
            LIMIT 10
        """)
        
        samples = cursor.fetchall()
        print(f"\n3. 补偿记录示例（前10条）:")
        for row in samples:
            print(f"   ID={row[0]}, IP={row[1]}, 时间={row[2]}, 类型={row[3]}")
    
    # 最终统计
    cursor.execute(f"SELECT COUNT(DISTINCT ip) FROM botnet_nodes_{botnet_type}")
    total_nodes = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(DISTINCT ip) FROM {comm_table}")
    nodes_with_comm = cursor.fetchone()[0]
    
    coverage = nodes_with_comm / total_nodes * 100 if total_nodes > 0 else 0
    
    print(f"\n4. 最终数据状态:")
    print(f"   节点总数: {total_nodes:,}")
    print(f"   有通信记录的节点: {nodes_with_comm:,}")
    print(f"   覆盖率: {coverage:.2f}%")
    
    if coverage >= 99.9:
        print(f"\n[OK] 数据修复成功！覆盖率达到 {coverage:.2f}%")
    else:
        print(f"\n[WARNING] 仍有数据缺失，覆盖率仅 {coverage:.2f}%")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    verify_fix_details('test')
