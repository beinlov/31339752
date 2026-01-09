"""
IP信息增强器模块
使用ip_location模块查询IP的地理位置、ISP、ASN等信息
"""
import sys
import os
import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

# 添加父目录到路径以便导入ip_location
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ip_location.ip_query import ip_query

logger = logging.getLogger(__name__)


class IPEnricher:
    """IP信息增强器"""
    
    def __init__(self, cache_size: int = 10000, cache_ttl: int = 86400, max_concurrent: int = 50):
        """
        初始化IP信息增强器
        
        Args:
            cache_size: 缓存大小
            cache_ttl: 缓存过期时间（秒）
            max_concurrent: 最大并发查询数（防止并发风暴）
        """
        self.cache = {}  # {ip: {'info': dict, 'timestamp': datetime}}
        self.cache_size = cache_size
        self.cache_ttl = cache_ttl
        self.query_count = 0
        self.cache_hit_count = 0
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)  # 并发控制
        
    async def enrich(self, ip: str) -> Optional[Dict]:
        """
        增强单个IP的信息（带并发控制）
        
        Args:
            ip: IP地址
            
        Returns:
            IP信息字典，包含country, province, city, isp, asn, longitude, latitude等
        """
        try:
            # 检查缓存
            cached = self._get_from_cache(ip)
            if cached:
                self.cache_hit_count += 1
                logger.debug(f"Cache hit for IP: {ip}")
                return cached
                
            # 并发控制：防止并发风暴
            async with self.semaphore:
                # 再次检查缓存（其他并发任务可能已查询）
                cached = self._get_from_cache(ip)
                if cached:
                    self.cache_hit_count += 1
                    return cached
                
                # 查询IP信息
                self.query_count += 1
                ip_info = await ip_query(ip)
            
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
            
            # 添加到缓存
            self._add_to_cache(ip, enriched_info)
            
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
        return {
            'total_queries': self.query_count,
            'cache_hits': self.cache_hit_count,
            'cache_size': len(self.cache),
            'cache_hit_rate': f"{(self.cache_hit_count / max(1, self.query_count)) * 100:.2f}%"
        }
        
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("IP cache cleared")


