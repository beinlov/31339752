#!/usr/bin/env python3
"""调试配置加载"""

import json
import os
from pathlib import Path

def load_config(config_file: str = "config.json"):
    """加载配置文件"""
    default_config = {
        "botnet": {
            "botnet_type": "ramnit",
            "log_dir": "/home/ubuntu/logs",
            "log_file_pattern": "ramnit_{datetime}.log"
        }
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"[OK] 加载配置文件: {config_file}")
                return config
        except Exception as e:
            print(f"[FAIL] 加载配置失败: {e}，使用默认配置")
            return default_config
    else:
        print(f"[FAIL] 配置文件不存在: {config_file}，使用默认配置")
        return default_config

CONFIG = load_config()
LOG_SOURCES_RAW = CONFIG.get("log_sources", {})
LOG_SOURCES = {k: v for k, v in LOG_SOURCES_RAW.items() if not k.startswith('_')}

print(f"\nLOG_SOURCES_RAW keys: {list(LOG_SOURCES_RAW.keys())}")
print(f"LOG_SOURCES keys (filtered): {list(LOG_SOURCES.keys())}")
print(f"LOG_SOURCES empty? {not LOG_SOURCES}")
print(f"LOG_SOURCES bool: {bool(LOG_SOURCES)}")

if LOG_SOURCES:
    print("\n[OK] 多日志源模式")
    for name, config in LOG_SOURCES.items():
        print(f"  - {name}: {config.get('log_type')}")
else:
    print("\n[FAIL] 兼容模式（单日志源）")
