#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP Blacklist Management Script - File Monitoring Version
Deployed on gateway devices to monitor local config file changes and auto-apply to iptables

How it works:
1. Platform pushes IP blacklist config file via SSH
2. This script uses watchdog to monitor config file changes
3. When config file updates, automatically apply to iptables ipset

Deployment: Gateway device (device that can filter Bot traffic)
Dependencies: ipset, iptables, watchdog

Usage:
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

# Default configuration
DEFAULT_CONFIG_PATH = "/opt/suppression_config"
DEFAULT_CONFIG_FILE = "ip_blacklist.txt"
SET_NAME = "blacklist_set"


def run_cmd(cmd):
    """Execute system command"""
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class IPBlacklistManager:
    """IP Blacklist Manager"""
    
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.set_name = SET_NAME
        self.initialized = False
        
    def cleanup(self, signum=None, frame=None):
        """Cleanup function: remove iptables rules and ipset"""
        print(f"\n[{time.strftime('%H:%M:%S')}] Script stopping, cleaning up firewall rules...")
        run_cmd(["sudo", "iptables", "-D", "FORWARD", "-m", "set", "--match-set", self.set_name, "dst", "-j", "DROP"])
        run_cmd(["sudo", "iptables", "-D", "OUTPUT", "-m", "set", "--match-set", self.set_name, "dst", "-j", "DROP"])
        run_cmd(["sudo", "ipset", "destroy", self.set_name])
        print("Environment cleaned, original firewall policy unchanged.")
        sys.exit(0)
        
    def init_env(self):
        """Initialize environment: ensure ipset is installed and create ipset"""
        print("Initializing IP blacklist management environment...")
        
        # Check if ipset is installed
        if run_cmd(["which", "ipset"]).returncode != 0:
            print("Error: ipset not found, please run: sudo apt install ipset")
            sys.exit(1)
            
        # Clean up possible remnants
        run_cmd(["sudo", "iptables", "-D", "FORWARD", "-m", "set", "--match-set", self.set_name, "dst", "-j", "DROP"])
        run_cmd(["sudo", "iptables", "-D", "OUTPUT", "-m", "set", "--match-set", self.set_name, "dst", "-j", "DROP"])
        run_cmd(["sudo", "ipset", "destroy", self.set_name])
        
        # Create ipset
        run_cmd(["sudo", "ipset", "create", self.set_name, "hash:ip"])
        
        # Insert iptables rules
        run_cmd(["sudo", "iptables", "-I", "FORWARD", "1", "-m", "set", "--match-set", self.set_name, "dst", "-j", "DROP"])
        run_cmd(["sudo", "iptables", "-I", "OUTPUT", "1", "-m", "set", "--match-set", self.set_name, "dst", "-j", "DROP"])
        
        print(f"IP blacklist set {self.set_name} mounted to iptables")
        self.initialized = True
        
    def load_and_apply(self):
        """Load IP blacklist from config file and apply"""
        if not self.initialized:
            return
            
        try:
            # Check if config file exists
            if not os.path.exists(self.config_file_path):
                print(f"[{time.strftime('%H:%M:%S')}] Config file not found: {self.config_file_path}")
                return
                
            # Read config file
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Extract valid IP addresses
            ips = []
            for line in lines:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    ips.append(line)
                    
            # Full update ipset (flush then add)
            run_cmd(["sudo", "ipset", "flush", self.set_name])
            
            for ip in ips:
                run_cmd(["sudo", "ipset", "add", self.set_name, ip])
                
            print(f"[{time.strftime('%H:%M:%S')}] IP blacklist updated, contains {len(ips)} IPs")
            
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Failed to load config: {e}")


class ConfigFileHandler(FileSystemEventHandler):
    """Config file change listener"""
    
    def __init__(self, manager, config_filename):
        self.manager = manager
        self.config_filename = config_filename
        
    def on_modified(self, event):
        """File modification event"""
        if event.is_directory:
            return
            
        # Only process target config file
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


def main():
    parser = argparse.ArgumentParser(description="IP Blacklist Auto-sync Script (File Monitoring Version)")
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
        
    # Create config directory if not exists
    os.makedirs(args.config_path, exist_ok=True)
    
    config_file_path = os.path.join(args.config_path, args.config_file)
    
    # Create manager
    manager = IPBlacklistManager(config_file_path)
    
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
    print("IP Blacklist Auto-sync Script Started (File Monitoring Mode)")
    print(f"Config directory: {args.config_path}")
    print(f"Config file: {config_file_path}")
    print(f"ipset name: {SET_NAME}")
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
