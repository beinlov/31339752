"""快速测试API是否正常"""
import requests

try:
    # 测试节点详情接口
    response = requests.get('http://localhost:8000/api/node-details', params={
        'botnet_type': 'asruex',
        'page': 1,
        'page_size': 10
    }, timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        print("✓ API响应成功")
        print(f"  状态码: {response.status_code}")
        print(f"  总数: {data.get('data', {}).get('total', 0)}")
        print(f"  节点数: {len(data.get('data', {}).get('nodes', []))}")
        
        if data.get('data', {}).get('nodes'):
            node = data['data']['nodes'][0]
            print(f"  示例节点: IP={node.get('ip')}, active_time={node.get('active_time')}, last_active={node.get('last_active')}")
        print("\n✓ API工作正常！")
    else:
        print(f"✗ API错误: {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("✗ 无法连接到后端服务")
    print("  请确保后端服务正在运行: python main.py")
except Exception as e:
    print(f"✗ 错误: {e}")
