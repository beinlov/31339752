"""
统一 utg-q-008 命名为 utg_q_008
修改数据库中的相关记录
"""
import pymysql
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from config import DB_CONFIG

def migrate_naming():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("=" * 70)
        print("开始统一命名：utg-q-008 -> utg_q_008")
        print("=" * 70)
        
        # 1. 修改 botnet_types 表
        print("\n1. 检查 botnet_types 表")
        cursor.execute("SELECT name FROM botnet_types WHERE name = 'utg-q-008'")
        if cursor.fetchone():
            print("   找到 'utg-q-008'，准备更新...")
            cursor.execute("UPDATE botnet_types SET name = 'utg_q_008' WHERE name = 'utg-q-008'")
            print("   ✅ 已更新 botnet_types 表")
        else:
            cursor.execute("SELECT name FROM botnet_types WHERE name = 'utg_q_008'")
            if cursor.fetchone():
                print("   ✅ 已经是 'utg_q_008'，无需更新")
            else:
                print("   ⚠️  未找到相关记录")
        
        # 2. 修改 server_management 表
        print("\n2. 检查 server_management 表")
        cursor.execute("SELECT COUNT(*) FROM server_management WHERE Botnet_Name = 'utg-q-008'")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"   找到 {count} 条 'utg-q-008' 记录，准备更新...")
            cursor.execute("UPDATE server_management SET Botnet_Name = 'utg_q_008' WHERE Botnet_Name = 'utg-q-008'")
            print(f"   ✅ 已更新 {count} 条记录")
        else:
            cursor.execute("SELECT COUNT(*) FROM server_management WHERE Botnet_Name = 'utg_q_008'")
            count2 = cursor.fetchone()[0]
            if count2 > 0:
                print(f"   ✅ 已经是 'utg_q_008'（{count2} 条记录），无需更新")
            else:
                print("   ⚠️  未找到相关记录")
        
        # 提交更改
        conn.commit()
        
        print("\n" + "=" * 70)
        print("验证修改结果")
        print("=" * 70)
        
        # 验证 botnet_types
        print("\n1. botnet_types 表:")
        cursor.execute("SELECT name, display_name FROM botnet_types WHERE name LIKE '%utg%'")
        for name, display_name in cursor.fetchall():
            print(f"   - {name}: {display_name}")
        
        # 验证 server_management
        print("\n2. server_management 表:")
        cursor.execute("SELECT id, ip, location, Botnet_Name FROM server_management WHERE Botnet_Name LIKE '%utg%'")
        for row in cursor.fetchall():
            print(f"   - ID: {row[0]}, IP: {row[1]}, Location: {row[2]}, Botnet: {row[3]}")
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("✅ 数据库迁移完成！")
        print("=" * 70)
        print("\n下一步:")
        print("1. 修改 backend/config.py 中的 C2_CLEANUP_CONFIG")
        print("2. 删除代码中的名称转换函数")
        print("3. 重启后端服务")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    migrate_naming()
