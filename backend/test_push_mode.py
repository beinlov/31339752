#!/usr/bin/env python3
"""
推送模式测试脚本
用于测试中转服务器向本服务器推送数据的功能
"""

import requests
import json
import hmac
import hashlib
from datetime import datetime
import sys
import argparse

# 测试配置（与config.py中的配置保持一致）
API_BASE_URL = "http://localhost:8000"
API_KEY = "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
SIGNATURE_SECRET = "CHANGE_ME_IN_PRODUCTION_use_strong_random_key_here"

def generate_hmac_signature(request_body: str, timestamp: str, nonce: str = None) -> str:
    """
    生成HMAC签名
    
    Args:
        request_body: JSON请求体字符串
        timestamp: ISO格式时间戳
        nonce: 随机数（可选）
    
    Returns:
        HMAC签名（hex格式）
    """
    # 构造待签名消息：timestamp + nonce + request_body
    message_parts = [timestamp]
    if nonce:
        message_parts.append(nonce)
    message_parts.append(request_body)
    message = ''.join(message_parts)
    
    # 计算HMAC-SHA256签名
    signature = hmac.new(
        SIGNATURE_SECRET.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature


def test_push_data(botnet_type: str = "ramnit", count: int = 10, use_signature: bool = True):
    """
    测试推送数据到本服务器
    
    Args:
        botnet_type: 僵尸网络类型
        count: 推送数据条数
        use_signature: 是否使用HMAC签名
    """
    print("=" * 70)
    print(f"测试推送数据到本服务器")
    print(f"僵尸网络类型: {botnet_type}")
    print(f"数据条数: {count}")
    print(f"使用签名: {use_signature}")
    print("=" * 70)
    
    # 1. 构造测试数据
    timestamp = datetime.now().isoformat()
    nonce = f"test-nonce-{int(datetime.now().timestamp())}"
    
    test_data = {
        "botnet_type": botnet_type,
        "data": [
            {
                "ip": f"192.168.{i//256}.{i%256}",
                "timestamp": datetime.now().isoformat(),
                "event_type": "test",
                "source": "test_script",
                "botnet_type": botnet_type
            }
            for i in range(1, count + 1)
        ],
        "timestamp": timestamp,
        "nonce": nonce,
        "relay_server_id": "test-relay-001"
    }
    
    # 2. 序列化请求体
    request_body = json.dumps(test_data, ensure_ascii=False)
    
    # 3. 生成签名
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    if use_signature:
        signature = generate_hmac_signature(request_body, timestamp, nonce)
        headers["X-Signature"] = signature
        print(f"\n生成的签名: {signature[:32]}...{signature[-8:]}")
    
    # 4. 发送请求
    url = f"{API_BASE_URL}/api/data-push"
    print(f"\n发送推送请求到: {url}")
    print(f"请求头: {json.dumps(headers, indent=2)}")
    
    try:
        response = requests.post(
            url,
            data=request_body,
            headers=headers,
            timeout=30
        )
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("\n✅ 推送成功！")
            return True
        else:
            print(f"\n❌ 推送失败: {response.json().get('detail', 'Unknown error')}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败：请确保服务器正在运行")
        return False
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        return False


def test_push_status():
    """测试获取推送状态"""
    print("=" * 70)
    print("获取推送模式状态")
    print("=" * 70)
    
    url = f"{API_BASE_URL}/api/push-status"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"\n响应状态码: {response.status_code}")
        print(f"推送状态: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("\n✅ 状态查询成功！")
            return True
        else:
            print(f"\n❌ 状态查询失败")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败：请确保服务器正在运行")
        return False
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        return False


def test_push_health():
    """测试推送健康检查"""
    print("=" * 70)
    print("推送模式健康检查")
    print("=" * 70)
    
    url = f"{API_BASE_URL}/api/push-health"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"\n响应状态码: {response.status_code}")
        print(f"健康状态: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("\n✅ 健康检查通过！")
            return True
        else:
            print(f"\n❌ 健康检查失败")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败：请确保服务器正在运行并且已启用推送模式")
        return False
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="推送模式测试脚本")
    parser.add_argument('--botnet-type', default='ramnit', help='僵尸网络类型')
    parser.add_argument('--count', type=int, default=10, help='推送数据条数')
    parser.add_argument('--no-signature', action='store_true', help='不使用签名（测试认证失败）')
    parser.add_argument('--base-url', default='http://localhost:8000', help='API基础URL')
    parser.add_argument('--api-key', help='API密钥（覆盖默认值）')
    parser.add_argument('--secret', help='签名密钥（覆盖默认值）')
    
    args = parser.parse_args()
    
    # 更新配置
    global API_BASE_URL, API_KEY, SIGNATURE_SECRET
    API_BASE_URL = args.base_url
    if args.api_key:
        API_KEY = args.api_key
    if args.secret:
        SIGNATURE_SECRET = args.secret
    
    print("\n" + "=" * 70)
    print("推送模式测试工具")
    print("=" * 70)
    print(f"服务器地址: {API_BASE_URL}")
    print(f"API密钥: {API_KEY[:16]}...{API_KEY[-4:]}")
    print(f"签名密钥: {SIGNATURE_SECRET[:16]}...{SIGNATURE_SECRET[-4:]}")
    print("=" * 70 + "\n")
    
    # 测试顺序
    tests = [
        ("健康检查", test_push_health),
        ("状态查询", test_push_status),
        ("数据推送", lambda: test_push_data(
            botnet_type=args.botnet_type,
            count=args.count,
            use_signature=not args.no_signature
        ))
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print("\n")
        except Exception as e:
            print(f"\n❌ 测试 '{test_name}' 异常: {e}")
            results.append((test_name, False))
    
    # 打印总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    print("=" * 70)
    
    # 返回退出码
    all_passed = all(result for _, result in results)
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
