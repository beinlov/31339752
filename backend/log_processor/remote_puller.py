"""
远程数据拉取模块 - 作为日志处理器的一部分

功能：
- 定期从C2端拉取数据
- 作为后台任务运行
- 拉取的数据直接传递给日志处理器
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class RemotePuller:
    """远程数据拉取器 - 从C2端拉取数据"""
    
    def __init__(self, c2_config: List[Dict], processor):
        """
        初始化远程拉取器
        
        Args:
            c2_config: C2端点配置列表
            processor: 日志处理器实例（用于调用process_api_data）
        """
        self.c2_config = c2_config
        self.processor = processor
        self.running = False
        self.sessions = {}
        
        # 统计
        self.stats = {
            'total_pulled': 0,
            'total_saved': 0,
            'error_count': 0,
            'last_pull_time': None
        }
        
        logger.info(f"初始化远程拉取器，配置了 {len(c2_config)} 个C2端点")
    
    async def start(self):
        """启动拉取器"""
        if self.running:
            logger.warning("拉取器已在运行")
            return
        
        self.running = True
        logger.info("远程拉取器已启动")
        
        # 为每个C2端点创建HTTP会话
        for c2 in self.c2_config:
            if not c2.get('enabled', True):
                continue
            
            name = c2['name']
            timeout = aiohttp.ClientTimeout(total=c2.get('timeout', 30))
            
            self.sessions[name] = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'X-API-Key': c2['api_key'],
                    'User-Agent': 'BotnetLogProcessor-RemotePuller/1.0'
                }
            )
            logger.info(f"创建HTTP会话: {name}")
    
    async def stop(self):
        """停止拉取器"""
        self.running = False
        
        # 关闭所有HTTP会话
        for name, session in self.sessions.items():
            if not session.closed:
                await session.close()
                logger.info(f"关闭HTTP会话: {name}")
        
        self.sessions.clear()
        logger.info("远程拉取器已停止")
    
    async def pull_cycle(self):
        """单次拉取循环"""
        if not self.running:
            return
        
        logger.debug(f"开始拉取循环 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 并行拉取所有C2端点
        tasks = []
        for c2 in self.c2_config:
            if not c2.get('enabled', True):
                continue
            tasks.append(self._pull_from_c2(c2))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        success_count = 0
        error_count = 0
        total_records = 0
        
        for c2, result in zip([c for c in self.c2_config if c.get('enabled', True)], results):
            if isinstance(result, Exception):
                logger.error(f"[{c2['name']}] 拉取异常: {result}")
                error_count += 1
            elif result:
                success_count += 1
                total_records += result
        
        self.stats['last_pull_time'] = datetime.now()
        
        if total_records > 0:
            logger.info(f"拉取循环完成: 成功 {success_count}, 失败 {error_count}, 总记录 {total_records}")
    
    async def _pull_from_c2(self, c2: Dict) -> Optional[int]:
        """
        从单个C2端点拉取数据
        
        Args:
            c2: C2配置
        
        Returns:
            拉取的记录数，失败返回None
        """
        name = c2['name']
        url = c2['url']
        batch_size = c2.get('batch_size', 1000)
        
        try:
            session = self.sessions.get(name)
            if not session:
                logger.error(f"[{name}] HTTP会话不存在")
                return None
            
            # 构造请求
            pull_url = f"{url}/api/pull"
            params = {
                'limit': batch_size,
                'confirm': 'true'  # 确认拉取（删除C2端数据）
            }
            
            logger.debug(f"[{name}] 拉取数据: {pull_url}")
            
            # 发送请求
            async with session.get(pull_url, params=params) as response:
                if response.status == 401:
                    logger.error(f"[{name}] 认证失败，请检查API Key")
                    self.stats['error_count'] += 1
                    return None
                
                if response.status != 200:
                    logger.error(f"[{name}] 拉取失败: HTTP {response.status}")
                    self.stats['error_count'] += 1
                    return None
                
                # 解析响应
                data = await response.json()
                
                if not data.get('success'):
                    logger.error(f"[{name}] 拉取失败: {data.get('error')}")
                    self.stats['error_count'] += 1
                    return None
                
                records = data.get('data', [])
                
                if not records:
                    logger.debug(f"[{name}] 没有新数据")
                    return 0
                
                # 按botnet_type分组
                records_by_type = {}
                for record in records:
                    botnet_type = record.get('botnet_type', 'unknown')
                    if botnet_type not in records_by_type:
                        records_by_type[botnet_type] = []
                    records_by_type[botnet_type].append(record)
                
                # 调用日志处理器处理数据
                total_saved = 0
                for botnet_type, type_records in records_by_type.items():
                    try:
                        await self.processor.process_api_data(botnet_type, type_records)
                        total_saved += len(type_records)
                        logger.info(f"[{name}] [{botnet_type}] 处理成功: {len(type_records)} 条")
                    except Exception as e:
                        logger.error(f"[{name}] [{botnet_type}] 处理失败: {e}")
                
                self.stats['total_pulled'] += len(records)
                self.stats['total_saved'] += total_saved
                
                logger.info(f"[{name}] ✓ 拉取成功: {len(records)} 条")
                
                return len(records)
        
        except asyncio.TimeoutError:
            logger.error(f"[{name}] 拉取超时")
            self.stats['error_count'] += 1
            return None
        
        except Exception as e:
            logger.error(f"[{name}] 拉取异常: {e}")
            self.stats['error_count'] += 1
            return None
    
    async def run(self):
        """运行拉取循环（作为后台任务）"""
        await self.start()
        
        # 获取默认的拉取间隔
        default_interval = 60
        
        try:
            while self.running:
                # 执行拉取
                await self.pull_cycle()
                
                # 等待下一次拉取
                # 可以从配置中读取间隔时间
                interval = min([c.get('pull_interval', default_interval) 
                               for c in self.c2_config if c.get('enabled', True)],
                              default=default_interval)
                
                await asyncio.sleep(interval)
        
        except asyncio.CancelledError:
            logger.info("拉取任务被取消")
        finally:
            await self.stop()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'total_pulled': self.stats['total_pulled'],
            'total_saved': self.stats['total_saved'],
            'error_count': self.stats['error_count'],
            'last_pull_time': self.stats['last_pull_time'].isoformat() if self.stats['last_pull_time'] else None
        }
