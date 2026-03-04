"""
验证一键清除配置修正是否正确
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from config import C2_CLEANUP_CONFIG

def verify_config():
    print("=" * 70)
    print("验证一键清除配置修正")
    print("=" * 70)
    
    # 1. 检查端口配置
    print("\n1. 端口配置")
    port = C2_CLEANUP_CONFIG['c2_port']
    expected_port = 443
    if port == expected_port:
        print(f"   ✅ c2_port: {port} (正确)")
    else:
        print(f"   ❌ c2_port: {port}, 应该是 {expected_port}")
    
    # 2. 检查路径前缀
    print("\n2. 路径前缀配置")
    path_prefix = C2_CLEANUP_CONFIG['c2_path_prefix']
    if path_prefix == '':
        print(f"   ✅ c2_path_prefix: '{path_prefix}' (空字符串，正确)")
    else:
        print(f"   ❌ c2_path_prefix: '{path_prefix}', 应该是空字符串")
    
    # 3. 模拟URL构建
    print("\n3. 模拟URL构建")
    test_ip = "43.99.37.118"
    test_botnet = "utg_q_008"
    test_action = "cleanup"
    
    # 模拟 call_c2_api 中的逻辑
    action_path = C2_CLEANUP_CONFIG['botnet_paths'][test_botnet][test_action]
    port = C2_CLEANUP_CONFIG['c2_port']
    protocol = 'https' if port == 443 else 'http'
    base_url = f"{protocol}://{test_ip}:{port}"
    path_prefix = C2_CLEANUP_CONFIG['c2_path_prefix']
    full_url = f"{base_url}{path_prefix}{action_path}"
    
    print(f"\n   测试参数:")
    print(f"     C2 IP: {test_ip}")
    print(f"     Botnet: {test_botnet}")
    print(f"     Action: {test_action}")
    
    print(f"\n   构建过程:")
    print(f"     Protocol: {protocol}")
    print(f"     Port: {port}")
    print(f"     Base URL: {base_url}")
    print(f"     Path Prefix: '{path_prefix}'")
    print(f"     Action Path: {action_path}")
    
    print(f"\n   最终URL:")
    print(f"     {full_url}")
    
    # 4. 验证所有僵网的URL
    print("\n4. 验证所有僵网的URL构建")
    for botnet_name, paths in C2_CLEANUP_CONFIG['botnet_paths'].items():
        print(f"\n   {botnet_name}:")
        for action, action_path in paths.items():
            port = C2_CLEANUP_CONFIG['c2_port']
            protocol = 'https' if port == 443 else 'http'
            base_url = f"{protocol}://{test_ip}:{port}"
            path_prefix = C2_CLEANUP_CONFIG['c2_path_prefix']
            full_url = f"{base_url}{path_prefix}{action_path}"
            print(f"     {action}: {full_url}")
    
    # 5. 预期结果
    print("\n" + "=" * 70)
    print("✅ 配置修正总结")
    print("=" * 70)
    print("\n修正前:")
    print("  - 端口: 8080")
    print("  - 路径前缀: '/execute'")
    print("  - URL示例: http://43.99.37.118:8080/execute/admin/ramnit/cleanup")
    
    print("\n修正后:")
    print("  - 端口: 443")
    print("  - 路径前缀: '' (空)")
    print("  - URL示例: https://43.99.37.118:443/admin/ramnit/cleanup")
    
    print("\n注意事项:")
    print("  ✅ 使用HTTPS协议（端口443）")
    print("  ✅ 直接访问/admin路径，无需/execute前缀")
    print("  ✅ SSL验证仍然关闭（verify_ssl=False）")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    verify_config()
