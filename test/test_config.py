#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试配置读取
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_config():
    """测试配置文件读取"""
    
    print("="*60)
    print("测试配置文件读取")
    print("="*60)
    
    try:
        from config import C2_ENDPOINTS, C2_PULL_INTERVAL_MINUTES
        
        print(f"\nC2_PULL_INTERVAL_MINUTES: {C2_PULL_INTERVAL_MINUTES} 分钟")
        print(f"\nC2_ENDPOINTS 数量: {len(C2_ENDPOINTS)}")
        
        for i, c2 in enumerate(C2_ENDPOINTS):
            print(f"\n端点 {i+1}:")
            print(f"  名称: {c2.get('name')}")
            print(f"  URL: {c2.get('url')}")
            print(f"  启用: {c2.get('enabled')}")
            print(f"  batch_size: {c2.get('batch_size')} ⬅️ 关键！")
            print(f"  pull_interval: {c2.get('pull_interval')} 秒")
            print(f"  timeout: {c2.get('timeout')}")
        
        print("\n" + "="*60)
        
        # 检查是否是预期值
        expected_batch_size = 5000
        expected_interval = 60
        
        actual_batch_size = C2_ENDPOINTS[0].get('batch_size')
        actual_interval = C2_ENDPOINTS[0].get('pull_interval')
        
        print("验证结果:")
        if actual_batch_size == expected_batch_size:
            print(f"✅ batch_size = {actual_batch_size} (正确)")
        else:
            print(f"❌ batch_size = {actual_batch_size} (期望 {expected_batch_size})")
            
        if actual_interval == expected_interval:
            print(f"✅ pull_interval = {actual_interval} (正确)")
        else:
            print(f"❌ pull_interval = {actual_interval} (期望 {expected_interval})")
        
        print("\n" + "="*60)
        
        if actual_batch_size != expected_batch_size:
            print("\n问题诊断:")
            print("1. config.py 文件是否保存了修改？")
            print("2. 是否在正确的 config.py 文件中修改？")
            print("   文件位置: backend/config.py")
            print("3. 修改的是 C2_ENDPOINTS[0]['batch_size'] 吗？")
            
    except Exception as e:
        print(f"\n❌ 配置读取失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_config()
