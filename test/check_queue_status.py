#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
队列状态检查工具
用于诊断Worker卡住的问题
"""

import sys
import os
import redis
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_queue_status():
    """检查队列状态"""
    
    print("=" * 80)
    print("🔍 队列状态诊断工具")
    print("=" * 80)
    print()
    
    # 1. 检查配置
    print("【1. 配置检查】")
    try:
        from config import QUEUE_MODE_ENABLED, QUEUE_REDIS_CONFIG, QUEUE_NAMES
        print(f"✅ 队列模式: {'启用' if QUEUE_MODE_ENABLED else '禁用'}")
        print(f"✅ Redis地址: {QUEUE_REDIS_CONFIG['host']}:{QUEUE_REDIS_CONFIG['port']}")
        print(f"✅ 配置的队列名称:")
        for key, value in QUEUE_NAMES.items():
            print(f"   - {key}: {value}")
    except ImportError as e:
        print(f"⚠️  无法导入config: {e}")
        # 使用默认值
        QUEUE_REDIS_CONFIG = {'host': 'localhost', 'port': 6379, 'db': 0}
        QUEUE_NAMES = {
            'ip_upload': 'botnet:ip_upload_queue',
            'task_queue': 'botnet:ip_upload_queue'
        }
    
    print()
    
    # 2. 检查旧配置（如果存在）
    print("【2. 旧配置检查】")
    try:
        from task_queue import QUEUE_NAME as OLD_QUEUE_NAME
        print(f"⚠️  检测到旧的task_queue.py，使用队列: {OLD_QUEUE_NAME}")
        if OLD_QUEUE_NAME != QUEUE_NAMES['task_queue']:
            print(f"❌ 警告：队列名称不匹配！")
            print(f"   - 旧配置: {OLD_QUEUE_NAME}")
            print(f"   - 新配置: {QUEUE_NAMES['task_queue']}")
            print(f"   - 建议：删除或重命名 backend/task_queue.py")
    except ImportError:
        print("✅ 未检测到旧的task_queue.py（正常）")
    
    print()
    
    # 3. 测试Redis连接
    print("【3. Redis连接测试】")
    try:
        redis_client = redis.Redis(
            host=QUEUE_REDIS_CONFIG['host'],
            port=QUEUE_REDIS_CONFIG['port'],
            db=QUEUE_REDIS_CONFIG.get('db', 0),
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        redis_client.ping()
        print("✅ Redis连接成功")
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        print("   - 请确保Redis已启动: redis-server")
        print("   - 检查防火墙和端口: netstat -ano | findstr :6379")
        return
    
    print()
    
    # 4. 检查所有可能的队列
    print("【4. 队列状态检查】")
    queue_names_to_check = [
        'botnet:ip_upload_queue',
        'botnet:task_queue',
    ]
    
    # 添加配置中的队列名称
    for name in QUEUE_NAMES.values():
        if name not in queue_names_to_check:
            queue_names_to_check.append(name)
    
    total_tasks = 0
    for queue_name in queue_names_to_check:
        try:
            length = redis_client.llen(queue_name)
            if length > 0:
                print(f"📋 {queue_name}: {length} 个任务")
                total_tasks += length
                
                # 显示第一个任务的预览
                first_task = redis_client.lindex(queue_name, 0)
                if first_task:
                    import json
                    try:
                        task_data = json.loads(first_task)
                        print(f"   └─ 首个任务: {task_data.get('task_id', 'N/A')}, "
                              f"类型: {task_data.get('botnet_type', 'N/A')}, "
                              f"IP数: {len(task_data.get('ip_data', []))}")
                    except:
                        print(f"   └─ 首个任务: {first_task[:100]}...")
            else:
                print(f"⚪ {queue_name}: 空")
        except Exception as e:
            print(f"⚠️  {queue_name}: 检查失败 - {e}")
    
    print()
    print(f"📊 总计: {total_tasks} 个待处理任务")
    
    print()
    
    # 5. 检查Redis客户端连接数
    print("【5. Redis客户端检查】")
    try:
        clients = redis_client.client_list()
        print(f"📡 当前连接数: {len(clients)}")
        
        # 筛选与队列相关的连接
        queue_clients = [c for c in clients if 'blpop' in c.get('cmd', '').lower()]
        if queue_clients:
            print(f"🔄 正在等待队列的客户端: {len(queue_clients)}")
            for client in queue_clients:
                addr = client.get('addr', 'N/A')
                age = client.get('age', 'N/A')
                cmd = client.get('cmd', 'N/A')
                print(f"   - {addr}, 运行时间: {age}秒, 命令: {cmd}")
        else:
            print("⚠️  没有客户端在等待队列（Worker可能未运行）")
    except Exception as e:
        print(f"⚠️  无法获取客户端列表: {e}")
    
    print()
    
    # 6. 建议
    print("【6. 诊断建议】")
    
    if total_tasks > 0:
        print(f"✅ 检测到 {total_tasks} 个任务在队列中")
        if len(queue_clients) == 0:
            print("❌ 但没有Worker在消费队列！")
            print()
            print("🔧 解决方案：")
            print("   1. 启动Worker进程:")
            print("      cd backend/log_processor")
            print("      python worker.py")
            print()
            print("   2. 或使用旧版Worker:")
            print("      cd backend")
            print("      python worker.py")
        else:
            print("✅ 有Worker在运行，数据应该正在处理中")
            print("   如果Worker卡住不动，请检查Worker日志:")
            print("   tail -f logs/worker.log")
    else:
        print("⚪ 队列中没有任务")
        print()
        print("🔧 可能的原因：")
        print("   1. 主程序未运行或未推送数据")
        print("   2. Worker已经处理完所有任务")
        print("   3. 队列名称不匹配")
        print()
        print("📝 检查主程序日志:")
        print("   tail -f logs/log_processor.log")
    
    print()
    print("=" * 80)


if __name__ == '__main__':
    try:
        check_queue_status()
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
