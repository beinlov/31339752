"""
删除测试数据库脚本
保留 test 数据库，删除其他测试数据库（如 test444, test888 等）
"""
import pymysql
import sys
import os

# 添加父目录到路径，以便导入config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG


def connect_db():
    """连接到MySQL数据库（不指定具体数据库），尝试多个密码"""
    # 常见密码列表
    passwords = [
        DB_CONFIG['password'],  # 配置文件中的密码
        '123456',               # Docker默认密码
        'Matrix123',            # 备用密码
    ]
    
    last_error = None
    for password in passwords:
        try:
            conn = pymysql.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=password,
                charset=DB_CONFIG['charset']
            )
            print(f"[OK] 使用密码: {password[:3]}*** 连接成功")
            return conn
        except pymysql.Error as e:
            last_error = e
            continue
    
    # 所有密码都失败
    raise last_error


def get_all_databases(cursor):
    """获取所有数据库列表"""
    cursor.execute("SHOW DATABASES")
    databases = [row[0] for row in cursor.fetchall()]
    return databases


def get_test_databases_to_delete(databases):
    """
    筛选出需要删除的测试数据库
    规则：以 test 开头但不是 test 本身的数据库
    """
    # 系统保留数据库
    system_databases = ['information_schema', 'mysql', 'performance_schema', 'sys']
    
    # 需要删除的数据库列表
    to_delete = []
    
    for db in databases:
        # 跳过系统数据库
        if db in system_databases:
            continue
        
        # 保留 test 数据库
        if db == 'test':
            print(f"[KEEP] 保留: {db}")
            continue
        
        # 删除以 test 开头的其他数据库
        if db.startswith('test'):
            to_delete.append(db)
    
    return to_delete


def delete_databases(cursor, databases_to_delete):
    """删除指定的数据库"""
    if not databases_to_delete:
        print("\n[INFO] 没有需要删除的测试数据库。")
        return
    
    print(f"\n[FOUND] 找到 {len(databases_to_delete)} 个需要删除的测试数据库:")
    for db in databases_to_delete:
        print(f"  - {db}")
    
    # 确认删除
    print("\n[WARNING] 警告：此操作将永久删除以上数据库及其所有数据！")
    confirm = input("确认删除? (输入 yes 继续): ")
    
    if confirm.lower() != 'yes':
        print("[CANCEL] 操作已取消。")
        return
    
    # 执行删除
    print("\n[DELETE] 开始删除...")
    for db in databases_to_delete:
        try:
            cursor.execute(f"DROP DATABASE `{db}`")
            print(f"[OK] 已删除: {db}")
        except Exception as e:
            print(f"[ERROR] 删除失败 {db}: {e}")
    
    print("\n[DONE] 删除完成！")


def main():
    """主函数"""
    print("=" * 60)
    print("测试数据库清理工具")
    print("=" * 60)
    print(f"数据库主机: {DB_CONFIG['host']}")
    print(f"连接用户: {DB_CONFIG['user']}")
    print("=" * 60)
    
    try:
        # 连接数据库
        print("\n[CONNECT] 连接到MySQL...")
        conn = connect_db()
        cursor = conn.cursor()
        
        # 获取所有数据库
        print("\n[LIST] 获取数据库列表...")
        all_databases = get_all_databases(cursor)
        print(f"[OK] 找到 {len(all_databases)} 个数据库")
        
        # 筛选需要删除的测试数据库
        databases_to_delete = get_test_databases_to_delete(all_databases)
        
        # 执行删除
        delete_databases(cursor, databases_to_delete)
        
        # 关闭连接
        cursor.close()
        conn.close()
        
    except pymysql.Error as e:
        print(f"\n[ERROR] 数据库错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
