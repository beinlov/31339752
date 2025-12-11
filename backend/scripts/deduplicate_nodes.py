"""
节点数据去重脚本
清理 botnet_nodes_* 表中的重复IP记录，保留每个IP最新的一条记录
"""
import pymysql
import sys
import os
from datetime import datetime

# 添加父目录到路径以便导入config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DB_CONFIG

# 僵尸网络类型列表
BOTNET_TYPES = ['asruex', 'mozi', 'andromeda', 'moobot', 'ramnit', 'leethozer']

def analyze_duplicates(cursor, botnet_type):
    """分析重复数据情况"""
    table_name = f"botnet_nodes_{botnet_type}"
    
    print(f"\n{'='*60}")
    print(f"分析 {botnet_type} 的重复数据...")
    print(f"{'='*60}")
    
    # 检查表是否存在
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM information_schema.tables 
        WHERE table_schema = %s AND table_name = %s
    """, (DB_CONFIG['database'], table_name))
    
    if cursor.fetchone()['count'] == 0:
        print(f"⚠️  表 {table_name} 不存在，跳过")
        return None
    
    # 总记录数
    cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
    total_records = cursor.fetchone()['total']
    
    # 唯一IP数
    cursor.execute(f"SELECT COUNT(DISTINCT ip) as unique_ips FROM {table_name}")
    unique_ips = cursor.fetchone()['unique_ips']
    
    # 重复记录数
    duplicate_records = total_records - unique_ips
    
    print(f"[+] 总记录数: {total_records:,}")
    print(f"[+] 唯一IP数: {unique_ips:,}")
    print(f"[+] 重复记录: {duplicate_records:,} ({duplicate_records/total_records*100:.2f}%)")
    
    # 重复IP统计
    cursor.execute(f"""
        SELECT ip, COUNT(*) as count 
        FROM {table_name}
        GROUP BY ip
        HAVING count > 1
        ORDER BY count DESC
        LIMIT 10
    """)
    
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"\n[-] 重复次数最多的IP（Top 10）:")
        for dup in duplicates:
            print(f"   - IP: {dup['ip']:15s} 重复 {dup['count']} 次")
    
    return {
        'total_records': total_records,
        'unique_ips': unique_ips,
        'duplicate_records': duplicate_records,
        'has_duplicates': duplicate_records > 0
    }

def deduplicate_nodes(cursor, botnet_type, dry_run=True):
    """
    去重节点数据
    
    策略：对于同一IP的多条记录，保留 updated_at 最新的一条，删除其他
    """
    table_name = f"botnet_nodes_{botnet_type}"
    
    print(f"\n{'='*60}")
    print(f"{'[模拟运行]' if dry_run else '[正式运行]'} 去重 {botnet_type}")
    print(f"{'='*60}")
    
    # 查找需要删除的记录
    cursor.execute(f"""
        SELECT t1.id, t1.ip, t1.updated_at
        FROM {table_name} t1
        WHERE EXISTS (
            SELECT 1 
            FROM {table_name} t2 
            WHERE t2.ip = t1.ip 
            AND (
                t2.updated_at > t1.updated_at 
                OR (t2.updated_at = t1.updated_at AND t2.id > t1.id)
            )
        )
        ORDER BY t1.ip, t1.updated_at
    """)
    
    records_to_delete = cursor.fetchall()
    
    if not records_to_delete:
        print("[!] 没有重复记录需要删除")
        return 0
    
    print(f"[-] 找到 {len(records_to_delete):,} 条需要删除的重复记录")
    
    if dry_run:
        print(f"\n[!] 这是模拟运行，不会实际删除数据")
        print("   如需真正删除，请运行: python deduplicate_nodes.py --execute")
        
        # 显示前5条示例
        print(f"\n[+] 示例（前5条）:")
        for i, record in enumerate(records_to_delete[:5], 1):
            print(f"   {i}. ID={record['id']}, IP={record['ip']}, Updated={record['updated_at']}")
        
        return len(records_to_delete)
    
    # 实际删除
    print(f"\n[!] 开始删除重复数据...")
    
    # 分批删除，避免一次性删除太多
    batch_size = 1000
    deleted_count = 0
    
    ids_to_delete = [record['id'] for record in records_to_delete]
    
    for i in range(0, len(ids_to_delete), batch_size):
        batch = ids_to_delete[i:i+batch_size]
        placeholders = ','.join(['%s'] * len(batch))
        
        cursor.execute(f"""
            DELETE FROM {table_name}
            WHERE id IN ({placeholders})
        """, tuple(batch))
        
        deleted_count += cursor.rowcount
        print(f"   已删除: {deleted_count:,} / {len(ids_to_delete):,} 记录")
    
    print(f"[!] 删除完成！共删除 {deleted_count:,} 条重复记录")
    
    return deleted_count

def verify_deduplication(cursor, botnet_type):
    """验证去重结果"""
    table_name = f"botnet_nodes_{botnet_type}"
    
    print(f"\n{'='*60}")
    print(f"验证 {botnet_type} 的去重结果")
    print(f"{'='*60}")
    
    # 检查是否还有重复
    cursor.execute(f"""
        SELECT ip, COUNT(*) as count
        FROM {table_name}
        GROUP BY ip
        HAVING count > 1
    """)
    
    remaining_duplicates = cursor.fetchall()
    
    if remaining_duplicates:
        print(f"[!] 仍有 {len(remaining_duplicates)} 个IP存在重复记录！")
        for dup in remaining_duplicates[:5]:
            print(f"   - IP: {dup['ip']} 仍有 {dup['count']} 条记录")
        return False
    else:
        print("[!] 验证通过：所有IP都是唯一的")
        
        # 显示最终统计
        cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
        total = cursor.fetchone()['total']
        print(f"[+] 最终记录数: {total:,}")
        
        return True

def main():
    import argparse
    import io
    import sys
    
    # 设置UTF-8输出，避免Windows编码问题
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    parser = argparse.ArgumentParser(description='节点数据去重工具')
    parser.add_argument('--execute', action='store_true', 
                       help='真正执行去重操作（默认为模拟运行）')
    parser.add_argument('--botnet', type=str, 
                       help='指定僵尸网络类型（默认处理所有）')
    parser.add_argument('--analyze-only', action='store_true',
                       help='仅分析，不执行去重')
    
    args = parser.parse_args()
    
    # 确定要处理的僵尸网络列表
    botnets = [args.botnet] if args.botnet else BOTNET_TYPES
    
    print("\n" + "="*60)
    print("[*] 节点数据去重工具")
    print("="*60)
    print(f"模式: {'正式运行' if args.execute else '模拟运行'}")
    print(f"处理范围: {', '.join(botnets)}")
    print("="*60)
    
    conn = None
    cursor = None
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        total_analyzed = 0
        total_deleted = 0
        
        for botnet_type in botnets:
            # 分析重复情况
            analysis = analyze_duplicates(cursor, botnet_type)
            
            if analysis is None:
                continue
                
            total_analyzed += 1
            
            if args.analyze_only:
                continue
            
            # 执行去重
            if analysis['has_duplicates']:
                deleted = deduplicate_nodes(cursor, botnet_type, dry_run=not args.execute)
                total_deleted += deleted
                
                # 如果是正式运行，验证结果
                if args.execute:
                    verify_deduplication(cursor, botnet_type)
                    conn.commit()
                    print("[!] 数据已提交到数据库")
        
        # 总结
        print("\n" + "="*60)
        print("[*] 总结")
        print("="*60)
        print(f"已分析: {total_analyzed} 个僵尸网络")
        print(f"{'将删除' if not args.execute else '已删除'}: {total_deleted:,} 条重复记录")
        
        if not args.execute and total_deleted > 0:
            print(f"\n[!] 提示：这是模拟运行，数据未被修改")
            print("   如需真正删除，请运行:")
            print("   python deduplicate_nodes.py --execute")
        
        print("="*60)
        
    except Exception as e:
        print(f"\n[!] 错误: {e}")
        if conn:
            conn.rollback()
            print("已回滚事务")
        raise
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
