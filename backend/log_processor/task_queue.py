# -*- coding: utf-8 -*-
"""
异步任务队列 - 使用Redis实现
将数据处理任务从Web请求中分离，防止前端卡死

重构说明：
- 所有配置参数从 backend/config.py 读取
- 支持通过环境变量覆盖配置
"""

import asyncio
import json
import redis
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# 导入配置
try:
    from config import QUEUE_REDIS_CONFIG, QUEUE_NAMES, QUEUE_MODE_ENABLED
except ImportError:
    # 如果config.py不在路径中，使用默认值
    logger.warning("无法从config.py导入配置，使用默认值")
    QUEUE_REDIS_CONFIG = {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'password': None,
        'socket_connect_timeout': 5,
        'socket_timeout': 5,
        'retry_on_timeout': True,
        'health_check_interval': 30,
        'decode_responses': True,
    }
    QUEUE_NAMES = {
        'ip_upload': 'botnet:ip_upload_queue',
        'task_queue': 'botnet:task_queue',
    }
    QUEUE_MODE_ENABLED = True


class TaskQueue:
    """异步任务队列"""
    
    def __init__(self, queue_name: Optional[str] = None):
        """
        初始化Redis连接
        
        Args:
            queue_name: 队列名称，默认使用config中的task_queue
        """
        self.queue_name = queue_name or QUEUE_NAMES['task_queue']
        
        # 从config读取Redis配置
        redis_config = QUEUE_REDIS_CONFIG.copy()
        
        # 移除password如果为None
        if redis_config.get('password') is None:
            redis_config.pop('password', None)
        
        try:
            self.redis_client = redis.Redis(**redis_config)
            logger.info(f"TaskQueue初始化成功: {redis_config['host']}:{redis_config['port']}, 队列: {self.queue_name}")
        except Exception as e:
            logger.error(f"TaskQueue初始化失败: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        测试Redis连接是否正常
        
        Returns:
            连接是否成功
        """
        try:
            self.redis_client.ping()
            logger.info(f"Redis连接成功: {QUEUE_REDIS_CONFIG['host']}:{QUEUE_REDIS_CONFIG['port']}")
            return True
        except redis.ConnectionError as e:
            logger.error(f"Redis连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"Redis连接测试异常: {e}")
            return False
        
    def push_task(self, botnet_type: str, ip_data: List[Dict], client_ip: str) -> str:
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
        self.redis_client.rpush(self.queue_name, json.dumps(task))
        
        logger.info(f"任务已入队: {task['task_id']}, {len(ip_data)} 条IP数据")
        
        return task['task_id']
    
    def get_queue_length(self) -> int:
        """获取队列长度"""
        try:
            # 使用较短的超时避免长时间阻塞
            return self.redis_client.llen(self.queue_name)
        except Exception as e:
            logger.debug(f"获取队列长度失败: {e}")
            return 0
    
    def pop_task(self, timeout: int = 0) -> Optional[Dict]:
        """
        从队列中获取任务（阻塞）
        
        Args:
            timeout: 超时时间（秒），0表示无限等待
            
        Returns:
            任务字典，如果超时返回None
        """
        try:
            result = self.redis_client.blpop(self.queue_name, timeout=timeout)
            
            if result:
                _, task_json = result
                return json.loads(task_json)
            
            return None
        except Exception as e:
            # timeout是正常的，使用debug级别
            import redis
            if isinstance(e, redis.TimeoutError):
                logger.debug(f"队列获取超时（正常）")
            else:
                logger.error(f"从队列获取任务失败: {e}")
            return None
    
    def clear_queue(self) -> int:
        """
        清空队列（谨慎使用）
        
        Returns:
            清除的任务数量
        """
        try:
            count = self.redis_client.llen(self.queue_name)
            self.redis_client.delete(self.queue_name)
            logger.warning(f"队列已清空: {self.queue_name}, 清除 {count} 个任务")
            return count
        except Exception as e:
            logger.error(f"清空队列失败: {e}")
            return 0
    
    def get_queue_info(self) -> Dict:
        """
        获取队列详细信息
        
        Returns:
            队列信息字典
        """
        try:
            queue_len = self.get_queue_length()
            redis_info = self.redis_client.info('memory')
            
            return {
                'queue_name': self.queue_name,
                'queue_length': queue_len,
                'redis_host': QUEUE_REDIS_CONFIG['host'],
                'redis_port': QUEUE_REDIS_CONFIG['port'],
                'redis_memory_used': redis_info.get('used_memory_human', 'N/A'),
                'redis_connected_clients': self.redis_client.client_list().__len__(),
            }
        except Exception as e:
            logger.error(f"获取队列信息失败: {e}")
            return {
                'queue_name': self.queue_name,
                'error': str(e)
            }


# 全局队列实例（兼容旧代码）
# 仅在队列模式启用时创建
task_queue = None

if QUEUE_MODE_ENABLED:
    try:
        task_queue = TaskQueue()
        logger.info("[队列模式] TaskQueue全局实例已创建")
    except Exception as e:
        logger.error(f"[队列模式] TaskQueue创建失败: {e}")
        logger.warning("[队列模式] 将自动降级为直接处理模式")
        task_queue = None
else:
    logger.info("[直接模式] 队列模式已禁用，使用直接处理模式")
