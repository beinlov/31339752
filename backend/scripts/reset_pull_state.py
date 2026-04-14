#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置远程拉取器状态
解决拉取不到数据的问题
"""

import os
import json
import sys
from datetime import datetime

STATE_FILE = '.remote_puller_state.json'


def check_state():
    """检查当前状态"""
    if not os.path.exists(STATE_FILE):
        print("[INFO] 状态文件不存在")
        return None
    
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        print("\n" + "=" * 60)
        print("当前拉取状态")
        print("=" * 60)
        
        timestamps = state.get('last_timestamps', {})
        updated_at = state.get('updated_at', 'unknown')
        
        print(f"状态文件更新时间: {updated_at}")
        print(f"记录的C2端点数: {len(timestamps)}")
        print()
        
        if timestamps:
            print("各端点的断点续传时间戳:")
            for name, ts in timestamps.items():
                print(f"  {name}: {ts}")
        else:
            print("  (无记录)")
        
        print()
        return state
    except Exception as e:
        print(f"[ERROR] 读取状态文件失败: {e}")
        return None


def reset_state():
    """重置拉取状态"""
    if not os.path.exists(STATE_FILE):
        print("[INFO] 状态文件不存在，无需重置")
        return
    
    try:
        # 备份原文件
        backup_file = f"{STATE_FILE}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(STATE_FILE, 'r') as f:
            content = f.read()
        with open(backup_file, 'w') as f:
            f.write(content)
        
        print(f"[OK] 已备份状态文件到: {backup_file}")
        
        # 删除状态文件
        os.remove(STATE_FILE)
        print(f"[OK] 已删除状态文件: {STATE_FILE}")
        print()
        print("=" * 60)
        print("状态已重置！")
        print("=" * 60)
        print()
        print("下次日志处理器启动时将:")
        print("  1. 不使用since参数")
        print("  2. 拉取C2端的全部数据")
        print("  3. 重新建立断点续传状态")
        print()
        
    except Exception as e:
        print(f"[ERROR] 重置失败: {e}")


def reset_specific_endpoint(endpoint_name):
    """重置特定端点的时间戳"""
    if not os.path.exists(STATE_FILE):
        print("[INFO] 状态文件不存在")
        return
    
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        if endpoint_name in state.get('last_timestamps', {}):
            del state['last_timestamps'][endpoint_name]
            state['updated_at'] = datetime.now().isoformat()
            
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
            
            print(f"[OK] 已重置端点 {endpoint_name} 的时间戳")
        else:
            print(f"[INFO] 端点 {endpoint_name} 不存在")
    
    except Exception as e:
        print(f"[ERROR] 重置失败: {e}")


def main():
    """主函数"""
    print()
    print("=" * 60)
    print("远程拉取器状态管理工具")
    print("=" * 60)
    print()
    
    # 切换到backend目录
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'check':
            # 检查状态
            check_state()
        
        elif command == 'reset':
            # 重置全部
            if len(sys.argv) > 2:
                # 重置特定端点
                endpoint = sys.argv[2]
                reset_specific_endpoint(endpoint)
            else:
                # 重置全部
                check_state()
                print()
                confirm = input("确认要重置拉取状态吗? [y/N]: ")
                if confirm.lower() == 'y':
                    reset_state()
                else:
                    print("[CANCEL] 已取消")
        
        else:
            print(f"[ERROR] 未知命令: {command}")
            print_usage()
    
    else:
        # 默认：检查并提示
        state = check_state()
        
        if state:
            print()
            print("=" * 60)
            print("可能的问题")
            print("=" * 60)
            
            timestamps = state.get('last_timestamps', {})
            if timestamps:
                print()
                print("如果拉取不到数据，可能的原因:")
                print("  1. since时间戳太新，C2端在此之后无新数据")
                print("  2. C2端的数据时间戳都比since早")
                print()
                print("解决方案:")
                print("  运行: python reset_pull_state.py reset")
                print("  这将清除时间戳，下次拉取全部数据")
                print()
        
        print()
        print("用法:")
        print_usage()


def print_usage():
    """打印用法"""
    print("  python reset_pull_state.py check              # 查看状态")
    print("  python reset_pull_state.py reset              # 重置全部状态")
    print("  python reset_pull_state.py reset <endpoint>   # 重置特定端点")
    print()
    print("示例:")
    print("  python reset_pull_state.py check")
    print("  python reset_pull_state.py reset")
    print("  python reset_pull_state.py reset C2-test-local")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[CANCEL] 已取消")
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
