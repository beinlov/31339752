"""
测试一键清除API是否正常返回数据
"""
import requests
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# 假设后端运行在本地
API_URL = "http://localhost:8000/api/cleanup/check-permissions"

print("=" * 70)
print("测试一键清除API")
print("=" * 70)

try:
    # 不需要token进行测试（如果需要，从浏览器复制）
    # 或者先登录获取token
    response = requests.get(API_URL)
    
    print(f"\n状态码: {response.status_code}")
    print(f"\n响应数据:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    if response.status_code == 200:
        data = response.json()
        if data.get('status') == 'success':
            botnets = data.get('data', {}).get('botnets', [])
            print(f"\n✅ API正常工作")
            print(f"返回 {len(botnets)} 个僵网:")
            for botnet in botnets:
                print(f"  - {botnet.get('botnet_name')}: {botnet.get('display_name')} "
                      f"(权限: {'✅' if botnet.get('has_c2_permission') else '❌'})")
            
            # 检查 utg_q_008
            utg = next((b for b in botnets if b.get('botnet_name') == 'utg_q_008'), None)
            if utg:
                print(f"\n✅ 找到 utg_q_008:")
                print(f"   botnet_name: {utg.get('botnet_name')}")
                print(f"   display_name: {utg.get('display_name')}")
                print(f"   has_c2_permission: {utg.get('has_c2_permission')}")
                print(f"   c2_ip: {utg.get('c2_ip')}")
            else:
                print(f"\n❌ 未找到 utg_q_008")
                print(f"   可用的僵网名称: {[b.get('botnet_name') for b in botnets]}")
        else:
            print(f"\n❌ API返回失败状态: {data.get('status')}")
    else:
        print(f"\n❌ HTTP错误: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ 无法连接到后端服务器")
    print("   请确保后端服务正在运行（通常是 http://localhost:8000）")
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
