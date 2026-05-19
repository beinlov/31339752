#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中继节点文件监控服务 - 基于文件系统的命令接收和状态上报

工作原理:
1. 大屏通过SSH/SMB/HTTP等方式将命令写入到 commands/ 目录
2. 中继节点实时监控 commands/ 目录，发现新文件则读取并执行
3. 中继节点将状态写入到 status/ 目录
4. 大屏定时读取 status/ 目录的文件获取最新状态

运行方式:
python relay_node_file_monitor.py --share-path /path/to/relay_share --interface "VMware Network Adapter VMnet1"
"""

import os
import sys
import json
import time
import argparse
import logging
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from scapy.all import sniff, IP, TCP
from collections import defaultdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('relay_node.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConnectionMonitor:
    """连接状态监控器 - 使用Scapy监听流量"""
    
    def __init__(self, interface: str, status_dir: Path):
        self.interface = interface
        self.status_dir = status_dir
        self.connections: Dict[str, dict] = {}
        self.target_connections: Dict[str, tuple] = {}  # attack_id -> (target_ip, target_port)
        self.monitoring = False
        self.monitor_thread = None
        
    def add_target(self, attack_id: str, target_ip: str, target_port: int):
        """添加需要监控的目标"""
        self.target_connections[attack_id] = (target_ip, target_port)
        logger.info(f"添加监控目标: {attack_id} -> {target_ip}:{target_port}")
        
    def remove_target(self, attack_id: str):
        """移除监控目标"""
        if attack_id in self.target_connections:
            del self.target_connections[attack_id]
            logger.info(f"移除监控目标: {attack_id}")
            
    def packet_callback(self, pkt):
        """Scapy数据包回调函数"""
        if not pkt.haslayer(IP) or not pkt.haslayer(TCP):
            return
            
        ip = pkt[IP]
        tcp = pkt[TCP]
        
        # 检查是否是监控的目标
        for attack_id, (target_ip, target_port) in self.target_connections.items():
            src_match = (ip.src == target_ip and tcp.sport == target_port)
            dst_match = (ip.dst == target_ip and tcp.dport == target_port)
            
            if src_match or dst_match:
                # 构建连接键
                conn_key = f"{ip.src}:{tcp.sport}-{ip.dst}:{tcp.dport}"
                
                # 更新连接信息
                if conn_key not in self.connections:
                    self.connections[conn_key] = {
                        'attack_id': attack_id,
                        'src_ip': ip.src,
                        'src_port': tcp.sport,
                        'dst_ip': ip.dst,
                        'dst_port': tcp.dport,
                        'first_seen': datetime.now().isoformat(),
                        'last_seen': datetime.now().isoformat(),
                        'packet_count': 0,
                        'status': 'active',
                        'flags': []
                    }
                
                conn = self.connections[conn_key]
                conn['last_seen'] = datetime.now().isoformat()
                conn['packet_count'] += 1
                
                # 记录TCP标志
                flags = []
                if tcp.flags & 0x02: flags.append('SYN')
                if tcp.flags & 0x10: flags.append('ACK')
                if tcp.flags & 0x01: flags.append('FIN')
                if tcp.flags & 0x04: flags.append('RST')
                
                if flags:
                    conn['flags'] = flags
                    
                # 检测连接状态
                if tcp.flags & 0x01 or tcp.flags & 0x04:  # FIN or RST
                    conn['status'] = 'closed'
                    logger.info(f"连接关闭: {conn_key} [{','.join(flags)}]")
                else:
                    conn['status'] = 'active'
                    
                # 写入状态文件
                self._write_status(attack_id)
                    
    def _write_status(self, attack_id: str):
        """写入状态到文件"""
        try:
            # 收集该攻击的所有连接
            attack_connections = [
                conn for conn in self.connections.values()
                if conn.get('attack_id') == attack_id
            ]
            
            # 检查超时连接
            for conn in attack_connections:
                last_seen = datetime.fromisoformat(conn['last_seen'])
                if (datetime.now() - last_seen).total_seconds() > 10:
                    conn['status'] = 'timeout'
            
            status_file = self.status_dir / f"{attack_id}_status.json"
            status_data = {
                'attack_id': attack_id,
                'timestamp': datetime.now().isoformat(),
                'connections': attack_connections,
                'total_connections': len(attack_connections),
                'active_count': sum(1 for c in attack_connections if c['status'] == 'active'),
                'closed_count': sum(1 for c in attack_connections if c['status'] == 'closed')
            }
            
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"写入状态文件失败: {e}")
                
    def start_monitoring(self):
        """启动流量监听"""
        if self.monitoring:
            logger.warning("监控已在运行")
            return
            
        self.monitoring = True
        
        def monitor_loop():
            logger.info(f"开始监听接口: {self.interface}")
            try:
                sniff(
                    iface=self.interface,
                    prn=self.packet_callback,
                    store=False,
                    stop_filter=lambda x: not self.monitoring
                )
            except Exception as e:
                logger.error(f"监听失败: {e}")
                self.monitoring = False
                
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("流量监听已启动")
        
    def stop_monitoring(self):
        """停止流量监听"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("流量监听已停止")

class AttackExecutor:
    """攻击执行器"""
    
    def __init__(self, interface: str, status_dir: Path):
        self.interface = interface
        self.status_dir = status_dir
        self.running_attacks: Dict[str, subprocess.Popen] = {}
        
    def start_attack(self, attack_id: str, target_ip: str, target_port: int, 
                     capture_interface: str = None, inject_interface: str = None):
        """启动TCP RST攻击"""
        if attack_id in self.running_attacks:
            logger.warning(f"攻击任务已存在: {attack_id}")
            return False
            
        try:
            script_path = os.path.join(os.path.dirname(__file__), 'tcp_rst.py')
            
            if not os.path.exists(script_path):
                logger.error(f"tcp_rst.py脚本不存在: {script_path}")
                return False
            
            cmd = [
                'python3',
                script_path,
                '--target-ip', target_ip,
                '--target-port', str(target_port),
                '--capture-interface', capture_interface or self.interface,
                '--inject-interface', inject_interface or self.interface
            ]
            
            logger.info(f"执行命令: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.running_attacks[attack_id] = process
            
            # 写入启动状态
            self._write_attack_status(attack_id, 'running', {
                'target_ip': target_ip,
                'target_port': target_port,
                'pid': process.pid,
                'start_time': datetime.now().isoformat()
            })
            
            logger.info(f"攻击任务启动成功: {attack_id}, PID={process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"启动攻击失败: {e}")
            self._write_attack_status(attack_id, 'failed', {'error': str(e)})
            return False
            
    def stop_attack(self, attack_id: str):
        """停止攻击"""
        if attack_id not in self.running_attacks:
            logger.warning(f"攻击任务不存在: {attack_id}")
            return False
            
        try:
            process = self.running_attacks[attack_id]
            process.terminate()
            process.wait(timeout=5)
            del self.running_attacks[attack_id]
            
            self._write_attack_status(attack_id, 'stopped', {
                'stop_time': datetime.now().isoformat()
            })
            
            logger.info(f"攻击任务已停止: {attack_id}")
            return True
        except Exception as e:
            logger.error(f"停止攻击失败: {e}")
            return False
            
    def _write_attack_status(self, attack_id: str, status: str, data: dict):
        """写入攻击状态到文件"""
        try:
            status_file = self.status_dir / f"{attack_id}_attack.json"
            status_data = {
                'attack_id': attack_id,
                'status': status,
                'timestamp': datetime.now().isoformat(),
                **data
            }
            
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"写入攻击状态失败: {e}")
            
    def get_attack_status(self, attack_id: str) -> Optional[str]:
        """获取攻击状态"""
        if attack_id not in self.running_attacks:
            return None
            
        process = self.running_attacks[attack_id]
        if process.poll() is None:
            return 'running'
        else:
            return 'stopped'

class CommandFileHandler(FileSystemEventHandler):
    """命令文件监控处理器"""
    
    def __init__(self, executor: AttackExecutor, monitor: ConnectionMonitor, 
                 commands_dir: Path, processed_dir: Path):
        self.executor = executor
        self.monitor = monitor
        self.commands_dir = commands_dir
        self.processed_dir = processed_dir
        
    def on_created(self, event):
        """当新文件创建时"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # 只处理.json文件
        if file_path.suffix != '.json':
            return
            
        # 等待文件写入完成
        time.sleep(0.5)
        
        logger.info(f"检测到新命令文件: {file_path.name}")
        self._process_command_file(file_path)
        
    def _process_command_file(self, file_path: Path):
        """处理命令文件"""
        try:
            # 读取命令
            with open(file_path, 'r', encoding='utf-8') as f:
                command = json.load(f)
                
            logger.info(f"读取命令: {json.dumps(command, ensure_ascii=False)}")
            
            cmd_type = command.get('type')
            attack_id = command.get('attack_id')
            
            if not attack_id:
                logger.error("命令缺少attack_id字段")
                return
                
            if cmd_type == 'start_attack':
                target_ip = command.get('target_ip')
                target_port = command.get('target_port')
                capture_interface = command.get('capture_interface')
                inject_interface = command.get('inject_interface')
                
                if not target_ip or not target_port:
                    logger.error("启动命令缺少必要参数")
                    return
                    
                # 启动攻击
                success = self.executor.start_attack(
                    attack_id, target_ip, target_port,
                    capture_interface, inject_interface
                )
                
                if success:
                    # 添加到监控列表
                    self.monitor.add_target(attack_id, target_ip, target_port)
                    
            elif cmd_type == 'stop_attack':
                # 停止攻击
                self.executor.stop_attack(attack_id)
                self.monitor.remove_target(attack_id)
                
            else:
                logger.warning(f"未知命令类型: {cmd_type}")
                
            # 移动到已处理目录
            processed_file = self.processed_dir / file_path.name
            file_path.rename(processed_file)
            logger.info(f"命令文件已处理并移动到: {processed_file}")
            
        except json.JSONDecodeError as e:
            logger.error(f"命令文件JSON格式错误: {e}")
        except Exception as e:
            logger.error(f"处理命令文件失败: {e}")

class RelayNodeFileMonitor:
    """中继节点文件监控服务主类"""
    
    def __init__(self, share_path: str, interface: str):
        self.share_path = Path(share_path)
        self.interface = interface
        
        # 创建必要的目录
        self.commands_dir = self.share_path / 'commands'
        self.status_dir = self.share_path / 'status'
        self.processed_dir = self.share_path / 'processed'
        
        self.commands_dir.mkdir(parents=True, exist_ok=True)
        self.status_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self.monitor = ConnectionMonitor(interface, self.status_dir)
        self.executor = AttackExecutor(interface, self.status_dir)
        
        # 文件监控
        self.event_handler = CommandFileHandler(
            self.executor, self.monitor,
            self.commands_dir, self.processed_dir
        )
        self.observer = Observer()
        
    def start(self):
        """启动服务"""
        logger.info("=" * 60)
        logger.info("中继节点文件监控服务启动")
        logger.info(f"共享目录: {self.share_path}")
        logger.info(f"命令目录: {self.commands_dir}")
        logger.info(f"状态目录: {self.status_dir}")
        logger.info(f"网络接口: {self.interface}")
        logger.info("=" * 60)
        
        # 启动流量监听
        self.monitor.start_monitoring()
        
        # 启动文件监控
        self.observer.schedule(self.event_handler, str(self.commands_dir), recursive=False)
        self.observer.start()
        logger.info(f"开始监控命令目录: {self.commands_dir}")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n收到停止信号，正在关闭...")
            self.stop()
            
    def stop(self):
        """停止服务"""
        self.observer.stop()
        self.observer.join()
        self.monitor.stop_monitoring()
        
        # 停止所有攻击
        for attack_id in list(self.executor.running_attacks.keys()):
            self.executor.stop_attack(attack_id)
            
        logger.info("服务已停止")

def main():
    parser = argparse.ArgumentParser(description="中继节点文件监控服务")
    parser.add_argument('--share-path', required=True,
                        help='共享目录路径, 例如: /path/to/relay_share')
    parser.add_argument('--interface', required=True,
                        help='网络接口名称, 例如: "VMware Network Adapter VMnet1"')
    args = parser.parse_args()
    
    service = RelayNodeFileMonitor(args.share_path, args.interface)
    service.start()

if __name__ == "__main__":
    main()
