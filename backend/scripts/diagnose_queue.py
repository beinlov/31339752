#!/usr/bin/env python3
"""
诊断数据传输问题：检查队列和数据流
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_queue_mode():
    """检查队列模式配置"""
    print("=" * 80)
    print("诊断数据传输问题")
    print("=" * 80)
    
    # 1. 检查是否启用队列模式
    print("\n【1. 检查队列模式】")
    try:
        from task_queue import task_queue
        print("  ✅ task_queue模块已导入")
        print(f"  ✅ task_queue对象: {task_queue}")
        
        # 检查Redis连接
        try:
            queue_len = task_queue.get_queue_length()
            print(f"  ✅ Redis连接正常")
            print(f"  ✅ 当前队列长度: {queue_len}")
            
            if queue_len > 0:
                print(f"\n  ⚠️  警告：队列中有 {queue_len} 个待处理任务！")
                print("  原因：数据已推送到Redis队列，但没有Worker在消费")
                print("\n  解决方案：")
                print("    方案1（推荐）：启动Worker")
                print("      cd backend")
                print("      python worker.py")
                print("\n    方案2：禁用队列模式")
                print("      重命名或删除 backend/task_queue.py")
                print("      重启日志处理器")
        except Exception as e:
            print(f"  ❌ Redis连接失败: {e}")
            print("  原因：task_queue模块存在但Redis不可用")
            print("  建议：检查Redis服务是否运行")
            
    except ImportError as e:
        print("  ⚠️  task_queue模块未导入")
        print("  说明：将使用直接处理模式（不经过队列）")
        print("  这是正常的，数据应该直接写入数据库")
    
    # 2. 检查日志处理器配置
    print("\n【2. 检查日志处理器配置】")
    try:
        # 模拟main.py的导入逻辑
        try:
            from task_queue import task_queue
            USE_QUEUE_FOR_PULLING = True
        except ImportError:
            task_queue = None
            USE_QUEUE_FOR_PULLING = False
        
        print(f"  USE_QUEUE_FOR_PULLING: {USE_QUEUE_FOR_PULLING}")
        print(f"  task_queue对象: {task_queue}")
        
        if USE_QUEUE_FOR_PULLING and task_queue:
            print("\n  📋 队列模式已启用")
            print("  数据流: C2端 → 平台拉取器 → Redis队列 → Worker → 数据库")
            print("  ⚠️  必须启动Worker才能处理数据！")
        else:
            print("\n  📋 直接处理模式")
            print("  数据流: C2端 → 平台拉取器 → IP富化 → 数据库")
            print("  ✅ 数据应该直接写入数据库")
            
    except Exception as e:
        print(f"  ❌ 检查失败: {e}")
    
    # 3. 检查Worker进程
    print("\n【3. 检查Worker进程】")
    try:
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        worker_lines = [line for line in result.stdout.split('\n') if 'worker.py' in line.lower()]
        
        if worker_lines:
            print("  ✅ 找到Worker进程：")
            for line in worker_lines:
                print(f"    {line}")
        else:
            print("  ❌ 未找到Worker进程")
            print("  如果队列模式已启用，需要启动Worker：")
            print("    python backend/worker.py")
    except Exception as e:
        # Windows系统没有ps命令
        print("  ⚠️  无法检查进程（Windows系统）")
        print("  请手动检查是否运行了worker.py")
    
    # 4. 检查Redis队列内容
    print("\n【4. 检查Redis队列详情】")
    try:
        from task_queue import task_queue
        import json
        
        queue_len = task_queue.get_queue_length()
        print(f"  队列长度: {queue_len}")
        
        if queue_len > 0:
            # 尝试查看队列中的任务
            try:
                import redis
                r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                
                # 查看前5个任务
                tasks = r.lrange('botnet:task_queue', 0, 4)
                print(f"\n  前{len(tasks)}个任务预览：")
                for i, task_json in enumerate(tasks, 1):
                    try:
                        task = json.loads(task_json)
                        print(f"\n  任务 #{i}:")
                        print(f"    ID: {task.get('task_id')}")
                        print(f"    类型: {task.get('botnet_type')}")
                        print(f"    IP数: {len(task.get('ip_data', []))}")
                        print(f"    创建时间: {task.get('created_at')}")
                    except:
                        print(f"  任务 #{i}: 无法解析")
            except Exception as e:
                print(f"  ⚠️  无法查看队列详情: {e}")
                
    except ImportError:
        print("  ⚠️  队列模式未启用，跳过")
    except Exception as e:
        print(f"  ❌ 检查失败: {e}")
    
    # 5. 给出建议
    print("\n" + "=" * 80)
    print("诊断总结")
    print("=" * 80)
    
    try:
        from task_queue import task_queue
        queue_len = task_queue.get_queue_length()
        
        if queue_len > 0:
            print("\n⚠️  问题确认：")
            print(f"  - 队列模式已启用")
            print(f"  - Redis队列中有 {queue_len} 个待处理任务")
            print(f"  - 但是没有Worker在消费队列")
            
            print("\n✅ 解决方案（二选一）：")
            print("\n【方案1：启动Worker（推荐）】")
            print("  cd backend")
            print("  python worker.py")
            print("  # Worker会自动处理队列中的任务")
            print("  # 可以启动多个Worker并发处理")
            
            print("\n【方案2：禁用队列模式】")
            print("  # 临时禁用")
            print("  mv backend/task_queue.py backend/task_queue.py.bak")
            print("  # 重启日志处理器")
            print("  pkill -f main.py && python backend/log_processor/main.py")
            print("  # 数据将直接处理，不经过队列")
            
        else:
            print("\n✅ 队列正常")
            print("  - 队列中没有积压任务")
            if task_queue:
                print("  - 队列模式已启用且运行正常")
            
    except ImportError:
        print("\n📋 当前配置：")
        print("  - 队列模式未启用（task_queue模块不存在）")
        print("  - 使用直接处理模式")
        print("  - 数据应该直接写入数据库")
        print("\n如果数据仍未写入，请检查：")
        print("  1. 日志处理器是否正常运行")
        print("  2. 日志中是否有错误信息")
        print("  3. botnet_type是否匹配")

if __name__ == '__main__':
    check_queue_mode()
