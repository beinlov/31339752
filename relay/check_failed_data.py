#!/usr/bin/env python3
"""
失败数据检查脚本
查看中转服务器中失败数据的详细信息
"""

import sqlite3
import sys
import json
from datetime import datetime
from pathlib import Path

# 默认数据库路径
DEFAULT_DB = "./relay_cache.db"


def check_failed_data(db_file: str = DEFAULT_DB):
    """检查失败数据的详细信息"""
    
    if not Path(db_file).exists():
        print(f"❌ 数据库文件不存在: {db_file}")
        print(f"   请确保路径正确，或使用 --db 参数指定数据库文件")
        return
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("中转服务器数据状态检查")
    print("=" * 80)
    print(f"数据库: {db_file}")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 1. 总体统计
    print("\n【总体统计】")
    cursor.execute("""
        SELECT 
            status,
            COUNT(*) as count,
            MIN(created_at) as first_time,
            MAX(created_at) as last_time
        FROM data_records
        GROUP BY status
    """)
    
    rows = cursor.fetchall()
    if rows:
        print(f"{'状态':<12} {'数量':<10} {'最早时间':<25} {'最晚时间':<25}")
        print("-" * 80)
        for row in rows:
            status, count, first_time, last_time = row
            print(f"{status:<12} {count:<10} {first_time or 'N/A':<25} {last_time or 'N/A':<25}")
    else:
        print("暂无数据")
    
    # 2. 失败数据统计（按重试次数分组）
    print("\n【失败数据统计（按重试次数）】")
    cursor.execute("""
        SELECT 
            retry_count,
            COUNT(*) as count,
            MIN(created_at) as oldest,
            MAX(created_at) as newest
        FROM data_records
        WHERE status = 'failed'
        GROUP BY retry_count
        ORDER BY retry_count ASC
    """)
    
    rows = cursor.fetchall()
    if rows:
        print(f"{'重试次数':<12} {'数量':<10} {'最早创建':<25} {'最新创建':<25}")
        print("-" * 80)
        total_failed = 0
        for row in rows:
            retry_count, count, oldest, newest = row
            total_failed += count
            status_mark = "⚠️" if retry_count > 15 else ""
            print(f"{retry_count:<12} {count:<10} {oldest or 'N/A':<25} {newest or 'N/A':<25} {status_mark}")
        print("-" * 80)
        print(f"失败数据总计: {total_failed} 条")
    else:
        print("✅ 无失败数据")
    
    # 3. 高重试次数数据（告警）
    print("\n【高重试次数数据告警】")
    cursor.execute("""
        SELECT COUNT(*), MAX(retry_count)
        FROM data_records
        WHERE status = 'failed' AND retry_count > 10
    """)
    
    row = cursor.fetchone()
    if row and row[0] > 0:
        count, max_retry = row
        print(f"⚠️ 警告: {count} 条数据重试次数 > 10")
        print(f"   最大重试次数: {max_retry}")
        print(f"   建议: 检查平台服务器连接状态")
    else:
        print("✅ 无高重试次数数据")
    
    # 4. 即将被放弃的数据（retry_count > 20）
    print("\n【即将被放弃的数据】")
    cursor.execute("""
        SELECT COUNT(*), MAX(retry_count)
        FROM data_records
        WHERE status = 'failed' AND retry_count > 20
    """)
    
    row = cursor.fetchone()
    if row and row[0] > 0:
        count, max_retry = row
        print(f"🚨 严重警告: {count} 条数据将被放弃（retry_count > 20）")
        print(f"   最大重试次数: {max_retry}")
        print(f"   这些数据将不再自动重试")
        print(f"   建议: 立即修复平台连接，或手动重置这些数据")
    else:
        print("✅ 无即将被放弃的数据")
    
    # 5. C2服务器来源统计
    print("\n【数据来源统计】")
    cursor.execute("""
        SELECT 
            c2_server,
            status,
            COUNT(*) as count
        FROM data_records
        GROUP BY c2_server, status
        ORDER BY c2_server, status
    """)
    
    rows = cursor.fetchall()
    if rows:
        print(f"{'C2服务器':<30} {'状态':<12} {'数量':<10}")
        print("-" * 80)
        for row in rows:
            c2_server, status, count = row
            c2_display = c2_server or 'unknown'
            print(f"{c2_display:<30} {status:<12} {count:<10}")
    else:
        print("暂无数据")
    
    # 6. 最近的失败记录（Top 5）
    print("\n【最近失败的记录（Top 5）】")
    cursor.execute("""
        SELECT 
            id,
            botnet_type,
            ip,
            retry_count,
            created_at,
            c2_server
        FROM data_records
        WHERE status = 'failed'
        ORDER BY created_at DESC
        LIMIT 5
    """)
    
    rows = cursor.fetchall()
    if rows:
        for i, row in enumerate(rows, 1):
            record_id, botnet_type, ip, retry_count, created_at, c2_server = row
            print(f"\n{i}. ID: {record_id}")
            print(f"   类型: {botnet_type}, IP: {ip}")
            print(f"   重试: {retry_count} 次")
            print(f"   创建: {created_at}")
            print(f"   来源: {c2_server or 'unknown'}")
    else:
        print("✅ 无失败记录")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)


def reset_failed_data(db_file: str = DEFAULT_DB, max_retry: int = None):
    """重置失败数据，将其改回pending状态"""
    
    if not Path(db_file).exists():
        print(f"❌ 数据库文件不存在: {db_file}")
        return
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    if max_retry is not None:
        print(f"重置 retry_count > {max_retry} 的失败数据...")
        cursor.execute("""
            UPDATE data_records
            SET status = 'pending'
            WHERE status = 'failed' AND retry_count > ?
        """, (max_retry,))
    else:
        print("重置所有失败数据...")
        cursor.execute("""
            UPDATE data_records
            SET status = 'pending'
            WHERE status = 'failed'
        """)
    
    updated = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"✅ 已重置 {updated} 条数据为 pending 状态")
    print(f"   这些数据将在下次推送循环中重新尝试")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="中转服务器失败数据检查工具")
    parser.add_argument('--db', default=DEFAULT_DB, help=f"数据库文件路径 (默认: {DEFAULT_DB})")
    parser.add_argument('--reset', action='store_true', help="重置所有失败数据为pending状态")
    parser.add_argument('--reset-threshold', type=int, metavar='N', 
                       help="重置retry_count > N的失败数据")
    
    args = parser.parse_args()
    
    if args.reset:
        confirm = input("⚠️ 确认重置所有失败数据为pending? (yes/no): ")
        if confirm.lower() == 'yes':
            reset_failed_data(args.db)
        else:
            print("已取消")
    elif args.reset_threshold is not None:
        confirm = input(f"⚠️ 确认重置retry_count > {args.reset_threshold}的失败数据? (yes/no): ")
        if confirm.lower() == 'yes':
            reset_failed_data(args.db, args.reset_threshold)
        else:
            print("已取消")
    else:
        check_failed_data(args.db)


if __name__ == '__main__':
    main()
