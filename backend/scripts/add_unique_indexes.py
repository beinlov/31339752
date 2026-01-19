"""
为僵尸网络节点表添加唯一索引
目的：从数据库层面防止IP重复插入，根治数据重复问题

警告：
1. 执行前必须先去重数据（运行 deduplicate_nodes.py --execute）
2. 如果表中已有重复数据，添加索引会失败
3. 建议在低峰期执行
"""
import pymysql
import sys
import os

# 添加父目录到路径以便导入config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DB_CONFIG

# 僵尸网络类型列表
BOTNET_TYPES = ['asruex', 'mozi', 'andromeda', 'moobot', 'ramnit', 'leethozer']

def check_duplicates(cursor, botnet_type):
    """检查表中是否有重复IP"""
    table_name = f"botnet_nodes_{botnet_type}"
    
    cursor.execute(f"""
        SELECT COUNT(*) as total_records,
               COUNT(DISTINCT ip) as unique_ips
        FROM {table_name}
    """)
    
    result = cursor.fetchone()
    total = result['total_records']
    unique = result['unique_ips']
    duplicates = total - unique
    
    return {
        'total_records': total,
        'unique_ips': unique,
        'duplicates': duplicates,
        'has_duplicates': duplicates > 0
    }

def check_existing_index(cursor, botnet_type):
    """检查是否已存在唯一索引"""
    table_name = f"botnet_nodes_{botnet_type}"
    
    cursor.execute("""
        SELECT INDEX_NAME, NON_UNIQUE
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = %s 
          AND TABLE_NAME = %s
          AND COLUMN_NAME = 'ip'
    """, (DB_CONFIG['database'], table_name))
    
    indexes = cursor.fetchall()
    
    for index in indexes:
        if index['NON_UNIQUE'] == 0:  # 0 表示唯一索引
            return True, index['INDEX_NAME']
    
    return False, None

def add_unique_index(cursor, botnet_type, force=False):
    """为表添加唯一索引"""
    table_name = f"botnet_nodes_{botnet_type}"
    
    print(f"\n{'='*60}")
    print(f"处理 {botnet_type}")
    print(f"{'='*60}")
    
    # 检查表是否存在
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM information_schema.tables 
        WHERE table_schema = %s AND table_name = %s
    """, (DB_CONFIG['database'], table_name))
    
    if cursor.fetchone()['count'] == 0:
        print(f"[!] 表 {table_name} 不存在，跳过")
        return False
    
    # 检查是否已存在唯一索引
    has_index, index_name = check_existing_index(cursor, botnet_type)
    if has_index:
        print(f"[!] 表 {table_name} 已存在唯一索引: {index_name}")
        if not force:
            print(f"    跳过（如需强制重建，使用 --force 参数）")
            return False
        else:
            print(f"    强制模式：将删除旧索引并重建")
            try:
                cursor.execute(f"ALTER TABLE {table_name} DROP INDEX {index_name}")
                print(f"    [+] 已删除旧索引 {index_name}")
            except Exception as e:
                print(f"    [!] 删除旧索引失败: {e}")
    
    # 检查重复数据
    print("\n[*] 检查重复数据...")
    dup_info = check_duplicates(cursor, botnet_type)
    print(f"    总记录数: {dup_info['total_records']:,}")
    print(f"    唯一IP数: {dup_info['unique_ips']:,}")
    print(f"    重复记录: {dup_info['duplicates']:,}")
    
    if dup_info['has_duplicates']:
        print(f"\n[!] 错误：表中存在 {dup_info['duplicates']:,} 条重复记录")
        print(f"    无法添加唯一索引，请先运行去重脚本：")
        print(f"    python deduplicate_nodes.py --execute --botnet {botnet_type}")
        return False
    
    # 添加唯一索引
    print(f"\n[*] 添加唯一索引...")
    try:
        cursor.execute(f"""
            ALTER TABLE {table_name} 
            ADD UNIQUE INDEX idx_unique_ip (ip)
        """)
        print(f"[+] 成功添加唯一索引 idx_unique_ip")
        return True
    except Exception as e:
        print(f"[!] 添加索引失败: {e}")
        return False

def verify_index(cursor, botnet_type):
    """验证唯一索引是否正常工作"""
    table_name = f"botnet_nodes_{botnet_type}"
    test_ip = '999.999.999.999'
    
    print(f"\n[*] 验证唯一索引...")
    
    try:
        # 第一次插入
        cursor.execute(f"""
            INSERT INTO {table_name} 
            (ip, longitude, latitude, country, province, city, continent, isp, asn, 
             status, active_time, is_china, created_time, updated_at)
            VALUES 
            (%s, 0, 0, 'Test', 'Test', 'Test', 'Test', 'Test', 'Test', 'active', NOW(), 0, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                country = VALUES(country),
                updated_at = NOW()
        """, (test_ip,))
        
        # 第二次插入相同IP
        cursor.execute(f"""
            INSERT INTO {table_name} 
            (ip, longitude, latitude, country, province, city, continent, isp, asn, 
             status, active_time, is_china, created_time, updated_at)
            VALUES 
            (%s, 0, 0, 'Test2', 'Test2', 'Test2', 'Test2', 'Test2', 'Test2', 'active', NOW(), 0, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                country = VALUES(country),
                updated_at = NOW()
        """, (test_ip,))
        
        # 检查是否只有一条记录
        cursor.execute(f"""
            SELECT COUNT(*) as count FROM {table_name} WHERE ip = %s
        """, (test_ip,))
        
        count = cursor.fetchone()['count']
        
        # 清理测试数据
        cursor.execute(f"DELETE FROM {table_name} WHERE ip = %s", (test_ip,))
        
        if count == 1:
            print(f"[+] 验证通过：唯一索引工作正常（重复IP自动更新）")
            return True
        else:
            print(f"[!] 验证失败：发现 {count} 条记录（应该为1）")
            return False
            
    except Exception as e:
        print(f"[!] 验证失败: {e}")
        # 尝试清理测试数据
        try:
            cursor.execute(f"DELETE FROM {table_name} WHERE ip = %s", (test_ip,))
        except:
            pass
        return False

def main():
    import argparse
    import io
    
    # 设置UTF-8输出
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    parser = argparse.ArgumentParser(description='为僵尸网络节点表添加唯一索引')
    parser.add_argument('--botnet', type=str, 
                       help='指定僵尸网络类型（默认处理所有）')
    parser.add_argument('--force', action='store_true',
                       help='强制重建已存在的索引')
    parser.add_argument('--verify', action='store_true',
                       help='添加索引后验证其是否工作')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='自动确认，不询问')
    
    args = parser.parse_args()
    
    # 确定要处理的僵尸网络列表
    botnets = [args.botnet] if args.botnet else BOTNET_TYPES
    
    print("\n" + "="*60)
    print("[*] 唯一索引添加工具")
    print("="*60)
    print(f"处理范围: {', '.join(botnets)}")
    print(f"强制模式: {'是' if args.force else '否'}")
    print(f"验证模式: {'是' if args.verify else '否'}")
    print("="*60)
    
    print("\n[!] 警告：")
    print("    1. 如果表中有重复数据，添加索引会失败")
    print("    2. 请确保已运行去重脚本")
    print("    3. 建议先备份数据库")
    
    if not args.yes:
        input("\n按 Enter 继续，或 Ctrl+C 取消...")
    else:
        print("\n[*] 自动确认模式，继续执行...")
    
    conn = None
    cursor = None
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for botnet_type in botnets:
            result = add_unique_index(cursor, botnet_type, args.force)
            
            if result:
                success_count += 1
                
                # 验证索引
                if args.verify:
                    if verify_index(cursor, botnet_type):
                        print(f"[+] {botnet_type} 索引验证通过")
                    else:
                        print(f"[!] {botnet_type} 索引验证失败")
                
                conn.commit()
                print(f"[+] {botnet_type} 的更改已提交")
            elif result is False:
                has_index, _ = check_existing_index(cursor, botnet_type)
                if has_index and not args.force:
                    skipped_count += 1
                else:
                    failed_count += 1
        
        # 总结
        print("\n" + "="*60)
        print("[*] 执行完成总结")
        print("="*60)
        print(f"成功添加索引: {success_count} 个")
        print(f"跳过（已存在）: {skipped_count} 个")
        print(f"失败: {failed_count} 个")
        
        if success_count > 0:
            print("\n[+] 唯一索引已成功添加！")
            print("\n[*] 下一步操作：")
            print("    1. 重建聚合表：python rebuild_aggregation.py")
            print("    2. 验证数据一致性")
            print("    3. 导入新数据测试")
        
        if failed_count > 0:
            print("\n[!] 部分表添加索引失败，请检查错误信息")
            print("    可能需要先运行去重脚本")
        
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
