# -*- coding: utf-8 -*-
import pymysql
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DB_CONFIG, BOTNET_CONFIG

def test_backfill():
    """Test backfill functionality"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        print("=" * 70)
        print("Testing Backfill Functionality")
        print("=" * 70)
        
        # Get enabled botnet types
        botnet_types = [bt for bt, config in BOTNET_CONFIG.items() if config.get('enabled', True)]
        
        for botnet_type in botnet_types:
            table_name = f"botnet_communications_{botnet_type}"
            
            print(f"\n{'='*70}")
            print(f"Botnet Type: {botnet_type}")
            print(f"Table: {table_name}")
            print(f"{'='*70}")
            
            # Check if table exists
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (DB_CONFIG['database'], table_name))
            
            if cursor.fetchone()['count'] == 0:
                print(f"  Table does not exist, skipping...")
                continue
            
            # Check if unit/industry fields exist
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = %s
                AND COLUMN_NAME IN ('unit', 'industry')
            """, (table_name,))
            
            existing_fields = {row['COLUMN_NAME'] for row in cursor.fetchall()}
            
            if 'unit' not in existing_fields or 'industry' not in existing_fields:
                print(f"  unit/industry fields do not exist, skipping...")
                continue
            
            # Statistics
            print("\n1. Current Statistics:")
            
            cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
            total = cursor.fetchone()['total']
            print(f"   Total records: {total}")
            
            cursor.execute(f"""
                SELECT COUNT(*) as count 
                FROM {table_name} 
                WHERE unit IS NOT NULL AND unit != ''
            """)
            has_unit = cursor.fetchone()['count']
            print(f"   Records with unit: {has_unit} ({has_unit*100.0/total:.1f}%)")
            
            cursor.execute(f"""
                SELECT COUNT(*) as count 
                FROM {table_name} 
                WHERE industry IS NOT NULL AND industry != ''
            """)
            has_industry = cursor.fetchone()['count']
            print(f"   Records with industry: {has_industry} ({has_industry*100.0/total:.1f}%)")
            
            cursor.execute(f"""
                SELECT COUNT(*) as count 
                FROM {table_name} 
                WHERE (unit IS NULL OR unit = '') 
                AND (industry IS NULL OR industry = '')
            """)
            needs_backfill = cursor.fetchone()['count']
            print(f"   Records needing backfill: {needs_backfill} ({needs_backfill*100.0/total:.1f}%)")
            
            # Sample data before backfill
            print("\n2. Sample Data (before backfill):")
            cursor.execute(f"""
                SELECT ip, unit, industry 
                FROM {table_name}
                WHERE (unit IS NULL OR unit = '') 
                AND (industry IS NULL OR industry = '')
                LIMIT 5
            """)
            samples = cursor.fetchall()
            
            if samples:
                print(f"   {'IP':<20} {'Unit':<30} {'Industry':<20}")
                print("   " + "-" * 70)
                for row in samples:
                    print(f"   {row['ip']:<20} {row['unit'] or '(null)':<30} {row['industry'] or '(null)':<20}")
            else:
                print("   (no records need backfill)")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 70)
        print("Test completed!")
        print("=" * 70)
        print("\nNext step: Start the backend service to trigger backfill")
        print("Command: python main.py")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_backfill()
