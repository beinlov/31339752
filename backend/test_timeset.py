#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from router.cleanup import update_timeset_after_cleanup

print("测试 utg_q_008 的 timeset 更新...")
result = update_timeset_after_cleanup('utg_q_008')
print(f"更新结果: {'成功' if result else '失败'}")
