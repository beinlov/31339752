# -*- coding: utf-8 -*-
import pymysql
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DB_CONFIG, BOTNET_CONFIG

def check_communications_fields():
    """Check if unit and industry fields exist in communications tables"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        print("=" * 70)
        print("Checking Communications Tables for unit/industry Fields")
        print("=" * 70)
        
        # Get enabled botnet types
        botnet_types = [bt for bt, config in BOTNET_CONFIG.items() if config.get('enabled', True)]
        
        for botnet_type in botnet_types:
            table_name = f"botnet_communications_{botnet_type}"
            
            print(f"\n{botnet_type.upper()}:")
            print(f"  Table: {table_name}")
            
            # Check if table exists
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (DB_CONFIG['database'], table_name))
            
            if cursor.fetchone()['count'] == 0:
                print(f"  Status: Table does NOT exist")
                continue
            
            # Check fields
            cursor.execute("""
                SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = %s
                AND COLUMN_NAME IN ('unit', 'industry')
            """, (table_name,))
            
            fields = cursor.fetchall()
            
            if not fields:
                print(f"  Status: Table exists but NO unit/industry fields")
                print(f"  Action: Fields will be added on next service startup")
            else:
                print(f"  Status: Table exists with fields:")
                for field in fields:
                    print(f"    - {field['COLUMN_NAME']} ({field['COLUMN_TYPE']}) - {field['COLUMN_COMMENT']}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 70)
        print("Check completed!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_communications_fields()
