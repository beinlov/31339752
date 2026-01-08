"""测试通信记录API"""
import requests
import json

# 测试API
ip = "136.158.11.248"
botnet_type = "ramnit"

url = "http://localhost:8000/api/node-communications"
params = {
    'botnet_type': botnet_type,
    'ip': ip,
    'page': 1,
    'page_size': 10
}

print(f"Testing API: {url}")
print(f"Parameters: {json.dumps(params, indent=2)}")
print("="*60)

try:
    response = requests.get(url, params=params, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print("="*60)
    
    if response.status_code == 200:
        data = response.json()
        print("Response JSON:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("Error Response:")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to backend. Is it running?")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
