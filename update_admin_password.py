#!/usr/bin/env python3
"""
更新admin用户密码的脚本
将admin账号的密码从123456改为Matrix!!23
"""
import pymysql
import hashlib
import sys

def get_password_hash(password: str) -> str:
    """使用MD5哈希密码"""
    return hashlib.md5(password.encode()).hexdigest()

def update_admin_password():
    """更新admin用户的密码"""
    
    # 数据库配置 - 从config导入
    try:
        from backend.config import DB_CONFIG
    except ImportError:
        print("错误：无法导入数据库配置")
        print("请确保backend/config.py文件存在")
        sys.exit(1)
    
    # 旧密码和新密码
    old_password = "123456"
    new_password = "Matrix!!23"
    
    # 计算哈希值
    old_hash = get_password_hash(old_password)
    new_hash = get_password_hash(new_password)
    
    print(f"旧密码: {old_password}")
    print(f"旧密码MD5: {old_hash}")
    print(f"新密码: {new_password}")
    print(f"新密码MD5: {new_hash}")
    print()
    
    try:
        # 连接数据库
        print("正在连接数据库...")
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 查询admin用户当前信息
        cursor.execute(
            "SELECT id, username, password FROM users WHERE username = 'admin'"
        )
        admin_user = cursor.fetchone()
        
        if not admin_user:
            print("错误：未找到admin用户")
            cursor.close()
            conn.close()
            sys.exit(1)
        
        user_id, username, current_password_hash = admin_user
        print(f"找到用户: {username} (ID: {user_id})")
        print(f"当前密码哈希: {current_password_hash}")
        print()
        
        # 验证当前密码是否为123456
        if current_password_hash == old_hash:
            print("✓ 确认当前密码为123456")
        else:
            print(f"⚠ 警告：当前密码哈希与123456的哈希不匹配")
            print(f"是否仍要继续更新密码？(y/n): ", end="")
            confirm = input().strip().lower()
            if confirm != 'y':
                print("已取消操作")
                cursor.close()
                conn.close()
                sys.exit(0)
        
        # 更新密码
        print(f"\n正在更新密码为: {new_password}")
        cursor.execute(
            "UPDATE users SET password = %s WHERE username = 'admin'",
            (new_hash,)
        )
        conn.commit()
        
        # 验证更新
        cursor.execute(
            "SELECT password FROM users WHERE username = 'admin'"
        )
        updated_hash = cursor.fetchone()[0]
        
        if updated_hash == new_hash:
            print("✓ 密码更新成功！")
            print(f"新密码: {new_password}")
            print(f"新密码MD5哈希: {new_hash}")
        else:
            print("✗ 密码更新失败")
            
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Admin密码更新脚本")
    print("=" * 60)
    print()
    update_admin_password()
    print()
    print("=" * 60)
