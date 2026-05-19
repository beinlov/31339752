#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP黑名单管控脚本 - 文件监控版本
部署在网关设备上，监控本地配置文件的变化并自动应用到iptables

工作原理:
1. 平台通过SSH推送IP黑名单配置文件到本地
2. 本脚本使用watchdog监控配置文件变化
3. 配置文件更新时，自动应用到iptables ipset

部署位置: 网关设备（能够过滤Bot流量的设备）
依赖: ipset, iptables, watchdog

运行方式:
sudo python3 gateway_black_white_file.py --config-path /opt/suppression_config
"""

import subprocess
import time
import signal
import sys
import os
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 默认配置
DEFAULT_CONFIG_PATH = "/opt/suppression_config"
DEFAULT_CONFIG_FILE = "ip_blacklist.txt"
SET_NAME = "blacklist_set"


def run_cmd(cmd):
    """封装系统命令执行"""
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class IPBlacklistManager:
    """IP黑名单管理器"""
    
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.set_name = SET_NAME
        self.initialized = False
        
    def cleanup(self, signum=None, frame=None):
        """清理函数：删除iptables规则和ipset集合"""
        print(f"\n[{time.strftime('%H:%M:%S')}] 脚本停止，正在清理防火墙规则...")
        run_cmd(["sudo", "iptables", "-D", "FORWARD", "-m", "set", "--match-set", self.set_name, "dst", "-j", "DROP"])
        run_cmd(["sudo", "iptables", "-D", "OUTPUT", "-m", "set", "--match-set", self.set_name, "dst", "-j", "DROP"])
        run_cmd(["sudo", "ipset", "destroy", self.set_name])
        print("环境已清理，原有防火墙策略保持不变。")
        sys.exit(0)
        
    def init_env(self):
        """初始化环境：确保ipset已安装并创建ipset集合"""
        print("正在初始化IP黑名单管控环境...")
        
        # 检查ipset是否安装
        if run_cmd(["which", "ipset"]).returncode != 0:
            print("错误：未找到 ipset 工具，请先执行 sudo apt install ipset")
            sys.exit(1)
            
        # 清理可能的残留
        run_cmd(["sudo", "iptables", "-D", "FORWARD", "-m", "set", "--match-set", self.set_name, "dst", "-j", "DROP"])
        run_cmd(["sudo", "iptables", "-D", "OUTPUT", "-m", "set", "--match-set", self.set_name, "dst", "-j", "DROP"])
        run_cmd(["sudo", "ipset", "destroy", self.set_name])
        
        # 创建ipset集合
        run_cmd(["sudo", "ipset", "create", self.set_name, "hash:ip"])
        
        # 在iptables中插入规则
        run_cmd(["sudo", "iptables", "-I", "FORWARD", "1", "-m", "set", "--match-set", self.set_name, "dst", "-j", "DROP"])
        run_cmd(["sudo", "iptables", "-I", "OUTPUT", "1", "-m", "set", "--match-set", self.set_name, "dst", "-j", "DROP"])
        
        print(f"IP黑名单集合 {self.set_name} 已挂载到 iptables")
        self.initialized = True
        
    def load_and_apply(self):
        """从配置文件加载IP黑名单并应用"""
        if not self.initialized:
            return
            
        try:
            # 检查配置文件是否存在
            if not os.path.exists(self.config_file_path):
                print(f"[{time.strftime('%H:%M:%S')}] 配置文件不存在: {self.config_file_path}")
                return
                
            # 读取配置文件
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # 提取有效IP地址
            ips = []
            for line in lines:
                line = line.strip()
                # 跳过空行和注释
                if line and not line.startswith('#'):
                    ips.append(line)
                    
            # 全量更新ipset（先清空再添加）
            run_cmd(["sudo", "ipset", "flush", self.set_name])
            
            for ip in ips:
                run_cmd(["sudo", "ipset", "add", self.set_name, ip])
                
            print(f"[{time.strftime('%H:%M:%S')}] IP黑名单已更新，当前包含 {len(ips)} 个IP")
            
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] 加载配置失败: {e}")


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变化监听器"""
    
    def __init__(self, manager, config_filename):
        self.manager = manager
        self.config_filename = config_filename
        
    def on_modified(self, event):
        """文件修改事件"""
        if event.is_directory:
            return
            
        # 只处理目标配置文件
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


def main():
    parser = argparse.ArgumentParser(description="IP黑名单自动同步脚本（文件监控版本）")
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
        
    # 创建配置目录（如果不存在）
    os.makedirs(args.config_path, exist_ok=True)
    
    config_file_path = os.path.join(args.config_path, args.config_file)
    
    # 创建管理器
    manager = IPBlacklistManager(config_file_path)
    
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
    print("IP黑名单自动同步脚本已启动（文件监控模式）")
    print(f"配置目录: {args.config_path}")
    print(f"配置文件: {config_file_path}")
    print(f"ipset集合: {SET_NAME}")
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
