#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终API测试脚本 - 验证新增统计功能
"""

import http.client
import json
import sys

def test_api_with_http_client(host, port, path, description):
    """使用http.client测试API接口"""
    print(f"\n测试: {description}")
    print(f"请求: GET {path}")
    print("-" * 50)
    
    try:
        # 创建HTTP连接
        conn = http.client.HTTPConnection(host, port, timeout=30)
        
        # 发送GET请求
        conn.request("GET", path)
        
        # 获取响应
        response = conn.getresponse()
        status_code = response.status
        content = response.read().decode('utf-8')
        
        print(f"[OK] 状态码: {status_code}")
        
        if status_code == 200:
            try:
                data = json.loads(content)
                print(f"[OK] JSON解析成功")
                print(f"状态: {data.get('status', 'N/A')}")
                print(f"消息: {data.get('message', 'N/A')}")
                
                # 根据不同接口检查数据结构
                if 'health' in path:
                    # 健康检查接口
                    if 'database_connection' in data:
                        print(f"数据库连接: {data.get('database_connection', 'N/A')}")
                    return True
                    
                elif 'latest' in path:
                    # 最新统计数据接口
                    if 'data' in data:
                        stats_data = data['data']
                        
                        # 检查基础统计
                        if 'total_stats' in stats_data:
                            total = stats_data['total_stats']
                            print(f"总节点数: {total.get('total_nodes', 'N/A')}")
                            print(f"国内节点: {total.get('total_domestic_nodes', 'N/A')}")
                            print(f"国外节点: {total.get('total_foreign_nodes', 'N/A')}")
                        
                        # 检查新增的已清除节点统计
                        if 'cleaned_stats' in stats_data:
                            cleaned = stats_data['cleaned_stats']
                            print(f"[OK] 已清除节点统计:")
                            print(f"  总数: {cleaned.get('cleaned_total_nodes', 'N/A')}")
                            print(f"  国内: {cleaned.get('cleaned_domestic_nodes', 'N/A')}")
                            print(f"  国外: {cleaned.get('cleaned_foreign_nodes', 'N/A')}")
                        else:
                            print("[ERROR] 缺少已清除节点统计")
                            return False
                        
                        # 检查新增的抑制阻断策略统计
                        if 'suppression_stats' in stats_data:
                            suppression = stats_data['suppression_stats']
                            print(f"[OK] 抑制阻断策略统计:")
                            print(f"  总次数: {suppression.get('suppression_total_count', 'N/A')}")
                            print(f"  近一个月: {suppression.get('monthly_suppression_count', 'N/A')}")
                        else:
                            print("[ERROR] 缺少抑制阻断策略统计")
                            return False
                        
                        # 检查近一个月清除节点统计
                        if 'monthly_cleaned_stats' in stats_data:
                            monthly_cleaned = stats_data['monthly_cleaned_stats']
                            print(f"[OK] 近一个月清除节点统计:")
                            print(f"  总数: {monthly_cleaned.get('monthly_cleaned_total_nodes', 'N/A')}")
                            print(f"  国内: {monthly_cleaned.get('monthly_cleaned_domestic_nodes', 'N/A')}")
                            print(f"  国外: {monthly_cleaned.get('monthly_cleaned_foreign_nodes', 'N/A')}")
                        else:
                            print("[ERROR] 缺少近一个月清除节点统计")
                            return False
                    
                    return True
                    
                elif 'detail' in path:
                    # 详细统计数据接口
                    if 'data' in data:
                        detail_data = data['data']
                        print(f"数据条数: {len(detail_data)}")
                        
                        if len(detail_data) > 0:
                            first_item = detail_data[0]
                            print(f"第一个类型: {first_item.get('botnet_type', 'N/A')}")
                            
                            # 检查新增字段
                            required_fields = ['cleaned_stats', 'monthly_cleaned_stats', 'suppression_stats']
                            all_present = True
                            
                            for field in required_fields:
                                if field in first_item:
                                    print(f"[OK] 包含 {field}")
                                else:
                                    print(f"[ERROR] 缺少 {field}")
                                    all_present = False
                            
                            return all_present
                    
                    return True
                
                return True
                
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON解析失败: {e}")
                print(f"响应内容前200字符: {content[:200]}...")
                return False
        else:
            print(f"[ERROR] 状态码 {status_code}")
            print(f"响应内容: {content[:200]}...")
            return False
            
    except Exception as e:
        print(f"[ERROR] 请求失败: {e}")
        return False
    finally:
        try:
            conn.close()
        except:
            pass

def main():
    """主测试函数"""
    print("=" * 60)
    print("接管节点统计API最终测试")
    print("验证新增的已清除节点和抑制阻断策略统计功能")
    print("=" * 60)
    
    host = "localhost"
    port = 8000
    
    # 测试用例
    test_cases = [
        ("/api/takeover-stats/health", "健康检查"),
        ("/api/takeover-stats/latest", "最新统计数据"),
        ("/api/takeover-stats/detail", "详细统计数据")
    ]
    
    results = []
    
    for path, description in test_cases:
        result = test_api_with_http_client(host, port, path, description)
        results.append(result)
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("[OK] 所有测试通过！")
        print("新增的统计功能正常工作:")
        print("- 已清除节点统计 (cleaned_stats)")
        print("- 近一个月清除节点统计 (monthly_cleaned_stats)")
        print("- 抑制阻断策略统计 (suppression_stats)")
        return True
    else:
        print("[ERROR] 部分测试失败，请检查相关功能")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
