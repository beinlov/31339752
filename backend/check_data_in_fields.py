# -*- coding: utf-8 -*-
import pymysql
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DB_CONFIG

def check_data_in_fields():
    """Check which tables have actual data in unit/industry fields"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        print("=" * 70)
        print("Check botnet_nodes_* tables for unit/industry data")
        print("=" * 70)
        
        # Find all botnet_nodes_* tables
        cursor.execute("""
            SELECT TABLE_NAME
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND TABLE_NAME LIKE 'botnet_nodes_%%'
            ORDER BY TABLE_NAME
        """, (DB_CONFIG['database'],))
        
        tables = [row['TABLE_NAME'] for row in cursor.fetchall()]
        
        print(f"\nFound {len(tables)} botnet_nodes_* tables\n")
        
        tables_with_data = []
        tables_with_fields_but_no_data = []
        tables_without_fields = []
        
        for table_name in tables:
            # Check if table has unit and industry fields
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = %s
                AND COLUMN_NAME IN ('unit', 'industry')
                ORDER BY COLUMN_NAME
            """, (DB_CONFIG['database'], table_name))
            
            fields = [row['COLUMN_NAME'] for row in cursor.fetchall()]
            
            if len(fields) < 2:
                tables_without_fields.append(table_name)
                print(f"X {table_name}")
                print(f"  Status: Missing fields (only {len(fields)} fields)")
                print()
                continue
            
            # Both fields exist, check for data
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(CASE WHEN unit IS NOT NULL AND unit != '' THEN 1 ELSE 0 END) as has_unit,
                    SUM(CASE WHEN industry IS NOT NULL AND industry != '' THEN 1 ELSE 0 END) as has_industry,
                    SUM(CASE WHEN (unit IS NOT NULL AND unit != '') OR (industry IS NOT NULL AND industry != '') THEN 1 ELSE 0 END) as has_either
                FROM {table_name}
            """)
            
            stats = cursor.fetchone()
            
            if stats['has_either'] > 0:
                # Has data
                tables_with_data.append({
                    'table': table_name,
                    'total': stats['total_records'],
                    'has_unit': stats['has_unit'],
                    'has_industry': stats['has_industry'],
                    'has_either': stats['has_either']
                })
                print(f"+ {table_name}")
                print(f"  Status: HAS DATA")
                print(f"  Total records: {stats['total_records']:,}")
                print(f"  Records with unit: {stats['has_unit']:,} ({stats['has_unit']*100.0/stats['total_records']:.2f}%)")
                print(f"  Records with industry: {stats['has_industry']:,} ({stats['has_industry']*100.0/stats['total_records']:.2f}%)")
                print(f"  Records with either: {stats['has_either']:,} ({stats['has_either']*100.0/stats['total_records']:.2f}%)")
                
                # Show sample data
                cursor.execute(f"""
                    SELECT ip, unit, industry
                    FROM {table_name}
                    WHERE (unit IS NOT NULL AND unit != '') OR (industry IS NOT NULL AND industry != '')
                    LIMIT 3
                """)
                samples = cursor.fetchall()
                if samples:
                    print(f"  Sample data:")
                    for sample in samples:
                        print(f"    IP: {sample['ip']}, Unit: {sample['unit'] or '-'}, Industry: {sample['industry'] or '-'}")
                print()
            else:
                # Has fields but no data
                tables_with_fields_but_no_data.append({
                    'table': table_name,
                    'total': stats['total_records']
                })
                print(f"- {table_name}")
                print(f"  Status: Has fields but NO data")
                print(f"  Total records: {stats['total_records']:,}")
                print(f"  Records with unit: 0 (0.00%)")
                print(f"  Records with industry: 0 (0.00%)")
                print()
        
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total tables: {len(tables)}")
        print(f"Tables WITH data: {len(tables_with_data)}")
        print(f"Tables with fields but NO data: {len(tables_with_fields_but_no_data)}")
        print(f"Tables without fields: {len(tables_without_fields)}")
        
        if tables_with_data:
            print(f"\nTables WITH data ({len(tables_with_data)}):")
            for item in tables_with_data:
                print(f"  + {item['table']}")
                print(f"    Total: {item['total']:,}, With data: {item['has_either']:,} ({item['has_either']*100.0/item['total']:.2f}%)")
        
        if tables_with_fields_but_no_data:
            print(f"\nTables with fields but NO data ({len(tables_with_fields_but_no_data)}):")
            for item in tables_with_fields_but_no_data:
                print(f"  - {item['table']} - {item['total']:,} records, all empty")
        
        if tables_without_fields:
            print(f"\nTables without fields ({len(tables_without_fields)}):")
            for table in tables_without_fields:
                print(f"  X {table}")
        
        print("=" * 70)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_data_in_fields()
