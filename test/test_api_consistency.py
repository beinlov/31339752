#!/usr/bin/env python3
"""
测试三个接口的数据一致性
"""
import requests
import json

BASE_URL = "http://localhost:8000"
BOTNET_TYPE = "asruex"

print("=" * 100)
print("API 数据一致性测试")
print("=" * 100)

# 测试1: /api/botnet-distribution (图一的数据源)
print("\n【图一】展示处置平台 - /api/botnet-distribution")
print("-" * 100)
try:
    response = requests.get(f"{BASE_URL}/api/botnet-distribution")
    if response.status_code == 200:
        data = response.json()
        asruex_data = next((item for item in data if item['name'] == BOTNET_TYPE), None)
        if asruex_data:
            print(f"china_amount (全国数量):  {asruex_data['china_amount']:,}")
            print(f"global_amount (全球数量): {asruex_data['global_amount']:,}")
            print(f"\n💡 注意: global_amount 是 global_botnet 表的直接总和")
        else:
            print(f"未找到 {BOTNET_TYPE} 的数据")
    else:
        print(f"请求失败: {response.status_code}")
except Exception as e:
    print(f"请求异常: {e}")

# 测试2: /api/node-stats/{botnet_type} (图二、图三的数据源)
print("\n【图二、图三】后台管理系统 - /api/node-stats/{botnet_type}")
print("-" * 100)
try:
    response = requests.get(f"{BASE_URL}/api/node-stats/{BOTNET_TYPE}")
    if response.status_code == 200:
        result = response.json()
        data = result.get('data', {})
        
        print(f"total_nodes (总节点数):     {data.get('total_nodes', 0):,}")
        print(f"active_nodes (活跃节点):    {data.get('active_nodes', 0):,}")
        print(f"inactive_nodes (非活跃节点): {data.get('inactive_nodes', 0):,}")
        
        # 计算 country_distribution 的总和（图三显示的数据）
        country_dist = data.get('country_distribution', {})
        country_total = sum(country_dist.values())
        
        print(f"\ncountry_distribution 统计:")
        print(f"  国家数量: {len(country_dist)}")
        print(f"  节点总和: {country_total:,}")
        
        # 显示前10个国家
        print(f"\n  Top 10 国家分布:")
        sorted_countries = sorted(country_dist.items(), key=lambda x: x[1], reverse=True)[:10]
        for country, count in sorted_countries:
            print(f"    {country}: {count:,}")
        
        print(f"\n💡 计算方式: china_botnet 表 + global_botnet 表(非中国节点)")
        print(f"💡 数据来源: {data.get('data_source', 'unknown')}")
        
        # 验证数据一致性
        if country_total != data.get('total_nodes', 0):
            print(f"\n⚠️  数据不一致！")
            print(f"   total_nodes = {data.get('total_nodes', 0):,}")
            print(f"   country_distribution 总和 = {country_total:,}")
            print(f"   差异 = {abs(country_total - data.get('total_nodes', 0)):,}")
        else:
            print(f"\n✅ 数据一致: total_nodes = country_distribution 总和")
    else:
        print(f"请求失败: {response.status_code}")
except Exception as e:
    print(f"请求异常: {e}")

# 对比分析
print("\n" + "=" * 100)
print("对比分析")
print("=" * 100)

try:
    # 获取两个接口的数据
    resp1 = requests.get(f"{BASE_URL}/api/botnet-distribution")
    resp2 = requests.get(f"{BASE_URL}/api/node-stats/{BOTNET_TYPE}")
    
    if resp1.status_code == 200 and resp2.status_code == 200:
        data1 = next((item for item in resp1.json() if item['name'] == BOTNET_TYPE), None)
        data2 = resp2.json().get('data', {})
        
        if data1:
            print(f"\n接口1 (amount.py) - global_amount:        {data1['global_amount']:,}")
            print(f"接口2 (node.py) - total_nodes:            {data2.get('total_nodes', 0):,}")
            print(f"接口2 (node.py) - country_dist 总和:      {sum(data2.get('country_distribution', {}).values()):,}")
            
            diff1 = data1['global_amount'] - data2.get('total_nodes', 0)
            diff2 = sum(data2.get('country_distribution', {}).values()) - data2.get('total_nodes', 0)
            
            print(f"\n差异分析:")
            print(f"  global_amount - total_nodes = {diff1:,}")
            print(f"  country_dist总和 - total_nodes = {diff2:,}")
            
            if diff1 == 0 and diff2 == 0:
                print(f"\n✅ 三个数据源完全一致！")
            elif diff1 == 0:
                print(f"\n⚠️  图一和图二一致，但图三与它们相差 {abs(diff2)} 个节点")
            elif diff2 == 0:
                print(f"\n⚠️  图二和图三一致，但图一与它们相差 {abs(diff1)} 个节点")
            else:
                print(f"\n❌ 三个数据源都不一致！")
                print(f"   这与用户报告的问题一致：")
                print(f"   - 图一(global_amount)和图二(total_nodes)显示 116,090")
                print(f"   - 图三(country_dist)显示 116,108")
                print(f"   - 差异 18 个节点")

except Exception as e:
    print(f"对比分析异常: {e}")

print("\n" + "=" * 100)
