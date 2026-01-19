#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
C2连接健康监控脚本
建议每5分钟运行一次（crontab或Windows任务计划）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import time
from datetime import datetime

def check_c2_health():
    """检查C2连接健康状态"""
    
    from config import C2_ENDPOINTS
    
    results = []
    all_healthy = True
    
    for c2 in C2_ENDPOINTS:
        if not c2.get('enabled'):
            continue
            
        name = c2['name']
        url = c2['url']
        api_key = c2['api_key']
        
        start_time = time.time()
        status = {
            'name': name,
            'url': url,
            'healthy': False,
            'response_time': None,
            'error': None
        }
        
        try:
            # 测试连接
            test_url = f"{url}/api/pull"
            headers = {'X-API-Key': api_key}
            params = {'limit': 1, 'confirm': 'false'}
            
            response = requests.get(test_url, headers=headers, params=params, timeout=10)
            response_time = (time.time() - start_time) * 1000  # ms
            
            if response.status_code == 200:
                status['healthy'] = True
                status['response_time'] = f"{response_time:.0f}ms"
            else:
                status['error'] = f"HTTP {response.status_code}"
                all_healthy = False
                
        except requests.exceptions.Timeout:
            status['error'] = "连接超时"
            all_healthy = False
        except requests.exceptions.ConnectionError:
            status['error'] = "连接失败"
            all_healthy = False
        except Exception as e:
            status['error'] = str(e)
            all_healthy = False
        
        results.append(status)
    
    # 输出结果
    print(f"\n{'='*60}")
    print(f"C2连接健康检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    for r in results:
        symbol = "✅" if r['healthy'] else "❌"
        print(f"{symbol} [{r['name']}]")
        print(f"   URL: {r['url']}")
        if r['healthy']:
            print(f"   响应时间: {r['response_time']}")
        else:
            print(f"   错误: {r['error']}")
        print()
    
    # 如果有问题，发送告警（可以集成邮件、钉钉、企业微信等）
    if not all_healthy:
        print("⚠️ 警告：部分C2连接异常，请检查网络或服务状态")
        # TODO: 发送告警通知
        return 1
    else:
        print("✅ 所有C2连接正常")
        return 0

if __name__ == '__main__':
    exit_code = check_c2_health()
    sys.exit(exit_code)
