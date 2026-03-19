# -*- coding: utf-8 -*-
import pymysql
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DB_CONFIG
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_fields_to_all_communications_tables():
    """Add unit and industry fields to all botnet_communications_* tables"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        print("=" * 70)
        print("Adding unit/industry Fields to All Communications Tables")
        print("=" * 70)
        
        # 1. Find all botnet_communications_* tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_name LIKE 'botnet_communications_%%'
            ORDER BY table_name
        """, (DB_CONFIG['database'],))
        
        tables = [row['table_name'] for row in cursor.fetchall()]
        
        if not tables:
            print("\nNo botnet_communications_* tables found!")
            return
        
        print(f"\nFound {len(tables)} communications tables:")
        for table in tables:
            print(f"  - {table}")
        
        print("\n" + "=" * 70)
        
        # 2. Add fields to each table
        total_added = 0
        total_existed = 0
        
        for table_name in tables:
            print(f"\nProcessing: {table_name}")
            print("-" * 70)
            
            # Check if fields exist
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = %s
                AND COLUMN_NAME IN ('unit', 'industry')
            """, (table_name,))
            
            existing_fields = {row['COLUMN_NAME'] for row in cursor.fetchall()}
            
            fields_added = 0
            
            # Add unit field
            if 'unit' not in existing_fields:
                print(f"  Adding unit field...")
                try:
                    cursor.execute(f"""
                        ALTER TABLE {table_name}
                        ADD COLUMN unit VARCHAR(255) DEFAULT NULL COMMENT 'Organization'
                        AFTER city
                    """)
                    print(f"  OK unit field added")
                    fields_added += 1
                    
                    # Add index
                    try:
                        cursor.execute(f"""
                            ALTER TABLE {table_name}
                            ADD INDEX idx_unit (unit)
                        """)
                        print(f"  OK unit index added")
                    except Exception as e:
                        if 'Duplicate key name' not in str(e):
                            print(f"  ! Warning: Failed to add unit index: {e}")
                    
                except Exception as e:
                    print(f"  X Failed to add unit field: {e}")
            else:
                print(f"  - unit field already exists")
                total_existed += 1
            
            # Add industry field
            if 'industry' not in existing_fields:
                print(f"  Adding industry field...")
                try:
                    cursor.execute(f"""
                        ALTER TABLE {table_name}
                        ADD COLUMN industry VARCHAR(255) DEFAULT NULL COMMENT 'Industry'
                        AFTER unit
                    """)
                    print(f"  OK industry field added")
                    fields_added += 1
                    
                    # Add index
                    try:
                        cursor.execute(f"""
                            ALTER TABLE {table_name}
                            ADD INDEX idx_industry (industry)
                        """)
                        print(f"  OK industry index added")
                    except Exception as e:
                        if 'Duplicate key name' not in str(e):
                            print(f"  ! Warning: Failed to add industry index: {e}")
                    
                except Exception as e:
                    print(f"  X Failed to add industry field: {e}")
            else:
                print(f"  - industry field already exists")
                total_existed += 1
            
            if fields_added > 0:
                total_added += fields_added
                print(f"  Summary: {fields_added} field(s) added")
            else:
                print(f"  Summary: All fields already exist")
        
        # 3. Commit changes
        conn.commit()
        
        print("\n" + "=" * 70)
        print("Summary:")
        print(f"  Tables processed: {len(tables)}")
        print(f"  Fields added: {total_added}")
        print(f"  Fields already existed: {total_existed}")
        print("=" * 70)
        
        # 4. Backfill historical data (optional)
        print("\nDo you want to backfill historical data? (y/n): ", end='')
        try:
            response = input().strip().lower()
        except:
            response = 'n'
        
        if response == 'y':
            print("\nBackfilling historical data...")
            backfill_historical_data(cursor, tables)
            conn.commit()
        else:
            print("\nSkipping historical data backfill.")
            print("You can run the backfill later by restarting the service.")
        
        cursor.close()
        conn.close()
        
        print("\nOK All done!")
        
    except Exception as e:
        print(f"\nX Error: {e}")
        import traceback
        traceback.print_exc()

def backfill_historical_data(cursor, tables):
    """Backfill historical data"""
    try:
        # Import mapper
        from utils.ip_unit_industry_mapper import get_ip_unit_industry_mapper
        
        mapper = get_ip_unit_industry_mapper(DB_CONFIG)
        
        if not mapper._table_exists:
            print("  ! ip_info table does not exist, skipping backfill")
            return
        
        total_updated = 0
        
        for table_name in tables:
            print(f"\n  Processing {table_name}...")
            
            # Query records needing backfill
            cursor.execute(f"""
                SELECT DISTINCT ip
                FROM {table_name}
                WHERE (unit IS NULL OR unit = '') 
                AND (industry IS NULL OR industry = '')
                LIMIT 10000
            """)
            
            ips_to_update = [row['ip'] for row in cursor.fetchall()]
            
            if not ips_to_update:
                print(f"    No records need backfill")
                continue
            
            print(f"    Found {len(ips_to_update)} IPs needing backfill")
            
            # Batch query
            ip_mapping = mapper.batch_get_unit_industry(ips_to_update)
            
            # Filter records with data
            updates = []
            for ip, (unit, industry) in ip_mapping.items():
                if unit or industry:
                    updates.append((unit, industry, ip))
            
            if not updates:
                print(f"    No matching data found in ip_info")
                continue
            
            print(f"    Found {len(updates)} IPs with data")
            
            # Batch update
            batch_size = 500
            updated = 0
            
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i+batch_size]
                
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
                
                params = []
                for unit, industry, ip in batch:
                    params.extend([ip, unit])
                for unit, industry, ip in batch:
                    params.extend([ip, industry])
                for unit, industry, ip in batch:
                    params.append(ip)
                
                cursor.execute(update_sql, params)
                updated += cursor.rowcount
            
            print(f"    OK Updated {updated} records")
            total_updated += updated
        
        print(f"\n  Total records updated: {total_updated}")
        
    except ImportError:
        print("  ! Cannot import ip_unit_industry_mapper, skipping backfill")
    except Exception as e:
        print(f"  ! Backfill error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    add_fields_to_all_communications_tables()
