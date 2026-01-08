"""测试API返回的编码"""
import requests
import json

try:
    # 测试统计接口
    response = requests.get('http://localhost:8000/api/node-stats/ramnit', timeout=10)
    
    if response.status_code == 200:
        # 获取原始字节
        raw_bytes = response.content
        print("Raw response (first 500 bytes):")
        print(raw_bytes[:500])
        print("\n" + "=" * 80)
        
        # 解析JSON
        data = response.json()
        
        print("\nParsed JSON structure:")
        print(f"Keys: {list(data.keys())}")
        
        if 'data' in data:
            data_keys = list(data['data'].keys())
            print(f"Data keys: {data_keys}")
            
            # 检查省份分布
            if 'provinceDistribution' in data['data']:
                provinces = data['data']['provinceDistribution']
                print(f"\nProvince distribution ({len(provinces)} provinces):")
                for i, (prov, count) in enumerate(list(provinces.items())[:5], 1):
                    # 打印省份名的编码信息
                    prov_bytes = prov.encode('utf-8')
                    print(f"  {i}. '{prov}' (UTF-8 bytes: {prov_bytes[:30]}...): {count}")
            
            # 检查国家分布
            if 'countryDistribution' in data['data']:
                countries = data['data']['countryDistribution']
                print(f"\nCountry distribution ({len(countries)} countries):")
                for i, (country, count) in enumerate(list(countries.items())[:5], 1):
                    country_bytes = country.encode('utf-8')
                    print(f"  {i}. '{country}' (UTF-8 bytes: {country_bytes}): {count}")
        
        print("\nOK: API response received successfully!")
        print("If province/country names look correct above, encoding is fine.")
        
    else:
        print(f"Error: HTTP {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to backend")
    print("Make sure backend is running: python main.py")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
