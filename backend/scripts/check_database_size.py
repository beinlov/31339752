#!/usr/bin/env python3
"""
检查数据库大小和数据量
显示各表的记录数、存储大小、索引大小等信息
"""
import pymysql
import sys
import os
from datetime import datetime, timedelta

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG, BOTNET_CONFIG

def format_size(bytes_size):
    """格式化字节大小"""
    if bytes_size is None:
        return "N/A"
    # 转换为float以支持decimal.Decimal类型
    bytes_size = float(bytes_size)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def check_table_info(cursor, table_name):
    """获取表的详细信息"""
    # 获取表大小
    cursor.execute(f"""
        SELECT 
            table_rows,
            data_length,
            index_length,
            data_length + index_length as total_size,
            create_time,
            update_time
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        AND table_name = '{table_name}'
    """)
    result = cursor.fetchone()
    
    if not result:
        return None
    
    return {
        'rows': result[0] or 0,
        'data_size': result[1] or 0,
        'index_size': result[2] or 0,
        'total_size': result[3] or 0,
        'create_time': result[4],
        'update_time': result[5]
    }

def check_old_data(cursor, table_name, days=180):
    """检查旧数据量"""
    try:
        cursor.execute(f"""
            SELECT COUNT(*) FROM {table_name}
            WHERE communication_time < DATE_SUB(NOW(), INTERVAL {days} DAY)
        """)
        return cursor.fetchone()[0]
    except:
        return 0

def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='检查数据库大小')
    parser.add_argument('--retention-days', type=int, default=180, help='保留天数（用于计算可清理数据）')
    args = parser.parse_args()
    
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("=" * 100)
        print(f"数据库大小检查报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)
        
        # 1. 数据库总体信息
        cursor.execute(f"""
            SELECT 
                SUM(data_length + index_length) as total_size,
                SUM(data_length) as data_size,
                SUM(index_length) as index_size
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
        """)
        db_total = cursor.fetchone()
        
        print(f"\n【数据库总体】")
        print(f"  数据大小:  {format_size(db_total[1])}")
        print(f"  索引大小:  {format_size(db_total[2])}")
        print(f"  总大小:    {format_size(db_total[0])}")
        
        # 2. 各僵尸网络类型统计
        print(f"\n【各僵尸网络类型统计】")
        print("-" * 100)
        print(f"{'类型':<15} {'节点表记录数':<15} {'通信记录数':<15} {'节点表大小':<15} {'通信表大小':<15} {'总大小':<15}")
        print("-" * 100)
        
        total_nodes = 0
        total_comms = 0
        total_old_comms = 0
        total_size = 0
        
        for botnet_type in sorted(BOTNET_CONFIG.keys()):
            if not BOTNET_CONFIG[botnet_type].get('enabled', True):
                continue
            
            node_table = f"botnet_nodes_{botnet_type}"
            comm_table = f"botnet_communications_{botnet_type}"
            
            # 获取节点表信息
            node_info = check_table_info(cursor, node_table)
            comm_info = check_table_info(cursor, comm_table)
            
            if not node_info and not comm_info:
                continue
            
            node_rows = node_info['rows'] if node_info else 0
            comm_rows = comm_info['rows'] if comm_info else 0
            node_size = node_info['total_size'] if node_info else 0
            comm_size = comm_info['total_size'] if comm_info else 0
            
            total_nodes += node_rows
            total_comms += comm_rows
            total_size += node_size + comm_size
            
            print(f"{botnet_type:<15} {node_rows:<15,} {comm_rows:<15,} {format_size(node_size):<15} {format_size(comm_size):<15} {format_size(node_size + comm_size):<15}")
        
        print("-" * 100)
        print(f"{'总计':<15} {total_nodes:<15,} {total_comms:<15,} {'':15} {'':15} {format_size(total_size):<15}")
        
        # 3. 可清理数据统计
        print(f"\n【可清理数据统计】（{args.retention_days}天前的数据）")
        print("-" * 100)
        print(f"{'类型':<15} {'可清理记录数':<20} {'占比':<15} {'预估释放空间':<15}")
        print("-" * 100)
        
        for botnet_type in sorted(BOTNET_CONFIG.keys()):
            if not BOTNET_CONFIG[botnet_type].get('enabled', True):
                continue
            
            comm_table = f"botnet_communications_{botnet_type}"
            comm_info = check_table_info(cursor, comm_table)
            
            if not comm_info or comm_info['rows'] == 0:
                continue
            
            old_count = check_old_data(cursor, comm_table, args.retention_days)
            
            if old_count > 0:
                total_old_comms += old_count
                ratio = old_count * 100 / comm_info['rows']
                estimated_space = comm_info['total_size'] * (old_count / comm_info['rows'])
                print(f"{botnet_type:<15} {old_count:<20,} {ratio:>6.1f}% {'':8} {format_size(estimated_space):<15}")
        
        if total_old_comms > 0:
            print("-" * 100)
            total_old_ratio = total_old_comms * 100 / total_comms if total_comms > 0 else 0
            print(f"{'总计':<15} {total_old_comms:<20,} {total_old_ratio:>6.1f}%")
        else:
            print("暂无可清理数据")
        
        # 4. 数据增长趋势（最近7天）
        print(f"\n【数据增长趋势】（最近7天）")
        print("-" * 100)
        
        for days_ago in [7, 6, 5, 4, 3, 2, 1, 0]:
            date = datetime.now() - timedelta(days=days_ago)
            date_str = date.strftime('%Y-%m-%d')
            
            total_day_records = 0
            for botnet_type in BOTNET_CONFIG.keys():
                if not BOTNET_CONFIG[botnet_type].get('enabled', True):
                    continue
                    
                comm_table = f"botnet_communications_{botnet_type}"
                try:
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {comm_table}
                        WHERE DATE(communication_time) = %s
                    """, (date_str,))
                    count = cursor.fetchone()[0]
                    total_day_records += count
                except:
                    pass
            
            if total_day_records > 0:
                print(f"  {date_str}: {total_day_records:,} 条记录")
        
        # 5. 存储建议
        print(f"\n【存储建议】")
        print("-" * 100)
        
        daily_avg = total_comms / 30 if total_comms > 0 else 1000000  # 假设30天数据
        daily_size = total_size / 30 if total_size > 0 else 550 * 1024 * 1024  # 550MB
        
        retention_scenarios = [30, 60, 90, 180, 365, 730]
        
        print(f"  当前数据量: {total_comms:,} 条通信记录")
        print(f"  当前存储: {format_size(total_size)}")
        print(f"\n  不同保留期的存储需求预估:")
        
        for days in retention_scenarios:
            estimated_records = daily_avg * days
            estimated_size = daily_size * days
            print(f"    {days:>3}天: {estimated_records:>12,.0f} 条记录, 约 {format_size(estimated_size)}")
        
        print(f"\n  推荐保留期: 180天（约90GB，性能和存储的最佳平衡）")
        
        print("\n" + "=" * 100)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    main()
