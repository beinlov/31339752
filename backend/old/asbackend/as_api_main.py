import requests
import time

# 启动 Clean 模式服务器（只执行一次）
try:
    res1 = requests.get('http://127.0.0.1:5000/start-clean-server')
    print("启动服务器：", res1.status_code, res1.json())
except Exception as e:
    print("[错误] 启动服务器失败：", str(e))

# 每 5 秒执行更新 + 查询操作
while True:
    try:
        # 1. 调用处理 clean1 日志并更新数据库
        res2 = requests.get('http://127.0.0.1:5000/process-clean1-ips')
        data = res2.json()
        print("\n处理日志并更新数据库：", res2.status_code, data)

        # 2. 获取数据库清除记录
        res = requests.get('http://127.0.0.1:5000/get-clean-records')
        records = res.json()
        print("查询清除记录：", res.status_code)
        for r in records.get("records", []):
            print(f"  IP: {r['ip']} | 时间: {r['clean_time']} | 操作: {r['operate']}")

    except Exception as e:
        print("[错误] 请求失败：", str(e))

    # 3. 等待 5 秒后下一轮
    time.sleep(5)
