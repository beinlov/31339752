"""
Script to update server botnet_name for testing
"""
import pymysql
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

def update_servers():
    """Update servers with botnet names for testing"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Get all servers
        cursor.execute("SELECT id, ip FROM Server_Management")
        servers = cursor.fetchall()
        
        print("=== Updating Server Botnet Names ===\n")
        
        # Update server 8 with 'mozi' botnet
        cursor.execute("""
            UPDATE Server_Management 
            SET Botnet_Name = %s 
            WHERE id = %s
        """, ('mozi', 8))
        print(f"Updated Server ID 8 with botnet_name: mozi")
        
        # Update server 9 with 'andromeda' botnet
        cursor.execute("""
            UPDATE Server_Management 
            SET Botnet_Name = %s 
            WHERE id = %s
        """, ('andromeda', 9))
        print(f"Updated Server ID 9 with botnet_name: andromeda")
        
        conn.commit()
        
        # Verify updates
        print("\n=== Verification ===\n")
        cursor.execute("""
            SELECT id, ip, Botnet_Name 
            FROM Server_Management 
            ORDER BY id
        """)
        servers = cursor.fetchall()
        
        for server in servers:
            print(f"Server ID {server['id']}:")
            print(f"  IP: {server['ip']}")
            print(f"  Botnet_Name: {server['Botnet_Name']}")
            
            # Get node count if botnet_name is set
            if server['Botnet_Name']:
                table_name = f"botnet_nodes_{server['Botnet_Name']}"
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM `{table_name}`")
                    count = cursor.fetchone()['count']
                    print(f"  Node Count: {count}")
                except Exception as e:
                    print(f"  Node Count: Error - {e}")
            else:
                print(f"  Node Count: N/A (no botnet_name)")
            print()
        
        print("Update completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    update_servers()
