import pymysql
from config import DB_CONFIG

TABLE = "botnet_nodes_utg_q_008"

def add_area_field():
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        print(f"Adding 'area' field to table {TABLE}...")
        
        # Check if area field already exists
        cur.execute(f"SHOW COLUMNS FROM {TABLE} LIKE 'area'")
        if cur.fetchone():
            print("Field 'area' already exists!")
            return
        
        # Add area field after city
        sql = f"""
        ALTER TABLE {TABLE} 
        ADD COLUMN area VARCHAR(50) NULL AFTER city
        """
        
        cur.execute(sql)
        conn.commit()
        
        print("Successfully added 'area' field!")
        print("\nTable structure updated:")
        cur.execute(f"DESCRIBE {TABLE}")
        for row in cur.fetchall():
            print(f"  {row[0]:<20} {row[1]:<25} {row[2]:<10}")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    add_area_field()
