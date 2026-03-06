#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试智能更新逻辑：只更新今天和补充缺失日期"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from router.cleanup import update_timeset_after_cleanup

print("=" * 70)
print("测试智能 Timeset 更新逻辑")
print("=" * 70)
print("\n新逻辑说明：")
print("1. 只更新今天的数据（即使 timeset 表中已存在今天的条目）")
print("2. 补充一个月内缺失的日期（不存在的日期会被创建）")
print("3. 不修改已存在的历史数据（非今天的日期如果已存在则跳过）")
print("\n开始更新 utg_q_008 的 timeset...\n")

result = update_timeset_after_cleanup('utg_q_008')

print("\n" + "=" * 70)
print(f"更新结果: {'成功' if result else '失败'}")
print("=" * 70)
print("\n提示：查看日志了解哪些日期被更新，哪些日期被跳过")
