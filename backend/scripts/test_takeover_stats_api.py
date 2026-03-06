#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试接管节点统计API接口
验证新增的统计数据是否正确返回
"""

import requests
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_latest_stats():
    """测试获取最新统计数据接口"""
    print("=" * 60)
    print("测试最新统计数据接口")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8000/api/takeover-stats/latest")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ 接口调用成功")
            print(f"状态: {data['status']}")
            print(f"消息: {data['message']}")
            
            # 检查数据结构
            if 'data' in data:
                stats_data = data['data']
                
                # 检查总体统计
                if 'total_stats' in stats_data:
                    total = stats_data['total_stats']
                    print(f"总节点数: {total.get('total_nodes', 'N/A')}")
                    print(f"国内节点: {total.get('total_domestic_nodes', 'N/A')}")
                    print(f"国外节点: {total.get('total_foreign_nodes', 'N/A')}")
                
                # 检查已清除节点统计
                if 'cleaned_stats' in stats_data:
                    cleaned = stats_data['cleaned_stats']
                    print(f"已清除总节点: {cleaned.get('cleaned_total_nodes', 'N/A')}")
                    print(f"已清除国内节点: {cleaned.get('cleaned_domestic_nodes', 'N/A')}")
                    print(f"已清除国外节点: {cleaned.get('cleaned_foreign_nodes', 'N/A')}")
                else:
                    print("✗ 缺少已清除节点统计数据")
                
                # 检查抑制阻断策略统计
                if 'suppression_stats' in stats_data:
                    suppression = stats_data['suppression_stats']
                    print(f"抑制阻断策略总次数: {suppression.get('suppression_total_count', 'N/A')}")
                    print(f"近一个月抑制阻断次数: {suppression.get('monthly_suppression_count', 'N/A')}")
                else:
                    print("✗ 缺少抑制阻断策略统计数据")
                
                print(f"时间戳: {stats_data.get('timestamp', 'N/A')}")
            
            return True
        else:
            print(f"✗ 接口调用失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到API服务器，请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_detail_stats():
    """测试获取详细统计数据接口"""
    print("\n" + "=" * 60)
    print("测试详细统计数据接口")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8000/api/takeover-stats/detail")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ 接口调用成功")
            print(f"状态: {data['status']}")
            print(f"数据条数: {data.get('count', 0)}")
            
            if 'data' in data and len(data['data']) > 0:
                # 检查第一条数据的结构
                first_item = data['data'][0]
                print(f"第一个僵尸网络类型: {first_item.get('botnet_type', 'N/A')}")
                
                # 检查是否包含新增的统计字段
                if 'cleaned_stats' in first_item:
                    print("✓ 包含已清除节点统计数据")
                else:
                    print("✗ 缺少已清除节点统计数据")
                
                if 'suppression_stats' in first_item:
                    print("✓ 包含抑制阻断策略统计数据")
                else:
                    print("✗ 缺少抑制阻断策略统计数据")
            
            return True
        else:
            print(f"✗ 接口调用失败，状态码: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到API服务器")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_health_check():
    """测试健康检查接口"""
    print("\n" + "=" * 60)
    print("测试健康检查接口")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8000/api/takeover-stats/health")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ 健康检查通过")
            print(f"状态: {data.get('status', 'N/A')}")
            print(f"数据库连接: {data.get('database_connection', 'N/A')}")
            print(f"最新更新: {data.get('latest_update', 'N/A')}")
            print(f"数据是否新鲜: {data.get('is_data_fresh', 'N/A')}")
            return True
        else:
            print(f"✗ 健康检查失败，状态码: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到API服务器")
        return False
    except Exception as e:
        print(f"✗ 健康检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("接管节点统计API接口测试")
    print("测试新增的已清除节点和抑制阻断策略统计功能")
    
    results = []
    
    # 测试各个接口
    results.append(test_latest_stats())
    results.append(test_detail_stats())
    results.append(test_health_check())
    
    # 汇总测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有测试通过，新增统计功能正常工作")
        return True
    else:
        print("✗ 部分测试失败，请检查相关功能")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
