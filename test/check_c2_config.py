#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查C2端点的实际配置
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_c2_config():
    """检查C2配置"""
    
    print("="*60)
    print("C2端点配置检查")
    print("="*60)
    print()
    
    # 检查环境变量
    print("【环境变量】")
    c2_env_vars = [
        'C2_ENDPOINT_1', 'C2_API_KEY_1',
        'C2_ENDPOINT_2', 'C2_API_KEY_2',
    ]
    
    for var in c2_env_vars:
        value = os.environ.get(var)
        if value:
            # API Key只显示前后几位
            if 'API_KEY' in var and len(value) > 10:
                display_value = f"{value[:6]}...{value[-4:]}"
            else:
                display_value = value
            print(f"  {var} = {display_value}")
        else:
            print(f"  {var} = (未设置)")
    print()
    
    # 导入配置
    print("【实际配置】")
    try:
        from config import C2_ENDPOINTS
        
        for i, c2 in enumerate(C2_ENDPOINTS):
            print(f"\nC2端点 {i+1}:")
            print(f"  名称: {c2.get('name')}")
            print(f"  URL: {c2.get('url')}  ⬅️ 这是实际使用的地址")
            print(f"  启用: {c2.get('enabled')}")
            print(f"  API Key: {c2.get('api_key')[:6]}...{c2.get('api_key')[-4:]}")
            print(f"  batch_size: {c2.get('batch_size')}")
            print(f"  pull_interval: {c2.get('pull_interval')} 秒")
            print(f"  timeout: {c2.get('timeout')}")
            print(f"  verify_ssl: {c2.get('verify_ssl')}")
            
            # 分析URL
            url = c2.get('url', '')
            if 'localhost' in url or '127.0.0.1' in url:
                print(f"  ⚠️  使用本地地址！")
                print(f"      - 如果C2在远程服务器，这个配置无法访问")
                print(f"      - 如果能访问，可能有端口转发或环境变量覆盖")
            elif url.startswith('http://') and not url.startswith('http://localhost'):
                print(f"  ⚠️  使用HTTP协议（未加密）")
            elif url.startswith('https://'):
                print(f"  ✅ 使用HTTPS协议（加密）")
        
        print()
        print("="*60)
        print("说明:")
        print("1. 如果'URL'显示localhost但能访问远程服务器，检查：")
        print("   - 是否在同一台服务器上运行")
        print("   - 是否有SSH隧道: ssh -L 8888:远程IP:8888")
        print("   - 环境变量是否设置了远程地址")
        print()
        print("2. 推荐配置（远程C2）:")
        print("   方法1: 设置环境变量")
        print("   set C2_ENDPOINT_1=http://公网IP:8888")
        print()
        print("   方法2: 直接修改config.py中的url字段")
        print("="*60)
        
    except Exception as e:
        print(f"❌ 配置读取失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_c2_config()
