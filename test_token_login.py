#!/usr/bin/env python3
"""
Token方式自动登录测试脚本

演示如何从其他平台生成登录token并跳转到本平台
"""
import requests
import webbrowser
import sys
import time

# 配置
BACKEND_URL = "http://localhost:8000"  # 后端API地址
FRONTEND_URL = "http://localhost:9000"  # 前端地址

def generate_login_token(username, password, expires_minutes=5):
    """
    生成登录token
    
    Args:
        username: 用户名
        password: 密码
        expires_minutes: token过期时间（分钟）
    
    Returns:
        token信息字典，如果失败返回None
    """
    print("\n" + "="*60)
    print("步骤 1: 生成登录Token")
    print("="*60)
    print(f"用户名: {username}")
    print(f"过期时间: {expires_minutes}分钟")
    print(f"API地址: {BACKEND_URL}/api/user/generate-login-token")
    
    try:
        # 发送POST请求生成token
        response = requests.post(
            f"{BACKEND_URL}/api/user/generate-login-token",
            params={
                'username': username,
                'password': password,
                'expires_minutes': expires_minutes
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n? Token生成成功！")
            print(f"  Token: {data['token'][:20]}...（已截断）")
            print(f"  完整Token: {data['token']}")
            print(f"  过期时间: {data['expires_at']}")
            print(f"  有效期: {data['expires_in_seconds']}秒")
            return data
        else:
            print(f"\n? Token生成失败！")
            print(f"  状态码: {response.status_code}")
            print(f"  错误信息: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"\n? 连接失败！无法连接到后端服务器 {BACKEND_URL}")
        print("  请确保后端服务正在运行")
        return None
    except Exception as e:
        print(f"\n? 请求失败！")
        print(f"  错误: {str(e)}")
        return None

def build_login_url(token_data, menu=None):
    """
    构建登录URL
    
    Args:
        token_data: token信息
        menu: 可选的菜单参数
    
    Returns:
        完整的登录URL
    """
    print("\n" + "="*60)
    print("步骤 2: 构建登录URL")
    print("="*60)
    
    # 基础URL
    login_url = f"{FRONTEND_URL}{token_data['login_url']}"
    
    # 添加菜单参数（如果有）
    if menu:
        login_url += f"&menu={menu}"
        print(f"菜单参数: {menu}")
    
    print(f"登录URL: {login_url}")
    print(f"\n注意：URL中只包含token，不包含账号密码明文！")
    
    return login_url

def open_browser(url, auto_open=True):
    """
    在浏览器中打开URL
    
    Args:
        url: 要打开的URL
        auto_open: 是否自动打开浏览器
    """
    print("\n" + "="*60)
    print("步骤 3: 在浏览器中打开登录URL")
    print("="*60)
    
    if auto_open:
        print("正在打开浏览器...")
        try:
            webbrowser.open(url)
            print("? 浏览器已打开！")
            print("\n前端将自动完成以下步骤：")
            print("  1. 检测URL中的token参数")
            print("  2. 调用auto-login接口验证token")
            print("  3. 保存JWT令牌到localStorage")
            print("  4. 清除URL中的token参数（安全措施）")
            print("  5. 根据用户角色跳转到对应页面")
        except Exception as e:
            print(f"? 打开浏览器失败: {str(e)}")
            print(f"\n请手动复制以下URL到浏览器：")
            print(f"{url}")
    else:
        print(f"请手动复制以下URL到浏览器：")
        print(f"{url}")

def test_token_login(username, password, menu=None, auto_open=True):
    """
    测试完整的token登录流程
    
    Args:
        username: 用户名
        password: 密码
        menu: 可选的菜单参数
        auto_open: 是否自动打开浏览器
    """
    print("\n" + "="*60)
    print("Token方式自动登录 - 完整测试")
    print("="*60)
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 步骤1: 生成token
    token_data = generate_login_token(username, password)
    if not token_data:
        print("\n测试失败：无法生成token")
        return False
    
    # 步骤2: 构建登录URL
    login_url = build_login_url(token_data, menu)
    
    # 步骤3: 打开浏览器
    open_browser(login_url, auto_open)
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
    return True

def compare_methods():
    """
    对比传统方式和token方式
    """
    print("\n" + "="*60)
    print("登录方式对比")
    print("="*60)
    
    print("\n【传统方式 - 不安全】")
    print("URL示例:")
    print("  http://localhost:9000/login?username=admin&password=Matrix!!23")
    print("\n问题:")
    print("  ? URL中直接显示账号密码明文")
    print("  ? 可被浏览器历史记录")
    print("  ? 可被日志系统记录")
    print("  ? 容易被截获和滥用")
    
    print("\n【Token方式 - 安全】")
    print("URL示例:")
    print("  http://localhost:9000/login?token=xB3mK9pL2qR8vN4hS7tY1zW6cF5jD0aE...")
    print("\n优势:")
    print("  ? URL中不含账号密码")
    print("  ? Token只能使用一次")
    print("  ? Token有过期时间（5分钟）")
    print("  ? 泄露风险极小")

if __name__ == "__main__":
    print("="*60)
    print("Token方式自动登录 - 测试脚本")
    print("="*60)
    
    # 显示对比
    compare_methods()
    
    # 获取用户输入
    print("\n请输入登录信息：")
    
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
        menu = sys.argv[3] if len(sys.argv) >= 4 else None
    else:
        username = input("用户名 [admin]: ").strip() or "admin"
        password = input("密码 [Matrix!!23]: ").strip() or "Matrix!!23"
        menu = input("菜单（可选，回车跳过）: ").strip() or None
    
    # 询问是否自动打开浏览器
    auto_open_input = input("\n是否自动打开浏览器？(y/n) [y]: ").strip().lower()
    auto_open = auto_open_input != 'n'
    
    # 执行测试
    success = test_token_login(username, password, menu, auto_open)
    
    if success:
        print("\n提示：")
        print("- 如果后端服务未运行，请先启动后端")
        print("- 如果前端服务未运行，请先启动前端")
        print("- Token有效期为5分钟，请及时使用")
        print("- Token只能使用一次，使用后立即失效")
    
    sys.exit(0 if success else 1)
