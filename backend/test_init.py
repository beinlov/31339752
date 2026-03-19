# -*- coding: utf-8 -*-
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DB_CONFIG, BOTNET_CONFIG
from log_processor.db_writer import BotnetDBWriter
import pymysql

def test_immediate_initialization():
    """Test that fields are added immediately on service startup"""
    
    print("=" * 70)
    print("Testing Immediate Database Initialization")
    print("=" * 70)
    
    # Get enabled botnet types
    botnet_types = [bt for bt, config in BOTNET_CONFIG.items() if config.get('enabled', True)]
    
    for botnet_type in botnet_types:
        print(f"\n{'='*70}")
        print(f"Testing: {botnet_type}")
        print(f"{'='*70}")
        
        table_name = f"botnet_communications_{botnet_type}"
        
        # Check fields BEFORE creating writer
        print("\n1. Before creating BotnetDBWriter:")
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], table_name))
        
        table_exists_before = cursor.fetchone()['count'] > 0
        
        if table_exists_before:
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = %s
                AND COLUMN_NAME IN ('unit', 'industry')
            """, (table_name,))
            
            fields_before = {row['COLUMN_NAME'] for row in cursor.fetchall()}
            print(f"   Table exists: Yes")
            print(f"   unit field: {'Yes' if 'unit' in fields_before else 'No'}")
            print(f"   industry field: {'Yes' if 'industry' in fields_before else 'No'}")
        else:
            print(f"   Table exists: No")
            fields_before = set()
        
        cursor.close()
        conn.close()
        
        # Create writer (should trigger initialization)
        print(f"\n2. Creating BotnetDBWriter (should trigger initialization)...")
        print("   Watch for initialization logs above...")
        
        writer = BotnetDBWriter(
            botnet_type,
            DB_CONFIG,
            batch_size=100,
            use_connection_pool=False,
            enable_monitoring=False
        )
        
        # Check fields AFTER creating writer
        print(f"\n3. After creating BotnetDBWriter:")
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], table_name))
        
        table_exists_after = cursor.fetchone()['count'] > 0
        
        if table_exists_after:
            cursor.execute("""
                SELECT COLUMN_NAME, COLUMN_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = %s
                AND COLUMN_NAME IN ('unit', 'industry')
            """, (table_name,))
            
            fields_after = cursor.fetchall()
            print(f"   Table exists: Yes")
            
            if fields_after:
                print(f"   Fields found:")
                for field in fields_after:
                    status = "ADDED" if field['COLUMN_NAME'] not in fields_before else "existed"
                    print(f"     - {field['COLUMN_NAME']} ({field['COLUMN_TYPE']}) [{status}]")
            else:
                print(f"   unit field: No")
                print(f"   industry field: No")
        else:
            print(f"   Table exists: No (ERROR!)")
        
        cursor.close()
        conn.close()
        
        # Summary
        print(f"\n4. Summary:")
        if not table_exists_before and table_exists_after:
            print(f"   ? Table created successfully")
        elif table_exists_before:
            print(f"   ? Table already existed")
        
        if 'unit' not in fields_before and any(f['COLUMN_NAME'] == 'unit' for f in fields_after):
            print(f"   ? unit field ADDED on initialization")
        elif 'unit' in fields_before:
            print(f"   ? unit field already existed")
        else:
            print(f"   ? unit field NOT added (ERROR!)")
        
        if 'industry' not in fields_before and any(f['COLUMN_NAME'] == 'industry' for f in fields_after):
            print(f"   ? industry field ADDED on initialization")
        elif 'industry' in fields_before:
            print(f"   ? industry field already existed")
        else:
            print(f"   ? industry field NOT added (ERROR!)")
    
    print("\n" + "=" * 70)
    print("Test completed!")
    print("=" * 70)

if __name__ == '__main__':
    test_immediate_initialization()
