import pymysql
from config import DB_CONFIG

TABLE = "botnet_nodes_utg_q_008"

def fix_hongkong_data():
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        print("="*80)
        print("Fixing Hong Kong Data")
        print("="*80)
        
        # Check current data
        print("\nChecking current data...")
        cur.execute(f"""
            SELECT COUNT(*) 
            FROM {TABLE} 
            WHERE country LIKE '%香港%' OR country = 'Hong Kong'
        """)
        count = cur.fetchone()[0]
        print(f"Found {count} rows with Hong Kong in country field")
        
        if count > 0:
            # Show some examples
            cur.execute(f"""
                SELECT ip, country, province, city 
                FROM {TABLE} 
                WHERE country LIKE '%香港%' OR country = 'Hong Kong'
                LIMIT 5
            """)
            print("\nExamples (before update):")
            print(f"{'IP':<20} {'Country':<20} {'Province':<15} {'City':<15}")
            print("-"*70)
            for row in cur.fetchall():
                print(f"{row[0]:<20} {row[1] or '':<20} {row[2] or '':<15} {row[3] or '':<15}")
        
        # Update the data
        print(f"\nUpdating Hong Kong data...")
        sql = f"""
            UPDATE {TABLE}
            SET 
                country = '中国',
                province = '香港'
            WHERE country LIKE '%香港%' OR country = 'Hong Kong'
        """
        
        cur.execute(sql)
        updated = cur.rowcount
        conn.commit()
        
        print(f"Updated {updated} rows")
        
        # Verify
        if updated > 0:
            print("\nVerifying updates...")
            cur.execute(f"""
                SELECT ip, country, province, city 
                FROM {TABLE} 
                WHERE province = '香港'
                LIMIT 5
            """)
            print("\nExamples (after update):")
            print(f"{'IP':<20} {'Country':<20} {'Province':<15} {'City':<15}")
            print("-"*70)
            for row in cur.fetchall():
                print(f"{row[0]:<20} {row[1] or '':<20} {row[2] or '':<15} {row[3] or '':<15}")
        
        # Check for other special regions
        print("\n" + "="*80)
        print("Checking for other special regions...")
        print("="*80)
        
        regions = ['澳门', 'Macau', '台湾', 'Taiwan']
        for region in regions:
            cur.execute(f"""
                SELECT COUNT(*) 
                FROM {TABLE} 
                WHERE country LIKE '%{region}%'
            """)
            count = cur.fetchone()[0]
            if count > 0:
                print(f"Found {count} rows with '{region}' in country field")
        
        print("\n" + "="*80)
        print("Hong Kong data fixed successfully!")
        print("="*80)
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    fix_hongkong_data()
