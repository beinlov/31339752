#!/usr/bin/env python3
"""
背压控制测试脚本 - 模拟不同场景下的缓存控制
"""

import time
from cache_backpressure import BackpressureController


def test_scenario_1():
    """场景1: 平台正常拉取（缓存保持在低水位）"""
    print("\n" + "="*60)
    print("场景1: 平台正常拉取")
    print("="*60)
    
    config = {
        'max_cached_records': 10000,
        'high_watermark': 8000,
        'low_watermark': 2000,
        'read_batch_size': 5000,
        'adaptive_read': True
    }
    
    controller = BackpressureController(config)
    cache_size = 1500
    
    for cycle in range(1, 11):
        read_size, reason = controller.calculate_read_size(cache_size)
        print(f"\n周期 {cycle}:")
        print(f"  缓存量: {cache_size} 条")
        print(f"  决策: {reason}")
        print(f"  读取: {read_size} 条")
        
        # 模拟：读取后增加，平台拉取后减少
        cache_size += read_size
        pulled = 4500  # 平台拉取
        cache_size -= pulled
        print(f"  平台拉取: {pulled} 条")
        print(f"  新缓存量: {cache_size} 条")
    
    controller.log_stats()


def test_scenario_2():
    """场景2: 平台未拉取（缓存增长触发背压）"""
    print("\n" + "="*60)
    print("场景2: 平台未拉取（背压触发）")
    print("="*60)
    
    config = {
        'max_cached_records': 10000,
        'high_watermark': 8000,
        'low_watermark': 2000,
        'read_batch_size': 5000,
        'adaptive_read': True
    }
    
    controller = BackpressureController(config)
    cache_size = 1500
    
    for cycle in range(1, 11):
        read_size, reason = controller.calculate_read_size(cache_size)
        print(f"\n周期 {cycle}:")
        print(f"  缓存量: {cache_size} 条")
        print(f"  决策: {reason}")
        print(f"  读取: {read_size} 条")
        
        # 模拟：只读取，不拉取
        cache_size += read_size
        print(f"  平台拉取: 0 条（未拉取）")
        print(f"  新缓存量: {cache_size} 条")
        
        # 模拟在第7周期平台开始拉取
        if cycle == 7:
            print(f"  🔄 平台开始拉取！")
            pulled = 6000
            cache_size -= pulled
            print(f"  平台拉取: {pulled} 条")
            print(f"  恢复后缓存量: {cache_size} 条")
    
    controller.log_stats()


def test_scenario_3():
    """场景3: 平台拉取速度不匹配（节流效果）"""
    print("\n" + "="*60)
    print("场景3: 平台拉取速度慢（节流调整）")
    print("="*60)
    
    config = {
        'max_cached_records': 10000,
        'high_watermark': 8000,
        'low_watermark': 2000,
        'read_batch_size': 5000,
        'adaptive_read': True
    }
    
    controller = BackpressureController(config)
    cache_size = 1500
    
    for cycle in range(1, 16):
        read_size, reason = controller.calculate_read_size(cache_size)
        print(f"\n周期 {cycle}:")
        print(f"  缓存量: {cache_size} 条")
        print(f"  决策: {reason}")
        print(f"  读取: {read_size} 条")
        
        # 模拟：读取量大于拉取量
        cache_size += read_size
        pulled = 2000  # 平台每次只拉取2000条
        cache_size = max(0, cache_size - pulled)
        print(f"  平台拉取: {pulled} 条")
        print(f"  新缓存量: {cache_size} 条")
    
    controller.log_stats()


def test_comparison():
    """对比测试：有背压 vs 无背压"""
    print("\n" + "="*60)
    print("对比测试: 有背压 vs 无背压")
    print("="*60)
    
    # 无背压（固定读取）
    print("\n【无背压控制】")
    cache_no_bp = 1500
    for cycle in range(1, 11):
        read_size = 5000  # 固定读取
        cache_no_bp += read_size
        pulled = 0  # 不拉取
        print(f"周期 {cycle}: 缓存 {cache_no_bp} 条 (读取 {read_size})")
    
    print(f"\n最终缓存: {cache_no_bp} 条 ❌ 无限增长！")
    
    # 有背压
    print("\n【有背压控制】")
    config = {
        'max_cached_records': 10000,
        'high_watermark': 8000,
        'low_watermark': 2000,
        'read_batch_size': 5000,
        'adaptive_read': True
    }
    controller = BackpressureController(config)
    cache_with_bp = 1500
    
    for cycle in range(1, 11):
        read_size, reason = controller.calculate_read_size(cache_with_bp)
        cache_with_bp += read_size
        pulled = 0  # 不拉取
        print(f"周期 {cycle}: 缓存 {cache_with_bp} 条 (读取 {read_size}, {reason})")
    
    print(f"\n最终缓存: {cache_with_bp} 条 ✅ 受控！")
    
    print("\n对比结果:")
    print(f"  无背压: {cache_no_bp} 条")
    print(f"  有背压: {cache_with_bp} 条")
    print(f"  节省内存: {cache_no_bp - cache_with_bp} 条 ({(1-cache_with_bp/cache_no_bp)*100:.1f}%)")


if __name__ == '__main__':
    print("\n" + "🔬 背压控制效果测试".center(60, "="))
    
    test_scenario_1()
    time.sleep(1)
    
    test_scenario_2()
    time.sleep(1)
    
    test_scenario_3()
    time.sleep(1)
    
    test_comparison()
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
