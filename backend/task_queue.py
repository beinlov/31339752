# -*- coding: utf-8 -*-
"""
异步任务队列 - 使用Redis实现
将数据处理任务从Web请求中分离，防止前端卡死
"""

import asyncio
import json
import redis
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)

# Redis连接配置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
QUEUE_NAME = 'botnet:ip_upload_queue'

class TaskQueue:
    """异步任务队列"""
    
    def __init__(self):
        """初始化Redis连接"""
        self.queue_name = QUEUE_NAME  # 记录队列名称，方便诊断
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5,  # 连接超时5秒
            socket_timeout=5,           # 操作超时5秒
            retry_on_timeout=True,      # 超时重试
            health_check_interval=30    # 健康检查间隔
        )
    
    def test_connection(self) -> bool:
        """
        测试Redis连接是否正常
        
        Returns:
            连接是否成功
        """
        try:
            self.redis_client.ping()
            logger.info(f"Redis连接成功: {REDIS_HOST}:{REDIS_PORT}")
            return True
        except redis.ConnectionError as e:
            logger.error(f"Redis连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"Redis连接测试异常: {e}")
            return False
        
    def push_task(self, botnet_type: str, ip_data: List[Dict], client_ip: str):
        """
        推送任务到队列
        
        Args:
            botnet_type: 僵尸网络类型
            ip_data: IP数据列表
            client_ip: 客户端IP
            
        Returns:
            任务ID
        """
        task = {
            'task_id': f"{botnet_type}_{datetime.now().timestamp()}",
            'botnet_type': botnet_type,
            'ip_data': ip_data,
            'client_ip': client_ip,
            'created_at': datetime.now().isoformat()
        }
        
        # 推送到队列
        self.redis_client.rpush(QUEUE_NAME, json.dumps(task))
        
        logger.info(f"任务已入队: {task['task_id']}, {len(ip_data)} 条IP数据")
        
        return task['task_id']
    
    def get_queue_length(self) -> int:
        """获取队列长度"""
        return self.redis_client.llen(QUEUE_NAME)
    
    def pop_task(self, timeout: int = 0):
        """
        从队列中获取任务（阻塞）
        
        Args:
            timeout: 超时时间（秒），0表示无限等待
            
        Returns:
            任务字典，如果超时返回None
        """
        result = self.redis_client.blpop(QUEUE_NAME, timeout=timeout)
        
        if result:
            _, task_json = result
            return json.loads(task_json)
        
        return None


# 全局队列实例
task_queue = TaskQueue()
