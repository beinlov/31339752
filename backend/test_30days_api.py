"""
测试30天API数据
"""
import requests

def test_30days_api():
    url = "http://localhost:8000/api/node-count-history/ramnit?days=30"
    
    try:
        print(f"测试API: {url}")
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n返回数据条数: {len(data)}")
            print("\n前3条数据:")
            for item in data[:3]:
                print(f"  日期: {item['timestamp']}, 中国: {item['china_count']}, 全球: {item['global_count']}")
            print("\n后3条数据:")
            for item in data[-3:]:
                print(f"  日期: {item['timestamp']}, 中国: {item['china_count']}, 全球: {item['global_count']}")
        else:
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_30days_api()
