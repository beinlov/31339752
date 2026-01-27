#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充缺失的通信记录
为只有节点记录但没有通信记录的IP补充数据
"""
import pymysql
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DB_CONFIG

def fix_missing_communications(botnet_type='test', dry_run=True):
    """
    为没有通信记录的节点补充记录
    
    Args:
        botnet_type: 僵尸网络类型
        dry_run: True=只查询不修改，False=实际执行修复
    """
    print("=" * 80)
    print(f"补充缺失的通信记录 - {botnet_type} 僵尸网络")
    print(f"模式: {'预览模式（不会修改数据）' if dry_run else '执行模式（将修改数据）'}")
    print("=" * 80)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    node_table = f"botnet_nodes_{botnet_type}"
    comm_table = f"botnet_communications_{botnet_type}"
    
    try:
        # 1. 统计缺失情况
        print("\n1. 统计数据...")
        
        cursor.execute(f"SELECT COUNT(DISTINCT ip) FROM {node_table}")
        total_nodes = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT COUNT(DISTINCT ip) FROM {comm_table}")
        nodes_with_comm = cursor.fetchone()[0]
        
        missing_count = total_nodes - nodes_with_comm
        coverage = nodes_with_comm / total_nodes * 100 if total_nodes > 0 else 0
        
        print(f"   节点总数: {total_nodes:,}")
        print(f"   有通信记录的节点: {nodes_with_comm:,}")
        print(f"   缺失通信记录的节点: {missing_count:,}")
        print(f"   覆盖率: {coverage:.2f}%")
        
        if missing_count == 0:
            print("\n[OK] 数据完整，无需修复！")
            return
        
        # 2. 查找缺失的节点
        print(f"\n2. 查找缺失的节点...")
        sql = f"""
            SELECT n.id, n.ip, n.first_seen, n.longitude, n.latitude,
                   n.country, n.province, n.city, n.continent, n.isp, n.asn,
                   n.status, n.is_china
            FROM {node_table} n
            LEFT JOIN {comm_table} c ON n.ip = c.ip
            WHERE c.ip IS NULL
        """
        
        cursor.execute(sql)
        missing_nodes = cursor.fetchall()
        
        print(f"   找到 {len(missing_nodes):,} 个缺失通信记录的节点")
        
        # 3. 显示示例
        print(f"\n3. 缺失节点示例（前10个）:")
        for i, row in enumerate(missing_nodes[:10], 1):
            node_id, ip, first_seen, *_ = row
            print(f"   [{i}] ID={node_id}, IP={ip}, 首次发现={first_seen}")
        
        if len(missing_nodes) > 10:
            print(f"   ... 还有 {len(missing_nodes) - 10} 个节点")
        
        # 4. 检查时间分布（可能发现系统崩溃的时间点）
        print(f"\n4. 分析缺失节点的时间分布:")
        
        cursor.execute(f"""
            SELECT 
                DATE(n.first_seen) as date,
                COUNT(*) as count
            FROM {node_table} n
            LEFT JOIN {comm_table} c ON n.ip = c.ip
            WHERE c.ip IS NULL
            GROUP BY DATE(n.first_seen)
            ORDER BY count DESC
            LIMIT 10
        """)
        
        time_dist = cursor.fetchall()
        if time_dist:
            print(f"   缺失最多的日期:")
            for date, count in time_dist:
                print(f"   {date}: {count} 个节点")
        
        # 5. 执行修复（如果不是dry_run）
        if not dry_run:
            print(f"\n5. 开始修复...")
            
            # 准备插入数据
            comm_sql = f"""
                INSERT IGNORE INTO {comm_table}
                (node_id, ip, communication_time, longitude, latitude, country, province,
                 city, continent, isp, asn, event_type, status, is_china)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            comm_values = []
            for row in missing_nodes:
                comm_values.append((
                    row[0],  # node_id
                    row[1],  # ip
                    row[2] or datetime.now(),  # communication_time (使用first_seen或当前时间)
                    row[3],  # longitude
                    row[4],  # latitude
                    row[5],  # country
                    row[6],  # province
                    row[7],  # city
                    row[8],  # continent
                    row[9],  # isp
                    row[10], # asn
                    'data_补偿',  # event_type (标记为补偿记录)
                    row[11], # status
                    row[12]  # is_china
                ))
            
            # 分批插入（每批500条）
            batch_size = 500
            total_inserted = 0
            
            for i in range(0, len(comm_values), batch_size):
                batch = comm_values[i:i+batch_size]
                cursor.executemany(comm_sql, batch)
                total_inserted += len(batch)
                print(f"   已插入 {total_inserted}/{len(comm_values)} 条记录...")
            
            conn.commit()
            print(f"\n[OK] 修复完成！已补充 {total_inserted:,} 条通信记录")
            
            # 6. 验证修复结果
            print(f"\n6. 验证修复结果...")
            cursor.execute(f"SELECT COUNT(DISTINCT ip) FROM {comm_table}")
            new_nodes_with_comm = cursor.fetchone()[0]
            
            new_coverage = new_nodes_with_comm / total_nodes * 100 if total_nodes > 0 else 0
            
            print(f"   修复前覆盖率: {coverage:.2f}%")
            print(f"   修复后覆盖率: {new_coverage:.2f}%")
            print(f"   新增通信记录: {new_nodes_with_comm - nodes_with_comm:,} 条")
            
            if new_coverage >= 99.9:
                print(f"\n[OK] 数据已修复！覆盖率达到 {new_coverage:.2f}%")
            else:
                print(f"\n[WARNING] 警告：仍有部分数据未修复，覆盖率 {new_coverage:.2f}%")
        else:
            print(f"\n5. 预览模式：不执行实际修复")
            print(f"   如需执行修复，请运行:")
            print(f"   python fix_missing_communications.py {botnet_type} --execute")
    
    except Exception as e:
        print(f"\n[ERROR] 错误: {e}")
        conn.rollback()
        raise
    
    finally:
        cursor.close()
        conn.close()

def main():
    """主函数"""
    botnet_type = sys.argv[1] if len(sys.argv) > 1 else 'test'
    execute = '--execute' in sys.argv or '-e' in sys.argv
    
    if execute:
        confirm = input(f"\n[WARNING] 确认要修改 {botnet_type} 僵尸网络的数据吗？(yes/no): ")
        if confirm.lower() != 'yes':
            print("已取消")
            return
    
    fix_missing_communications(botnet_type, dry_run=not execute)

if __name__ == '__main__':
    main()
