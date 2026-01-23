"""
数据库数据量检查工具
查看各表的数据量、存储空间和时间分布
"""
import pymysql
import sys
import os
from datetime import datetime
from tabulate import tabulate

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG

def format_bytes(bytes_size):
    """格式化字节大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def check_table_sizes():
    """检查所有表的大小"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n" + "="*80)
        print("数据库表大小统计")
        print("="*80)
        
        # 查询表大小
        cursor.execute("""
            SELECT 
                table_name,
                table_rows,
                data_length,
                index_length,
                data_length + index_length as total_length
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name LIKE 'botnet_%'
            ORDER BY total_length DESC
        """)
        
        tables_data = []
        total_size = 0
        total_rows = 0
        
        for row in cursor.fetchall():
            table_name, rows, data_len, index_len, total_len = row
            total_size += total_len
            total_rows += rows if rows else 0
            
            tables_data.append([
                table_name,
                f"{rows:,}" if rows else "0",
                format_bytes(data_len),
                format_bytes(index_len),
                format_bytes(total_len)
            ])
        
        # 打印表格
        headers = ["表名", "记录数", "数据大小", "索引大小", "总大小"]
        print(tabulate(tables_data, headers=headers, tablefmt="grid"))
        
        print(f"\n总记录数: {total_rows:,}")
        print(f"总存储空间: {format_bytes(total_size)}")
        
        conn.close()
        
    except Exception as e:
        print(f"查询失败: {e}")

def check_data_distribution():
    """检查数据时间分布"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n" + "="*80)
        print("通信记录时间分布")
        print("="*80)
        
        # 获取所有通信记录表
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name LIKE 'botnet_communications_%'
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        distribution_data = []
        
        for table_name in tables:
            botnet_type = table_name.replace('botnet_communications_', '')
            
            # 查询时间范围和记录数
            cursor.execute(f"""
                SELECT 
                    MIN(communication_time) as earliest,
                    MAX(communication_time) as latest,
                    COUNT(*) as total_count
                FROM {table_name}
            """)
            
            result = cursor.fetchone()
            if result and result[0]:
                earliest, latest, count = result
                
                days_span = (latest - earliest).days + 1
                avg_per_day = count / days_span if days_span > 0 else 0
                
                distribution_data.append([
                    botnet_type,
                    earliest.strftime('%Y-%m-%d'),
                    latest.strftime('%Y-%m-%d'),
                    f"{days_span} 天",
                    f"{count:,}",
                    f"{avg_per_day:,.0f}"
                ])
        
        # 打印表格
        headers = ["僵尸网络", "最早时间", "最新时间", "数据跨度", "总记录数", "日均记录"]
        print(tabulate(distribution_data, headers=headers, tablefmt="grid"))
        
        conn.close()
        
    except Exception as e:
        print(f"查询失败: {e}")

def check_old_data():
    """检查可清理的旧数据"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n" + "="*80)
        print("可清理的旧数据统计（超过30天）")
        print("="*80)
        
        # 获取所有通信记录表
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name LIKE 'botnet_communications_%'
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        old_data = []
        total_old_count = 0
        
        for table_name in tables:
            botnet_type = table_name.replace('botnet_communications_', '')
            
            # 查询30天前的数据量
            cursor.execute(f"""
                SELECT COUNT(*) as count
                FROM {table_name}
                WHERE communication_time < DATE_SUB(NOW(), INTERVAL 30 DAY)
            """)
            
            count = cursor.fetchone()[0]
            total_old_count += count
            
            if count > 0:
                # 计算数据大小（估算）
                cursor.execute(f"""
                    SELECT 
                        data_length,
                        table_rows
                    FROM information_schema.tables
                    WHERE table_schema = DATABASE()
                    AND table_name = %s
                """, [table_name])
                
                data_len, total_rows = cursor.fetchone()
                
                if total_rows > 0:
                    estimated_size = (data_len / total_rows) * count
                else:
                    estimated_size = 0
                
                old_data.append([
                    botnet_type,
                    f"{count:,}",
                    format_bytes(estimated_size),
                    f"{(count/total_rows*100):.1f}%" if total_rows > 0 else "0%"
                ])
        
        # 打印表格
        headers = ["僵尸网络", "可清理记录", "预计释放空间", "占比"]
        print(tabulate(old_data, headers=headers, tablefmt="grid"))
        
        print(f"\n总计可清理: {total_old_count:,} 条记录")
        
        conn.close()
        
    except Exception as e:
        print(f"查询失败: {e}")

def main():
    """主函数"""
    print("\n" + "="*80)
    print("僵尸网络平台数据量评估工具")
    print(f"评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 1. 表大小统计
    check_table_sizes()
    
    # 2. 时间分布
    check_data_distribution()
    
    # 3. 旧数据统计
    check_old_data()
    
    print("\n" + "="*80)
    print("评估完成")
    print("="*80)
    print("\n建议:")
    print("1. 如果总存储空间 > 10GB，建议启用数据清理")
    print("2. 如果数据跨度 > 90天，建议启用数据归档")
    print("3. 运行 'python scripts/retention_manager.py --mode daily --dry-run' 查看预计清理量")
    print()

if __name__ == "__main__":
    main()
