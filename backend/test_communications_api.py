# -*- coding: utf-8 -*-
"""
测试 /api/active-botnet-communications API 返回的数据
"""
import requests

# 测试API
url = "http://localhost:8000/api/active-botnet-communications?botnet_type=utg_q_008"

print(f"请求URL: {url}\n")

try:
    response = requests.get(url)
    data = response.json()
    
    print(f"状态码: {response.status_code}")
    print(f"返回数据数量: {len(data)}\n")
    
    if data:
        print("第一条数据:")
        first_item = data[0]
        for key, value in first_item.items():
            print(f"  {key}: {value}")
        
        print("\n字段列表:")
        print(f"  {list(first_item.keys())}")
        
        # 检查是否有 province 和 city
        has_province = 'province' in first_item
        has_city = 'city' in first_item
        
        print(f"\n字段检查:")
        print(f"  有 province 字段: {has_province}")
        print(f"  有 city 字段: {has_city}")
        
        if has_province:
            print(f"  province 值: '{first_item['province']}'")
        if has_city:
            print(f"  city 值: '{first_item['city']}'")
            
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
