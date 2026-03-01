#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查C2服务器的数据量
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

def check_c2_data():
    """检查C2端有多少数据"""
    
    api_key = 'KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4'
    base_url = 'http://localhost:8888'
    
    print("="*60)
    print("检查C2服务器数据量")
    print("="*60)
    
    # 测试不同的limit值
    for limit in [10, 100, 1000, 5000]:
        url = f'{base_url}/api/pull'
        params = {
            'limit': limit,
            'confirm': 'false'
        }
        headers = {
            'X-API-Key': api_key
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    records = data.get('data', [])
                    print(f"\nlimit={limit:5d} -> 返回数据: {len(records):5d} 条")
                    
                    if len(records) < limit:
                        print(f"  ⚠️  C2端实际数据不足{limit}条")
                else:
                    print(f"\nlimit={limit} -> 错误: {data.get('message')}")
            else:
                print(f"\nlimit={limit} -> HTTP {response.status_code}")
                
        except Exception as e:
            print(f"\nlimit={limit} -> 异常: {e}")
    
    print("\n" + "="*60)
    print("建议:")
    print("1. 如果所有limit都返回相同数量，说明C2端实际数据就这么多")
    print("2. 如果返回数量随limit增加，说明配置生效了")
    print("3. 请确保C2服务器有足够的测试数据")
    print("="*60)

if __name__ == '__main__':
    check_c2_data()
