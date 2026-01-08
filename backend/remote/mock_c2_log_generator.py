#!/usr/bin/env python3
"""
模拟C2日志生成器 - 用于测试数据传输

功能：
- 每小时生成一个日志文件
- 文件格式：test_YYYY-MM-DD_HH.log
- 日志格式：YYYY-MM-DD HH:MM:SS,IP
- 每个文件约4000-5000条日志
"""

import os
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
import argparse


class MockC2LogGenerator:
    """模拟C2日志生成器"""
    
    def __init__(self, log_dir: str = "./mock_logs", prefix: str = "test"):
        """
        初始化生成器
        
        Args:
            log_dir: 日志文件目录
            prefix: 文件名前缀
        """
        self.log_dir = Path(log_dir)
        self.prefix = prefix
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"日志生成器初始化完成")
        print(f"  - 日志目录: {self.log_dir.absolute()}")
        print(f"  - 文件前缀: {self.prefix}")
    
    def generate_random_ip(self) -> str:
        """
        生成随机公网IP地址
        
        Returns:
            随机IP地址
        """
        while True:
            # 生成四个字段
            octets = [random.randint(1, 254) for _ in range(4)]
            ip = '.'.join(map(str, octets))
            
            # 排除私有IP段
            if ip.startswith('10.'):
                continue
            if ip.startswith('192.168.'):
                continue
            if ip.startswith('172.'):
                second = int(ip.split('.')[1])
                if 16 <= second <= 31:
                    continue
            if ip.startswith('127.'):
                continue
            if ip.startswith('169.254.'):
                continue
            
            return ip
    
    def generate_log_file(self, target_time: datetime, log_count: int = None):
        """
        生成指定小时的日志文件
        
        Args:
            target_time: 目标时间
            log_count: 日志条数（默认随机4000-5000）
        """
        # 文件名：test_2025-12-18_15.log
        filename = f"{self.prefix}_{target_time.strftime('%Y-%m-%d_%H')}.log"
        file_path = self.log_dir / filename
        
        # 如果文件已存在，跳过
        if file_path.exists():
            print(f"[跳过] 文件已存在: {filename}")
            return
        
        # 随机生成4000-5000条日志
        if log_count is None:
            log_count = random.randint(4000, 5000)
        
        print(f"[生成] {filename} ({log_count} 条日志)")
        
        # 生成日志内容
        logs = []
        for i in range(log_count):
            # 在该小时内随机分布时间
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            log_time = target_time.replace(minute=minute, second=second)
            
            # 生成随机IP
            ip = self.generate_random_ip()
            
            # 格式：2025-12-03 15:59:08,171.233.146.163
            log_line = f"{log_time.strftime('%Y-%m-%d %H:%M:%S')},{ip}\n"
            logs.append(log_line)
        
        # 按时间排序（更真实）
        logs.sort()
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(logs)
        
        print(f"  ✓ 完成: {file_path.absolute()}")
    
    def generate_historical_logs(self, hours: int = 24):
        """
        生成历史日志文件（用于初始化测试）
        
        Args:
            hours: 生成多少小时的历史日志
        """
        print(f"\n开始生成历史日志（最近 {hours} 小时）...")
        
        now = datetime.now()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        
        for i in range(hours, 0, -1):
            target_time = current_hour - timedelta(hours=i)
            self.generate_log_file(target_time)
        
        print(f"\n✓ 历史日志生成完成")
    
    def run_continuous(self, interval: int = 3600):
        """
        持续运行模式：每小时生成新日志
        
        Args:
            interval: 检查间隔（秒），默认3600（1小时）
        """
        print(f"\n开始持续运行模式（每 {interval} 秒检查一次）...")
        print("按 Ctrl+C 停止")
        
        try:
            while True:
                now = datetime.now()
                current_hour = now.replace(minute=0, second=0, microsecond=0)
                
                # 生成上一个小时的日志（当前小时的日志还在写入中）
                last_hour = current_hour - timedelta(hours=1)
                self.generate_log_file(last_hour)
                
                # 等待下一次检查
                print(f"[等待] 下次检查时间: {(now + timedelta(seconds=interval)).strftime('%Y-%m-%d %H:%M:%S')}")
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n\n停止日志生成器")
    
    def run_fast_mode(self, count: int = 10, interval: int = 5):
        """
        快速模式：快速生成多个日志文件（用于快速测试）
        
        Args:
            count: 生成文件数量
            interval: 每个文件间隔（秒）
        """
        print(f"\n快速测试模式：生成 {count} 个文件（间隔 {interval} 秒）...")
        
        now = datetime.now()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        
        for i in range(count):
            target_time = current_hour - timedelta(hours=count-i)
            self.generate_log_file(target_time, log_count=random.randint(4000, 5000))
            
            if i < count - 1:
                print(f"  等待 {interval} 秒...")
                time.sleep(interval)
        
        print(f"\n✓ 快速测试完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='模拟C2日志生成器')
    parser.add_argument('--log-dir', default='./mock_logs', help='日志文件目录（默认：./mock_logs）')
    parser.add_argument('--prefix', default='test', help='文件名前缀（默认：test）')
    
    # 运行模式
    parser.add_argument('--mode', choices=['historical', 'continuous', 'fast'], 
                       default='historical',
                       help='运行模式：historical=生成历史日志，continuous=持续运行，fast=快速测试')
    
    # 参数
    parser.add_argument('--hours', type=int, default=24, 
                       help='历史模式：生成多少小时的日志（默认：24）')
    parser.add_argument('--interval', type=int, default=3600, 
                       help='持续模式：检查间隔秒数（默认：3600）')
    parser.add_argument('--count', type=int, default=10, 
                       help='快速模式：生成文件数量（默认：10）')
    parser.add_argument('--fast-interval', type=int, default=5, 
                       help='快速模式：文件间隔秒数（默认：5）')
    
    args = parser.parse_args()
    
    # 创建生成器
    generator = MockC2LogGenerator(log_dir=args.log_dir, prefix=args.prefix)
    
    # 根据模式运行
    if args.mode == 'historical':
        generator.generate_historical_logs(hours=args.hours)
    elif args.mode == 'continuous':
        generator.run_continuous(interval=args.interval)
    elif args.mode == 'fast':
        generator.run_fast_mode(count=args.count, interval=args.fast_interval)


if __name__ == '__main__':
    main()
