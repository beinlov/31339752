"""
测试timeset数据修复 - 验证active和cleaned字段是否正确填充
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from pymysql.cursors import DictCursor
from config import DB_CONFIG, ALLOWED_BOTNET_TYPES
from datetime import date

def test_timeset_data():
    """检查今天的timeset数据"""
    today = date.today()
    
    conn = pymysql.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor(DictCursor)
        
        print(f"\n{'='*80}")
        print(f"检查日期: {today}")
        print(f"{'='*80}\n")
        
        for botnet_type in ALLOWED_BOTNET_TYPES:
            timeset_table = f"botnet_timeset_{botnet_type}"
            
            # 检查表是否存在
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = %s
            """, (timeset_table,))
            
            if cursor.fetchone()["count"] == 0:
                print(f"[{botnet_type}] ⚠️  表不存在: {timeset_table}")
                continue
            
            # 查询今天的数据（只查询active和cleaned字段）
            cursor.execute(f"""
                SELECT 
                    date,
                    global_active,
                    china_active,
                    global_cleaned,
                    china_cleaned
                FROM {timeset_table}
                WHERE date = %s
            """, (today,))
            
            row = cursor.fetchone()
            
            if not row:
                print(f"[{botnet_type}] ❌ 今天没有数据")
                continue
            
            print(f"[{botnet_type}] 数据检查:")
            print(f"  全球活跃: {row['global_active']} {'✅' if row['global_active'] > 0 else '❌ 为0'}")
            print(f"  中国活跃: {row['china_active']} {'✅' if row['china_active'] > 0 else '❌ 为0'}")
            print(f"  全球清除: {row['global_cleaned']} {'✅' if row['global_cleaned'] > 0 else '⚠️  为0'}")
            print(f"  中国清除: {row['china_cleaned']} {'✅' if row['china_cleaned'] > 0 else '⚠️  为0'}")
            print()
        
        cursor.close()
    finally:
        conn.close()

if __name__ == "__main__":
    test_timeset_data()
