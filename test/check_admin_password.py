import pymysql
from config import DB_CONFIG
import hashlib

def check_admin_password():
    try:
        print("Checking admin password hash...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        cursor.execute("SELECT username, password FROM users WHERE username='admin'")
        result = cursor.fetchone()
        
        if result:
            username, stored_hash = result
            print(f"Username: {username}")
            print(f"Stored password hash: {stored_hash}")
            
            # Test common passwords
            test_passwords = ['admin', '123456', 'admin123', 'password']
            for pwd in test_passwords:
                test_hash = hashlib.md5(pwd.encode()).hexdigest()
                if test_hash == stored_hash:
                    print(f"\n[SUCCESS] Password is: {pwd}")
                    return pwd
            
            print("\n[INFO] Password is not one of the common ones tested")
            print("Try resetting the password or check the database")
        else:
            print("[ERROR] Admin user not found")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"[ERROR] Failed to check password: {e}")

if __name__ == "__main__":
    check_admin_password()
