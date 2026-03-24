import requests
import json

url = "http://localhost:8000/api/active-botnet-communications?botnet_type=utg_q_008"

print(f"Testing API: {url}\n")

try:
    response = requests.get(url)
    data = response.json()
    
    print(f"Status code: {response.status_code}")
    print(f"Number of records: {len(data)}\n")
    
    if data:
        print("First record:")
        print(json.dumps(data[0], indent=2, ensure_ascii=False))
        
        print("\nKeys in first record:")
        print(list(data[0].keys()))
        
        print("\nChecking province and city:")
        print(f"  'province' in keys: {'province' in data[0]}")
        print(f"  'city' in keys: {'city' in data[0]}")
        
        if 'province' in data[0]:
            print(f"  province value: {data[0]['province']}")
        if 'city' in data[0]:
            print(f"  city value: {data[0]['city']}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
