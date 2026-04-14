#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查后端运行状态和代码版本"""
import requests
import sys

print("=" * 70)
print("后端服务状态检查")
print("=" * 70)
print()

# 检查服务是否运行
try:
    url = "http://localhost:8000/api/active-botnet-communications?botnet_type=utg_q_008"
    print("1. 测试 API 连接...")
    response = requests.get(url, timeout=5)
    print(f"   ✓ 服务运行中 (状态码: {response.status_code})")
    
    data = response.json()
    print(f"\n2. API 返回数据检查:")
    print(f"   - 数据类型: {type(data)}")
    print(f"   - 记录数量: {len(data) if isinstance(data, list) else 'N/A'}")
    
    if isinstance(data, list) and len(data) > 0:
        first_record = data[0]
        print(f"   - 第一条记录字段: {list(first_record.keys())}")
        print(f"   - 是否有 status 字段: {'✓ 是' if 'status' in first_record else '✗ 否'}")
        
        if 'status' not in first_record:
            print("\n❌ 问题确认: API 返回数据缺少 status 字段")
            print("\n可能原因:")
            print("1. 后端代码没有真正重新加载")
            print("2. uvicorn 使用了旧的 .pyc 缓存")
            print("3. 有多个 Python 进程在运行")
        else:
            print(f"\n✓ status 字段存在，值为: {first_record['status']}")
    
    print("\n" + "=" * 70)
    print("请查看后端服务窗口，确认是否有以下日志:")
    print("[ACTIVE-BOTNET-COMM] Returned X records")
    print("[ACTIVE-BOTNET-COMM] Keys: [...]")
    print("=" * 70)
    
except requests.exceptions.ConnectionError:
    print("✗ 无法连接到后端服务 (http://localhost:8000)")
    print("  后端服务可能没有运行")
    sys.exit(1)
except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
