#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNS域名黑名单管控脚本 - 文件监控版本
部署在DNS服务器上，监控本地配置文件的变化并自动应用到dnsmasq

工作原理:
1. 平台通过SSH推送域名黑名单配置文件到本地
2. 本脚本使用watchdog监控配置文件变化
3. 配置文件更新时，自动生成dnsmasq配置并重启服务

部署位置: DNS服务器（运行dnsmasq的设备）
依赖: dnsmasq, watchdog

运行方式:
sudo python3 dns_black_white_file.py --config-path /opt/suppression_config
"""

import subprocess
import time
import os
import argparse
import signal
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 默认配置
DEFAULT_CONFIG_PATH = "/opt/suppression_config"
DEFAULT_CONFIG_FILE = "domain_blacklist.txt"
DEFAULT_DNSMASQ_CONF = "/etc/dnsmasq.d/dns_blacklist.conf"


class DomainBlacklistManager:
    """域名黑名单管理器"""
    
    def __init__(self, config_file_path, dnsmasq_conf_path):
        self.config_file_path = config_file_path
        self.dnsmasq_conf_path = dnsmasq_conf_path
        
    def load_and_apply(self):
        """从配置文件加载域名黑名单并应用到dnsmasq"""
        try:
            # 检查配置文件是否存在
            if not os.path.exists(self.config_file_path):
                print(f"[{time.strftime('%H:%M:%S')}] 配置文件不存在: {self.config_file_path}")
                return
                
            # 读取配置文件
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # 提取有效域名
            domains = []
            for line in lines:
                line = line.strip()
                # 跳过空行和注释
                if line and not line.startswith('#'):
                    domains.append(line)
                    
            # 生成dnsmasq配置内容
            new_content = "# Auto-generated blacklist by platform\n"
            new_content += f"# Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            for domain in domains:
                # 将域名指向0.0.0.0实现拦截
                new_content += f"address=/{domain}/0.0.0.0\n"
                
            # 检查是否有更新（避免重复重启服务）
            if os.path.exists(self.dnsmasq_conf_path):
                with open(self.dnsmasq_conf_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
                    
                if current_content == new_content:
                    print(f"[{time.strftime('%H:%M:%S')}] 域名黑名单未变化，跳过更新")
                    return
                    
            # 写入dnsmasq配置文件
            with open(self.dnsmasq_conf_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            # 重启dnsmasq服务
            print(f"[{time.strftime('%H:%M:%S')}] 检测到更新，正在重启 dnsmasq...")
            result = subprocess.run(
                ["sudo", "systemctl", "restart", "dnsmasq"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"[{time.strftime('%H:%M:%S')}] 域名黑名单已更新，当前包含 {len(domains)} 个域名")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] dnsmasq重启失败: {result.stderr}")
                
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] 加载配置失败: {e}")
            
    def cleanup(self, signum=None, frame=None):
        """清理函数"""
        print(f"\n[{time.strftime('%H:%M:%S')}] 脚本停止")
        # 可选：删除dnsmasq配置文件
        # if os.path.exists(self.dnsmasq_conf_path):
        #     os.remove(self.dnsmasq_conf_path)
        #     subprocess.run(["sudo", "systemctl", "restart", "dnsmasq"])
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


def main():
    parser = argparse.ArgumentParser(description="DNS域名黑名单自动同步脚本（文件监控版本）")
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
    parser.add_argument(
        "--dnsmasq-conf",
        default=DEFAULT_DNSMASQ_CONF,
        help=f"dnsmasq配置文件路径 (默认: {DEFAULT_DNSMASQ_CONF})"
    )
    args = parser.parse_args()
    
    # 检查权限
    if os.geteuid() != 0:
        print("错误：必须使用 sudo 运行此脚本")
        sys.exit(1)
        
    # 检查dnsmasq是否安装
    if subprocess.run(["which", "dnsmasq"], capture_output=True).returncode != 0:
        print("错误：未找到 dnsmasq，请先安装")
        sys.exit(1)
        
    # 创建配置目录
    os.makedirs(args.config_path, exist_ok=True)
    os.makedirs(os.path.dirname(args.dnsmasq_conf), exist_ok=True)
    
    config_file_path = os.path.join(args.config_path, args.config_file)
    
    # 创建管理器
    manager = DomainBlacklistManager(config_file_path, args.dnsmasq_conf)
    
    # 注册退出信号
    signal.signal(signal.SIGINT, manager.cleanup)
    signal.signal(signal.SIGTERM, manager.cleanup)
    
    # 首次加载配置
    manager.load_and_apply()
    
    # 设置文件监控
    event_handler = ConfigFileHandler(manager, args.config_file)
    observer = Observer()
    observer.schedule(event_handler, args.config_path, recursive=False)
    observer.start()
    
    print("=" * 60)
    print("DNS域名黑名单自动同步脚本已启动（文件监控模式）")
    print(f"配置目录: {args.config_path}")
    print(f"配置文件: {config_file_path}")
    print(f"dnsmasq配置: {args.dnsmasq_conf}")
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
