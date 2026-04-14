#!/usr/bin/env python3
"""
数据拉取客户端
从多个C2服务器(服务器A)拉取数据
通过OpenVPN连接进行安全传输
"""

import requests
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DataPuller:
    """C2数据拉取客户端"""
    
    def __init__(self, config: Dict):
        """
        初始化拉取客户端
        
        Args:
            config: 配置字典，包含C2服务器列表和拉取参数
        """
        self.c2_servers = config.get('c2_servers', [])
        self.batch_size = config.get('batch_size', 1000)
        self.timeout = config.get('timeout', 30)
        self.use_two_phase = config.get('use_two_phase_commit', True)
        
        # 断点续传：记录每个C2服务器的最大seq_id
        self.last_seq_ids = {}
        
        logger.info(f"数据拉取客户端初始化: {len(self.c2_servers)} 个C2服务器")
    
    def pull_from_server(self, server_config: Dict) -> Optional[Dict]:
        """
        从单个C2服务器拉取数据
        
        Args:
            server_config: 服务器配置
            
        Returns:
            拉取的数据或None
        """
        server_url = server_config['url']
        api_key = server_config.get('api_key', '')
        server_id = server_config.get('id', server_url)
        
        try:
            url = f"{server_url}/api/pull"
            params = {
                'limit': self.batch_size,
                'confirm': 'false' if self.use_two_phase else 'true'
            }
            
            # 断点续传：如果有上次的seq_id，只拉取新数据
            if server_id in self.last_seq_ids:
                params['since_seq'] = self.last_seq_ids[server_id]
                logger.debug(f"使用断点续传: since_seq={params['since_seq']}")
            
            headers = {
                'X-API-Key': api_key
            }
            
            logger.info(f"从C2拉取数据: {server_id}")
            
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            count = data.get('count', 0)
            
            logger.info(f"✅ 拉取成功: {server_id}, {count} 条记录")
            
            # 保存max_seq_id用于断点续传
            if 'max_seq_id' in data and data['max_seq_id'] > 0:
                self.last_seq_ids[server_id] = data['max_seq_id']
                logger.debug(f"保存断点: max_seq_id={data['max_seq_id']}")
            
            # 添加服务器标识
            data['server_id'] = server_id
            data['server_url'] = server_url
            
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ C2拉取超时: {server_id}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ C2连接失败: {server_id} (OpenVPN可能未连接)")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ C2拉取HTTP错误: {server_id}, {e}")
            return None
        except Exception as e:
            logger.error(f"❌ C2拉取异常: {server_id}, {e}")
            return None
    
    def confirm_pull(self, server_config: Dict, count: int) -> bool:
        """
        确认C2服务器删除已拉取的数据（两阶段提交）
        
        Args:
            server_config: 服务器配置
            count: 确认的记录数
            
        Returns:
            是否确认成功
        """
        if not self.use_two_phase:
            return True
        
        server_url = server_config['url']
        api_key = server_config.get('api_key', '')
        server_id = server_config.get('id', server_url)
        
        try:
            url = f"{server_url}/api/confirm"
            headers = {
                'X-API-Key': api_key,
                'Content-Type': 'application/json'
            }
            data = {'count': count}
            
            response = requests.post(
                url,
                json=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"✅ 已确认C2删除: {server_id}, {count} 条")
            return True
            
        except Exception as e:
            logger.error(f"❌ C2确认失败: {server_id}, {e}")
            return False
    
    def pull_from_all_servers(self) -> List[Dict]:
        """
        从所有C2服务器拉取数据
        
        Returns:
            拉取结果列表
        """
        results = []
        
        for server_config in self.c2_servers:
            data = self.pull_from_server(server_config)
            if data:
                results.append({
                    'server_config': server_config,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
        
        return results
    
    def health_check(self, server_config: Dict) -> bool:
        """
        检查C2服务器健康状态
        
        Args:
            server_config: 服务器配置
            
        Returns:
            是否健康
        """
        server_url = server_config['url']
        api_key = server_config.get('api_key', '')
        server_id = server_config.get('id', server_url)
        
        try:
            url = f"{server_url}/health"
            headers = {'X-API-Key': api_key}
            
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            
            logger.debug(f"C2服务器健康: {server_id}")
            return True
            
        except Exception as e:
            logger.warning(f"C2服务器不健康: {server_id}, {e}")
            return False
    
    def check_all_servers(self) -> Dict[str, bool]:
        """
        检查所有C2服务器健康状态
        
        Returns:
            服务器ID到健康状态的映射
        """
        results = {}
        
        for server_config in self.c2_servers:
            server_id = server_config.get('id', server_config['url'])
            results[server_id] = self.health_check(server_config)
        
        healthy_count = sum(1 for v in results.values() if v)
        logger.info(f"C2服务器健康检查: {healthy_count}/{len(results)} 健康")
        
        return results
