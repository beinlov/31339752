# -*- coding: utf-8 -*-
import pymysql
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DB_CONFIG
from utils.ip_unit_industry_mapper import get_ip_unit_industry_mapper

def backfill_all_tables():
    """Backfill unit and industry data for all communications tables"""
    try:
        print("=" * 70)
        print("Backfilling Historical Data")
        print("=" * 70)
        
        # Initialize mapper
        print("\nLoading IP-Unit-Industry mapper...")
        mapper = get_ip_unit_industry_mapper(DB_CONFIG)
        
        print(f"  Mapper table_exists: {mapper._table_exists}")
        print(f"  Mapper has_unit_field: {mapper._has_unit_field}")
        print(f"  Mapper has_industry_field: {mapper._has_industry_field}")
        
        if mapper._table_exists is None:
            print("  Checking table...")
            mapper._check_table_and_fields()
        
        if not mapper._table_exists:
            print("ERROR: ip_info table does not exist!")
            return
        
        print(f"  Loading cache...")
        mapper._load_cache()
        print(f"OK Mapper loaded with {len(mapper._cache)} records")
        
        # Connect to database
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Find all communications tables
        cursor.execute("""
            SELECT TABLE_NAME
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND TABLE_NAME LIKE 'botnet_communications_%%'
            ORDER BY TABLE_NAME
        """, (DB_CONFIG['database'],))
        
        tables = [row['TABLE_NAME'] for row in cursor.fetchall()]
        
        print(f"\nFound {len(tables)} tables to process")
        print("=" * 70)
        
        total_updated = 0
        
        for table_name in tables:
            print(f"\nProcessing: {table_name}")
            print("-" * 70)
            
            # Check if table has unit and industry fields
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = %s
                AND COLUMN_NAME IN ('unit', 'industry')
            """, (table_name,))
            
            fields = {row['COLUMN_NAME'] for row in cursor.fetchall()}
            
            if 'unit' not in fields or 'industry' not in fields:
                print(f"  Skipping: Missing unit/industry fields")
                continue
            
            # Count total records
            cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
            total = cursor.fetchone()['total']
            print(f"  Total records: {total}")
            
            # Count records needing backfill
            cursor.execute(f"""
                SELECT COUNT(*) as count
                FROM {table_name}
                WHERE (unit IS NULL OR unit = '') 
                AND (industry IS NULL OR industry = '')
            """)
            need_backfill = cursor.fetchone()['count']
            print(f"  Records needing backfill: {need_backfill}")
            
            if need_backfill == 0:
                print(f"  OK All records already have data")
                continue
            
            # Get distinct IPs needing backfill
            print(f"  Querying IPs needing backfill...")
            cursor.execute(f"""
                SELECT DISTINCT ip
                FROM {table_name}
                WHERE (unit IS NULL OR unit = '') 
                AND (industry IS NULL OR industry = '')
            """)
            
            ips_to_update = [row['ip'] for row in cursor.fetchall()]
            print(f"  Found {len(ips_to_update)} distinct IPs")
            
            # Batch query mapper
            print(f"  Looking up IP data...")
            ip_mapping = mapper.batch_get_unit_industry(ips_to_update)
            
            # Filter IPs with data
            updates = []
            for ip, (unit, industry) in ip_mapping.items():
                if unit or industry:
                    updates.append((unit, industry, ip))
            
            if not updates:
                print(f"  No matching data found in ip_info table")
                continue
            
            print(f"  Found {len(updates)} IPs with unit/industry data")
            
            # Batch update
            print(f"  Updating records...")
            batch_size = 500
            updated = 0
            
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i+batch_size]
                
                # Build CASE WHEN statement
                update_sql = f"""
                    UPDATE {table_name}
                    SET 
                        unit = CASE ip
                            {' '.join([f"WHEN %s THEN %s" for _ in batch])}
                            ELSE unit
                        END,
                        industry = CASE ip
                            {' '.join([f"WHEN %s THEN %s" for _ in batch])}
                            ELSE industry
                        END
                    WHERE ip IN ({','.join(['%s'] * len(batch))})
                    AND (unit IS NULL OR unit = '')
                    AND (industry IS NULL OR industry = '')
                """
                
                # Build parameters
                params = []
                # unit CASE
                for unit, industry, ip in batch:
                    params.extend([ip, unit])
                # industry CASE
                for unit, industry, ip in batch:
                    params.extend([ip, industry])
                # WHERE IN
                for unit, industry, ip in batch:
                    params.append(ip)
                
                cursor.execute(update_sql, params)
                batch_updated = cursor.rowcount
                updated += batch_updated
                
                if (i // batch_size + 1) % 10 == 0:
                    print(f"    Progress: {i + len(batch)}/{len(updates)} IPs processed")
            
            # Commit for this table
            conn.commit()
            
            print(f"  OK Updated {updated} records")
            total_updated += updated
            
            # Show statistics
            cursor.execute(f"""
                SELECT COUNT(*) as count
                FROM {table_name}
                WHERE unit IS NOT NULL AND unit != ''
            """)
            has_unit = cursor.fetchone()['count']
            
            cursor.execute(f"""
                SELECT COUNT(*) as count
                FROM {table_name}
                WHERE industry IS NOT NULL AND industry != ''
            """)
            has_industry = cursor.fetchone()['count']
            
            print(f"  Statistics after backfill:")
            print(f"    Records with unit: {has_unit}/{total} ({has_unit*100.0/total:.1f}%)")
            print(f"    Records with industry: {has_industry}/{total} ({has_industry*100.0/total:.1f}%)")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 70)
        print("Backfill Summary:")
        print(f"  Tables processed: {len(tables)}")
        print(f"  Total records updated: {total_updated}")
        print("=" * 70)
        print("\nOK All done!")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    backfill_all_tables()
