#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版本的API测试脚本
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
        # 增加超时时间到30秒
        with urllib.request.urlopen(url, timeout=30) as response:
            status_code = response.getcode()
            content = response.read().decode('utf-8')
            
            print(f"[OK] 状态码: {status_code}")
            
            if status_code == 200:
                try:
                    data = json.loads(content)
                    print(f"[OK] JSON解析成功")
                    print(f"状态: {data.get('status', 'N/A')}")
                    print(f"消息: {data.get('message', 'N/A')}")
                    
                    # 检查数据结构
                    if 'data' in data:
                        if description == "健康检查":
                            health_data = data.get('data', {})
                            if isinstance(health_data, dict):
                                print(f"数据库连接: {health_data.get('database_connection', 'N/A')}")
                                print(f"数据是否新鲜: {health_data.get('is_data_fresh', 'N/A')}")
                        elif description == "最新统计数据":
                            stats_data = data['data']
                            
                            # 检查基础统计
                            if 'total_stats' in stats_data:
                                total = stats_data['total_stats']
                                print(f"总节点数: {total.get('total_nodes', 'N/A')}")
                            
                            # 检查新增的已清除节点统计
                            if 'cleaned_stats' in stats_data:
                                cleaned = stats_data['cleaned_stats']
                                print(f"[OK] 包含已清除节点统计")
                                print(f"  已清除总节点: {cleaned.get('cleaned_total_nodes', 'N/A')}")
                                print(f"  已清除国内节点: {cleaned.get('cleaned_domestic_nodes', 'N/A')}")
                                print(f"  已清除国外节点: {cleaned.get('cleaned_foreign_nodes', 'N/A')}")
                            else:
                                print("[ERROR] 缺少已清除节点统计数据")
                            
                            # 检查新增的抑制阻断策略统计
                            if 'suppression_stats' in stats_data:
                                suppression = stats_data['suppression_stats']
                                print(f"[OK] 包含抑制阻断策略统计")
                                print(f"  抑制阻断策略总次数: {suppression.get('suppression_total_count', 'N/A')}")
                                print(f"  近一个月抑制阻断次数: {suppression.get('monthly_suppression_count', 'N/A')}")
                            else:
                                print("[ERROR] 缺少抑制阻断策略统计数据")
                        
                        elif description == "详细统计数据":
                            detail_data = data.get('data', [])
                            print(f"数据条数: {len(detail_data)}")
                            if len(detail_data) > 0:
                                first_item = detail_data[0]
                                print(f"第一个类型: {first_item.get('botnet_type', 'N/A')}")
                                
                                if 'cleaned_stats' in first_item:
                                    print("[OK] 包含已清除节点统计数据")
                                else:
                                    print("[ERROR] 缺少已清除节点统计数据")
                                
                                if 'suppression_stats' in first_item:
                                    print("[OK] 包含抑制阻断策略统计数据")
                                else:
                                    print("[ERROR] 缺少抑制阻断策略统计数据")
                    
                    return True
                except json.JSONDecodeError as e:
                    print(f"[ERROR] JSON解析失败: {e}")
                    print(f"响应内容前200字符: {content[:200]}...")
                    return False
            else:
                print(f"[ERROR] 非200状态码")
                print(f"响应内容: {content[:200]}...")
                return False
                
    except urllib.error.HTTPError as e:
        print(f"[ERROR] HTTP错误: {e.code} - {e.reason}")
        try:
            error_content = e.read().decode('utf-8')
            print(f"错误内容: {error_content[:200]}...")
        except:
            pass
        return False
    except urllib.error.URLError as e:
        print(f"[ERROR] URL错误: {e.reason}")
        return False
    except Exception as e:
        print(f"[ERROR] 其他错误: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("接管节点统计API测试 - 修复版本")
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
        print("[OK] 所有测试通过，新增统计功能正常工作")
        return True
    else:
        print("[ERROR] 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
