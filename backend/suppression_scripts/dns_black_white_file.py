#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNS Domain Blacklist Management Script - File Monitoring Version
Deployed on DNS server to monitor local config file changes and auto-apply to dnsmasq

How it works:
1. Platform pushes domain blacklist config file via SSH
2. This script uses watchdog to monitor config file changes
3. When config file updates, automatically generate dnsmasq config and restart service

Deployment: DNS server (device running dnsmasq)
Dependencies: dnsmasq, watchdog

Usage:
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

# Default configuration
DEFAULT_CONFIG_PATH = "/opt/suppression_config"
DEFAULT_CONFIG_FILE = "domain_blacklist.txt"
DEFAULT_DNSMASQ_CONF = "/etc/dnsmasq.d/dns_blacklist.conf"


class DomainBlacklistManager:
    """Domain Blacklist Manager"""
    
    def __init__(self, config_file_path, dnsmasq_conf_path):
        self.config_file_path = config_file_path
        self.dnsmasq_conf_path = dnsmasq_conf_path
        
    def load_and_apply(self):
        """Load domain blacklist from config file and apply to dnsmasq"""
        try:
            # Check if config file exists
            if not os.path.exists(self.config_file_path):
                print(f"[{time.strftime('%H:%M:%S')}] Config file not found: {self.config_file_path}")
                return
                
            # Read config file
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Extract valid domains
            domains = []
            for line in lines:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    domains.append(line)
                    
            # Generate dnsmasq config content
            new_content = "# Auto-generated blacklist by platform\n"
            new_content += f"# Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            for domain in domains:
                # Point domain to 0.0.0.0 to block
                new_content += f"address=/{domain}/0.0.0.0\n"
                
            # Check if there are updates (avoid unnecessary service restarts)
            if os.path.exists(self.dnsmasq_conf_path):
                with open(self.dnsmasq_conf_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
                    
                if current_content == new_content:
                    print(f"[{time.strftime('%H:%M:%S')}] Domain blacklist unchanged, skipping update")
                    return
                    
            # Write dnsmasq config file
            with open(self.dnsmasq_conf_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            # Restart dnsmasq service
            print(f"[{time.strftime('%H:%M:%S')}] Update detected, restarting dnsmasq...")
            result = subprocess.run(
                ["sudo", "systemctl", "restart", "dnsmasq"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"[{time.strftime('%H:%M:%S')}] Domain blacklist updated, contains {len(domains)} domains")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] dnsmasq restart failed: {result.stderr}")
                
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Failed to load config: {e}")
            
    def cleanup(self, signum=None, frame=None):
        """Cleanup function"""
        print(f"\n[{time.strftime('%H:%M:%S')}] Script stopping")
        # Optional: remove dnsmasq config file
        # if os.path.exists(self.dnsmasq_conf_path):
        #     os.remove(self.dnsmasq_conf_path)
        #     subprocess.run(["sudo", "systemctl", "restart", "dnsmasq"])
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


def main():
    parser = argparse.ArgumentParser(description="DNS Domain Blacklist Auto-sync Script (File Monitoring Version)")
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
    parser.add_argument(
        "--dnsmasq-conf",
        default=DEFAULT_DNSMASQ_CONF,
        help=f"dnsmasq config file path (default: {DEFAULT_DNSMASQ_CONF})"
    )
    args = parser.parse_args()
    
    # Check permissions
    if os.geteuid() != 0:
        print("Error: Must run this script with sudo")
        sys.exit(1)
        
    # Check if dnsmasq is installed
    if subprocess.run(["which", "dnsmasq"], capture_output=True).returncode != 0:
        print("Error: dnsmasq not found, please install first")
        sys.exit(1)
        
    # Create config directories
    os.makedirs(args.config_path, exist_ok=True)
    os.makedirs(os.path.dirname(args.dnsmasq_conf), exist_ok=True)
    
    config_file_path = os.path.join(args.config_path, args.config_file)
    
    # Create manager
    manager = DomainBlacklistManager(config_file_path, args.dnsmasq_conf)
    
    # Register exit signals
    signal.signal(signal.SIGINT, manager.cleanup)
    signal.signal(signal.SIGTERM, manager.cleanup)
    
    # Load config for the first time
    manager.load_and_apply()
    
    # Setup file monitoring
    event_handler = ConfigFileHandler(manager, args.config_file)
    observer = Observer()
    observer.schedule(event_handler, args.config_path, recursive=False)
    observer.start()
    
    print("=" * 60)
    print("DNS Domain Blacklist Auto-sync Script Started (File Monitoring Mode)")
    print(f"Config directory: {args.config_path}")
    print(f"Config file: {config_file_path}")
    print(f"dnsmasq config: {args.dnsmasq_conf}")
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
