# -*- coding: utf-8 -*-
import pymysql
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import DB_CONFIG
    print("Step 1: Config loaded successfully")
    print(f"Database: {DB_CONFIG['database']}")
    
    print("\nStep 2: Connecting to database...")
    conn = pymysql.connect(**DB_CONFIG)
    print("Connected successfully")
    
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    print("\nStep 3: Checking ip_info table...")
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM information_schema.tables 
        WHERE table_schema = %s AND table_name = 'ip_info'
    """, (DB_CONFIG['database'],))
    
    result = cursor.fetchone()
    if result['count'] == 0:
        print("ip_info table does NOT exist")
    else:
        print("ip_info table EXISTS")
        
        print("\nStep 4: Checking table structure...")
        cursor.execute("DESCRIBE ip_info")
        columns = cursor.fetchall()
        print(f"Found {len(columns)} columns:")
        for col in columns:
            print(f"  - {col['Field']} ({col['Type']})")
        
        print("\nStep 5: Checking data count...")
        cursor.execute("SELECT COUNT(*) as total FROM ip_info")
        total = cursor.fetchone()['total']
        print(f"Total records: {total}")
    
    cursor.close()
    conn.close()
    print("\nTest completed successfully!")
    
except Exception as e:
    print(f"\nError occurred: {e}")
    import traceback
    traceback.print_exc()
