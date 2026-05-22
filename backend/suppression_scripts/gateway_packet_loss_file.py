#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gateway Intermittent Packet Loss Policy Script - File Monitoring Version
Deployed on gateway devices to monitor local config file changes and auto-apply to iptables

How it works:
1. Platform pushes packet loss policy config file (JSON format) via SSH
2. This script uses watchdog to monitor config file changes
3. When config file updates, automatically sync to iptables rules

Deployment: Gateway device (device that can filter Bot traffic)
Dependencies: iptables, watchdog

Usage:
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

# Default configuration
DEFAULT_CONFIG_PATH = "/opt/suppression_config"
DEFAULT_CONFIG_FILE = "packet_loss.json"
CHAIN_NAME = "INTERMITTENT_DROP"


class PacketLossManager:
    """Packet Loss Policy Manager"""
    
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.chain_name = CHAIN_NAME
        self.current_policies = {}  # {ip: rate}
        self.initialized = False
        
    def _run_cmd(self, cmd):
        """Execute iptables command"""
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
            
    def init_env(self):
        """Initialize iptables environment"""
        print(f"[{time.strftime('%H:%M:%S')}] Initializing policy chain: {self.chain_name}")
        
        # Clean up old environment
        self._run_cmd(['iptables', '-D', 'FORWARD', '-j', self.chain_name])
        self._run_cmd(['iptables', '-F', self.chain_name])
        self._run_cmd(['iptables', '-X', self.chain_name])
        
        # Create and mount
        self._run_cmd(['iptables', '-N', self.chain_name])
        self._run_cmd(['iptables', '-I', 'FORWARD', '1', '-j', self.chain_name])
        
        self.initialized = True
        print(f"[{time.strftime('%H:%M:%S')}] iptables policy chain created")
        
    def apply_rule(self, ip, rate, action="ADD"):
        """Apply or remove packet loss rule"""
        flag = "-A" if action == "ADD" else "-D"
        # Apply to both incoming and outgoing traffic
        cmds = [
            ['iptables', flag, self.chain_name, '-d', ip, '-m', 'statistic', 
             '--mode', 'random', '--probability', str(rate), '-j', 'DROP'],
            ['iptables', flag, self.chain_name, '-s', ip, '-m', 'statistic',
             '--mode', 'random', '--probability', str(rate), '-j', 'DROP']
        ]
        for cmd in cmds:
            self._run_cmd(cmd)
            
    def load_and_apply(self):
        """Load packet loss policy from config file and sync"""
        if not self.initialized:
            return
            
        try:
            # Check if config file exists
            if not os.path.exists(self.config_file_path):
                print(f"[{time.strftime('%H:%M:%S')}] Config file not found: {self.config_file_path}")
                # Clear all rules
                for ip, rate in list(self.current_policies.items()):
                    self.apply_rule(ip, rate, "DELETE")
                    del self.current_policies[ip]
                return
                
            # Read JSON config file
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                new_policies = json.load(f)
                
            # Validate format
            if not isinstance(new_policies, dict):
                print(f"[{time.strftime('%H:%M:%S')}] Config file format error, should be JSON dict")
                return
                
            # 1. Remove IPs no longer in list or with changed probability
            for ip, rate in list(self.current_policies.items()):
                if ip not in new_policies or new_policies[ip] != rate:
                    self.apply_rule(ip, rate, "DELETE")
                    del self.current_policies[ip]
                    print(f"[{time.strftime('%H:%M:%S')}] Removed rule: {ip}")
                    
            # 2. Add new IPs or apply updated probability
            for ip, rate in new_policies.items():
                if ip not in self.current_policies:
                    self.apply_rule(ip, float(rate), "ADD")
                    self.current_policies[ip] = float(rate)
                    print(f"[{time.strftime('%H:%M:%S')}] Activated rule: {ip} (loss rate: {float(rate)*100:.1f}%)")
                    
            print(f"[{time.strftime('%H:%M:%S')}] Packet loss policy updated, contains {len(self.current_policies)} rules")
            
        except json.JSONDecodeError as e:
            print(f"[{time.strftime('%H:%M:%S')}] JSON parse failed: {e}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Failed to load config: {e}")
            
    def cleanup(self, signum=None, frame=None):
        """Cleanup function: remove iptables rules"""
        print(f"\n[{time.strftime('%H:%M:%S')}] Script stopping, cleaning up iptables rules...")
        self._run_cmd(['iptables', '-D', 'FORWARD', '-j', self.chain_name])
        self._run_cmd(['iptables', '-F', self.chain_name])
        self._run_cmd(['iptables', '-X', self.chain_name])
        print("Environment cleaned")
        sys.exit(0)


class ConfigFileHandler(FileSystemEventHandler):
    """Config file change listener"""
    
    def __init__(self, manager, config_filename):
        self.manager = manager
        self.config_filename = config_filename
        
    def on_modified(self, event):
        """File modification event"""
        if event.is_directory:
            return
            
        if os.path.basename(event.src_path) == self.config_filename:
            print(f"[{time.strftime('%H:%M:%S')}] Config file update detected: {event.src_path}")
            time.sleep(0.5)  # Wait for file write to complete
            self.manager.load_and_apply()
            
    def on_created(self, event):
        """File creation event"""
        if event.is_directory:
            return
            
        if os.path.basename(event.src_path) == self.config_filename:
            print(f"[{time.strftime('%H:%M:%S')}] Config file creation detected: {event.src_path}")
            time.sleep(0.5)
            self.manager.load_and_apply()
            
    def on_deleted(self, event):
        """File deletion event"""
        if event.is_directory:
            return
            
        if os.path.basename(event.src_path) == self.config_filename:
            print(f"[{time.strftime('%H:%M:%S')}] Config file deletion detected: {event.src_path}")
            self.manager.load_and_apply()


def main():
    parser = argparse.ArgumentParser(description="Intermittent Packet Loss Policy Auto-sync Script (File Monitoring Version)")
    parser.add_argument(
        "--config-path",
        default=DEFAULT_CONFIG_PATH,
        help=f"Config file directory path (default: {DEFAULT_CONFIG_PATH})"
    )
    parser.add_argument(
        "--config-file",
        default=DEFAULT_CONFIG_FILE,
        help=f"Config file name (default: {DEFAULT_CONFIG_FILE})"
    )
    args = parser.parse_args()
    
    # Check permissions
    if os.geteuid() != 0:
        print("Error: Must run this script with sudo")
        sys.exit(1)
        
    # Create config directory
    os.makedirs(args.config_path, exist_ok=True)
    
    config_file_path = os.path.join(args.config_path, args.config_file)
    
    # Create manager
    manager = PacketLossManager(config_file_path)
    
    # Register exit signals
    signal.signal(signal.SIGINT, manager.cleanup)
    signal.signal(signal.SIGTERM, manager.cleanup)
    
    # Initialize environment
    manager.init_env()
    
    # Load config for the first time
    manager.load_and_apply()
    
    # Setup file monitoring
    event_handler = ConfigFileHandler(manager, args.config_file)
    observer = Observer()
    observer.schedule(event_handler, args.config_path, recursive=False)
    observer.start()
    
    print("=" * 60)
    print("Intermittent Packet Loss Policy Auto-sync Script Started (File Monitoring Mode)")
    print(f"Config directory: {args.config_path}")
    print(f"Config file: {config_file_path}")
    print(f"Policy chain: {CHAIN_NAME}")
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
