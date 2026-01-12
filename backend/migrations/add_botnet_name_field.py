"""
Migration script to add/update Botnet_Name field in Server_Management table
"""
import pymysql
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

def migrate():
    """Add or update Botnet_Name field in Server_Management table"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if Server_Management table exists
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], 'Server_Management'))
        
        if cursor.fetchone()[0] == 0:
            print("Server_Management table does not exist. Creating it...")
            cursor.execute("""
                CREATE TABLE Server_Management (
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
            print("Server_Management table created successfully with Botnet_Name field")
        else:
            # Check if Botnet_Name column exists
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.columns
                WHERE table_schema = %s 
                AND table_name = 'Server_Management'
                AND column_name = 'Botnet_Name'
            """, (DB_CONFIG['database'],))
            
            if cursor.fetchone()[0] == 0:
                print("Botnet_Name column does not exist. Adding it...")
                cursor.execute("""
                    ALTER TABLE Server_Management 
                    ADD COLUMN Botnet_Name VARCHAR(255) DEFAULT NULL COMMENT '所控制的僵尸网络名称'
                """)
                conn.commit()
                print("Botnet_Name column added successfully")
            else:
                print("Botnet_Name column already exists")
                # Update column comment if needed
                cursor.execute("""
                    ALTER TABLE Server_Management 
                    MODIFY COLUMN Botnet_Name VARCHAR(255) DEFAULT NULL COMMENT '所控制的僵尸网络名称'
                """)
                conn.commit()
                print("Botnet_Name column comment updated")
        
        # Show current table structure
        cursor.execute("DESCRIBE Server_Management")
        print("\nCurrent Server_Management table structure:")
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
