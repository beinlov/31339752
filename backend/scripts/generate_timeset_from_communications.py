#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据 communications 表的 received_at 时间生成历史 timeset 数据
按每天的通信记录统计当天的节点数据并写入 timeset 表
"""
import pymysql
import sys
import os
from datetime import datetime, date, timedelta

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DB_CONFIG, ALLOWED_BOTNET_TYPES


def generate_timeset_from_communications(days=30, botnet_type=None):
    """
    根据 communications 表生成过去 N 天的 timeset 数据
    
    Args:
        days: 生成多少天的历史数据（默认30天）
        botnet_type: 僵尸网络类型，None表示处理所有类型
    """
    print("=" * 60)
    print(f"开始根据 communications 表生成过去 {days} 天的 timeset 数据")
    print("=" * 60)
    
    conn = None
    cursor = None
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        today = date.today()
        start_date = today - timedelta(days=days - 1)
        
        # 处理所有僵尸网络类型或指定的类型
        if botnet_type:
            botnet_types = [botnet_type]
        else:
            botnet_types = ALLOWED_BOTNET_TYPES
        
        print(f"\n将处理以下僵尸网络类型: {', '.join(botnet_types)}")
        print(f"日期范围: {start_date} ~ {today}")
        
        total_success = 0
        total_skip = 0
        
        for botnet_type in botnet_types:
            print(f"\n{'=' * 60}")
            print(f"处理僵尸网络: {botnet_type}")
            print(f"{'=' * 60}")
            
            comm_table = f"botnet_communications_{botnet_type}"
            timeset_table = f"botnet_timeset_{botnet_type}"
            
            # 检查 communications 表是否存在
            cursor.execute(f"""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = %s
            """, (comm_table,))
            
            if cursor.fetchone()['count'] == 0:
                print(f"[跳过] {comm_table} 表不存在")
                continue
            
            # 检查 timeset 表是否存在
            cursor.execute(f"""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = %s
            """, (timeset_table,))
            
            if cursor.fetchone()['count'] == 0:
                print(f"[跳过] {timeset_table} 表不存在")
                continue
            
            # 遍历每一天
            current_date = start_date
            success_count = 0
            skip_count = 0
            
            while current_date <= today:
                # 统计当天 communications 表的数据
                cursor.execute(f"""
                    SELECT 
                        COUNT(DISTINCT ip) as total_ips,
                        COUNT(DISTINCT CASE WHEN status = 'active' THEN ip END) as active_ips,
                        COUNT(DISTINCT CASE WHEN status = 'cleaned' THEN ip END) as cleaned_ips,
                        COUNT(DISTINCT CASE WHEN country = '中国' THEN ip END) as china_total,
                        COUNT(DISTINCT CASE WHEN country = '中国' AND status = 'active' THEN ip END) as china_active,
                        COUNT(DISTINCT CASE WHEN country = '中国' AND status = 'cleaned' THEN ip END) as china_cleaned
                    FROM {comm_table}
                    WHERE DATE(received_at) = %s
                """, (current_date,))
                
                result = cursor.fetchone()
                
                global_count = int(result['total_ips'] or 0)
                global_active = int(result['active_ips'] or 0)
                global_cleaned = int(result['cleaned_ips'] or 0)
                china_count = int(result['china_total'] or 0)
                china_active = int(result['china_active'] or 0)
                china_cleaned = int(result['china_cleaned'] or 0)
                
                # 如果当天没有通信记录，跳过（保持原有数据或0）
                if global_count == 0:
                    print(f"  {current_date}: 无通信记录，跳过")
                    skip_count += 1
                    current_date += timedelta(days=1)
                    continue
                
                # 写入或更新 timeset 表
                cursor.execute(f"""
                    INSERT INTO {timeset_table} 
                    (date, global_count, china_count, global_active, china_active, global_cleaned, china_cleaned)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        global_count = VALUES(global_count),
                        china_count = VALUES(china_count),
                        global_active = VALUES(global_active),
                        china_active = VALUES(china_active),
                        global_cleaned = VALUES(global_cleaned),
                        china_cleaned = VALUES(china_cleaned),
                        updated_at = CURRENT_TIMESTAMP
                """, (current_date, global_count, china_count, global_active, china_active, global_cleaned, china_cleaned))
                
                print(f"  {current_date}: 全球 {global_count:,} (活跃{global_active}, 清除{global_cleaned}), "
                      f"中国 {china_count:,} (活跃{china_active}, 清除{china_cleaned})")
                
                success_count += 1
                current_date += timedelta(days=1)
            
            print(f"\n[{botnet_type}] 成功: {success_count} 天, 跳过: {skip_count} 天")
            total_success += success_count
            total_skip += skip_count
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print(f"所有僵尸网络生成完成！")
        print(f"  总成功: {total_success} 天")
        print(f"  总跳过: {total_skip} 天（无通信记录）")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[错误] {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def main():
    """主函数"""
    days = 30  # 默认30天
    botnet_type = None  # 默认处理所有类型
    
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print("用法: python generate_timeset_from_communications.py [days] [botnet_type]")
            print("示例: python generate_timeset_from_communications.py 30")
            print("      python generate_timeset_from_communications.py 30 ramnit")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        botnet_type = sys.argv[2]
    
    success = generate_timeset_from_communications(days, botnet_type)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
