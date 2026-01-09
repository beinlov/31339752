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
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class RemotePuller:
    """远程数据拉取器 - 从 C2端拉取数据（支持两阶段确认和断点续传）"""
    
    def __init__(self, c2_config: List[Dict], processor, state_file: str = '.remote_puller_state.json'):
        """
        初始化远程拉取器
        
        Args:
            c2_config: C2端点配置列表
            processor: 日志处理器实例（用于调用process_api_data）
            state_file: 状态文件路径（用于断点续传）
        """
        self.c2_config = c2_config
        self.processor = processor
        self.running = False
        self.sessions = {}
        self.state_file = state_file
        self.last_timestamps = {}  # 每个 C2 的最后处理时间戳
        
        # 统计
        self.stats = {
            'total_pulled': 0,
            'total_saved': 0,
            'error_count': 0,
            'last_pull_time': None
        }
        
        # 加载状态（断点续传）
        self.load_state()
        
        logger.info(f"初始化远程拉取器，配置了 {len(c2_config)} 个 C2端点")
    
    def load_state(self):
        """加载拉取状态（用于断点续传）"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.last_timestamps = state.get('last_timestamps', {})
                    logger.info(f"加载拉取状态: {len(self.last_timestamps)} 个 C2 端点")
        except Exception as e:
            logger.warning(f"加载拉取状态失败: {e}，将从头开始拉取")
            self.last_timestamps = {}
    
    def save_state(self):
        """保存拉取状态"""
        try:
            state = {
                'last_timestamps': self.last_timestamps,
                'updated_at': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"保存拉取状态失败: {e}")
    
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
        从单个 C2端点拉取数据（使用两阶段确认）
        
        Args:
            c2: C2配置
        
        Returns:
            拉取的记录数，失败返回 None
        """
        name = c2['name']
        url = c2['url']
        batch_size = c2.get('batch_size', 1000)
        
        try:
            session = self.sessions.get(name)
            if not session:
                logger.error(f"[{name}] HTTP会话不存在")
                return None
            
            # 阶段1：拉取数据（confirm=false，不删除）
            pull_url = f"{url}/api/pull"
            params = {
                'limit': batch_size,
                'confirm': 'false'  # 不自动确认，使用两阶段确认
            }
            
            # 支持断点续传（可通过环境变量禁用）
            enable_resume = os.environ.get('ENABLE_PULL_RESUME', 'true').lower() == 'true'
            last_timestamp = self.last_timestamps.get(name) if enable_resume else None
            
            if last_timestamp:
                params['since'] = last_timestamp
                logger.info(f"[{name}] 使用断点续传: since={last_timestamp}")
            else:
                logger.info(f"[{name}] 拉取全部数据（无断点续传）")
            
            logger.debug(f"[{name}] 拉取数据: {pull_url}")
            
            # 发送请求
            async with session.get(pull_url, params=params) as response:
                if response.status == 401:
                    logger.error(f"[{name}] 认证失败，请检查 API Key")
                    self.stats['error_count'] += 1
                    return None
                
                if response.status != 200:
                    logger.error(f"[{name}] 拉取失败: HTTP {response.status}")
                
                # 解析响应
                data = await response.json()
                
                if not data.get('success'):
                    logger.error(f"[{name}] 拉取失败: {data.get('error')}")
                    self.stats['error_count'] += 1
                    return None
                
                records = data.get('data', [])
                
                if not records:
                    # 如果使用了since参数但返回0条，可能时间戳太新，清除后重试
                    if last_timestamp and name in self.last_timestamps:
                        logger.warning(f"[{name}] 使用since={last_timestamp}返回0条数据，清除时间戳准备下次重试")
                        del self.last_timestamps[name]
                        self.save_state()
                        logger.info(f"[{name}] 已清除断点续传时间戳，下次将拉取全部数据")
                    else:
                        logger.debug(f"[{name}] 没有新数据")
                    return 0
                
                # 按 botnet_type 分组
                records_by_type = {}
                max_timestamp = None
                
                for record in records:
                    botnet_type = record.get('botnet_type', 'unknown')
                    if botnet_type not in records_by_type:
                        records_by_type[botnet_type] = []
                    records_by_type[botnet_type].append(record)
                    
                    # 记录最大时间戳（用于断点续传）
                    timestamp = record.get('timestamp')
                    if timestamp:
                        if not max_timestamp or timestamp > max_timestamp:
                            max_timestamp = timestamp
                
                # 调用日志处理器处理数据
                total_saved = 0
                save_error = False
                
                for botnet_type, type_records in records_by_type.items():
                    try:
                        await self.processor.process_api_data(botnet_type, type_records)
                        total_saved += len(type_records)
                        logger.info(f"[{name}] [{botnet_type}] 处理成功: {len(type_records)} 条")
                    except Exception as e:
                        logger.error(f"[{name}] [{botnet_type}] 处理失败: {e}")
                        save_error = True
                
                # 阶段2：只有当保存成功时才确认删除
                if not save_error and total_saved > 0:
                    try:
                        confirm_url = f"{url}/api/confirm"
                        confirm_data = {'count': len(records)}
                        
                        async with session.post(confirm_url, json=confirm_data) as confirm_response:
                            if confirm_response.status == 200:
                                logger.info(f"[{name}] 已确认删除: {len(records)} 条")
                                
                                # 更新断点续传状态
                                if max_timestamp:
                                    self.last_timestamps[name] = max_timestamp
                                    self.save_state()
                            else:
                                logger.warning(f"[{name}] 确认删除失败: HTTP {confirm_response.status}")
                    except Exception as e:
                        logger.error(f"[{name}] 确认删除异常: {e}")
                else:
                    logger.warning(f"[{name}] 保存失败，未确认删除，下次将重试")
                
                self.stats['total_pulled'] += len(records)
                self.stats['total_saved'] += total_saved
                
                logger.info(f"[{name}] 拉取成功: {len(records)} 条, 保存: {total_saved} 条")
                
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
