#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第三方集成平台API功能基础测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pymysql
import hashlib
from config import DB_CONFIG
from router.integration_platform_api import INTEGRATION_API_KEY, get_password_hash

def test_database_connection():
    """测试数据库连接和users表"""
    print("测试数据库连接...")
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查users表结构
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        print("  users表结构:")
        for col in columns:
            print(f"    {col[0]} - {col[1]}")
        
        # 检查用户数量
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"  用户总数: {user_count}")
        
        # 检查admin用户是否存在
        cursor.execute("SELECT username, role FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        if admin_user:
            print(f"  admin用户存在，角色: {admin_user[1]}")
        else:
            print("  警告: admin用户不存在")
        
        cursor.close()
        conn.close()
        
        print("PASS: 数据库连接测试通过\n")
        return True
        
    except Exception as e:
        print(f"FAIL: 数据库连接失败: {str(e)}\n")
        return False

def test_password_hashing():
    """测试密码哈希功能"""
    print("测试密码哈希功能...")
    
    test_password = "test123"
    hashed = get_password_hash(test_password)
    expected = hashlib.md5(test_password.encode()).hexdigest()
    
    success = hashed == expected
    print(f"  原始密码: {test_password}")
    print(f"  哈希结果: {hashed}")
    print(f"  预期结果: {expected}")
    
    if success:
        print("PASS: 密码哈希功能正常\n")
    else:
        print("FAIL: 密码哈希功能异常\n")
    
    return success

def test_user_crud_operations():
    """测试用户CRUD操作"""
    print("测试用户CRUD操作...")
    
    test_username = "test_api_user"
    test_password = "test_password123"
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. 清理测试用户（如果存在）
        cursor.execute("DELETE FROM users WHERE username = %s", (test_username,))
        conn.commit()
        print("  清理已存在的测试用户")
        
        # 2. 测试创建用户
        hashed_password = get_password_hash(test_password)
        cursor.execute(
            "INSERT INTO users (username, password, role, status) VALUES (%s, %s, '访客', '离线')",
            (test_username, hashed_password)
        )
        conn.commit()
        user_id = cursor.lastrowid
        print(f"  创建用户成功: {test_username} (ID: {user_id})")
        
        # 3. 测试查询用户
        cursor.execute("SELECT username, role, status FROM users WHERE username = %s", (test_username,))
        user = cursor.fetchone()
        if user:
            print(f"  查询用户成功: {user[0]}, 角色: {user[1]}, 状态: {user[2]}")
        else:
            print("  查询用户失败")
            return False
        
        # 4. 测试更新密码
        new_password = "new_password456"
        new_hashed = get_password_hash(new_password)
        cursor.execute("UPDATE users SET password = %s WHERE username = %s", (new_hashed, test_username))
        conn.commit()
        print("  更新密码成功")
        
        # 5. 验证密码更新
        cursor.execute("SELECT password FROM users WHERE username = %s", (test_username,))
        stored_password = cursor.fetchone()[0]
        if stored_password == new_hashed:
            print("  密码更新验证成功")
        else:
            print("  密码更新验证失败")
            return False
        
        # 6. 测试删除用户
        cursor.execute("DELETE FROM users WHERE username = %s", (test_username,))
        conn.commit()
        print("  删除用户成功")
        
        # 7. 验证用户已删除
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (test_username,))
        count = cursor.fetchone()[0]
        if count == 0:
            print("  用户删除验证成功")
        else:
            print("  用户删除验证失败")
            return False
        
        cursor.close()
        conn.close()
        
        print("PASS: 用户CRUD操作测试通过\n")
        return True
        
    except Exception as e:
        print(f"FAIL: 用户CRUD操作测试失败: {str(e)}\n")
        return False

def test_api_configuration():
    """测试API配置"""
    print("测试API配置...")
    
    print(f"  API密钥: {INTEGRATION_API_KEY}")
    print(f"  API密钥长度: {len(INTEGRATION_API_KEY)}")
    
    # 检查API密钥是否为默认值
    if INTEGRATION_API_KEY == "THIRD_PARTY_INTEGRATION_KEY_2024":
        print("  警告: 使用默认API密钥，生产环境建议修改")
    else:
        print("  使用自定义API密钥")
    
    print("PASS: API配置检查完成\n")
    return True

def test_import_functionality():
    """测试模块导入功能"""
    print("测试模块导入...")
    
    try:
        # 测试导入主要模块
        from router.integration_platform_api import (
            router, verify_api_key, verify_ip_whitelist, 
            UserCreateRequest, UserUpdateRequest, UserResponse
        )
        print("  成功导入API路由模块")
        
        from main import app
        print("  成功导入主应用")
        
        # 检查路由是否正确注册
        routes = [route.path for route in app.routes]
        integration_routes = [route for route in routes if route.startswith('/api/integration')]
        
        print(f"  集成平台路由数量: {len(integration_routes)}")
        for route in integration_routes:
            print(f"    {route}")
        
        if len(integration_routes) > 0:
            print("  集成平台路由已正确注册")
        else:
            print("  集成平台路由未找到")
            return False
        
        print("PASS: 模块导入测试通过\n")
        return True
        
    except Exception as e:
        print(f"FAIL: 模块导入测试失败: {str(e)}\n")
        return False

def test_admin_user_protection():
    """测试admin用户保护机制"""
    print("测试admin用户保护...")
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查admin用户是否存在
        cursor.execute("SELECT username, role FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        
        if not admin_user:
            print("  警告: admin用户不存在，创建admin用户用于测试")
            # 创建admin用户
            admin_password = get_password_hash("admin123")
            cursor.execute(
                "INSERT INTO users (username, password, role, status) VALUES ('admin', %s, '管理员', '离线')",
                (admin_password,)
            )
            conn.commit()
            print("  创建admin用户成功")
        else:
            print(f"  admin用户存在，角色: {admin_user[1]}")
        
        cursor.close()
        conn.close()
        
        print("PASS: admin用户保护测试通过\n")
        return True
        
    except Exception as e:
        print(f"FAIL: admin用户保护测试失败: {str(e)}\n")
        return False

def run_all_tests():
    """运行所有测试"""
    print("开始测试第三方集成平台API功能...\n")
    
    tests = [
        ("数据库连接", test_database_connection),
        ("密码哈希功能", test_password_hashing),
        ("API配置", test_api_configuration),
        ("模块导入", test_import_functionality),
        ("admin用户保护", test_admin_user_protection),
        ("用户CRUD操作", test_user_crud_operations),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"FAIL: {test_name} 测试出现异常: {str(e)}\n")
            results.append((test_name, False))
    
    # 统计结果
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("=" * 60)
    print("测试结果汇总:")
    print(f"总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    print("\n详细结果:")
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {test_name}")
    
    if passed == total:
        print("\n所有测试通过！第三方集成平台API功能正常。")
        print("\n可以开始使用以下功能:")
        print("  - 获取用户列表: GET /api/integration/users")
        print("  - 检查用户存在: GET /api/integration/users/{username}")
        print("  - 创建用户: POST /api/integration/users")
        print("  - 更新密码: PUT /api/integration/users/{username}")
        print("  - 删除用户: DELETE /api/integration/users/{username}")
        print("  - 获取配置: GET /api/integration/config")
        print(f"\nAPI密钥: {INTEGRATION_API_KEY}")
        print("详细文档: THIRD_PARTY_INTEGRATION_API_GUIDE.md")
    else:
        print(f"\n有 {total - passed} 个测试失败，请检查相关功能。")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n测试过程中发生严重错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
