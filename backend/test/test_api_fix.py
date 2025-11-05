#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API修复是否成功
"""
import requests
import json

API_BASE = "http://localhost:8000"

def test_api(endpoint, name):
    """测试API端点"""
    url = f"{API_BASE}{endpoint}"
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功！")
            print(f"响应数据预览: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
            return True
        else:
            print(f"❌ 失败！")
            print(f"错误信息: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 连接失败！请确保后端服务正在运行。")
        return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  僵尸网络API修复测试")
    print("="*60)
    
    tests = [
        ("/api/province-amounts", "省份僵尸网络数量统计"),
        ("/api/world-amounts", "全球僵尸网络数量统计"),
        ("/api/user-events", "用户事件日志"),
        ("/api/anomaly-reports", "异常报告"),
        ("/api/upload-status", "上传接口状态"),
    ]
    
    results = []
    for endpoint, name in tests:
        result = test_api(endpoint, name)
        results.append((name, result))
    
    # 总结
    print("\n" + "="*60)
    print("  测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！前端应该可以正常显示数据了。")
    else:
        print("\n⚠️ 部分测试失败，请检查：")
        print("1. 后端服务是否正在运行？")
        print("2. 数据库密码配置是否正确？")
        print("3. 数据库表是否存在？")
        print("\n运行以下命令检查数据库：")
        print("  cd backend")
        print("  python test_db.py")

if __name__ == "__main__":
    main()



