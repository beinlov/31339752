#!/usr/bin/env python3
"""
中转服务器示例脚本
模拟中转服务器从C2端拉取数据并推送到本服务器
"""

import requests
import hmac
import hashlib
import json
from datetime import datetime
import time
import argparse
import sys

# 配置（可通过命令行参数覆盖）
DEFAULT_CONFIG = {
    'c2_url': 'http://43.99.37.118:8888',  # C2端地址
    'c2_api_key': 'KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4',
    'platform_url': 'http://localhost:8000',  # 本服务器地址
    'platform_api_key': 'KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4',
    'signature_secret': 'CHANGE_ME_IN_PRODUCTION_use_strong_random_key_here',
    'pull_interval': 10,  # 拉取间隔（秒）
    'batch_size': 1000,   # 每次拉取数量
    'relay_id': 'relay-001'
}


class RelayServer:
    """中转服务器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.stats = {
            'total_pulled': 0,
            'total_pushed': 0,
            'error_count': 0,
            'last_pull_time': None,
            'last_push_time': None
        }
    
    def generate_signature(self, request_body_str: str, timestamp: str, nonce: str) -> str:
        """生成HMAC签名"""
        message = timestamp + nonce + request_body_str
        signature = hmac.new(
            self.config['signature_secret'].encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def pull_from_c2(self) -> dict:
        """从C2端拉取数据"""
        try:
            url = f"{self.config['c2_url']}/api/pull"
            params = {
                'limit': self.config['batch_size'],
                'confirm': 'false'  # 使用两阶段确认
            }
            headers = {
                'X-API-Key': self.config['c2_api_key']
            }
            
            print(f"[{datetime.now()}] 从C2拉取数据: {url}")
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            count = data.get('count', 0)
            
            self.stats['total_pulled'] += count
            self.stats['last_pull_time'] = datetime.now()
            
            print(f"  ✅ 拉取成功: {count} 条记录")
            return data
            
        except Exception as e:
            print(f"  ❌ C2拉取失败: {e}")
            self.stats['error_count'] += 1
            return None
    
    def confirm_c2_pull(self, count: int) -> bool:
        """确认C2端删除已拉取的数据"""
        try:
            url = f"{self.config['c2_url']}/api/confirm"
            headers = {
                'X-API-Key': self.config['c2_api_key'],
                'Content-Type': 'application/json'
            }
            data = {'count': count}
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            
            print(f"  ✅ 已确认C2删除: {count} 条")
            return True
            
        except Exception as e:
            print(f"  ❌ C2确认失败: {e}")
            return False
    
    def push_to_platform(self, botnet_type: str, data: list) -> dict:
        """推送数据到本服务器"""
        try:
            timestamp = datetime.now().isoformat()
            nonce = f"relay-{int(time.time() * 1000)}"
            
            # 构造推送数据
            push_data = {
                'botnet_type': botnet_type,
                'data': data,
                'timestamp': timestamp,
                'nonce': nonce,
                'relay_server_id': self.config['relay_id']
            }
            
            # 序列化请求体
            request_body = json.dumps(push_data, ensure_ascii=False)
            
            # 生成签名
            signature = self.generate_signature(request_body, timestamp, nonce)
            
            # 发送请求
            url = f"{self.config['platform_url']}/api/data-push"
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': self.config['platform_api_key'],
                'X-Signature': signature
            }
            
            print(f"[{datetime.now()}] 推送到平台: {url}")
            print(f"  - 类型: {botnet_type}, 数量: {len(data)}")
            
            response = requests.post(
                url,
                data=request_body,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            self.stats['total_pushed'] += len(data)
            self.stats['last_push_time'] = datetime.now()
            
            print(f"  ✅ 推送成功: {result.get('message', '')}")
            print(f"  - 处理: {result.get('processed_count', 0)} 条")
            print(f"  - 耗时: {result.get('processing_time_ms', 0):.2f} ms")
            
            return result
            
        except Exception as e:
            print(f"  ❌ 平台推送失败: {e}")
            self.stats['error_count'] += 1
            return None
    
    def relay_cycle(self):
        """单次中转循环"""
        print("\n" + "=" * 70)
        print(f"开始中转循环 - {datetime.now()}")
        print("=" * 70)
        
        # 1. 从C2拉取数据
        c2_data = self.pull_from_c2()
        
        if not c2_data or c2_data.get('count', 0) == 0:
            print("  ℹ️  无新数据")
            return
        
        # 2. 按botnet_type分组数据
        records = c2_data.get('data', [])
        grouped = {}
        for record in records:
            botnet_type = record.get('botnet_type', 'unknown')
            if botnet_type not in grouped:
                grouped[botnet_type] = []
            grouped[botnet_type].append(record)
        
        print(f"\n按类型分组: {', '.join([f'{k}({len(v)})' for k, v in grouped.items()])}")
        
        # 3. 推送到平台
        all_success = True
        for botnet_type, data in grouped.items():
            result = self.push_to_platform(botnet_type, data)
            if not result or not result.get('success', False):
                all_success = False
        
        # 4. 确认C2删除（仅当全部推送成功）
        if all_success:
            self.confirm_c2_pull(len(records))
        else:
            print(f"  ⚠️  推送失败，不确认C2删除（下次将重试）")
    
    def run(self):
        """运行中转服务"""
        print("=" * 70)
        print("中转服务器启动")
        print("=" * 70)
        print(f"C2端地址: {self.config['c2_url']}")
        print(f"平台地址: {self.config['platform_url']}")
        print(f"中转ID: {self.config['relay_id']}")
        print(f"拉取间隔: {self.config['pull_interval']} 秒")
        print(f"批量大小: {self.config['batch_size']}")
        print("=" * 70)
        
        try:
            while True:
                try:
                    self.relay_cycle()
                except Exception as e:
                    print(f"\n❌ 循环异常: {e}")
                    self.stats['error_count'] += 1
                
                # 打印统计
                print("\n" + "-" * 70)
                print(f"统计: 已拉取{self.stats['total_pulled']}条, "
                      f"已推送{self.stats['total_pushed']}条, "
                      f"错误{self.stats['error_count']}次")
                print("-" * 70)
                
                # 等待下次循环
                time.sleep(self.config['pull_interval'])
                
        except KeyboardInterrupt:
            print("\n\n收到中断信号，正在停止...")
            self.print_final_stats()
    
    def print_final_stats(self):
        """打印最终统计"""
        print("\n" + "=" * 70)
        print("中转服务器统计")
        print("=" * 70)
        print(f"总拉取: {self.stats['total_pulled']} 条")
        print(f"总推送: {self.stats['total_pushed']} 条")
        print(f"错误次数: {self.stats['error_count']}")
        if self.stats['last_pull_time']:
            print(f"最后拉取: {self.stats['last_pull_time']}")
        if self.stats['last_push_time']:
            print(f"最后推送: {self.stats['last_push_time']}")
        print("=" * 70)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="中转服务器示例")
    parser.add_argument('--c2-url', default=DEFAULT_CONFIG['c2_url'],
                      help='C2端地址')
    parser.add_argument('--c2-api-key', default=DEFAULT_CONFIG['c2_api_key'],
                      help='C2端API密钥')
    parser.add_argument('--platform-url', default=DEFAULT_CONFIG['platform_url'],
                      help='本服务器地址')
    parser.add_argument('--platform-api-key', default=DEFAULT_CONFIG['platform_api_key'],
                      help='本服务器API密钥')
    parser.add_argument('--signature-secret', default=DEFAULT_CONFIG['signature_secret'],
                      help='HMAC签名密钥')
    parser.add_argument('--interval', type=int, default=DEFAULT_CONFIG['pull_interval'],
                      help='拉取间隔（秒）')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_CONFIG['batch_size'],
                      help='批量拉取大小')
    parser.add_argument('--relay-id', default=DEFAULT_CONFIG['relay_id'],
                      help='中转服务器ID')
    
    args = parser.parse_args()
    
    # 构造配置
    config = {
        'c2_url': args.c2_url,
        'c2_api_key': args.c2_api_key,
        'platform_url': args.platform_url,
        'platform_api_key': args.platform_api_key,
        'signature_secret': args.signature_secret,
        'pull_interval': args.interval,
        'batch_size': args.batch_size,
        'relay_id': args.relay_id
    }
    
    # 创建并运行中转服务器
    relay = RelayServer(config)
    relay.run()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        sys.exit(1)
