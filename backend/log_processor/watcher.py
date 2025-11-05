"""
日志文件监控器模块
监控多个僵尸网络的日志目录，实时处理新增日志
"""
import os
import time
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

logger = logging.getLogger(__name__)


class BotnetLogHandler(FileSystemEventHandler):
    """僵尸网络日志文件处理器"""
    
    def __init__(self, botnet_type: str, callback: Callable, state_file: str, loop: asyncio.AbstractEventLoop):
        """
        初始化日志处理器
        
        Args:
            botnet_type: 僵尸网络类型
            callback: 处理日志行的回调函数
            state_file: 状态文件路径
            loop: asyncio事件循环
        """
        super().__init__()
        self.botnet_type = botnet_type
        self.callback = callback
        self.state_file = state_file
        self.loop = loop
        self.file_positions = self._load_state()
        
    def on_modified(self, event):
        """文件修改事件"""
        if event.is_directory:
            return
            
        if event.src_path.endswith('.txt'):
            # 使用 asyncio.run_coroutine_threadsafe 在主事件循环中安全地调度协程
            asyncio.run_coroutine_threadsafe(
                self._process_file(event.src_path),
                self.loop
            )
            
    def on_created(self, event):
        """文件创建事件"""
        if event.is_directory:
            return
            
        if event.src_path.endswith('.txt'):
            logger.info(f"[{self.botnet_type}] New log file detected: {event.src_path}")
            # 使用 asyncio.run_coroutine_threadsafe 在主事件循环中安全地调度协程
            asyncio.run_coroutine_threadsafe(
                self._process_file(event.src_path),
                self.loop
            )
            
    async def _process_file(self, filepath: str):
        """
        处理日志文件
        
        Args:
            filepath: 文件路径
        """
        try:
            # 获取上次读取位置
            last_pos = self.file_positions.get(filepath, 0)
            
            # 读取新增内容
            with open(filepath, 'r', encoding='utf-8') as f:
                f.seek(last_pos)
                new_lines = f.readlines()
                
                if new_lines:
                    logger.info(f"[{self.botnet_type}] Processing {len(new_lines)} new lines from {os.path.basename(filepath)}")
                    
                    # 处理每一行
                    for line in new_lines:
                        if line.strip():
                            await self.callback(self.botnet_type, line)
                            
                # 更新位置
                current_pos = f.tell()
                if current_pos != last_pos:
                    self.file_positions[filepath] = current_pos
                    self._save_state()
                    
        except Exception as e:
            logger.error(f"[{self.botnet_type}] Error processing file {filepath}: {e}")
            
    def _load_state(self) -> Dict:
        """加载文件位置状态"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    all_states = json.load(f)
                    return all_states.get(self.botnet_type, {})
            return {}
        except Exception as e:
            logger.error(f"[{self.botnet_type}] Error loading state: {e}")
            return {}
            
    def _save_state(self):
        """保存文件位置状态"""
        try:
            # 读取所有状态
            all_states = {}
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    all_states = json.load(f)
                    
            # 更新当前僵尸网络的状态
            all_states[self.botnet_type] = self.file_positions
            
            # 保存
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(all_states, f, indent=2)
                
        except Exception as e:
            logger.error(f"[{self.botnet_type}] Error saving state: {e}")


class BotnetLogWatcher:
    """统一日志监控器"""
    
    def __init__(self, botnet_configs: Dict, callback: Callable, state_file: str, loop: asyncio.AbstractEventLoop):
        """
        初始化日志监控器
        
        Args:
            botnet_configs: 僵尸网络配置字典
            callback: 处理日志行的回调函数
            state_file: 状态文件路径
            loop: asyncio事件循环
        """
        self.botnet_configs = botnet_configs
        self.callback = callback
        self.state_file = state_file
        self.loop = loop
        self.observers = {}
        
    def start(self):
        """启动监控所有已启用的僵尸网络日志"""
        for botnet_type, config in self.botnet_configs.items():
            if not config.get('enabled', True):
                logger.info(f"[{botnet_type}] Disabled, skipping...")
                continue
                
            log_dir = config['log_dir']
            
            # 确保日志目录存在
            if not os.path.exists(log_dir):
                logger.warning(f"[{botnet_type}] Log directory does not exist: {log_dir}")
                os.makedirs(log_dir, exist_ok=True)
                logger.info(f"[{botnet_type}] Created log directory: {log_dir}")
                
            # 创建处理器,传入事件循环
            handler = BotnetLogHandler(botnet_type, self.callback, self.state_file, self.loop)
            
            # 创建观察者
            observer = Observer()
            observer.schedule(handler, log_dir, recursive=False)
            observer.start()
            
            self.observers[botnet_type] = {
                'observer': observer,
                'handler': handler
            }
            
            logger.info(f"[{botnet_type}] Started monitoring: {log_dir}")
            
        logger.info(f"Started monitoring {len(self.observers)} botnet log directories")
        
    def stop(self):
        """停止所有监控"""
        for botnet_type, observer_info in self.observers.items():
            observer_info['observer'].stop()
            observer_info['observer'].join()
            logger.info(f"[{botnet_type}] Stopped monitoring")
            
        logger.info("All log monitors stopped")
        
    async def process_existing_logs(self):
        """处理已存在的日志文件（启动时扫描一次）"""
        logger.info("Scanning existing log files...")
        
        for botnet_type, config in self.botnet_configs.items():
            if not config.get('enabled', True):
                continue
                
            log_dir = config['log_dir']
            if not os.path.exists(log_dir):
                continue
                
            # 扫描目录中的所有.txt文件
            for filename in os.listdir(log_dir):
                if filename.endswith('.txt'):
                    filepath = os.path.join(log_dir, filename)
                    
                    # 触发处理 - 直接await调用
                    if botnet_type in self.observers:
                        handler = self.observers[botnet_type]['handler']
                        try:
                            await handler._process_file(filepath)
                        except Exception as e:
                            logger.error(f"Error processing existing file {filepath}: {e}")
                        
        logger.info("Existing log files scanned")
        
    def get_stats(self) -> Dict:
        """获取监控统计信息"""
        stats = {}
        for botnet_type, observer_info in self.observers.items():
            handler = observer_info['handler']
            stats[botnet_type] = {
                'monitored_files': len(handler.file_positions),
                'files': list(handler.file_positions.keys())
            }
        return stats

