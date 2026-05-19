#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网关间歇性丢包策略脚本 - 文件监控版本
部署在网关设备上，监控本地配置文件的变化并自动应用到iptables

工作原理:
1. 平台通过SSH推送丢包策略配置文件(JSON格式)到本地
2. 本脚本使用watchdog监控配置文件变化
3. 配置文件更新时，自动同步到iptables规则

部署位置: 网关设备（能够过滤Bot流量的设备）
依赖: iptables, watchdog

运行方式:
sudo python3 gateway_packet_loss_file.py --config-path /opt/suppression_config
"""

import subprocess
import time
import json
import os
import argparse
import signal
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 默认配置
DEFAULT_CONFIG_PATH = "/opt/suppression_config"
DEFAULT_CONFIG_FILE = "packet_loss.json"
CHAIN_NAME = "INTERMITTENT_DROP"


class PacketLossManager:
    """丢包策略管理器"""
    
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.chain_name = CHAIN_NAME
        self.current_policies = {}  # {ip: rate}
        self.initialized = False
        
    def _run_cmd(self, cmd):
        """执行iptables命令"""
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
            
    def init_env(self):
        """初始化iptables环境"""
        print(f"[{time.strftime('%H:%M:%S')}] 初始化策略链: {self.chain_name}")
        
        # 清理旧环境
        self._run_cmd(['iptables', '-D', 'FORWARD', '-j', self.chain_name])
        self._run_cmd(['iptables', '-F', self.chain_name])
        self._run_cmd(['iptables', '-X', self.chain_name])
        
        # 创建并挂载
        self._run_cmd(['iptables', '-N', self.chain_name])
        self._run_cmd(['iptables', '-I', 'FORWARD', '1', '-j', self.chain_name])
        
        self.initialized = True
        print(f"[{time.strftime('%H:%M:%S')}] iptables策略链已创建")
        
    def apply_rule(self, ip, rate, action="ADD"):
        """应用或删除丢包规则"""
        flag = "-A" if action == "ADD" else "-D"
        # 同时作用于进入和发出的流量
        cmds = [
            ['iptables', flag, self.chain_name, '-d', ip, '-m', 'statistic', 
             '--mode', 'random', '--probability', str(rate), '-j', 'DROP'],
            ['iptables', flag, self.chain_name, '-s', ip, '-m', 'statistic',
             '--mode', 'random', '--probability', str(rate), '-j', 'DROP']
        ]
        for cmd in cmds:
            self._run_cmd(cmd)
            
    def load_and_apply(self):
        """从配置文件加载丢包策略并同步"""
        if not self.initialized:
            return
            
        try:
            # 检查配置文件是否存在
            if not os.path.exists(self.config_file_path):
                print(f"[{time.strftime('%H:%M:%S')}] 配置文件不存在: {self.config_file_path}")
                # 清空所有规则
                for ip, rate in list(self.current_policies.items()):
                    self.apply_rule(ip, rate, "DELETE")
                    del self.current_policies[ip]
                return
                
            # 读取JSON配置文件
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                new_policies = json.load(f)
                
            # 验证格式
            if not isinstance(new_policies, dict):
                print(f"[{time.strftime('%H:%M:%S')}] 配置文件格式错误，应该是JSON字典")
                return
                
            # 1. 移除已不在列表或概率发生变化的IP
            for ip, rate in list(self.current_policies.items()):
                if ip not in new_policies or new_policies[ip] != rate:
                    self.apply_rule(ip, rate, "DELETE")
                    del self.current_policies[ip]
                    print(f"[{time.strftime('%H:%M:%S')}] 移除规则: {ip}")
                    
            # 2. 增加新IP或应用更新后的概率
            for ip, rate in new_policies.items():
                if ip not in self.current_policies:
                    self.apply_rule(ip, float(rate), "ADD")
                    self.current_policies[ip] = float(rate)
                    print(f"[{time.strftime('%H:%M:%S')}] 激活规则: {ip} (丢包率: {float(rate)*100:.1f}%)")
                    
            print(f"[{time.strftime('%H:%M:%S')}] 丢包策略已更新，当前包含 {len(self.current_policies)} 条规则")
            
        except json.JSONDecodeError as e:
            print(f"[{time.strftime('%H:%M:%S')}] JSON解析失败: {e}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] 加载配置失败: {e}")
            
    def cleanup(self, signum=None, frame=None):
        """清理函数：删除iptables规则"""
        print(f"\n[{time.strftime('%H:%M:%S')}] 脚本停止，正在清理iptables规则...")
        self._run_cmd(['iptables', '-D', 'FORWARD', '-j', self.chain_name])
        self._run_cmd(['iptables', '-F', self.chain_name])
        self._run_cmd(['iptables', '-X', self.chain_name])
        print("环境已清理")
        sys.exit(0)


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变化监听器"""
    
    def __init__(self, manager, config_filename):
        self.manager = manager
        self.config_filename = config_filename
        
    def on_modified(self, event):
        """文件修改事件"""
        if event.is_directory:
            return
            
        if os.path.basename(event.src_path) == self.config_filename:
            print(f"[{time.strftime('%H:%M:%S')}] 检测到配置文件更新: {event.src_path}")
            time.sleep(0.5)  # 等待文件写入完成
            self.manager.load_and_apply()
            
    def on_created(self, event):
        """文件创建事件"""
        if event.is_directory:
            return
            
        if os.path.basename(event.src_path) == self.config_filename:
            print(f"[{time.strftime('%H:%M:%S')}] 检测到配置文件创建: {event.src_path}")
            time.sleep(0.5)
            self.manager.load_and_apply()
            
    def on_deleted(self, event):
        """文件删除事件"""
        if event.is_directory:
            return
            
        if os.path.basename(event.src_path) == self.config_filename:
            print(f"[{time.strftime('%H:%M:%S')}] 检测到配置文件删除: {event.src_path}")
            self.manager.load_and_apply()


def main():
    parser = argparse.ArgumentParser(description="间歇性丢包策略自动同步脚本（文件监控版本）")
    parser.add_argument(
        "--config-path",
        default=DEFAULT_CONFIG_PATH,
        help=f"配置文件目录路径 (默认: {DEFAULT_CONFIG_PATH})"
    )
    parser.add_argument(
        "--config-file",
        default=DEFAULT_CONFIG_FILE,
        help=f"配置文件名 (默认: {DEFAULT_CONFIG_FILE})"
    )
    args = parser.parse_args()
    
    # 检查权限
    if os.geteuid() != 0:
        print("错误：必须使用 sudo 运行此脚本")
        sys.exit(1)
        
    # 创建配置目录
    os.makedirs(args.config_path, exist_ok=True)
    
    config_file_path = os.path.join(args.config_path, args.config_file)
    
    # 创建管理器
    manager = PacketLossManager(config_file_path)
    
    # 注册退出信号
    signal.signal(signal.SIGINT, manager.cleanup)
    signal.signal(signal.SIGTERM, manager.cleanup)
    
    # 初始化环境
    manager.init_env()
    
    # 首次加载配置
    manager.load_and_apply()
    
    # 设置文件监控
    event_handler = ConfigFileHandler(manager, args.config_file)
    observer = Observer()
    observer.schedule(event_handler, args.config_path, recursive=False)
    observer.start()
    
    print("=" * 60)
    print("间歇性丢包策略自动同步脚本已启动（文件监控模式）")
    print(f"配置目录: {args.config_path}")
    print(f"配置文件: {config_file_path}")
    print(f"策略链: {CHAIN_NAME}")
    print("=" * 60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        manager.cleanup()
        
    observer.join()


if __name__ == "__main__":
    main()
