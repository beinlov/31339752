# -*- coding: utf-8 -*-
import pymysql
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DB_CONFIG

def check_ip_mismatch():
    """Check why IPs don't match between ip_info and communications tables"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        print("=" * 70)
        print("Checking IP Mismatch")
        print("=" * 70)
        
        # Sample IPs from ip_info
        print("\n1. Sample IPs from ip_info table:")
        cursor.execute("SELECT IP FROM ip_info LIMIT 10")
        ip_info_samples = cursor.fetchall()
        for row in ip_info_samples:
            print(f"  {row['IP']}")
        
        # Sample IPs from communications
        print("\n2. Sample IPs from botnet_communications_asruex:")
        cursor.execute("SELECT DISTINCT ip FROM botnet_communications_asruex LIMIT 10")
        comm_samples = cursor.fetchall()
        for row in comm_samples:
            print(f"  {row['ip']}")
        
        # Check if any match
        print("\n3. Checking for matches...")
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM botnet_communications_asruex c
            INNER JOIN ip_info i ON c.ip = i.IP
            LIMIT 1
        """)
        match_count = cursor.fetchone()['count']
        print(f"  Direct JOIN matches: {match_count}")
        
        # Check specific IP
        if comm_samples:
            test_ip = comm_samples[0]['ip']
            print(f"\n4. Testing specific IP: {test_ip}")
            print(f"  IP type: {type(test_ip)}")
            print(f"  IP length: {len(test_ip)}")
            print(f"  IP repr: {repr(test_ip)}")
            
            cursor.execute("SELECT * FROM ip_info WHERE IP = %s", (test_ip,))
            result = cursor.fetchone()
            if result:
                print(f"  Found in ip_info: YES")
                print(f"    unit: {result.get('unit')}")
                print(f"    industry: {result.get('industry')}")
            else:
                print(f"  Found in ip_info: NO")
                
                # Try case-insensitive
                cursor.execute("SELECT * FROM ip_info WHERE LOWER(IP) = LOWER(%s)", (test_ip,))
                result = cursor.fetchone()
                if result:
                    print(f"  Found with case-insensitive: YES")
                else:
                    print(f"  Found with case-insensitive: NO")
        
        # Count total distinct IPs
        print("\n5. IP Statistics:")
        cursor.execute("SELECT COUNT(DISTINCT IP) as count FROM ip_info")
        ip_info_count = cursor.fetchone()['count']
        print(f"  Distinct IPs in ip_info: {ip_info_count}")
        
        cursor.execute("SELECT COUNT(DISTINCT ip) as count FROM botnet_communications_asruex")
        comm_count = cursor.fetchone()['count']
        print(f"  Distinct IPs in communications: {comm_count}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_ip_mismatch()
