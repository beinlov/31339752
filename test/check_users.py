import pymysql
from config import DB_CONFIG

def check_users():
    try:
        print("Checking users in database...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        cursor.execute("SELECT username, role, status FROM users")
        users = cursor.fetchall()
        
        if users:
            print(f"\nFound {len(users)} users:")
            for user in users:
                print(f"  - Username: {user[0]}, Role: {user[1]}, Status: {user[2]}")
        else:
            print("\n[WARNING] No users found in database!")
            print("You may need to create an admin user.")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"[ERROR] Failed to check users: {e}")

if __name__ == "__main__":
    check_users()
