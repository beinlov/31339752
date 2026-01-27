"""
Redis缓存管理器
用于缓存僵尸网络统计数据，减少数据库查询压力
"""
import redis
import json
import logging
from typing import Optional, Any
from datetime import datetime
from config import REDIS_CONFIG

logger = logging.getLogger(__name__)


class BotnetStatsCache:
    """僵尸网络统计数据缓存管理器"""
    
    def __init__(self, redis_config: dict = None):
        """
        初始化缓存管理器
        
        Args:
            redis_config: Redis配置字典，如果为None则使用默认配置
        """
        self.redis_config = redis_config or REDIS_CONFIG
        self.redis_client = None
        self.cache_enabled = True
        
        try:
            # 检查Redis是否启用（如果配置中有enabled字段）
            if not self.redis_config.get('enabled', True):
                logger.info("Redis cache is disabled in config")
                self.cache_enabled = False
                return
            
            self.redis_client = redis.Redis(
                host=self.redis_config.get('host', 'localhost'),
                port=self.redis_config.get('port', 6379),
                db=self.redis_config.get('db', 0),
                password=self.redis_config.get('password'),
                decode_responses=True,  # 自动解码为字符串
                socket_timeout=self.redis_config.get('socket_timeout', 5),
                socket_connect_timeout=self.redis_config.get('socket_connect_timeout', 5)
            )
            # 测试连接
            self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}. Cache disabled.")
            self.cache_enabled = False
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果不存在或已过期返回None
        """
        if not self.cache_enabled or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            value: 要缓存的数据（需可JSON序列化）
            ttl: 过期时间（秒），默认300秒（5分钟）
        """
        if not self.cache_enabled or not self.redis_client:
            return
        
        try:
            json_value = json.dumps(value, ensure_ascii=False)
            self.redis_client.setex(key, ttl, json_value)
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {e}")
    
    def delete(self, key: str):
        """
        删除缓存数据
        
        Args:
            key: 缓存键
        """
        if not self.cache_enabled or not self.redis_client:
            return
        
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")
    
    def clear_pattern(self, pattern: str):
        """
        删除匹配模式的所有缓存
        
        Args:
            pattern: 键匹配模式，例如 "botnet:*"
        """
        if not self.cache_enabled or not self.redis_client:
            return
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache keys matching pattern: {pattern}")
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {e}")
    
    def get_stats_summary(self):
        """获取僵尸网络概览统计的缓存键"""
        return "botnet:stats:summary"
    
    def get_stats_detail(self, botnet_name: str):
        """获取指定僵尸网络详细统计的缓存键"""
        return f"botnet:stats:detail:{botnet_name}"
    
    def get_node_stats(self, botnet_name: str):
        """获取指定僵尸网络节点统计的缓存键"""
        return f"botnet:node:stats:{botnet_name}"


# 全局缓存实例
_cache_instance = None


def get_cache() -> BotnetStatsCache:
    """
    获取全局缓存实例（单例模式）
    
    Returns:
        BotnetStatsCache实例
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = BotnetStatsCache()
    return _cache_instance
