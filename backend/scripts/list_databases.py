"""
查看所有数据库列表脚本
"""
import pymysql
import sys
import os

# 添加父目录到路径，以便导入config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG


def connect_db():
    """连接到MySQL数据库"""
    passwords = [
        DB_CONFIG['password'],
        '123456',
        'Matrix123',
    ]
    
    for password in passwords:
        try:
            conn = pymysql.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=password,
                charset=DB_CONFIG['charset']
            )
            return conn
        except pymysql.Error:
            continue
    raise Exception("Unable to connect to database")


def main():
    """主函数"""
    print("=" * 60)
    print("Database List")
    print("=" * 60)
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        
        print("\nAll Databases:")
        print("-" * 60)
        for idx, (db_name,) in enumerate(databases, 1):
            # 标记test开头的数据库
            marker = ""
            if db_name.startswith('test'):
                if db_name == 'test':
                    marker = " [KEEP - Main test DB]"
                else:
                    marker = " [TEST DB - Should be deleted]"
            
            print(f"{idx:2d}. {db_name}{marker}")
        
        print("-" * 60)
        print(f"Total: {len(databases)} databases")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
