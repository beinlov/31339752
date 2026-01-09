#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP查询性能测试脚本
测试1000个IP查询需要多少时间
"""

import asyncio
import time
import random
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from ip_location.ip_query import ip_query


async def test_single_ip():
    """测试单个IP查询"""
    print("=" * 60)
    print("测试单个IP查询")
    print("=" * 60)
    
    ip = '171.34.246.78'
    start = time.time()
    ip_info = await ip_query(ip)
    elapsed = time.time() - start
    
    print(f"IP: {ip}")
    print(f"结果: {ip_info}")
    print(f"耗时: {elapsed:.4f}秒")
    print()


async def test_batch_ips(count=1000):
    """测试批量IP查询性能"""
    print("=" * 60)
    print(f"测试批量IP查询性能 - {count} 个IP")
    print("=" * 60)
    
    # 生成随机IP
    test_ips = []
    for _ in range(count):
        ip = f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        test_ips.append(ip)
    
    print(f"[OK] 生成了 {len(test_ips)} 个测试IP")
    print(f"  示例: {test_ips[:5]}")
    print()
    
    # 方式1: 逐个查询（串行）
    print("【方式1】逐个查询（串行）")
    print("-" * 60)
    start = time.time()
    success = 0
    errors = 0
    
    for ip in test_ips:
        try:
            result = await ip_query(ip)
            if result and result.get('country'):
                success += 1
        except Exception as e:
            errors += 1
    
    sync_time = time.time() - start
    print(f"  [OK] 耗时: {sync_time:.2f}秒")
    print(f"  [OK] 成功: {success}/{count}")
    print(f"  [OK] 失败: {errors}")
    print(f"  [OK] 速度: {count/sync_time:.0f} 个/秒")
    print()
    
    # 方式2: 并发查询（异步批量）
    print("【方式2】并发查询（异步批量）")
    print("-" * 60)
    start = time.time()
    
    tasks = [ip_query(ip) for ip in test_ips]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    async_time = time.time() - start
    success = sum(1 for r in results if isinstance(r, dict) and r.get('country'))
    errors = sum(1 for r in results if isinstance(r, Exception))
    
    print(f"  [OK] 耗时: {async_time:.2f}秒")
    print(f"  [OK] 成功: {success}/{count}")
    print(f"  [OK] 失败: {errors}")
    print(f"  [OK] 速度: {count/async_time:.0f} 个/秒")
    print()
    
    # 性能对比
    print("=" * 60)
    print("性能对比")
    print("=" * 60)
    print(f"串行查询: {sync_time:.2f}秒 ({count/sync_time:.0f} 个/秒)")
    print(f"并发查询: {async_time:.2f}秒 ({count/async_time:.0f} 个/秒)")
    
    if sync_time > async_time:
        speedup = sync_time / async_time
        print(f"[+] 并发提升: {speedup:.1f}x")
    else:
        print(f"[-] 并发未提升（可能是I/O限制）")
    print()
    
    # 估算Worker中的IP增强时间
    print("=" * 60)
    print("估算Worker中的实际性能")
    print("=" * 60)
    
    # Worker中使用的是串行查询，因为它是同步处理每个IP
    estimated_ip_time = sync_time
    estimated_db_write = 1.0  # 优化后的数据库写入时间
    estimated_total = estimated_ip_time + estimated_db_write + 1  # 加上其他开销
    
    print(f"1000个IP查询耗时: ~{estimated_ip_time:.2f}秒")
    print(f"数据库写入耗时: ~{estimated_db_write:.2f}秒")
    print(f"其他开销: ~1秒")
    print(f"─" * 60)
    print(f"Worker总耗时预计: ~{estimated_total:.2f}秒")
    print()
    
    # 与实际Worker日志对比
    print("=" * 60)
    print("与实际Worker性能对比")
    print("=" * 60)
    print(f"实际Worker耗时: 245.77秒 (优化前)")
    print(f"  - IP增强: ~53秒")
    print(f"  - 数据库写入: ~192秒 (executemany的问题)")
    print()
    print(f"优化后预计Worker耗时: ~{estimated_total:.2f}秒")
    print(f"  - IP增强: ~{estimated_ip_time:.2f}秒")
    print(f"  - 数据库写入: ~1秒 (使用批量INSERT)")
    print()
    if estimated_total < 245.77:
        improvement = 245.77 / estimated_total
        print(f"[+] 预期性能提升: {improvement:.1f}x")
    print()
    
    # 如果IP查询仍然很慢
    if estimated_ip_time > 10:
        print("[!] 警告：IP查询速度较慢")
        print(f"   1000个IP需要 {estimated_ip_time:.2f}秒")
        print(f"   平均每个IP: {estimated_ip_time/count*1000:.2f}毫秒")
        print()
        print("可能的优化方向:")
        print("  1. 检查AWDB文件是否在SSD上")
        print("  2. 增加内存缓存")
        print("  3. 使用更快的IP数据库（如MaxMind GeoIP2）")
        print("  4. 考虑预加载数据库到内存")
        print()


async def main():
    """主函数"""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "IP查询性能测试工具" + " " * 22 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    # 测试单个IP
    await test_single_ip()
    
    # 测试1000个IP的性能
    await test_batch_ips(1000)
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
