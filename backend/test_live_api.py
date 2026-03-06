#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试实际运行中的 API 返回数据"""
import requests
import json

try:
    url = "http://localhost:8000/api/active-botnet-communications?botnet_type=utg_q_008"
    print("=" * 70)
    print(f"测试 API: {url}")
    print("=" * 70)
    print()
    
    response = requests.get(url)
    print(f"状态码: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print("返回数据类型:", type(data))
        print("数据数量:", len(data) if isinstance(data, list) else "N/A")
        print()
        
        if isinstance(data, list) and len(data) > 0:
            print("前2条数据:")
            for i, item in enumerate(data[:2], 1):
                print(f"\n记录 {i}:")
                print(json.dumps(item, indent=2, ensure_ascii=False))
                print(f"  是否有 status 字段: {'status' in item}")
                if 'status' in item:
                    print(f"  status 值: '{item['status']}'")
        else:
            print("数据为空或非列表格式")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"请求失败: {response.text}")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
