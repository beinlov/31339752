#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试后端API是否正常工作
"""
import requests
import json
import sys

def test_api():
    """测试后端API"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("测试后端API")
    print("=" * 60)
    
    # 测试1: province-amounts API
    print("\n[1] 测试 /api/province-amounts API...")
    try:
        response = requests.get(f"{base_url}/api/province-amounts?botnet_type=ramnit", timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'ramnit' in data:
                provinces = data['ramnit']
                print(f"✓ 成功获取 {len(provinces)} 个省份的数据")
                
                # 显示前5个省份
                print("\n前5个省份:")
                for i, prov in enumerate(provinces[:5]):
                    print(f"  {i+1}. {prov['province']}: {prov['amount']} 个节点")
                
                # 检查是否有"新疆"
                xinjiang = [p for p in provinces if '新疆' in p['province']]
                if xinjiang:
                    print(f"\n✓ 找到新疆数据: {xinjiang[0]}")
                else:
                    print("\n⚠️ 没有找到新疆数据")
                
                # 检查是否有"广西"
                guangxi = [p for p in provinces if '广西' in p['province']]
                if guangxi:
                    print(f"✓ 找到广西数据: {guangxi[0]}")
                else:
                    print("⚠️ 没有找到广西数据")
                
                # 检查是否有"台湾"
                taiwan = [p for p in provinces if '台湾' in p['province']]
                if taiwan:
                    print(f"✓ 找到台湾数据: {taiwan[0]}")
                else:
                    print("⚠️ 没有找到台湾数据")
                
                # 检查是否有不规范的命名
                irregular = [p for p in provinces if '自治区' in p['province'] or '中国' in p['province']]
                if irregular:
                    print(f"\n❌ 发现不规范的省份名称:")
                    for p in irregular:
                        print(f"  - {p['province']}: {p['amount']}")
                else:
                    print("\n✓ 所有省份名称已规范化")
            else:
                print("❌ 响应格式错误，缺少 'ramnit' 字段")
                print(f"响应内容: {data}")
        else:
            print(f"❌ API返回错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务")
        print("   请确保后端服务正在运行: python main.py")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试2: node-stats API
    print("\n[2] 测试 /api/node-stats/ramnit API...")
    try:
        response = requests.get(f"{base_url}/api/node-stats/ramnit", timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                stats = data['data']
                print(f"✓ 总节点数: {stats.get('total_nodes', 0)}")
                print(f"✓ 在线节点: {stats.get('active_nodes', 0)}")
                
                country_dist = stats.get('country_distribution', {})
                print(f"\n国家分布 (共{len(country_dist)}个国家):")
                for i, (country, count) in enumerate(list(country_dist.items())[:5]):
                    print(f"  {i+1}. {country}: {count}")
                
                # 检查是否有"台湾"（不是"中国台湾"）
                if '台湾' in country_dist and '中国台湾' not in country_dist:
                    print(f"\n✓ 台湾命名已统一: {country_dist['台湾']}")
                elif '中国台湾' in country_dist:
                    print(f"\n❌ 仍然使用'中国台湾': {country_dist['中国台湾']}")
                
            else:
                print("❌ 响应格式错误")
        else:
            print(f"❌ API返回错误: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("API测试完成")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
