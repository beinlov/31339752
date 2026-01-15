#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志处理器启动诊断工具
检查日志处理器的配置和启动状态
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_config():
    """检查配置"""
    print("="*60)
    print("步骤1: 检查配置")
    print("="*60)
    
    try:
        from config import (
            C2_ENDPOINTS, 
            ENABLE_REMOTE_PULLING,
            C2_PULL_INTERVAL_MINUTES,
            BACKPRESSURE_CONFIG,
            INTERNAL_WORKER_CONFIG,
            QUEUE_REDIS_CONFIG,
            QUEUE_MODE_ENABLED
        )
        
        print(f"\n✅ 配置文件加载成功")
        
        # 检查C2端点
        print(f"\n【C2端点配置】")
        print(f"C2_ENDPOINTS 数量: {len(C2_ENDPOINTS)}")
        for i, c2 in enumerate(C2_ENDPOINTS):
            print(f"\n  端点 {i+1}:")
            print(f"    名称: {c2.get('name')}")
            print(f"    URL: {c2.get('url')}")
            print(f"    启用: {c2.get('enabled', True)}")
            print(f"    拉取间隔: {c2.get('pull_interval', 'N/A')} 秒")
        
        # 检查远程拉取开关
        print(f"\n【远程拉取配置】")
        print(f"ENABLE_REMOTE_PULLING: {ENABLE_REMOTE_PULLING}")
        print(f"C2_PULL_INTERVAL_MINUTES: {C2_PULL_INTERVAL_MINUTES} 分钟")
        
        if not ENABLE_REMOTE_PULLING:
            print(f"\n❌ 远程拉取未启用!")
            print(f"   原因: C2_ENDPOINTS为空或所有端点都被禁用")
            return False
        
        # 检查背压控制
        print(f"\n【背压控制配置】")
        print(f"启用: {BACKPRESSURE_CONFIG.get('enabled')}")
        print(f"高水位: {BACKPRESSURE_CONFIG.get('queue_high_watermark')}")
        print(f"低水位: {BACKPRESSURE_CONFIG.get('queue_low_watermark')}")
        
        # 检查队列模式
        print(f"\n【队列模式配置】")
        print(f"启用: {QUEUE_MODE_ENABLED}")
        print(f"Redis主机: {QUEUE_REDIS_CONFIG.get('host')}")
        print(f"Redis端口: {QUEUE_REDIS_CONFIG.get('port')}")
        print(f"队列名称: {QUEUE_REDIS_CONFIG.get('queue_name')}")
        
        # 检查内置Worker
        print(f"\n【内置Worker配置】")
        print(f"启用: {INTERNAL_WORKER_CONFIG.get('enabled')}")
        print(f"Worker数量: {INTERNAL_WORKER_CONFIG.get('worker_count')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_remote_puller():
    """检查远程拉取器"""
    print(f"\n{'='*60}")
    print("步骤2: 检查远程拉取器初始化")
    print("="*60)
    
    try:
        from config import C2_ENDPOINTS
        from log_processor.remote_puller import RemotePuller
        
        # 创建一个简单的mock处理器
        class MockProcessor:
            async def process_api_data(self, botnet_type, ip_data):
                print(f"[Mock] 接收到 {botnet_type} 的 {len(ip_data)} 条数据")
        
        mock_processor = MockProcessor()
        
        print(f"\n正在初始化RemotePuller...")
        puller = RemotePuller(C2_ENDPOINTS, mock_processor)
        print(f"✅ RemotePuller初始化成功")
        
        print(f"\n【拉取器属性】")
        print(f"C2配置数量: {len(puller.c2_config)}")
        print(f"运行状态: {puller.running}")
        print(f"背压状态: {puller.backpressure_active}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ RemotePuller初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_imports():
    """检查导入"""
    print(f"\n{'='*60}")
    print("步骤3: 检查模块导入")
    print("="*60)
    
    modules = [
        'config',
        'log_processor.remote_puller',
        'log_processor.task_queue',
        'log_processor.db_writer',
        'log_processor.watcher',
    ]
    
    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module}: {e}")
            all_ok = False
    
    return all_ok

def check_redis():
    """检查Redis连接"""
    print(f"\n{'='*60}")
    print("步骤4: 检查Redis连接")
    print("="*60)
    
    try:
        from config import QUEUE_REDIS_CONFIG, QUEUE_MODE_ENABLED
        import redis
        
        if not QUEUE_MODE_ENABLED:
            print(f"⚠️  队列模式未启用，跳过Redis检查")
            return True
        
        redis_host = QUEUE_REDIS_CONFIG.get('host', 'localhost')
        redis_port = QUEUE_REDIS_CONFIG.get('port', 6379)
        
        print(f"\n连接到 {redis_host}:{redis_port}...")
        
        r = redis.Redis(
            host=redis_host,
            port=redis_port,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        
        r.ping()
        print(f"✅ Redis连接成功")
        
        # 检查队列长度
        queue_name = QUEUE_REDIS_CONFIG.get('queue_name', 'botnet:ip_upload_queue')
        queue_len = r.llen(queue_name)
        print(f"队列 '{queue_name}' 长度: {queue_len}")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        print(f"\n请确保Redis正在运行:")
        print(f"  redis-server")
        return False

def main():
    """主函数"""
    print("="*60)
    print("日志处理器启动诊断工具")
    print("="*60)
    
    results = []
    
    # 检查配置
    results.append(("配置检查", check_config()))
    
    # 检查导入
    results.append(("模块导入", check_imports()))
    
    # 检查Redis
    results.append(("Redis连接", check_redis()))
    
    # 检查远程拉取器
    results.append(("远程拉取器", check_remote_puller()))
    
    # 总结
    print(f"\n{'='*60}")
    print("诊断总结")
    print("="*60)
    
    all_passed = True
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    print(f"\n{'='*60}")
    
    if all_passed:
        print("✅ 所有检查通过!")
        print("\n如果日志处理器仍然无法拉取数据，请:")
        print("1. 确保C2服务正在运行: python backend/remote/c2_data_server.py")
        print("2. 启动日志处理器并查看日志输出")
        print("3. 确认看到以下日志:")
        print("   - '远程拉取器已启动'")
        print("   - '执行首次数据拉取...'")
        print("   - '开始拉取循环'")
    else:
        print("❌ 部分检查失败，请先解决上述问题")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n诊断已取消")
    except Exception as e:
        print(f"\n❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
