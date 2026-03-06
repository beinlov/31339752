#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的API测试脚本
使用urllib避免依赖问题
"""

import urllib.request
import urllib.error
import json
import sys

def test_api_endpoint(url, description):
    """测试单个API端点"""
    print(f"\n测试: {description}")
    print(f"URL: {url}")
    print("-" * 50)
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            status_code = response.getcode()
            content = response.read().decode('utf-8')
            
            print(f"✓ 状态码: {status_code}")
            
            if status_code == 200:
                try:
                    data = json.loads(content)
                    print(f"✓ JSON解析成功")
                    print(f"状态: {data.get('status', 'N/A')}")
                    print(f"消息: {data.get('message', 'N/A')}")
                    
                    # 检查数据结构
                    if 'data' in data:
                        if description == "健康检查":
                            print(f"数据库连接: {data['data'].get('database_connection', 'N/A') if isinstance(data.get('data'), dict) else 'N/A'}")
                        elif description == "最新统计数据":
                            stats_data = data['data']
                            if 'cleaned_stats' in stats_data:
                                print("✓ 包含已清除节点统计")
                            else:
                                print("✗ 缺少已清除节点统计")
                            
                            if 'suppression_stats' in stats_data:
                                print("✓ 包含抑制阻断策略统计")
                            else:
                                print("✗ 缺少抑制阻断策略统计")
                    
                    return True
                except json.JSONDecodeError as e:
                    print(f"✗ JSON解析失败: {e}")
                    print(f"响应内容: {content[:200]}...")
                    return False
            else:
                print(f"✗ 非200状态码")
                print(f"响应内容: {content[:200]}...")
                return False
                
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP错误: {e.code} - {e.reason}")
        try:
            error_content = e.read().decode('utf-8')
            print(f"错误内容: {error_content[:200]}...")
        except:
            pass
        return False
    except urllib.error.URLError as e:
        print(f"✗ URL错误: {e.reason}")
        return False
    except Exception as e:
        print(f"✗ 其他错误: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("接管节点统计API简单测试")
    print("=" * 60)
    
    # 测试端点列表
    test_cases = [
        ("http://localhost:8000/api/takeover-stats/health", "健康检查"),
        ("http://localhost:8000/api/takeover-stats/latest", "最新统计数据"),
        ("http://localhost:8000/api/takeover-stats/detail", "详细统计数据")
    ]
    
    results = []
    
    for url, description in test_cases:
        result = test_api_endpoint(url, description)
        results.append(result)
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有测试通过")
        return True
    else:
        print("✗ 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
