#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试API返回数据
"""
import requests
import json
import sys
import io

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def debug_api():
    """调试API"""
    print("=" * 80)
    print("调试 node-stats API")
    print("=" * 80)
    
    url = 'http://localhost:8000/api/node-stats/ramnit'
    
    try:
        print(f"\n请求URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        
        print(f"状态码: {response.status_code}")
        print(f"\n完整响应:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        data = response.json()
        
        # 检查所有字段
        print(f"\n数据字段检查:")
        if 'data' in data:
            for key in data['data'].keys():
                print(f"  ✓ {key}")
            
            # 特别检查 province_distribution
            if 'province_distribution' in data['data']:
                province_dist = data['data']['province_distribution']
                print(f"\n✓ province_distribution 存在")
                print(f"  类型: {type(province_dist)}")
                print(f"  长度: {len(province_dist)}")
                if province_dist:
                    print(f"  示例数据:")
                    for i, (k, v) in enumerate(list(province_dist.items())[:5]):
                        print(f"    {k}: {v}")
            else:
                print(f"\n❌ province_distribution 不存在")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_api()
