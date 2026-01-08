"""完整的API性能测试"""
import requests
import time
import json

BASE_URL = 'http://localhost:8000'
BOTNET_TYPE = 'ramnit'

def test_api_endpoint(name, url, params=None):
    """测试单个API端点"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    if params:
        print(f"Params: {params}")
    print('-'*60)
    
    try:
        start = time.time()
        response = requests.get(url, params=params, timeout=30)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            
            # 分析响应
            print(f"[OK] Status: {response.status_code}")
            print(f"[OK] Response time: {elapsed:.3f}s")
            print(f"[OK] Response size: {len(response.content)} bytes")
            
            # 显示关键数据
            if 'data' in data:
                data_obj = data['data']
                if isinstance(data_obj, dict):
                    print(f"[OK] Data keys: {list(data_obj.keys())[:5]}")
                    
                    # 显示一些统计信息
                    if 'total_nodes' in data_obj:
                        print(f"  - total_nodes: {data_obj['total_nodes']}")
                    if 'nodes' in data_obj:
                        print(f"  - nodes count: {len(data_obj['nodes'])}")
                    if 'total_count' in data_obj:
                        print(f"  - total_count: {data_obj['total_count']}")
                    if 'provinceDistribution' in data_obj:
                        prov_count = len(data_obj['provinceDistribution'])
                        print(f"  - provinces: {prov_count}")
                        # 显示前3个省份
                        for i, (prov, count) in enumerate(list(data_obj['provinceDistribution'].items())[:3], 1):
                            print(f"    {i}. {prov}: {count}")
            
            # 性能评估
            if elapsed < 1:
                print("[EXCELLENT] Performance: <1s")
            elif elapsed < 3:
                print("[GOOD] Performance: 1-3s")
            elif elapsed < 5:
                print("[ACCEPTABLE] Performance: 3-5s")
            else:
                print("[SLOW] Performance: >5s")
            
            return True, elapsed
        else:
            print(f"[ERROR] HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False, 0
            
    except requests.exceptions.Timeout:
        print("[ERROR] REQUEST TIMEOUT (>30s)")
        return False, 30
    except requests.exceptions.ConnectionError:
        print("[ERROR] CONNECTION ERROR - Backend not running?")
        return False, 0
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False, 0

# 运行测试
print("="*60)
print("API Performance Test Suite")
print("="*60)

results = {}

# 测试1: 节点统计接口
success, time1 = test_api_endpoint(
    "Node Statistics",
    f"{BASE_URL}/api/node-stats/{BOTNET_TYPE}"
)
results['node-stats'] = (success, time1)

# 测试2: 节点详情接口（第1页）
success, time2 = test_api_endpoint(
    "Node Details (Page 1)",
    f"{BASE_URL}/api/node-details",
    params={'botnet_type': BOTNET_TYPE, 'page': 1, 'page_size': 100}
)
results['node-details-p1'] = (success, time2)

# 测试3: 节点详情接口（第10页）
success, time3 = test_api_endpoint(
    "Node Details (Page 10)",
    f"{BASE_URL}/api/node-details",
    params={'botnet_type': BOTNET_TYPE, 'page': 10, 'page_size': 100}
)
results['node-details-p10'] = (success, time3)

# 测试4: 带过滤条件的查询
success, time4 = test_api_endpoint(
    "Node Details (Filtered by status)",
    f"{BASE_URL}/api/node-details",
    params={'botnet_type': BOTNET_TYPE, 'page': 1, 'page_size': 100, 'status': 'active'}
)
results['node-details-filtered'] = (success, time4)

# 汇总结果
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)

total_tests = len(results)
passed_tests = sum(1 for success, _ in results.values() if success)
total_time = sum(t for _, t in results.values())

print(f"Tests passed: {passed_tests}/{total_tests}")
print(f"Total time: {total_time:.3f}s")
print(f"Average time: {total_time/total_tests:.3f}s")

print("\nDetailed results:")
for name, (success, elapsed) in results.items():
    status = "[PASS]" if success else "[FAIL]"
    print(f"  {status} {name:30s} {elapsed:6.3f}s")

if passed_tests == total_tests and total_time < 20:
    print("\n[OK] ALL TESTS PASSED - API is working correctly!")
else:
    print("\n[WARNING] Some tests failed or performance is poor")

print("="*60)
