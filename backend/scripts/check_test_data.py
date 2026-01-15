#!/usr/bin/env python3
"""
检查test僵尸网络数据存储情况
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from config import DB_CONFIG
from datetime import datetime, timedelta

def check_test_data():
    """检查test数据"""
    try:
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        print("=" * 80)
        print("检查test僵尸网络数据存储情况")
        print("=" * 80)
        
        # 1. 检查表是否存在
        print("\n【1. 检查表是否存在】")
        cursor.execute("""
            SELECT 
                TABLE_NAME,
                TABLE_ROWS,
                CREATE_TIME,
                UPDATE_TIME,
                ROUND(DATA_LENGTH/1024/1024, 2) as DATA_MB,
                ROUND(INDEX_LENGTH/1024/1024, 2) as INDEX_MB
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = 'botnet' 
              AND TABLE_NAME LIKE '%test%'
            ORDER BY TABLE_NAME
        """)
        tables = cursor.fetchall()
        if tables:
            for table in tables:
                print(f"  表名: {table['TABLE_NAME']}")
                print(f"    行数: {table['TABLE_ROWS']}")
                print(f"    创建时间: {table['CREATE_TIME']}")
                print(f"    最后更新: {table['UPDATE_TIME']}")
                print(f"    数据大小: {table['DATA_MB']} MB")
                print(f"    索引大小: {table['INDEX_MB']} MB")
                print()
        else:
            print("  ❌ 未找到test相关的表！")
            print("  提示：需要先运行日志处理器，会自动创建表")
        
        # 2. 检查最新数据
        print("\n【2. 检查最新通信记录 (最近10条)】")
        try:
            cursor.execute("""
                SELECT 
                    id,
                    ip,
                    communication_time,
                    received_at,
                    country,
                    province,
                    city,
                    event_type,
                    is_china
                FROM botnet_communications_test
                ORDER BY id DESC
                LIMIT 10
            """)
            records = cursor.fetchall()
            if records:
                print(f"  ✅ 找到 {len(records)} 条最新记录：")
                for i, record in enumerate(records, 1):
                    print(f"\n  #{i}")
                    print(f"    ID: {record['id']}")
                    print(f"    IP: {record['ip']}")
                    print(f"    通信时间: {record['communication_time']}")
                    print(f"    接收时间: {record['received_at']}")
                    print(f"    位置: {record['country']} {record['province']} {record['city']}")
                    print(f"    事件类型: {record['event_type']}")
                    print(f"    是否中国: {'是' if record['is_china'] else '否'}")
            else:
                print("  ❌ 表中没有数据！")
        except pymysql.err.ProgrammingError as e:
            print(f"  ❌ 表不存在或查询失败: {e}")
        
        # 3. 统计最近1小时的数据
        print("\n【3. 最近1小时的数据统计】")
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(DISTINCT ip) as unique_ips,
                    MIN(received_at) as earliest_time,
                    MAX(received_at) as latest_time
                FROM botnet_communications_test
                WHERE received_at > NOW() - INTERVAL 1 HOUR
            """)
            stats = cursor.fetchone()
            if stats['total_count'] > 0:
                print(f"  ✅ 总记录数: {stats['total_count']}")
                print(f"  ✅ 唯一IP数: {stats['unique_ips']}")
                print(f"  ✅ 最早时间: {stats['earliest_time']}")
                print(f"  ✅ 最晚时间: {stats['latest_time']}")
            else:
                print("  ⚠️  最近1小时内没有新数据")
        except:
            pass
        
        # 4. 统计今天的数据
        print("\n【4. 今天的数据统计】")
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(DISTINCT ip) as unique_ips,
                    MIN(received_at) as earliest_time,
                    MAX(received_at) as latest_time
                FROM botnet_communications_test
                WHERE DATE(received_at) = CURDATE()
            """)
            stats = cursor.fetchone()
            if stats['total_count'] > 0:
                print(f"  ✅ 总记录数: {stats['total_count']}")
                print(f"  ✅ 唯一IP数: {stats['unique_ips']}")
                print(f"  ✅ 最早时间: {stats['earliest_time']}")
                print(f"  ✅ 最晚时间: {stats['latest_time']}")
            else:
                print("  ⚠️  今天还没有数据")
        except:
            pass
        
        # 5. 检查所有僵尸网络的数据量
        print("\n【5. 所有僵尸网络数据量对比】")
        botnet_types = ['asruex', 'mozi', 'andromeda', 'moobot', 'ramnit', 'leethozer', 'test']
        for botnet_type in botnet_types:
            try:
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total_records,
                        MAX(received_at) as last_update
                    FROM botnet_communications_{botnet_type}
                """)
                result = cursor.fetchone()
                status = "✅" if result['total_records'] > 0 else "⚠️ "
                last_update = result['last_update'] if result['last_update'] else "无数据"
                print(f"  {status} {botnet_type:12} : {result['total_records']:10} 条  (最后更新: {last_update})")
            except pymysql.err.ProgrammingError:
                print(f"  ❌ {botnet_type:12} : 表不存在")
        
        # 6. 检查缓冲区状态（如果有）
        print("\n【6. 数据写入建议】")
        try:
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM botnet_communications_test 
                WHERE received_at > NOW() - INTERVAL 5 MINUTE
            """)
            recent = cursor.fetchone()['count']
            if recent == 0:
                print("  ⚠️  最近5分钟没有新数据写入")
                print("  建议检查：")
                print("    1. C2端是否有数据在缓存中（SELECT COUNT(*) FROM cache WHERE pulled = 0）")
                print("    2. 平台端日志处理器是否正在运行")
                print("    3. 平台端日志中的远程拉取统计")
            else:
                print(f"  ✅ 最近5分钟写入了 {recent} 条数据，系统正常工作")
        except:
            pass
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("检查完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n请检查：")
        print("  1. MySQL服务是否运行")
        print("  2. config.py中的DB_CONFIG配置是否正确")
        print("  3. 数据库botnet是否存在")

if __name__ == '__main__':
    check_test_data()
