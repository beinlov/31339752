"""
Script to test the server API endpoint
"""
import requests
import json

def test_api():
    """Test the /api/servers endpoint"""
    try:
        # Test the servers endpoint
        url = "http://localhost:8000/api/server/servers"
        params = {"page": 1, "page_size": 10}
        
        print("=== Testing Server API ===")
        print(f"URL: {url}")
        print(f"Params: {params}\n")
        
        response = requests.get(url, params=params)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n=== Response Data ===")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Check if servers have node_count
            if 'data' in data and 'servers' in data['data']:
                servers = data['data']['servers']
                print(f"\n=== Server Node Counts ===")
                for server in servers:
                    print(f"\nServer ID {server['id']}:")
                    print(f"  Botnet Name: {server.get('botnet_name', 'N/A')}")
                    print(f"  Node Count: {server.get('node_count', 'N/A')}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the API server at http://localhost:8000")
        print("Please make sure the backend server is running.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_api()
