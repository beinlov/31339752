import pymysql
from config import DB_CONFIG

TABLE = "botnet_nodes_utg_q_008"

def fix_hongkong():
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        print("="*80)
        print("Fixing Hong Kong Data")
        print("="*80)
        
        # Check current
        cur.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE country LIKE '%Hong Kong%' OR country LIKE '%香港%'")
        count = cur.fetchone()[0]
        print(f"\nFound {count} Hong Kong rows")
        
        if count > 0:
            cur.execute(f"SELECT ip, country, province FROM {TABLE} WHERE country LIKE '%Hong Kong%' OR country LIKE '%香港%' LIMIT 5")
            print("\nBefore:")
            for row in cur.fetchall():
                print(f"  {row[0]:<20} {row[1]:<20} {row[2] or 'NULL':<15}")
        
        # Update
        print("\nUpdating...")
        cur.execute(f"UPDATE {TABLE} SET country='中国', province='香港' WHERE country LIKE '%Hong Kong%' OR country LIKE '%香港%'")
        updated = cur.rowcount
        conn.commit()
        print(f"Updated {updated} rows")
        
        # Verify
        if updated > 0:
            cur.execute(f"SELECT ip, country, province FROM {TABLE} WHERE province='香港' LIMIT 5")
            print("\nAfter:")
            for row in cur.fetchall():
                print(f"  {row[0]:<20} {row[1]:<20} {row[2]:<15}")
        
        print("\n" + "="*80)
        print("Done!")
        print("="*80)
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    fix_hongkong()
