#!/usr/bin/env python3
"""测试多日志源功能"""

import json
import sqlite3
from pathlib import Path

# 测试1: 检查配置文件
print("=" * 60)
print("测试1: 检查配置文件")
print("=" * 60)

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

log_sources = config.get('log_sources', {})
# 过滤掉注释项
log_sources = {k: v for k, v in log_sources.items() if not k.startswith('_')}
print(f"找到 {len(log_sources)} 个日志源配置:")
for name, source in log_sources.items():
    print(f"  - {name}: {source.get('log_type')} ({source.get('storage_type')})")
    print(f"    路径: {source.get('path')}")
    print(f"    启用: {source.get('enabled')}")

# 测试2: 检查文件是否存在
print("\n" + "=" * 60)
print("测试2: 检查日志文件")
print("=" * 60)

online_config = log_sources.get('online', {})
if online_config:
    online_path = Path(online_config.get('path', ''))
    print(f"上线日志: {online_path}")
    print(f"  存在: {online_path.exists()}")
    if online_path.exists():
        print(f"  大小: {online_path.stat().st_size} 字节")
        # 读取前3行
        with open(online_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 3:
                    break
                print(f"  行{i+1}: {line.strip()}")

# 测试3: 检查数据库
print("\n" + "=" * 60)
print("测试3: 检查数据库")
print("=" * 60)

cleanup_config = log_sources.get('cleanup', {})
if cleanup_config:
    db_path = Path(cleanup_config.get('path', ''))
    print(f"清除日志数据库: {db_path}")
    print(f"  存在: {db_path.exists()}")
    
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"  表: {tables}")
        
        # 查询记录数
        table = cleanup_config.get('db_config', {}).get('table', 'reports')
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  记录数: {count}")
        
        # 显示前3条
        ip_field = cleanup_config.get('field_mapping', {}).get('ip_field', 'client_ip')
        ts_field = cleanup_config.get('field_mapping', {}).get('timestamp_field', 'timestamp')
        cursor.execute(f"SELECT {ip_field}, {ts_field} FROM {table} LIMIT 3")
        rows = cursor.fetchall()
        print(f"  前3条记录:")
        for i, row in enumerate(rows):
            print(f"    {i+1}. IP: {row[0]}, 时间: {row[1]}")
        
        conn.close()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
