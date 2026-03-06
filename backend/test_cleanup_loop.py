#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试清除后的循环更新逻辑"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import threading
import time
from router.cleanup import update_timeset_after_cleanup

def update_loop(botnet_name):
    end_time = time.time() + 60  # 1分钟后停止
    update_count = 0
    while time.time() < end_time:
        try:
            update_timeset_after_cleanup(botnet_name)
            update_count += 1
            print(f"[{botnet_name}] 第 {update_count} 次更新完成，剩余时间: {int(end_time - time.time())} 秒")
        except Exception as e:
            print(f"[{botnet_name}] 循环更新失败: {e}")
        time.sleep(5)  # 每5秒更新一次
    print(f"[{botnet_name}] 循环更新结束，共执行 {update_count} 次")

print("启动后台循环更新 utg_q_008（1分钟）...")
thread = threading.Thread(target=update_loop, args=('utg_q_008',), daemon=True)
thread.start()
print("后台线程已启动，等待完成...")
thread.join()  # 等待线程完成
print("测试完成！")
