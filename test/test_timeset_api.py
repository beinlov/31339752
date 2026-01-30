"""
测试timeset API是否正常返回数据
"""
import requests

def test_api():
    # 测试ramnit僵尸网络的近7天数据
    url = "http://localhost:8000/api/node-count-history/ramnit?days=7"
    
    try:
        print(f"测试API: {url}")
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n返回数据条数: {len(data)}")
            print("\n数据示例:")
            for item in data[:3]:  # 显示前3条
                print(f"  日期: {item['timestamp']}, 中国: {item['china_count']}, 全球: {item['global_count']}")
            
            if len(data) == 0:
                print("\n[警告] API返回空数组，需要先执行 manual_record_today.py 记录数据")
        else:
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_api()
