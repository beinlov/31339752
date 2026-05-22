#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Relay Node File Monitor Service - Command receiving and status reporting based on file system

Working principle:
1. Platform writes commands to commands/ directory via SSH/SMB/HTTP
2. Relay node monitors commands/ directory in real-time, reads and executes new files
3. Relay node writes status to status/ directory
4. Platform periodically reads files in status/ directory to get latest status

Usage:
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

# Configure logging
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
    """Connection status monitor - using Scapy to listen to traffic"""
    
    def __init__(self, interface: str, status_dir: Path):
        self.interface = interface
        self.status_dir = status_dir
        self.connections: Dict[str, dict] = {}
        self.target_connections: Dict[str, tuple] = {}  # attack_id -> (target_ip, target_port)
        self.monitoring = False
        self.monitor_thread = None
        
    def add_target(self, attack_id: str, target_ip: str, target_port: int):
        """Add target to monitor"""
        self.target_connections[attack_id] = (target_ip, target_port)
        logger.info(f"Add monitoring target: {attack_id} -> {target_ip}:{target_port}")
        
    def remove_target(self, attack_id: str):
        """Remove monitoring target"""
        if attack_id in self.target_connections:
            del self.target_connections[attack_id]
            logger.info(f"Remove monitoring target: {attack_id}")
            
    def packet_callback(self, pkt):
        """Scapy packet callback function"""
        if not pkt.haslayer(IP) or not pkt.haslayer(TCP):
            return
            
        ip = pkt[IP]
        tcp = pkt[TCP]
        
        # Check if it's a monitored target
        for attack_id, (target_ip, target_port) in self.target_connections.items():
            src_match = (ip.src == target_ip and tcp.sport == target_port)
            dst_match = (ip.dst == target_ip and tcp.dport == target_port)
            
            if src_match or dst_match:
                # Build connection key
                conn_key = f"{ip.src}:{tcp.sport}-{ip.dst}:{tcp.dport}"
                
                # Update connection info
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
                
                # Record TCP flags
                flags = []
                if tcp.flags & 0x02: flags.append('SYN')
                if tcp.flags & 0x10: flags.append('ACK')
                if tcp.flags & 0x01: flags.append('FIN')
                if tcp.flags & 0x04: flags.append('RST')
                
                if flags:
                    conn['flags'] = flags
                    
                # Detect connection status
                if tcp.flags & 0x01 or tcp.flags & 0x04:  # FIN or RST
                    conn['status'] = 'closed'
                    logger.info(f"Connection closed: {conn_key} [{','.join(flags)}]")
                else:
                    conn['status'] = 'active'
                    
                # Write status file
                self._write_status(attack_id)
                    
    def _write_status(self, attack_id: str):
        """Write status to file"""
        try:
            # Collect all connections for this attack
            attack_connections = [
                conn for conn in self.connections.values()
                if conn.get('attack_id') == attack_id
            ]
            
            # Check timeout connections
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
                'active_connections': len([c for c in attack_connections if c['status'] == 'active']),
                'closed_connections': len([c for c in attack_connections if c['status'] == 'closed'])
            }
            
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Write status failed: {e}")
            
    def start_monitoring(self):
        """Start monitoring"""
        if self.monitoring:
            return
            
        self.monitoring = True
        
        def monitor_loop():
            logger.info(f"Start monitoring interface: {self.interface}")
            try:
                sniff(
                    iface=self.interface,
                    prn=self.packet_callback,
                    store=False,
                    stop_filter=lambda x: not self.monitoring
                )
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                self.monitoring = False
                
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

class AttackExecutor:
    """Attack executor - responsible for starting and stopping attack scripts"""
    
    def __init__(self, interface: str, status_dir: Path):
        self.interface = interface
        self.status_dir = status_dir
        self.running_attacks: Dict[str, subprocess.Popen] = {}
        
    def start_attack(self, attack_id: str, target_ip: str, target_port: int,
                    capture_interface: Optional[str] = None,
                    inject_interface: Optional[str] = None) -> bool:
        """Start attack"""
        if attack_id in self.running_attacks:
            logger.warning(f"Attack task already exists: {attack_id}")
            return False
            
        try:
            # Get tcp_rst.py script path
            script_path = os.path.join(os.path.dirname(__file__), 'tcp_rst.py')
            
            if not os.path.exists(script_path):
                logger.error(f"tcp_rst.py script does not exist: {script_path}")
                return False
            
            cmd = [
                'sudo',
                'python3',
                script_path,
                '--target-ip', target_ip,
                '--target-port', str(target_port),
                '--capture-interface', capture_interface or self.interface,
                '--inject-interface', inject_interface or self.interface
            ]
            
            logger.info(f"Execute command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.running_attacks[attack_id] = process
            
            # Write startup status
            self._write_attack_status(attack_id, 'running', {
                'target_ip': target_ip,
                'target_port': target_port,
                'pid': process.pid,
                'start_time': datetime.now().isoformat()
            })
            
            logger.info(f"Attack task started successfully: {attack_id}, PID={process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Start attack failed: {e}")
            self._write_attack_status(attack_id, 'failed', {'error': str(e)})
            return False
            
    def stop_attack(self, attack_id: str):
        """Stop attack"""
        if attack_id not in self.running_attacks:
            logger.warning(f"Attack task does not exist: {attack_id}")
            return False
            
        try:
            process = self.running_attacks[attack_id]
            pid = process.pid
            
            # First try to terminate the process normally
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # If normal termination fails, force kill the process and all its children
                logger.warning(f"Process {pid} did not terminate, force killing...")
                subprocess.run(['sudo', 'pkill', '-9', '-P', str(pid)], check=False)
                subprocess.run(['sudo', 'kill', '-9', str(pid)], check=False)
                
            del self.running_attacks[attack_id]
            
            self._write_attack_status(attack_id, 'stopped', {
                'stop_time': datetime.now().isoformat()
            })
            
            logger.info(f"Attack task stopped: {attack_id}")
            return True
        except Exception as e:
            logger.error(f"Stop attack failed: {e}")
            return False
            
    def _write_attack_status(self, attack_id: str, status: str, data: dict):
        """Write attack status to file"""
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
            logger.error(f"Write attack status failed: {e}")
            
    def get_attack_status(self, attack_id: str) -> Optional[str]:
        """Get attack status"""
        if attack_id not in self.running_attacks:
            return None
            
        process = self.running_attacks[attack_id]
        if process.poll() is None:
            return 'running'
        else:
            return 'stopped'

class CommandFileHandler(FileSystemEventHandler):
    """Command file monitoring handler"""
    
    def __init__(self, executor: AttackExecutor, monitor: ConnectionMonitor, 
                 commands_dir: Path, processed_dir: Path):
        self.executor = executor
        self.monitor = monitor
        self.commands_dir = commands_dir
        self.processed_dir = processed_dir
        
    def on_created(self, event):
        """Handle file creation event"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Only process JSON files
        if file_path.suffix != '.json':
            return
            
        logger.info(f"Detected new command file: {file_path}")
        
        # Wait a moment to ensure file is fully written
        time.sleep(0.5)
        
        try:
            # Read command file
            with open(file_path, 'r', encoding='utf-8') as f:
                command = json.load(f)
                
            attack_id = command.get('attack_id')
            # Support both 'action' and 'type' fields
            action = command.get('action') or command.get('type', 'start')
            
            if not attack_id:
                logger.error(f"Command file missing attack_id: {file_path}")
                return
                
            # Normalize action names
            if action in ['start', 'start_attack']:
                action = 'start'
            elif action in ['stop', 'stop_attack']:
                action = 'stop'
                
            if action == 'start':
                # Start attack
                target_ip = command.get('target_ip')
                target_port = command.get('target_port')
                capture_interface = command.get('capture_interface')
                inject_interface = command.get('inject_interface')
                
                if not target_ip or not target_port:
                    logger.error(f"Command file missing required parameters: {file_path}")
                    return
                    
                # Add monitoring target
                self.monitor.add_target(attack_id, target_ip, target_port)
                
                # Start attack
                self.executor.start_attack(
                    attack_id, target_ip, target_port,
                    capture_interface, inject_interface
                )
                
            elif action == 'stop':
                # Stop attack
                self.executor.stop_attack(attack_id)
                self.monitor.remove_target(attack_id)
                
            # Move command file to processed directory
            processed_path = self.processed_dir / file_path.name
            file_path.rename(processed_path)
            logger.info(f"Command file processed: {file_path} -> {processed_path}")
            
        except Exception as e:
            logger.error(f"Process command file failed: {file_path}, error: {e}")

class RelayNodeFileMonitor:
    """Relay node file monitoring service"""
    
    def __init__(self, share_path: str, interface: str):
        self.share_path = Path(share_path)
        self.interface = interface
        
        # Create directory structure
        self.commands_dir = self.share_path / 'commands'
        self.status_dir = self.share_path / 'status'
        self.processed_dir = self.share_path / 'processed'
        
        for dir_path in [self.commands_dir, self.status_dir, self.processed_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # Initialize components
        self.monitor = ConnectionMonitor(interface, self.status_dir)
        self.executor = AttackExecutor(interface, self.status_dir)
        self.event_handler = CommandFileHandler(
            self.executor, self.monitor,
            self.commands_dir, self.processed_dir
        )
        
        # Initialize file system observer
        self.observer = Observer()
        
    def start(self):
        """Start service"""
        logger.info("=" * 60)
        logger.info("Relay Node File Monitor Service Started")
        logger.info(f"Share path: {self.share_path}")
        logger.info(f"Commands directory: {self.commands_dir}")
        logger.info(f"Status directory: {self.status_dir}")
        logger.info(f"Network interface: {self.interface}")
        logger.info("=" * 60)
        
        # Start traffic monitoring
        self.monitor.start_monitoring()
        
        # Start file monitoring
        self.observer.schedule(self.event_handler, str(self.commands_dir), recursive=False)
        self.observer.start()
        logger.info(f"Start monitoring commands directory: {self.commands_dir}")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nReceived stop signal, shutting down...")
            self.stop()
            
    def stop(self):
        """Stop service"""
        self.observer.stop()
        self.observer.join()
        self.monitor.stop_monitoring()
        
        # Stop all attacks
        for attack_id in list(self.executor.running_attacks.keys()):
            self.executor.stop_attack(attack_id)
            
        logger.info("Service stopped")

def main():
    parser = argparse.ArgumentParser(description="Relay Node File Monitor Service")
    parser.add_argument('--share-path', required=True,
                        help='Share directory path, e.g.: /path/to/relay_share')
    parser.add_argument('--interface', required=True,
                        help='Network interface name, e.g.: "VMware Network Adapter VMnet1"')
    args = parser.parse_args()
    
    service = RelayNodeFileMonitor(args.share_path, args.interface)
    service.start()

if __name__ == "__main__":
    main()
