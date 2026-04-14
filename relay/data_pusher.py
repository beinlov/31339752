#!/usr/bin/env python3
"""
数据推送客户端
向服务器C推送数据，包含HMAC签名和重试机制
"""

import requests
import hmac
import hashlib
import json
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DataPusher:
    """数据推送客户端"""
    
    def __init__(self, config: Dict):
        """
        初始化推送客户端
        
        Args:
            config: 配置字典，包含平台URL、密钥等
        """
        self.platform_url = config['platform_url']
        self.api_key = config['platform_api_key']
        self.signature_secret = config['signature_secret']
        self.relay_id = config.get('relay_id', 'relay-001')
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 2)
        
        logger.info(f"数据推送客户端初始化: {self.platform_url}")
    
    def generate_signature(self, request_body_str: str, timestamp: str, nonce: str) -> str:
        """
        生成HMAC-SHA256签名
        
        签名消息格式: timestamp + nonce + request_body
        
        Args:
            request_body_str: JSON序列化的请求体
            timestamp: ISO格式时间戳
            nonce: 唯一随机数
            
        Returns:
            十六进制签名字符串
        """
        message = timestamp + nonce + request_body_str
        signature = hmac.new(
            self.signature_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def push_data(self, botnet_type: str, data: List[Dict]) -> Optional[Dict]:
        """
        推送数据到平台服务器
        
        Args:
            botnet_type: 僵尸网络类型
            data: 数据记录列表
            
        Returns:
            推送结果或None
        """
        if not data:
            logger.warning("无数据推送")
            return None
        
        try:
            # 生成时间戳和nonce
            timestamp = datetime.now().isoformat()
            nonce = f"relay-{int(time.time() * 1000)}"
            
            # 构造推送数据
            push_data = {
                'botnet_type': botnet_type,
                'data': data,
                'timestamp': timestamp,
                'nonce': nonce,
                'relay_server_id': self.relay_id
            }
            
            # 序列化请求体
            request_body = json.dumps(push_data, ensure_ascii=False)
            
            # 生成签名
            signature = self.generate_signature(request_body, timestamp, nonce)
            
            # 发送请求
            url = f"{self.platform_url}/api/data-push"
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key,
                'X-Signature': signature
            }
            
            logger.info(f"推送到平台: {botnet_type}, {len(data)} 条记录")
            
            response = requests.post(
                url,
                data=request_body,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success', False):
                logger.info(f"✅ 推送成功: {result.get('message', '')}")
                logger.info(f"   处理: {result.get('processed_count', 0)} 条, "
                          f"耗时: {result.get('processing_time_ms', 0):.2f} ms")
                return result
            else:
                logger.error(f"❌ 推送失败: {result.get('message', '未知错误')}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ 平台推送超时: {botnet_type}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ 平台连接失败: {botnet_type}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ 平台推送HTTP错误: {botnet_type}, {e}")
            if e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"   错误详情: {error_data}")
                except:
                    logger.error(f"   响应内容: {e.response.text[:200]}")
            return None
        except Exception as e:
            logger.error(f"❌ 平台推送异常: {botnet_type}, {e}")
            return None
    
    def push_with_retry(self, botnet_type: str, data: List[Dict]) -> Optional[Dict]:
        """
        推送数据并自动重试
        
        Args:
            botnet_type: 僵尸网络类型
            data: 数据记录列表
            
        Returns:
            推送结果或None
        """
        for attempt in range(self.max_retries):
            result = self.push_data(botnet_type, data)
            
            if result and result.get('success', False):
                return result
            
            if attempt < self.max_retries - 1:
                wait_time = self.retry_delay * (2 ** attempt)  # 指数退避
                logger.info(f"推送失败，{wait_time}秒后重试 (尝试 {attempt + 1}/{self.max_retries})")
                time.sleep(wait_time)
        
        logger.error(f"推送最终失败，已重试 {self.max_retries} 次")
        return None
    
    def push_grouped_data(self, grouped_data: Dict[str, List[Dict]]) -> Dict[str, bool]:
        """
        推送按类型分组的数据
        
        Args:
            grouped_data: botnet_type -> 数据列表的映射
            
        Returns:
            botnet_type -> 是否成功的映射
        """
        results = {}
        
        for botnet_type, data in grouped_data.items():
            result = self.push_with_retry(botnet_type, data)
            results[botnet_type] = (result is not None and result.get('success', False))
        
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"推送完成: {success_count}/{len(results)} 组成功")
        
        return results
    
    def health_check(self) -> bool:
        """
        检查平台服务器健康状态
        
        Returns:
            是否健康
        """
        try:
            url = f"{self.platform_url}/api/push-health"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            status = data.get('status', 'unknown')
            
            if status == 'ok':
                logger.debug("平台服务器健康")
                return True
            else:
                logger.warning(f"平台服务器状态异常: {status}")
                return False
                
        except Exception as e:
            logger.warning(f"平台健康检查失败: {e}")
            return False
    
    def get_push_status(self) -> Optional[Dict]:
        """
        获取平台推送模式状态
        
        Returns:
            状态信息或None
        """
        try:
            url = f"{self.platform_url}/api/push-status"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"平台推送模式: {data.get('mode', 'unknown')}, "
                       f"启用: {data.get('enabled', False)}")
            return data
            
        except Exception as e:
            logger.error(f"获取平台状态失败: {e}")
            return None
