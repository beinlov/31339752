#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动修复缺失的通信记录（无需交互）
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入修复函数
from fix_missing_communications import fix_missing_communications

if __name__ == '__main__':
    botnet_type = sys.argv[1] if len(sys.argv) > 1 else 'test'
    
    print("=" * 80)
    print(f"自动修复 {botnet_type} 僵尸网络的缺失通信记录")
    print("=" * 80)
    
    # 直接执行修复（dry_run=False）
    fix_missing_communications(botnet_type, dry_run=False)
    
    print("\n修复完成!")
