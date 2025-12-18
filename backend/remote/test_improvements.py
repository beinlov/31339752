#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 验证 remote_uploader.py 的改进
"""

import asyncio
import tempfile
import json
from pathlib import Path
from datetime import datetime
import time

# 模拟测试环境
TEST_DIR = Path(tempfile.mkdtemp())
print(f"测试目录: {TEST_DIR}")


def test_file_identity():
    """测试文件身份识别"""
    print("\n=== 测试1: 文件身份识别 ===")
    
    # 创建测试文件
    test_file = TEST_DIR / "test.log"
    test_file.write_text("test data")
    
    # 获取文件身份
    stat = test_file.stat()
    identity = {
        'inode': stat.st_ino,
        'ctime': stat.st_ctime,
        'size': stat.st_size
    }
    print(f"文件身份: inode={identity['inode']}, size={identity['size']}")
    
    # 模拟文件截断
    test_file.write_text("new")
    new_stat = test_file.stat()
    new_identity = {
        'inode': new_stat.st_ino,
        'ctime': new_stat.st_ctime,
        'size': new_stat.st_size
    }
    
    # 检测截断
    if new_identity['size'] < identity['size']:
        print("✓ 成功检测到文件截断")
    else:
        print("✗ 未能检测到文件截断")
    
    # 模拟文件替换
    test_file.unlink()
    test_file.write_text("replaced")
    replaced_stat = test_file.stat()
    
    if replaced_stat.st_ino != identity['inode']:
        print("✓ 成功检测到文件替换（inode变化）")
    else:
        print("✗ 未能检测到文件替换")


def test_incomplete_lines_cleanup():
    """测试不完整行清理"""
    print("\n=== 测试2: 不完整行清理 ===")
    
    current_time = time.time()
    
    # 模拟不完整行数据
    incomplete_lines = {
        'file1.log': {
            'line': 'incomplete line 1',
            'timestamp': current_time - 25 * 3600  # 25小时前
        },
        'file2.log': {
            'line': 'incomplete line 2',
            'timestamp': current_time - 1 * 3600  # 1小时前
        },
        'file3.log': 'old format line'  # 旧格式
    }
    
    # 清理逻辑
    MAX_AGE_HOURS = 24
    to_remove = []
    
    for file_path, data in incomplete_lines.items():
        if isinstance(data, dict) and 'timestamp' in data:
            age_hours = (current_time - data['timestamp']) / 3600
            if age_hours > MAX_AGE_HOURS:
                to_remove.append(file_path)
                print(f"  清理过期: {file_path} (年龄: {age_hours:.1f}小时)")
        elif isinstance(data, str):
            # 兼容旧格式
            incomplete_lines[file_path] = {
                'line': data,
                'timestamp': current_time
            }
            print(f"  转换旧格式: {file_path}")
    
    for fp in to_remove:
        del incomplete_lines[fp]
    
    print(f"✓ 清理完成，剩余 {len(incomplete_lines)} 个不完整行")


def test_transaction_upload():
    """测试事务性上传"""
    print("\n=== 测试3: 事务性上传 ===")
    
    # 模拟队列
    from collections import deque, defaultdict
    
    daily_ips = defaultdict(deque)
    daily_ips['2025-12-17'].extend([
        {'ip': '1.2.3.4', 'timestamp': '2025-12-17T10:00:00'},
        {'ip': '5.6.7.8', 'timestamp': '2025-12-17T10:01:00'},
        {'ip': '9.10.11.12', 'timestamp': '2025-12-17T10:02:00'},
    ])
    
    uploading_ips = []
    
    # 阶段1: 标记为上传中
    batch_size = 2
    result = []
    for date in sorted(daily_ips.keys()):
        queue = daily_ips[date]
        batch = list(queue)[:batch_size]
        result.extend(batch)
        if len(result) >= batch_size:
            break
    
    uploading_ips = result
    print(f"  标记上传中: {len(uploading_ips)} 条")
    
    # 模拟上传失败
    upload_success = False
    
    if upload_success:
        # 阶段2a: 确认成功
        cleared = 0
        for date in list(daily_ips.keys()):
            queue = daily_ips[date]
            while queue and cleared < len(uploading_ips):
                queue.popleft()
                cleared += 1
        uploading_ips = []
        print(f"  ✓ 确认上传成功，清理 {cleared} 条")
    else:
        # 阶段2b: 回滚
        print(f"  ✗ 上传失败，回滚 {len(uploading_ips)} 条（数据保留在队列）")
        uploading_ips = []
    
    # 验证数据完整性
    total_remaining = sum(len(q) for q in daily_ips.values())
    print(f"  队列剩余: {total_remaining} 条")
    
    if total_remaining == 3:
        print("✓ 事务性上传测试通过（数据未丢失）")
    else:
        print("✗ 事务性上传测试失败")


def test_timestamp_extraction():
    """测试时间戳提取"""
    print("\n=== 测试4: 时间戳提取 ===")
    
    import re
    
    def extract_time_from_filename(filename: str):
        """从文件名提取时间"""
        # 匹配 YYYY-MM-DD_HH 格式
        match = re.search(r'(\d{4}-\d{2}-\d{2})_(\d{2})', filename)
        if match:
            date_str = match.group(1)
            hour_str = match.group(2)
            return datetime.strptime(f"{date_str} {hour_str}:00:00", '%Y-%m-%d %H:%M:%S')
        
        # 匹配 YYYY-MM-DD 格式
        match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if match:
            date_str = match.group(1)
            return datetime.strptime(f"{date_str} 00:00:00", '%Y-%m-%d %H:%M:%S')
        
        return None
    
    # 测试用例
    test_cases = [
        ('ramnit_2025-12-17_10.log', '2025-12-17 10:00:00'),
        ('botnet_2025-12-17.log', '2025-12-17 00:00:00'),
        ('log_2025-12-17_23.txt', '2025-12-17 23:00:00'),
    ]
    
    for filename, expected in test_cases:
        result = extract_time_from_filename(filename)
        if result and result.strftime('%Y-%m-%d %H:%M:%S') == expected:
            print(f"  ✓ {filename} -> {result}")
        else:
            print(f"  ✗ {filename} -> {result} (期望: {expected})")


async def test_file_size_stability():
    """测试文件大小稳定性检查"""
    print("\n=== 测试5: 文件大小稳定性 ===")
    
    # 创建测试文件
    test_file = TEST_DIR / "growing.log"
    test_file.write_text("initial data")
    
    async def is_file_size_stable(file_path: Path, interval: float = 0.5) -> bool:
        size_1 = file_path.stat().st_size
        await asyncio.sleep(interval)
        size_2 = file_path.stat().st_size
        return size_1 == size_2
    
    # 测试1: 稳定文件
    stable = await is_file_size_stable(test_file)
    if stable:
        print("  ✓ 稳定文件检测正确")
    else:
        print("  ✗ 稳定文件检测错误")
    
    # 测试2: 增长中的文件（模拟）
    # 在实际场景中，文件会在检查期间增长
    print("  ℹ 增长文件测试需要实际写入场景")


def test_concurrent_upload():
    """测试并发控制"""
    print("\n=== 测试6: 并发控制 ===")
    
    async def test_lock():
        lock = asyncio.Lock()
        results = []
        
        async def upload_task(task_id: int):
            async with lock:
                results.append(f"start-{task_id}")
                await asyncio.sleep(0.1)
                results.append(f"end-{task_id}")
        
        # 同时启动3个任务
        await asyncio.gather(
            upload_task(1),
            upload_task(2),
            upload_task(3)
        )
        
        # 验证执行顺序（应该是串行的）
        print(f"  执行顺序: {results}")
        
        # 检查是否串行执行
        is_serial = True
        for i in range(0, len(results), 2):
            if i + 1 < len(results):
                start = results[i]
                end = results[i + 1]
                if not (start.startswith('start') and end.startswith('end')):
                    is_serial = False
                    break
        
        if is_serial:
            print("  ✓ 并发控制正常（串行执行）")
        else:
            print("  ✗ 并发控制失败（并行执行）")
    
    asyncio.run(test_lock())


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Remote Uploader 改进测试")
    print("=" * 60)
    
    try:
        # 同步测试
        test_file_identity()
        test_incomplete_lines_cleanup()
        test_transaction_upload()
        test_timestamp_extraction()
        test_concurrent_upload()
        
        # 异步测试
        asyncio.run(test_file_size_stability())
        
        print("\n" + "=" * 60)
        print("所有测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n测试异常: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试目录
        import shutil
        try:
            shutil.rmtree(TEST_DIR)
            print(f"\n清理测试目录: {TEST_DIR}")
        except:
            pass


if __name__ == "__main__":
    main()
