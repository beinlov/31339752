#!/usr/bin/env python3
"""
重置平台端拉取状态
用于解决断点续传不一致的问题
"""
import json
import os
from pathlib import Path

# 状态文件路径（与remote_puller.py中的state_file保持一致）
STATE_FILE = Path(__file__).parent / '.remote_puller_state.json'

def reset_pull_state(c2_name=None):
    """
    重置拉取状态
    
    Args:
        c2_name: 要重置的C2端点名称，None表示全部重置
    """
    print("=" * 60)
    print("重置平台端拉取状态")
    print("=" * 60)
    print()
    
    if not STATE_FILE.exists():
        print("⚠️  状态文件不存在，无需重置")
        return
    
    # 读取当前状态
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        state = json.load(f)
    
    print("【当前状态】")
    print(f"  last_seq_ids: {state.get('last_seq_ids', {})}")
    print(f"  last_timestamps: {state.get('last_timestamps', {})}")
    print()
    
    # 备份
    backup_file = STATE_FILE.with_suffix('.json.backup')
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    print(f"✅ 已备份到: {backup_file}")
    print()
    
    # 重置
    if c2_name:
        # 只重置指定C2
        if c2_name in state.get('last_seq_ids', {}):
            del state['last_seq_ids'][c2_name]
            print(f"✅ 已清除 {c2_name} 的 seq_id 游标")
        
        if c2_name in state.get('last_timestamps', {}):
            del state['last_timestamps'][c2_name]
            print(f"✅ 已清除 {c2_name} 的 timestamp 游标")
    else:
        # 重置全部
        state['last_seq_ids'] = {}
        state['last_timestamps'] = {}
        print("✅ 已清除所有 C2 端点的游标")
    
    # 保存
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    
    print()
    print("【新状态】")
    print(f"  last_seq_ids: {state.get('last_seq_ids', {})}")
    print(f"  last_timestamps: {state.get('last_timestamps', {})}")
    print()
    print("=" * 60)
    print("重置完成！下次拉取将从头开始")
    print("⚠️  注意：如果C2缓存数据量很大，重新拉取可能需要较长时间")
    print("=" * 60)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        c2_name = sys.argv[1]
        print(f"将重置 C2: {c2_name}")
        print()
        reset_pull_state(c2_name)
    else:
        print("将重置所有 C2 端点")
        print()
        confirm = input("确认重置？(yes/no): ")
        if confirm.lower() in ['yes', 'y']:
            reset_pull_state()
        else:
            print("已取消")
