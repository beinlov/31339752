#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统负载实时监控脚本
监控队列长度、处理速度、延迟等关键指标
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import redis
from datetime import datetime
from config import QUEUE_REDIS_CONFIG

def monitor_load():
    """实时监控系统负载"""
    
    try:
        # 连接Redis
        r = redis.Redis(
            host=QUEUE_REDIS_CONFIG.get('host', 'localhost'),
            port=QUEUE_REDIS_CONFIG.get('port', 6379),
            db=QUEUE_REDIS_CONFIG.get('db', 0),
            decode_responses=True
        )
        
        queue_name = QUEUE_REDIS_CONFIG.get('queue_name', 'botnet:ip_upload_queue')
        
        print("\n" + "="*80)
        print("系统负载实时监控 (按 Ctrl+C 停止)")
        print("="*80)
        print()
        
        last_queue_len = 0
        check_count = 0
        
        while True:
            check_count += 1
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 获取队列长度
            queue_len = r.llen(queue_name)
            
            # 计算队列变化速度
            queue_change = queue_len - last_queue_len
            
            # 获取Redis内存使用
            redis_info = r.info('memory')
            memory_used_mb = redis_info['used_memory'] / 1024 / 1024
            
            # 评估状态
            if queue_len == 0:
                status = "✅ 空闲"
                color = ""
            elif queue_len < 1000:
                status = "✅ 正常"
                color = ""
            elif queue_len < 5000:
                status = "⚠️  轻度积压"
                color = ""
            elif queue_len < 10000:
                status = "⚠️  中度积压"
                color = ""
            else:
                status = "❌ 严重积压"
                color = ""
            
            # 计算处理速度（条/秒）
            if queue_change < 0:
                process_speed = abs(queue_change) / 5  # 每5秒检查一次
                speed_info = f"处理中 ({process_speed:.1f}条/秒)"
            elif queue_change > 0:
                speed_info = f"积压增加 (+{queue_change}条)"
            else:
                speed_info = "稳定"
            
            # 显示信息
            print(f"[{current_time}] {status}")
            print(f"  队列长度: {queue_len:,} 条")
            print(f"  变化量: {queue_change:+d} 条 ({speed_info})")
            print(f"  Redis内存: {memory_used_mb:.2f} MB")
            
            # 预警
            if queue_len > 10000:
                print(f"  ⚠️  警告: 队列积压严重，可能触发背压控制！")
            elif queue_len > 5000:
                print(f"  💡 建议: 考虑增加Worker数量")
            
            print("-" * 80)
            
            last_queue_len = queue_len
            
            # 每5秒检查一次
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n监控已停止")
    except Exception as e:
        print(f"\n❌ 监控失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    monitor_load()
