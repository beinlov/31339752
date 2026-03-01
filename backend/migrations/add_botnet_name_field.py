"""
Migration script to add/update Botnet_Name field in server_management table
"""
import pymysql
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

def migrate():
    """Add or update Botnet_Name field in server_management table"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if server_management table exists
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], 'server_management'))
        
        if cursor.fetchone()[0] == 0:
            print("server_management table does not exist. Creating it...")
            cursor.execute("""
                CREATE TABLE server_management (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    location VARCHAR(255) NOT NULL,
                    ip VARCHAR(50) NOT NULL,
                    domain VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    os VARCHAR(100) NOT NULL,
                    Botnet_Name VARCHAR(255) DEFAULT NULL COMMENT '所控制的僵尸网络名称',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("server_management table created successfully with Botnet_Name field")
        else:
            # Check if Botnet_Name column exists
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.columns
                WHERE table_schema = %s 
                AND table_name = 'server_management'
                AND column_name = 'Botnet_Name'
            """, (DB_CONFIG['database'],))
            
            if cursor.fetchone()[0] == 0:
                print("Botnet_Name column does not exist. Adding it...")
                cursor.execute("""
                    ALTER TABLE server_management 
                    ADD COLUMN Botnet_Name VARCHAR(255) DEFAULT NULL COMMENT '所控制的僵尸网络名称'
                """)
                conn.commit()
                print("Botnet_Name column added successfully")
            else:
                print("Botnet_Name column already exists")
                # Update column comment if needed
                cursor.execute("""
                    ALTER TABLE server_management 
                    MODIFY COLUMN Botnet_Name VARCHAR(255) DEFAULT NULL COMMENT '所控制的僵尸网络名称'
                """)
                conn.commit()
                print("Botnet_Name column comment updated")
        
        # Show current table structure
        cursor.execute("DESCRIBE server_management")
        print("\nCurrent server_management table structure:")
        for row in cursor.fetchall():
            print(f"  {row}")
        
        print("\nMigration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    migrate()
