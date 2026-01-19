"""
IP信息增强器模块
使用ip_location模块查询IP的地理位置、ISP、ASN等信息
"""
import sys
import os
import asyncio
import logging
import time
import hashlib
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict

# 添加父目录到路径以便导入ip_location
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ip_location.ip_query import ip_query

# 尝试导入Redis（可选）
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class IPEnricher:
    """IP信息增强器"""
    
    def __init__(self, cache_size: int = 10000, cache_ttl: int = 86400, max_concurrent: int = 50):
        """
        初始化IP信息增强器（三层缓存架构）
        
        Args:
            cache_size: L1缓存大小
            cache_ttl: L1缓存过期时间（秒）
            max_concurrent: 最大并发查询数（防止并发风暴）
        """
        # L1缓存：内存
        self.cache = {}  # {ip: {'info': dict, 'timestamp': datetime}}
        self.cache_size = cache_size
        self.cache_ttl = cache_ttl
        
        # L2缓存：Redis（可选）
        self.redis_client = None
        self.redis_enabled = False
        self._init_redis_cache()
        
        # 统计信息
        self.query_count = 0
        self.cache_hit_count = 0
        self.redis_hit_count = 0
        self.error_count = 0
        self.retry_count = 0
        
        # 并发控制
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # 限流控制（防投毒）
        self.query_rate_limiter = defaultdict(list)  # {ip: [timestamp1, timestamp2, ...]}
        
        # 加载配置
        from config import IP_ENRICHMENT_RETRY_CONFIG, IP_QUERY_RATE_LIMIT, REDIS_CONFIG
        self.retry_config = IP_ENRICHMENT_RETRY_CONFIG
        self.rate_limit_config = IP_QUERY_RATE_LIMIT
        self.redis_config = REDIS_CONFIG
        
    def _init_redis_cache(self):
        """初始化Redis缓存（可选）"""
        try:
            from config import REDIS_CONFIG
            if REDIS_AVAILABLE and REDIS_CONFIG.get('enabled', False):
                self.redis_client = redis.Redis(
                    host=REDIS_CONFIG['host'],
                    port=REDIS_CONFIG['port'],
                    db=REDIS_CONFIG['db'],
                    password=REDIS_CONFIG.get('password'),
                    socket_timeout=REDIS_CONFIG.get('socket_timeout', 5),
                    socket_connect_timeout=REDIS_CONFIG.get('socket_connect_timeout', 5),
                    decode_responses=True
                )
                # 测试连接
                self.redis_client.ping()
                self.redis_enabled = True
                logger.info("Redis缓存已启用")
        except Exception as e:
            logger.warning(f"Redis缓存初始化失败，将只使用内存缓存: {e}")
            self.redis_client = None
            self.redis_enabled = False
    
    def _check_rate_limit(self, ip: str) -> bool:
        """检查IP查询限流"""
        if not self.rate_limit_config.get('enabled', False):
            return True
        
        now = time.time()
        max_queries = self.rate_limit_config.get('max_queries_per_ip', 10)
        window = 60  # 1分钟窗口
        
        # 清理过期的时间戳
        self.query_rate_limiter[ip] = [
            ts for ts in self.query_rate_limiter[ip]
            if now - ts < window
        ]
        
        # 检查是否超限
        if len(self.query_rate_limiter[ip]) >= max_queries:
            logger.warning(f"IP查询限流: {ip} 在1分钟内查询次数超过 {max_queries}")
            return False
        
        self.query_rate_limiter[ip].append(now)
        return True
    
    def _get_from_redis(self, ip: str) -> Optional[Dict]:
        """从Redis获取IP信息"""
        if not self.redis_enabled or not self.redis_client:
            return None
        
        try:
            import json
            key = f"ip_info:{ip}"
            data = self.redis_client.get(key)
            if data:
                self.redis_hit_count += 1
                return json.loads(data)
        except Exception as e:
            logger.debug(f"Redis读取失败: {e}")
        return None
    
    def _save_to_redis(self, ip: str, info: Dict):
        """保存IP信息到Redis"""
        if not self.redis_enabled or not self.redis_client:
            return
        
        try:
            import json
            key = f"ip_info:{ip}"
            ttl = self.redis_config.get('ip_cache_ttl', 604800)  # 7天
            self.redis_client.setex(key, ttl, json.dumps(info))
        except Exception as e:
            logger.debug(f"Redis写入失败: {e}")
    
    async def _query_with_retry(self, ip: str) -> Optional[Dict]:
        """带重试机制的IP查询"""
        max_retries = self.retry_config.get('max_retries', 3)
        retry_delay = self.retry_config.get('retry_delay', 1)
        retry_backoff = self.retry_config.get('retry_backoff', 2)
        timeout = self.retry_config.get('timeout', 10)
        
        for attempt in range(max_retries + 1):
            try:
                # 使用超时控制
                ip_info = await asyncio.wait_for(
                    ip_query(ip), 
                    timeout=timeout
                )
                
                if ip_info:
                    if attempt > 0:
                        logger.info(f"IP查询成功（重试{attempt}次）: {ip}")
                        self.retry_count += 1
                    return ip_info
                    
            except asyncio.TimeoutError:
                logger.warning(f"IP查询超时（尝试{attempt+1}/{max_retries+1}）: {ip}")
                self.error_count += 1
                
            except Exception as e:
                logger.warning(f"IP查询失败（尝试{attempt+1}/{max_retries+1}）: {ip}, 错误: {e}")
                self.error_count += 1
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < max_retries:
                wait_time = retry_delay * (retry_backoff ** attempt)
                logger.debug(f"等待 {wait_time}秒 后重试: {ip}")
                await asyncio.sleep(wait_time)
        
        logger.error(f"IP查询最终失败（{max_retries+1}次尝试）: {ip}")
        return None
    
    async def enrich(self, ip: str) -> Optional[Dict]:
        """
        增强单个IP的信息（三层缓存+重试机制）
        
        Args:
            ip: IP地址
            
        Returns:
            IP信息字典，包含country, province, city, isp, asn, longitude, latitude等
        """
        try:
            # L1缓存：内存缓存
            cached = self._get_from_cache(ip)
            if cached:
                self.cache_hit_count += 1
                logger.debug(f"L1 cache hit for IP: {ip}")
                return cached
            
            # L2缓存：Redis缓存
            redis_cached = self._get_from_redis(ip)
            if redis_cached:
                logger.debug(f"L2 Redis cache hit for IP: {ip}")
                # 更新L1缓存
                self._add_to_cache(ip, redis_cached)
                return redis_cached
            
            # 限流检查
            if not self._check_rate_limit(ip):
                logger.warning(f"IP查询被限流: {ip}")
                self.error_count += 1
                return self._get_default_ip_info(ip)
                
            # 并发控制：防止并发风暴
            async with self.semaphore:
                # 再次检查缓存（其他并发任务可能已查询）
                cached = self._get_from_cache(ip)
                if cached:
                    self.cache_hit_count += 1
                    return cached
                
                # L3：实际查询（带重试机制）
                self.query_count += 1
                ip_info = await self._query_with_retry(ip)
            
            if not ip_info:
                logger.warning(f"Failed to query IP info for: {ip}")
                return self._get_default_ip_info(ip)
                
            # 提取并规范化信息
            enriched_info = {
                'ip': ip,
                'continent': ip_info.get('continent', ''),
                'country': ip_info.get('country', ''),
                'province': ip_info.get('province', ''),
                'city': ip_info.get('city', ''),
                'isp': ip_info.get('isp', ''),
                'asn': ip_info.get('asn', ''),
                'longitude': self._safe_float(ip_info.get('longitude', 0)),
                'latitude': self._safe_float(ip_info.get('latitude', 0)),
                'is_china': ip_info.get('country', '') == '中国'
            }
            
            # 添加到L1缓存
            self._add_to_cache(ip, enriched_info)
            
            # 添加到L2缓存（Redis）
            self._save_to_redis(ip, enriched_info)
            
            return enriched_info
            
        except Exception as e:
            logger.error(f"Error enriching IP {ip}: {e}")
            return self._get_default_ip_info(ip)
            
    async def batch_enrich(self, ips: List[str]) -> Dict[str, Dict]:
        """
        批量增强IP信息
        
        Args:
            ips: IP地址列表
            
        Returns:
            IP信息字典 {ip: info_dict}
        """
        # 去重
        unique_ips = list(set(ips))
        
        # 并发查询
        tasks = [self.enrich(ip) for ip in unique_ips]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 构建结果字典
        enriched_data = {}
        for ip, result in zip(unique_ips, results):
            if isinstance(result, Exception):
                logger.error(f"Error enriching IP {ip}: {result}")
                enriched_data[ip] = self._get_default_ip_info(ip)
            else:
                enriched_data[ip] = result
                
        return enriched_data
        
    def _get_from_cache(self, ip: str) -> Optional[Dict]:
        """从缓存获取IP信息"""
        if ip not in self.cache:
            return None
            
        cache_entry = self.cache[ip]
        
        # 检查是否过期
        if datetime.now() - cache_entry['timestamp'] > timedelta(seconds=self.cache_ttl):
            del self.cache[ip]
            return None
            
        return cache_entry['info']
        
    def _add_to_cache(self, ip: str, info: Dict):
        """添加IP信息到缓存"""
        # 如果缓存已满，删除最旧的条目
        if len(self.cache) >= self.cache_size:
            # 简单策略：删除第一个
            oldest_ip = next(iter(self.cache))
            del self.cache[oldest_ip]
            
        self.cache[ip] = {
            'info': info,
            'timestamp': datetime.now()
        }
        
    @staticmethod
    def _safe_float(value, default=0.0) -> float:
        """安全转换为浮点数"""
        try:
            return float(value) if value else default
        except (ValueError, TypeError):
            return default
            
    @staticmethod
    def _get_default_ip_info(ip: str) -> Dict:
        """获取默认IP信息（查询失败时使用）"""
        return {
            'ip': ip,
            'continent': '未知',
            'country': '未知',
            'province': '未知',
            'city': '未知',
            'isp': '未知',
            'asn': '未知',
            'longitude': 0.0,
            'latitude': 0.0,
            'is_china': False
        }
        
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_requests = self.cache_hit_count + self.redis_hit_count + self.query_count
        return {
            'total_requests': total_requests,
            'total_queries': self.query_count,
            'l1_cache_hits': self.cache_hit_count,
            'l2_redis_hits': self.redis_hit_count,
            'l1_cache_size': len(self.cache),
            'l1_hit_rate': f"{(self.cache_hit_count / max(1, total_requests)) * 100:.2f}%",
            'l2_hit_rate': f"{(self.redis_hit_count / max(1, total_requests)) * 100:.2f}%",
            'total_cache_hit_rate': f"{((self.cache_hit_count + self.redis_hit_count) / max(1, total_requests)) * 100:.2f}%",
            'error_count': self.error_count,
            'retry_count': self.retry_count,
            'redis_enabled': self.redis_enabled
        }
        
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("IP cache cleared")


