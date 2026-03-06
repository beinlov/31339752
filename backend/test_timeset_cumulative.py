#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试累加模式的 timeset 更新逻辑"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from router.cleanup import update_timeset_after_cleanup

print("=" * 60)
print("测试累加模式的 timeset 更新逻辑")
print("=" * 60)
print("\n当前逻辑：")
print("- 3月4日的 timeset = 统计所有 updated_at <= 3月4日的节点")
print("- 3月5日的 timeset = 统计所有 updated_at <= 3月5日的节点（累加）")
print("\n开始更新 utg_q_008 的 timeset...\n")

result = update_timeset_after_cleanup('utg_q_008')

print("\n" + "=" * 60)
print(f"更新结果: {'成功' if result else '失败'}")
print("=" * 60)
