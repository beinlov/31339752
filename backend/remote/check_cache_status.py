#!/usr/bin/env python3
"""
C2端缓存状态检查工具
用于诊断为什么平台拉取不到数据
"""
import sqlite3
import json
from datetime import datetime

# C2端数据缓存数据库路径
DB_PATH = './data_cache.db'

def check_cache_status():
    """检查缓存状态"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 60)
    print("C2端缓存状态诊断")
    print("=" * 60)
    print()
    
    # 1. 总体统计
    print("【1. 总体统计】")
    cursor.execute("SELECT COUNT(*) as total FROM cache")
    total = cursor.fetchone()['total']
    print(f"  总缓存记录数: {total}")
    
    cursor.execute("SELECT COUNT(*) as count FROM cache WHERE pulled = 0")
    unpulled = cursor.fetchone()['count']
    print(f"  未拉取记录数: {unpulled}")
    
    cursor.execute("SELECT COUNT(*) as count FROM cache WHERE pulled = 1")
    pulled = cursor.fetchone()['count']
    print(f"  已拉取记录数: {pulled}")
    print()
    
    # 2. seq_id范围
    print("【2. seq_id范围】")
    cursor.execute("SELECT MIN(seq_id) as min_seq, MAX(seq_id) as max_seq FROM cache")
    row = cursor.fetchone()
    print(f"  最小seq_id: {row['min_seq']}")
    print(f"  最大seq_id: {row['max_seq']}")
    
    cursor.execute("SELECT MIN(seq_id) as min_seq, MAX(seq_id) as max_seq FROM cache WHERE pulled = 0")
    row = cursor.fetchone()
    print(f"  未拉取记录的seq_id范围: {row['min_seq']} ~ {row['max_seq']}")
    print()
    
    # 3. 检查 seq_id > 396 的记录
    print("【3. seq_id > 396 的记录】")
    cursor.execute("SELECT COUNT(*) as count FROM cache WHERE seq_id > 396")
    count_gt_396 = cursor.fetchone()['count']
    print(f"  seq_id > 396 的总记录数: {count_gt_396}")
    
    cursor.execute("SELECT COUNT(*) as count FROM cache WHERE seq_id > 396 AND pulled = 0")
    count_gt_396_unpulled = cursor.fetchone()['count']
    print(f"  seq_id > 396 且未拉取的记录数: {count_gt_396_unpulled}")
    
    cursor.execute("SELECT COUNT(*) as count FROM cache WHERE seq_id > 396 AND pulled = 1")
    count_gt_396_pulled = cursor.fetchone()['count']
    print(f"  seq_id > 396 且已拉取的记录数: {count_gt_396_pulled}")
    print()
    
    # 4. 按log_type统计未拉取记录
    print("【4. 按log_type统计（未拉取）】")
    cursor.execute("""
        SELECT json_extract(data, '$.log_type') as log_type, 
               COUNT(*) as count,
               MIN(seq_id) as min_seq,
               MAX(seq_id) as max_seq
        FROM cache 
        WHERE pulled = 0
        GROUP BY log_type
    """)
    for row in cursor.fetchall():
        print(f"  {row['log_type']}: {row['count']} 条 (seq_id: {row['min_seq']} ~ {row['max_seq']})")
    print()
    
    # 5. 最近10条未拉取记录详情
    print("【5. 最近10条未拉取记录】")
    cursor.execute("""
        SELECT seq_id, 
               json_extract(data, '$.log_type') as log_type,
               json_extract(data, '$.ip') as ip,
               json_extract(data, '$.timestamp') as timestamp,
               pulled,
               created_at
        FROM cache 
        WHERE pulled = 0
        ORDER BY seq_id DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    if rows:
        print(f"  {'seq_id':<10} {'log_type':<10} {'IP':<18} {'timestamp':<20} {'created_at':<20}")
        print(f"  {'-'*10} {'-'*10} {'-'*18} {'-'*20} {'-'*20}")
        for row in rows:
            print(f"  {row['seq_id']:<10} {row['log_type']:<10} {row['ip']:<18} {str(row['timestamp'])[:20]:<20} {str(row['created_at'])[:20]:<20}")
    else:
        print("  没有未拉取记录")
    print()
    
    # 6. 最近10条已拉取记录详情
    print("【6. 最近10条已拉取记录】")
    cursor.execute("""
        SELECT seq_id, 
               json_extract(data, '$.log_type') as log_type,
               json_extract(data, '$.ip') as ip,
               json_extract(data, '$.timestamp') as timestamp,
               pulled,
               pulled_at
        FROM cache 
        WHERE pulled = 1
        ORDER BY seq_id DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    if rows:
        print(f"  {'seq_id':<10} {'log_type':<10} {'IP':<18} {'timestamp':<20} {'pulled_at':<20}")
        print(f"  {'-'*10} {'-'*10} {'-'*18} {'-'*20} {'-'*20}")
        for row in rows:
            print(f"  {row['seq_id']:<10} {row['log_type']:<10} {row['ip']:<18} {str(row['timestamp'])[:20]:<20} {str(row['pulled_at'])[:20]:<20}")
    else:
        print("  没有已拉取记录")
    print()
    
    # 7. 诊断结论
    print("=" * 60)
    print("【诊断结论】")
    print("=" * 60)
    
    if unpulled == 0:
        print("✅ 所有缓存数据已被拉取，等待新数据生成")
    elif count_gt_396_unpulled == 0:
        print("⚠️  有未拉取记录，但seq_id都 <= 396")
        print("   可能原因：")
        print("   1. 平台的断点续传游标(396)已经是最新的")
        print("   2. C2端没有生成新的数据")
        print("   解决方法：")
        print("   - 等待C2生成新的上线或清除日志")
        print("   - 或者重置平台的断点续传状态")
    else:
        print(f"✅ 有 {count_gt_396_unpulled} 条未拉取记录（seq_id > 396）")
        print("   平台应该能拉取到这些数据")
        print("   如果仍然拉取不到，请检查：")
        print("   1. C2端API服务是否正常运行")
        print("   2. 网络连接是否正常")
        print("   3. 平台端断点续传状态文件")
    
    conn.close()


if __name__ == '__main__':
    try:
        check_cache_status()
    except FileNotFoundError:
        print(f"错误: 找不到数据库文件 {DB_PATH}")
        print("请确保在C2服务器的工作目录下运行此脚本")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
