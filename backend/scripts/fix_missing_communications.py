"""
修复缺失的通信记录
为节点表中有数据但通信表中无对应记录的节点补充通信记录
"""
import pymysql
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

def fix_missing_communications(botnet_type='test', dry_run=True):
    """
    修复缺失的通信记录
    
    Args:
        botnet_type: 僵尸网络类型（默认test）
        dry_run: 是否只模拟运行不实际修复（默认True）
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        node_table = f"botnet_nodes_{botnet_type}"
        comm_table = f"botnet_communications_{botnet_type}"
        
        print(f"="*60)
        print(f"  修复 {botnet_type} 僵尸网络的缺失通信记录")
        print(f"  模式: {'模拟运行（不实际修改）' if dry_run else '实际修复'}")
        print(f"="*60)
        print()
        
        # Step 1: 检查缺失数量
        print("Step 1: 检查数据不一致情况...")
        
        cursor.execute(f"""
            SELECT COUNT(*) as total_nodes FROM {node_table}
        """)
        total_nodes = cursor.fetchone()['total_nodes']
        print(f"  节点表总数: {total_nodes}")
        
        cursor.execute(f"""
            SELECT COUNT(*) as total_comms FROM {comm_table}
        """)
        total_comms = cursor.fetchone()['total_comms']
        print(f"  通信表总数: {total_comms}")
        
        cursor.execute(f"""
            SELECT COUNT(DISTINCT node_id) as unique_nodes_in_comm FROM {comm_table}
        """)
        unique_nodes = cursor.fetchone()['unique_nodes_in_comm']
        print(f"  通信表中唯一节点数: {unique_nodes}")
        
        cursor.execute(f"""
            SELECT COUNT(DISTINCT n.id) as missing_count
            FROM {node_table} n
            LEFT JOIN {comm_table} c ON n.id = c.node_id
            WHERE c.id IS NULL
        """)
        missing_count = cursor.fetchone()['missing_count']
        print(f"  缺失通信记录的节点数: {missing_count}")
        
        if missing_count == 0:
            print("\n✅ 没有发现数据不一致，无需修复！")
            return
        
        print(f"\n⚠️  发现 {missing_count} 个节点缺失通信记录")
        
        # Step 2: 查询缺失的节点详情
        print("\nStep 2: 查询缺失节点的详细信息...")
        
        cursor.execute(f"""
            SELECT 
                n.id, n.ip, n.first_seen, n.last_seen,
                n.longitude, n.latitude, n.country, n.province, n.city,
                n.continent, n.isp, n.asn, n.status, n.is_china,
                n.communication_count
            FROM {node_table} n
            LEFT JOIN {comm_table} c ON n.id = c.node_id
            WHERE c.id IS NULL
            ORDER BY n.id
        """)
        
        missing_nodes = cursor.fetchall()
        
        # 显示前10条样本
        print(f"\n  缺失节点样本（前10条）:")
        print(f"  {'ID':<8} {'IP':<18} {'First Seen':<20} {'Country':<15} {'Comm Count':<12}")
        print(f"  {'-'*80}")
        for node in missing_nodes[:10]:
            print(f"  {node['id']:<8} {node['ip']:<18} {str(node['first_seen']):<20} {node['country']:<15} {node['communication_count']:<12}")
        
        if len(missing_nodes) > 10:
            print(f"  ... 还有 {len(missing_nodes) - 10} 条")
        
        # Step 3: 准备插入数据
        if dry_run:
            print(f"\n[模拟模式] 将为 {len(missing_nodes)} 个节点补充通信记录")
            print("\n要实际执行修复，请使用参数: dry_run=False")
            return
        
        # 实际修复
        print(f"\nStep 3: 开始补充缺失的通信记录...")
        
        # 准备批量插入数据
        insert_sql = f"""
            INSERT INTO {comm_table}
            (node_id, ip, communication_time, longitude, latitude, country, province, 
             city, continent, isp, asn, event_type, status, is_china)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        insert_values = []
        for node in missing_nodes:
            insert_values.append((
                node['id'],  # node_id
                node['ip'],
                node['first_seen'],  # 使用first_seen作为communication_time
                node['longitude'],
                node['latitude'],
                node['country'],
                node['province'],
                node['city'],
                node['continent'],
                node['isp'],
                node['asn'],
                'data_recovery',  # event_type标记为数据恢复
                node['status'],
                node['is_china']
            ))
        
        # 分批插入，每批500条
        batch_size = 500
        total_inserted = 0
        
        for i in range(0, len(insert_values), batch_size):
            batch = insert_values[i:i+batch_size]
            cursor.executemany(insert_sql, batch)
            total_inserted += len(batch)
            print(f"  已插入: {total_inserted}/{len(insert_values)} ({(total_inserted/len(insert_values)*100):.1f}%)")
        
        # 提交事务
        conn.commit()
        
        print(f"\n✅ 成功补充 {total_inserted} 条通信记录！")
        
        # Step 4: 验证修复结果
        print(f"\nStep 4: 验证修复结果...")
        
        cursor.execute(f"""
            SELECT COUNT(DISTINCT n.id) as missing_count_after
            FROM {node_table} n
            LEFT JOIN {comm_table} c ON n.id = c.node_id
            WHERE c.id IS NULL
        """)
        missing_after = cursor.fetchone()['missing_count_after']
        
        cursor.execute(f"""
            SELECT COUNT(*) as total_comms_after FROM {comm_table}
        """)
        total_comms_after = cursor.fetchone()['total_comms_after']
        
        print(f"  修复前缺失: {missing_count}")
        print(f"  修复后缺失: {missing_after}")
        print(f"  修复前通信表总数: {total_comms}")
        print(f"  修复后通信表总数: {total_comms_after}")
        print(f"  新增通信记录: {total_comms_after - total_comms}")
        
        if missing_after == 0:
            print(f"\n🎉 数据一致性修复完成！")
        else:
            print(f"\n⚠️  仍有 {missing_after} 条记录缺失，请检查")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        if not dry_run:
            try:
                conn.rollback()
                print("已回滚事务")
            except:
                pass
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def show_help():
    """显示帮助信息"""
    print("""
    用法:
        python fix_missing_communications.py [botnet_type] [--fix]
    
    参数:
        botnet_type   僵尸网络类型（默认: test）
        --fix         实际执行修复（不加此参数则只模拟运行）
    
    示例:
        # 模拟运行，检查test僵尸网络
        python fix_missing_communications.py
        
        # 模拟运行，检查mozi僵尸网络
        python fix_missing_communications.py mozi
        
        # 实际修复test僵尸网络
        python fix_missing_communications.py test --fix
        
        # 实际修复所有僵尸网络
        python fix_missing_communications.py all --fix
    """)

if __name__ == '__main__':
    import sys
    
    # 解析命令行参数
    botnet_type = 'test'
    dry_run = True
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h', 'help']:
            show_help()
            sys.exit(0)
        botnet_type = sys.argv[1]
    
    if '--fix' in sys.argv:
        dry_run = False
    
    if botnet_type == 'all':
        # 修复所有僵尸网络
        botnets = ['test', 'andromeda', 'asruex', 'autoupdate', 'leethozer', 'moobot', 'mozi', 'ramnit']
        print(f"\n将检查/修复所有僵尸网络...")
        print(f"模式: {'实际修复' if not dry_run else '模拟运行'}\n")
        
        for botnet in botnets:
            try:
                fix_missing_communications(botnet, dry_run)
                print("\n" + "="*60 + "\n")
            except Exception as e:
                print(f"处理 {botnet} 时出错: {e}\n")
                continue
    else:
        # 修复单个僵尸网络
        fix_missing_communications(botnet_type, dry_run)
