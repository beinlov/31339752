"""
Script to check current server data and botnet node tables
"""
import pymysql
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

def check_data():
    """Check current server data and available botnet node tables"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Check current server data
        print("=== Current Server Data ===")
        cursor.execute("SELECT id, location, ip, domain, status, os, Botnet_Name FROM Server_Management")
        servers = cursor.fetchall()
        
        if not servers:
            print("No servers found in database")
        else:
            for server in servers:
                print(f"\nServer ID {server['id']}:")
                print(f"  Location: {server['location']}")
                print(f"  IP: {server['ip']}")
                print(f"  Domain: {server['domain']}")
                print(f"  Status: {server['status']}")
                print(f"  OS: {server['os']}")
                print(f"  Botnet_Name: {server['Botnet_Name']}")
        
        # Check available botnet node tables
        print("\n\n=== Available Botnet Node Tables ===")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_name LIKE %s
            ORDER BY table_name
        """, (DB_CONFIG['database'], 'botnet_nodes_%'))
        
        tables = cursor.fetchall()
        if not tables:
            print("No botnet_nodes_* tables found")
        else:
            for table in tables:
                table_name = table['TABLE_NAME']
                print(f"\n{table_name}:")
                cursor.execute(f"SELECT COUNT(*) as count FROM `{table_name}`")
                count = cursor.fetchone()['count']
                print(f"  Node count: {count}")
        
        # Check botnet types
        print("\n\n=== Registered Botnet Types ===")
        cursor.execute("SELECT name, display_name, table_name FROM botnet_types")
        botnets = cursor.fetchall()
        
        if not botnets:
            print("No botnet types registered")
        else:
            for botnet in botnets:
                print(f"\n{botnet['name']}:")
                print(f"  Display Name: {botnet['display_name']}")
                print(f"  Table Name: {botnet['table_name']}")
        
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
    check_data()
