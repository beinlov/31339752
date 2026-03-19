# -*- coding: utf-8 -*-
import pymysql
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DB_CONFIG, BOTNET_TYPES

def check_node_fields():
    """Check if botnet_nodes_* tables have unit and industry fields"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        print("=" * 70)
        print("Checking Nodes Tables for unit/industry Fields")
        print("=" * 70)
        
        for botnet_type in BOTNET_TYPES:
            table_name = f"botnet_nodes_{botnet_type}"
            
            print(f"\n{botnet_type.upper()}:")
            print(f"  Table: {table_name}")
            
            # Check if table exists
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (DB_CONFIG['database'], table_name))
            
            if cursor.fetchone()['count'] == 0:
                print(f"  Status: Table does not exist")
                continue
            
            # Check for unit and industry fields
            cursor.execute("""
                SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = %s
                AND COLUMN_NAME IN ('unit', 'industry')
                ORDER BY COLUMN_NAME
            """, (DB_CONFIG['database'], table_name))
            
            fields = cursor.fetchall()
            
            if not fields:
                print(f"  Status: Table exists but NO unit/industry fields")
                print(f"  Action: Fields will be added on next service startup")
            else:
                print(f"  Status: Table exists with fields:")
                for field in fields:
                    comment = field['COLUMN_COMMENT'] or 'No comment'
                    print(f"    - {field['COLUMN_NAME']} ({field['COLUMN_TYPE']}) - {comment}")
                
                # Check data statistics
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN unit IS NOT NULL AND unit != '' THEN 1 ELSE 0 END) as has_unit,
                        SUM(CASE WHEN industry IS NOT NULL AND industry != '' THEN 1 ELSE 0 END) as has_industry
                    FROM {table_name}
                """)
                stats = cursor.fetchone()
                
                if stats['total'] > 0:
                    print(f"  Data Statistics:")
                    print(f"    Total records: {stats['total']}")
                    print(f"    Records with unit: {stats['has_unit']} ({stats['has_unit']*100.0/stats['total']:.1f}%)")
                    print(f"    Records with industry: {stats['has_industry']} ({stats['has_industry']*100.0/stats['total']:.1f}%)")
        
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
    check_node_fields()
