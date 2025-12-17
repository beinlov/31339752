"""
数据库迁移脚本：为Server_Management表添加Botnet_Name字段
"""
import pymysql
import sys
import os

# 添加父目录到路径以导入config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

def add_botnet_name_column():
    """为Server_Management表添加Botnet_Name列"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查列是否已存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_schema = %s 
            AND table_name = 'Server_Management' 
            AND column_name = 'Botnet_Name'
        """, (DB_CONFIG['database'],))
        
        if cursor.fetchone()[0] == 0:
            # 添加Botnet_Name列
            cursor.execute("""
                ALTER TABLE Server_Management 
                ADD COLUMN Botnet_Name VARCHAR(255) AFTER os
            """)
            conn.commit()
            print("[SUCCESS] Successfully added Botnet_Name column to Server_Management table")
        else:
            print("[INFO] Botnet_Name column already exists, skipping migration")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Starting database migration: Adding Botnet_Name field...")
    add_botnet_name_column()
    print("Migration completed!")
