import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://43.99.37.118:443"
AUTH_TOKEN = "3@UNyeExV9HzHeJ!9HG$k4v3FaefwU2RZ%DbgX6wFSTT3^&YqjG&X#*HfT7Y4S5n"
SAFETY_CODE = "Mrcm3YsTNFyJQ685m@bL&nhm!8jyaP&sw9@qz^BJMKkqHh@rzV5GEptkxq9@3Z5e"

headers = {
    "X-Auth-Token": AUTH_TOKEN,
    "X-Safety-Code": SAFETY_CODE
}

# 查询状态
resp = requests.post(f"{BASE_URL}/admin/irc/status", headers=headers, verify=False)
print(resp.json())
