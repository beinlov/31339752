import requests
import json

API_BASE = "http://localhost:8000/api/suppression"

def test_get(name, url):
    print(f"\nTesting: {name}")
    print(f"URL: {url}")
    try:
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Response:", json.dumps(response.json(), indent=2, ensure_ascii=False))
            return True
        else:
            print("Error:", response.text)
            return False
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend! Please start: python main.py")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

print("="*60)
print("API Diagnostic Test")
print("="*60)

# Test 1: Get IP blacklist
test_get("Get IP Blacklist", f"{API_BASE}/blacklist/ip")

# Test 2: Get domain blacklist
test_get("Get Domain Blacklist", f"{API_BASE}/blacklist/domain")

# Test 3: Get packet loss policies
test_get("Get Packet Loss Policies", f"{API_BASE}/packet-loss")

# Test 4: Get tasks
test_get("Get Tasks", f"{API_BASE}/tasks")

# Test 5: Get logs
test_get("Get Logs", f"{API_BASE}/logs?limit=10")

print("\n" + "="*60)
print("If all tests show 'Status: 200', the backend is working!")
print("If you see connection errors, start backend: python main.py")
print("="*60)