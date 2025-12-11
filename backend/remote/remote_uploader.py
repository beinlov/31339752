#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
远端日志上传脚本
部署在远端蜜罐服务器上，异步读取每日日志文件，去重后上传到本地服务器

架构设计:
- LogReader: 异步日志读取器，负责读取每日日志文件
- IPProcessor: IP处理器，负责解析、去重和缓存IP数据
- RemoteUploader: 上传器，负责将处理后的数据上传到本地服务器
"""

import asyncio
import aiofiles
import aiohttp
import time
import os
import sys
import json
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Set, Tuple
import logging
from pathlib import Path
from collections import defaultdict

# ============================================================
# Configuration Loading
# ============================================================

def load_config(config_file: str = None) -> Dict:
    """
    Load configuration from JSON file
    If config file doesn't exist, use default configuration and create template
    """
    # Default configuration
    default_config = {
        "server": {
            "api_endpoint": "https://periotic-multifaced-christena.ngrok-free.dev",
            "api_key": "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4",
            "local_server_host": "your-local-server-ip",
            "local_server_port": 8000
        },
        "botnet": {
            "botnet_type": "ramnit",
            "log_dir": "/home/ubuntu",
            "log_file_pattern": "ramnit_{date}.log"
        },
        "processing": {
            "upload_interval": 300,
            "batch_size": 500,
            "max_retries": 3,
            "retry_delay": 30,
            "read_chunk_size": 8192
        },
        "server_check": {
            "check_interval": 60,
            "check_timeout": 10,
            "max_check_retries": 5
        },
        "files": {
            "state_file": "/tmp/uploader_state.json",
            "duplicate_cache_file": "/tmp/ip_cache.json",
            "offset_state_file": "/tmp/file_offsets.json"
        },
        "cache": {
            "expire_days": 7
        }
    }
    
    # Determine config file path
    if config_file is None:
        # Try to find config.json in the same directory as this script
        script_dir = Path(__file__).parent
        config_file = script_dir / "config.json"
    else:
        config_file = Path(config_file)
    
    # Load from file if exists
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # Merge user config with default config
                for section, values in user_config.items():
                    if section in default_config:
                        default_config[section].update(values)
                    else:
                        default_config[section] = values
                print(f"Loaded configuration from: {config_file}")
        except Exception as e:
            print(f"Error loading config file: {e}")
            print("Using default configuration")
    else:
        #  修复问题1：Create template config file
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            print("="*60)
            print(f"✓ 已创建配置文件模板: {config_file}")
            print("  请先编辑配置文件，然后重新运行程序！")
            print("="*60)
            #  关键修复：提示后退出，避免用默认配置运行
            sys.exit(0)
        except Exception as e:
            print(f"Error creating config file: {e}")
    
    return default_config

# Load configuration
print("="*60)
print("正在加载配置...")
CONFIG = load_config()
print(f"配置加载完成！")
print(f"  API端点: {CONFIG['server']['api_endpoint']}")
print(f"  僵尸网络类型: {CONFIG['botnet']['botnet_type']}")
print(f"  日志目录: {CONFIG['botnet']['log_dir']}")
print(f"  批次大小: {CONFIG['processing']['batch_size']}")
print("="*60)

# Extract configuration values for easy access
API_ENDPOINT = CONFIG["server"]["api_endpoint"]
API_KEY = CONFIG["server"]["api_key"]
LOCAL_SERVER_HOST = CONFIG["server"]["local_server_host"]
LOCAL_SERVER_PORT = CONFIG["server"]["local_server_port"]

BOTNET_TYPE = CONFIG["botnet"]["botnet_type"]
LOG_DIR = CONFIG["botnet"]["log_dir"]
LOG_FILE_PATTERN = CONFIG["botnet"]["log_file_pattern"]

UPLOAD_INTERVAL = CONFIG["processing"]["upload_interval"]
BATCH_SIZE = CONFIG["processing"]["batch_size"]
MAX_RETRIES = CONFIG["processing"]["max_retries"]
RETRY_DELAY = CONFIG["processing"]["retry_delay"]
READ_CHUNK_SIZE = CONFIG["processing"]["read_chunk_size"]

SERVER_CHECK_INTERVAL = CONFIG["server_check"]["check_interval"]
SERVER_CHECK_TIMEOUT = CONFIG["server_check"]["check_timeout"]
MAX_SERVER_CHECK_RETRIES = CONFIG["server_check"]["max_check_retries"]

STATE_FILE = CONFIG["files"]["state_file"]
DUPLICATE_CACHE_FILE = CONFIG["files"]["duplicate_cache_file"]
OFFSET_STATE_FILE = CONFIG["files"]["offset_state_file"]
PENDING_QUEUE_FILE = "/tmp/pending_upload_queue.json"  # 待上传数据持久化队列

CACHE_EXPIRE_DAYS = CONFIG["cache"]["expire_days"]

# 内存限制配置
MAX_MEMORY_IPS = 10000  # 内存中最多保留的IP数量
FORCE_UPLOAD_THRESHOLD = 5000  # 达到此数量强制上传
MIN_UPLOAD_BATCH = 100  # 最小上传批次

# 文件扫描缓存配置
FILE_SCAN_CACHE_TTL = 300  # 文件列表缓存时间（秒），默认5分钟

# 不完整行缓存文件
INCOMPLETE_LINES_FILE = "/tmp/incomplete_lines.json"  # 保存不完整行的文件

# IP parsing regex
IP_REGEX = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')

# ============================================================
# 日志配置
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/remote_uploader.log')
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# 核心功能类
# ============================================================

class LogReader:
    """异步日志读取器（改进版：支持缓存和不完整行处理）"""
    
    def __init__(self, log_dir: str, file_pattern: str):
        self.log_dir = Path(log_dir)
        self.file_pattern = file_pattern
        self.processed_files = set()
        
        # 文件列表缓存
        self.file_cache = None
        self.file_cache_time = 0
        
        # 不完整行缓存
        self.incomplete_lines = {}  # {file_path: incomplete_line}
        self.load_incomplete_lines()
        
    def get_log_file_path(self, date: datetime) -> Path:
        """获取指定日期的日志文件路径"""
        date_str = date.strftime('%Y-%m-%d')
        filename = self.file_pattern.format(date=date_str)
        return self.log_dir / filename
    
    def get_available_log_files(self, days_back: int = 30, use_cache: bool = True) -> List[Tuple[datetime, Path]]:
        """获取可用的日志文件列表（支持缓存，减少文件系统扫描）"""
        current_time = time.time()
        
        #  优化：使用缓存，减少文件系统扫描
        if use_cache and self.file_cache is not None:
            if current_time - self.file_cache_time < FILE_SCAN_CACHE_TTL:
                logger.debug(f"使用文件列表缓存（{len(self.file_cache)} 个文件）")
                return self.file_cache
        
        files = []
        
        # 扫描目录中所有匹配的日志文件
        if self.log_dir.exists() and self.log_dir.is_dir():
            # 提取文件模式的前缀和后缀（例如：ramnit_{date}.log -> ramnit_*.log）
            pattern_parts = self.file_pattern.split('{date}')
            if len(pattern_parts) == 2:
                prefix, suffix = pattern_parts
                glob_pattern = f"{prefix}*{suffix}"
                
                # 使用glob查找所有匹配的文件
                for file_path in self.log_dir.glob(glob_pattern):
                    if file_path.is_file():
                        # 尝试从文件名中提取日期
                        try:
                            filename = file_path.name
                            # 移除前缀和后缀，提取日期部分
                            date_str = filename[len(prefix):-len(suffix)] if suffix else filename[len(prefix):]
                            
                            # 尝试解析日期（支持 YYYY-MM-DD 格式）
                            date = datetime.strptime(date_str, '%Y-%m-%d')
                            files.append((date, file_path))
                            logger.debug(f"发现日志文件: {file_path} (日期: {date_str})")
                        except ValueError:
                            logger.warning(f"无法从文件名解析日期: {file_path}")
                            continue
            else:
                logger.warning(f"文件模式格式不正确: {self.file_pattern}")
        else:
            logger.warning(f"日志目录不存在: {self.log_dir}")
        
        # 按日期排序（从旧到新）
        sorted_files = sorted(files, key=lambda x: x[0])
        
        # 更新缓存
        self.file_cache = sorted_files
        self.file_cache_time = current_time
        logger.debug(f"更新文件列表缓存（{len(sorted_files)} 个文件）")
        
        return sorted_files
    
    def invalidate_cache(self):
        """使缓存失效，强制重新扫描"""
        self.file_cache = None
        self.file_cache_time = 0
        logger.debug("文件列表缓存已失效")
    
    def load_incomplete_lines(self):
        """加载不完整行缓存"""
        try:
            if os.path.exists(INCOMPLETE_LINES_FILE):
                with open(INCOMPLETE_LINES_FILE, 'r') as f:
                    self.incomplete_lines = json.load(f)
                logger.debug(f"加载不完整行缓存: {len(self.incomplete_lines)} 个文件")
        except Exception as e:
            logger.warning(f"加载不完整行缓存失败: {e}")
            self.incomplete_lines = {}
    
    def save_incomplete_lines(self):
        """保存不完整行缓存"""
        try:
            with open(INCOMPLETE_LINES_FILE, 'w') as f:
                json.dump(self.incomplete_lines, f, indent=2)
            logger.debug(f"保存不完整行缓存: {len(self.incomplete_lines)} 个文件")
        except Exception as e:
            logger.error(f"保存不完整行缓存失败: {e}")
    
    async def read_log_file(self, file_path: Path, processor, start_offset: int = 0, max_lines: int = None) -> tuple[int, int]:
        """异步增量读取日志文件（改进版：支持限制行数，真正分块）
        
        Args:
            file_path: 日志文件路径
            processor: IP处理器
            start_offset: 开始读取的字节偏移量
            max_lines: 最大读取行数（None表示读到文件末尾）
            
        Returns:
            (processed_lines, end_offset): 处理的行数和结束偏移量
        """
        if not file_path.exists():
            logger.warning(f"日志文件不存在: {file_path}")
            return 0, start_offset
        
        file_size = file_path.stat().st_size
        
        #  修复问题2：offset > file_size 说明文件被截断，重置为0
        if start_offset > file_size:
            logger.warning(f"文件 {file_path} 被截断 (offset={start_offset} > size={file_size})，重置偏移量为0")
            start_offset = 0
        elif start_offset == file_size:
            logger.debug(f"文件 {file_path} 无新数据 (offset={start_offset}, size={file_size})")
            return 0, start_offset
        
        logger.info(f"读取日志文件: {file_path} (从偏移量 {start_offset} 开始)")
        processed_lines = 0
        current_offset = start_offset
        file_path_str = str(file_path)
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                # 定位到上次读取的位置
                await f.seek(start_offset)
                
                #  改进：恢复上次的不完整行
                buffer = self.incomplete_lines.get(file_path_str, "")
                if buffer:
                    logger.debug(f"恢复不完整行: {buffer[:50]}...")
                
                while True:
                    #  新增：支持限制读取行数
                    if max_lines and processed_lines >= max_lines:
                        logger.debug(f"达到最大行数限制 {max_lines}，停止读取")
                        break
                    
                    chunk = await f.read(READ_CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    buffer += chunk
                    lines = buffer.split('\n')
                    
                    #  改进：更安全的不完整行处理
                    if len(chunk) < READ_CHUNK_SIZE:  # 已到文件末尾
                        # 如果最后一行没有换行符，保存到缓存
                        if not chunk.endswith('\n') and lines[-1]:
                            self.incomplete_lines[file_path_str] = lines[-1]
                            logger.debug(f"保存不完整行到缓存: {lines[-1][:50]}...")
                            lines = lines[:-1]
                            buffer = self.incomplete_lines[file_path_str]
                        else:
                            # 最后一行已完整，清除缓存
                            if file_path_str in self.incomplete_lines:
                                del self.incomplete_lines[file_path_str]
                            buffer = ""
                    else:
                        buffer = lines[-1]
                        lines = lines[:-1]
                    
                    # 处理完整的行
                    line_index = 0
                    for line_index, line in enumerate(lines):
                        if line.strip():
                            await processor.process_line(line.strip())
                            processed_lines += 1
                            
                            #  新增：达到行数限制就停止
                            if max_lines and processed_lines >= max_lines:
                                #  修复问题4：将未处理的行回填到buffer
                                unprocessed_lines = lines[line_index + 1:]
                                if unprocessed_lines:
                                    # 把未处理的完整行拼回 buffer
                                    buffer = '\n'.join(unprocessed_lines)
                                    if buffer and not buffer.endswith('\n'):
                                        # buffer最后部分是原来的不完整行
                                        pass
                                    logger.debug(f"回填 {len(unprocessed_lines)} 行未处理数据到buffer")
                                break
                            
                            # 每处理一定数量的行就让出控制权
                            if processed_lines % 1000 == 0:
                                await asyncio.sleep(0.001)
                
                # 更新当前偏移量（减去未处理的buffer长度）
                current_offset = await f.tell() - len(buffer.encode('utf-8'))
                
                #  修复问题3：如果文件真正结束且有不完整行，尝试处理它
                if not max_lines:  # 只有在读到文件末尾时（而非因为max_lines限制）
                    if file_path_str in self.incomplete_lines:
                        final_line = self.incomplete_lines[file_path_str]
                        # 检查文件大小是否还在增长
                        current_file_size = file_path.stat().st_size
                        if current_offset >= current_file_size:
                            # 文件不再增长，处理最后一行
                            logger.info(f"文件结束，处理最后一行（无换行符）: {final_line[:50]}...")
                            if final_line.strip():
                                await processor.process_line(final_line.strip())
                                processed_lines += 1
                                current_offset += len(final_line.encode('utf-8'))
                            # 清除缓存
                            del self.incomplete_lines[file_path_str]
                
                # 保存不完整行缓存
                self.save_incomplete_lines()
        
        except Exception as e:
            logger.error(f"读取日志文件失败 {file_path}: {e}")
            #  改进：出错时也保存进度
            if processed_lines > 0:
                logger.warning(f"已处理 {processed_lines} 行，保存当前进度")
                return processed_lines, current_offset
            return 0, start_offset
        
        logger.info(f"读取日志文件完成: {file_path}, 处理了 {processed_lines} 行, 新偏移量: {current_offset}")
        return processed_lines, current_offset


class IPProcessor:
    """IP处理器 - 负责解析、去重和缓存IP数据（改进版：全局去重）"""
    
    def __init__(self, botnet_type: str, cache_file: str, pending_queue_file: str = PENDING_QUEUE_FILE):
        self.botnet_type = botnet_type
        self.cache_file = cache_file
        self.pending_queue_file = pending_queue_file
        
        #  改进：全局去重，而不是仅按日期去重
        self.global_ip_cache: Set[str] = set()  # 全局IP缓存，用于去重
        self.ip_last_seen: Dict[str, str] = {}  # 记录IP最后出现的日期
        
        self.daily_ips: Dict[str, Set[str]] = defaultdict(set)  # 按日期分组的IP
        self.daily_ips_with_time: Dict[str, List[Dict]] = defaultdict(list)  # 包含时间戳的IP数据
        self.processed_count = 0
        self.duplicate_count = 0
        self.global_duplicate_count = 0  # 全局重复计数
        
        self.load_cache()
        self.load_pending_queue()  # 加载未上传的数据
        self.last_persist_time = time.time()
    
    def load_cache(self):
        """加载IP缓存（用于全局去重）"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                #  改进：加载用于全局去重
                self.global_ip_cache = set()
                self.ip_last_seen = {}
                
                for ip_data in cache_data.get('ips', []):
                    ip = ip_data['ip']
                    self.global_ip_cache.add(ip)
                    # 记录最后出现日期
                    if 'date' in ip_data:
                        self.ip_last_seen[ip] = ip_data['date']
                
                logger.info(f"加载IP缓存: {len(self.global_ip_cache)} 个IP（用于全局去重）")
        except Exception as e:
            logger.warning(f"加载IP缓存失败: {e}")
            self.global_ip_cache = set()
            self.ip_last_seen = {}
    
    def save_cache(self):
        """保存IP缓存（包含最后出现日期）"""
        try:
            cache_data = {
                'updated_at': datetime.now().isoformat(),
                'ips': [
                    {
                        'ip': ip,
                        'date': self.ip_last_seen.get(ip, datetime.now().strftime('%Y-%m-%d')),
                        'timestamp': datetime.now().isoformat()
                    }
                    for ip in self.global_ip_cache
                ]
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.debug(f"保存IP缓存: {len(self.global_ip_cache)} 个IP")
        except Exception as e:
            logger.error(f"保存IP缓存失败: {e}")
    
    def load_pending_queue(self):
        """加载待上传队列（恢复未上传的数据）"""
        try:
            if os.path.exists(self.pending_queue_file):
                with open(self.pending_queue_file, 'r') as f:
                    queue_data = json.load(f)
                    
                # 恢复到内存中
                for item in queue_data.get('items', []):
                    date = item['date']
                    if date not in self.daily_ips_with_time:
                        self.daily_ips_with_time[date] = []
                    self.daily_ips_with_time[date].append(item)
                    self.daily_ips[date].add(item['ip'])
                    
                logger.info(f"从队列恢复 {len(queue_data.get('items', []))} 条待上传数据")
        except Exception as e:
            logger.warning(f"加载待上传队列失败: {e}")
    
    def save_pending_queue(self):
        """持久化待上传队列到磁盘"""
        try:
            all_items = []
            for date, ip_data_list in self.daily_ips_with_time.items():
                all_items.extend(ip_data_list)
            
            queue_data = {
                'updated_at': datetime.now().isoformat(),
                'count': len(all_items),
                'items': all_items
            }
            
            with open(self.pending_queue_file, 'w') as f:
                json.dump(queue_data, f, indent=2)
                
            logger.debug(f"持久化待上传队列: {len(all_items)} 条")
            self.last_persist_time = time.time()
        except Exception as e:
            logger.error(f"持久化队列失败: {e}")
    
    def should_persist(self) -> bool:
        """判断是否需要持久化（定期或数据量大时）"""
        total_items = sum(len(ips) for ips in self.daily_ips_with_time.values())
        time_elapsed = time.time() - self.last_persist_time
        
        # 条件：数据量超过阈值 或 距离上次持久化超过60秒
        return total_items > 1000 or time_elapsed > 60
    
    async def process_line(self, line: str):
        """处理单行日志，提取IP地址和时间戳（改进版：全局去重）"""
        self.processed_count += 1
        
        # 解析日志格式: 2025-11-12 10:32:32,125.162.162.237
        ip_data = self.extract_ip_and_timestamp_from_line(line)
        
        if ip_data and self.is_valid_ip(ip_data['ip']):
            ip = ip_data['ip']
            log_date = ip_data['date']
            
            #  改进：全局去重策略
            # 如果IP已经在全局缓存中，检查是否需要更新
            if ip in self.global_ip_cache:
                last_date = self.ip_last_seen.get(ip)
                
                # 如果是同一天出现，跳过
                if last_date == log_date:
                    self.duplicate_count += 1
                    return
                
                # 如果是不同天出现，可能需要更新updated_at
                # 这里可以选择：A) 每次都上传更新 B) 超过一定天数才更新
                # 当前策略：跨日期的IP也算重复，减少重复上传
                self.global_duplicate_count += 1
                
                # 更新最后出现日期
                self.ip_last_seen[ip] = log_date
                return
            
            # 新IP，添加到待上传队列
            if log_date not in self.daily_ips_with_time:
                self.daily_ips_with_time[log_date] = []
            
            self.daily_ips_with_time[log_date].append(ip_data)
            self.daily_ips[log_date].add(ip)
            
            # 更新全局缓存
            self.global_ip_cache.add(ip)
            self.ip_last_seen[ip] = log_date
    
    def extract_ip_and_timestamp_from_line(self, line: str) -> Optional[Dict]:
        """从日志行中提取IP地址和时间戳"""
        try:
            line = line.strip()
            if not line:
                return None
            
            # 尝试从行首提取时间戳
            # 支持格式：
            # 1. 2025/07/03 09:31:24 新IP首次连接: 180.254.163.108
            # 2. 2025-11-12 10:32:32,125.162.162.237
            # 3. 2025-11-12 10:32:32 其他文本 125.162.162.237
            
            timestamp_str = None
            log_time = None
            
            # 尝试解析行首的时间戳（两种格式）
            time_formats = [
                '%Y/%m/%d %H:%M:%S',  # 2025/07/03 09:31:24
                '%Y-%m-%d %H:%M:%S',  # 2025-11-12 10:32:32
            ]
            
            # 提取行首的时间戳字符串（前19个字符）
            if len(line) >= 19:
                potential_timestamp = line[:19]
                for fmt in time_formats:
                    try:
                        log_time = datetime.strptime(potential_timestamp, fmt)
                        timestamp_str = potential_timestamp
                        logger.debug(f"成功解析时间戳: {timestamp_str} -> {log_time}")
                        break
                    except ValueError:
                        continue
            
            # 如果没有解析到时间戳，使用当前时间
            if not log_time:
                logger.warning(f"未能从日志行提取时间戳，使用当前时间: {line[:50]}...")
                log_time = datetime.now()
            
            # 提取IP地址
            ips = IP_REGEX.findall(line)
            if ips:
                # 过滤掉时间戳中可能被误识别的数字
                valid_ips = [ip for ip in ips if self.is_valid_ip(ip)]
                if valid_ips:
                    return {
                        'ip': valid_ips[0],
                        'timestamp': log_time.isoformat(),
                        'date': log_time.strftime('%Y-%m-%d'),
                        'botnet_type': self.botnet_type
                    }
            
            return None
        except Exception as e:
            logger.debug(f"提取IP和时间戳失败: {line[:50]}... 错误: {e}")
            return None
    
    def extract_ip_from_line(self, line: str) -> Optional[str]:
        """从日志行中提取IP地址（保留兼容性）"""
        ip_data = self.extract_ip_and_timestamp_from_line(line)
        return ip_data['ip'] if ip_data else None
    
    def is_valid_ip(self, ip: str) -> bool:
        """验证IP地址是否有效"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            
            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            
            # 过滤私有IP和特殊IP
            if ip.startswith(('127.', '10.', '192.168.', '169.254.')):
                return False
            if ip.startswith('172.'):
                second_octet = int(parts[1])
                if 16 <= second_octet <= 31:
                    return False
            
            return True
        except:
            return False
    
    def get_new_ips_for_upload(self, max_count: int = None) -> List[Dict]:
        """获取需要上传的新IP数据（按时间戳排序）"""
        all_new_ips = []
        
        # 优先使用包含时间戳的数据，并按日期排序
        sorted_dates = sorted(self.daily_ips_with_time.keys())
        for date in sorted_dates:
            all_new_ips.extend(self.daily_ips_with_time[date])
        
        # 如果没有时间戳数据，回退到旧格式（兼容性）
        if not all_new_ips:
            sorted_dates = sorted(self.daily_ips.keys())
            for date in sorted_dates:
                for ip in self.daily_ips[date]:
                    all_new_ips.append({
                        'ip': ip,
                        'date': date,
                        'botnet_type': self.botnet_type,
                        'timestamp': datetime.now().isoformat()
                    })
        
        # 限制数量
        if max_count and len(all_new_ips) > max_count:
            return all_new_ips[:max_count]
        
        return all_new_ips
    
    def clear_uploaded_ips(self, uploaded_count: int):
        """清理已上传的IP（包含时间戳数据）"""
        # 优先清理时间戳数据
        cleared_count = 0
        
        for date in list(self.daily_ips_with_time.keys()):
            ip_data_list = self.daily_ips_with_time[date]
            
            # 清理指定数量的IP数据
            while ip_data_list and cleared_count < uploaded_count:
                ip_data = ip_data_list.pop(0)
                ip = ip_data['ip']
                
                # 同时从daily_ips中移除
                if date in self.daily_ips:
                    self.daily_ips[date].discard(ip)
                
                cleared_count += 1
            
            # 如果该日期的IP数据为空，删除该日期
            if not ip_data_list:
                del self.daily_ips_with_time[date]
            
            # 如果该日期的IP集合为空，删除该日期
            if date in self.daily_ips and not self.daily_ips[date]:
                del self.daily_ips[date]
            
            if cleared_count >= uploaded_count:
                break
        
        # 如果时间戳数据不足，继续清理普通IP数据（兼容性）
        if cleared_count < uploaded_count:
            for date in list(self.daily_ips.keys()):
                ips_list = list(self.daily_ips[date])
                
                for ip in ips_list:
                    if cleared_count >= uploaded_count:
                        break
                        
                    self.daily_ips[date].discard(ip)
                    cleared_count += 1
                
                # 如果该日期的IP集合为空，删除该日期
                if not self.daily_ips[date]:
                    del self.daily_ips[date]
                
                if cleared_count >= uploaded_count:
                    break
        
        logger.info(f"清理已上传的IP: {cleared_count} 个")
    
    def get_stats(self) -> Dict:
        """获取处理统计（增强版）"""
        # 修复：统计daily_ips_with_time中的数据
        total_new_ips = sum(len(ip_list) for ip_list in self.daily_ips_with_time.values())
        return {
            'processed_lines': self.processed_count,
            'duplicate_count': self.duplicate_count,
            'global_duplicate_count': self.global_duplicate_count,  # 新增
            'cached_ips': len(self.global_ip_cache),
            'new_ips_pending': total_new_ips,
            'unique_ips_total': len(self.global_ip_cache) + total_new_ips
        }
    
    def check_memory_pressure(self) -> bool:
        """检查内存压力"""
        total_items = sum(len(ip_list) for ip_list in self.daily_ips_with_time.values())
        return total_items >= MAX_MEMORY_IPS


class RemoteUploader:
    """远端上传器 - 负责将处理后的数据上传到本地服务器"""
    
    def __init__(self):
        self.upload_count = 0
        self.error_count = 0
        self.session = None
    
    async def create_session(self):
        """创建HTTP会话"""
        if self.session is None:
            # 增加超时时间到120秒，适应首次表结构升级等耗时操作
            # 注意：正常上传应该在几秒内完成，但首次可能需要更长时间
            timeout = aiohttp.ClientTimeout(total=120, connect=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close_session(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def check_server_online(self) -> bool:
        """
        检查服务器是否在线
        返回: True表示在线，False表示离线
        """
        await self.create_session()
        
        try:
            # 尝试连接到服务器的健康检查端点
            # 如果服务器没有专门的健康检查端点，使用普通的GET请求
            headers = {
                "X-API-Key": API_KEY
            }
            
            # 使用较短的超时时间进行健康检查
            timeout = aiohttp.ClientTimeout(total=SERVER_CHECK_TIMEOUT)
            
            async with self.session.get(
                API_ENDPOINT,
                headers=headers,
                timeout=timeout
            ) as response:
                # 只要能收到响应（无论状态码），就认为服务器在线
                # 因为服务器可能返回404或其他错误，但这表明服务器是运行的
                logger.info(f" 服务器在线检查通过 (HTTP {response.status})")
                return True
                
        except asyncio.TimeoutError:
            logger.warning(" 服务器连接超时，可能离线")
            return False
            
        except aiohttp.ClientConnectorError as e:
            logger.warning(f" 无法连接到服务器: {e}")
            return False
            
        except aiohttp.ClientError as e:
            logger.warning(f" 服务器连接错误: {e}")
            return False
            
        except Exception as e:
            logger.error(f" 服务器在线检查异常: {e}")
            return False
    
    async def upload_ips(self, ip_data: List[Dict]) -> bool:
        """异步上传IP数据到本地服务器"""
        if not ip_data:
            return True
        
        await self.create_session()
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        }
        
        data = {
            "botnet_type": BOTNET_TYPE,
            "ip_data": ip_data,
            "source_ip": await self.get_local_ip()
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"上传 {len(ip_data)} 个IP (尝试 {attempt + 1}/{MAX_RETRIES})")
                
                async with self.session.post(
                    API_ENDPOINT,
                    json=data,
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f" 上传成功: {result.get('received_count', len(ip_data))} 个IP")
                        self.upload_count += result.get('received_count', len(ip_data))
                        return True
                        
                    elif response.status == 401:
                        logger.error(" 认证失败: API密钥无效")
                        return False
                        
                    elif response.status == 403:
                        logger.error(" 权限不足: IP未在白名单中")
                        return False
                        
                    else:
                        error_text = await response.text()
                        logger.warning(f" 上传失败 (HTTP {response.status}): {error_text}")
                        
            except aiohttp.ClientError as e:
                logger.warning(f" 网络错误: {e}")
                
            except Exception as e:
                logger.error(f" 上传异常: {e}")
            
            # 重试延迟
            if attempt < MAX_RETRIES - 1:
                logger.info(f"等待 {RETRY_DELAY} 秒后重试...")
                await asyncio.sleep(RETRY_DELAY)
        
        # 所有重试都失败
        logger.error(f" 上传失败: 已重试 {MAX_RETRIES} 次")
        self.error_count += 1
        return False
    
    async def get_local_ip(self) -> str:
        """获取本机IP"""
        try:
            # 使用异步方式获取IP
            import socket
            loop = asyncio.get_event_loop()
            
            def _get_ip():
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            
            return await loop.run_in_executor(None, _get_ip)
        except:
            return "unknown"


class AsyncLogProcessor:
    """异步日志处理器 - 协调LogReader、IPProcessor和RemoteUploader（改进版）"""
    
    def __init__(self):
        self.log_reader = LogReader(LOG_DIR, LOG_FILE_PATTERN)
        self.ip_processor = IPProcessor(BOTNET_TYPE, DUPLICATE_CACHE_FILE, PENDING_QUEUE_FILE)
        self.uploader = RemoteUploader()
        self.state = self.load_state()
        self.server_offline_count = 0  # 服务器连续离线次数计数器
        self.upload_in_progress = False  # 上传进行中标志
    
    def load_state(self) -> Dict:
        """加载处理状态"""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                    logger.info(f"加载状态: 总共处理 {state.get('total_processed', 0)} 行")
                    return state
        except Exception as e:
            logger.warning(f"加载状态失败: {e}")
        
        return {
            'file_offsets': {},  # 记录每个文件的读取偏移量 {filepath: offset}
            'last_upload_time': None,
            'total_processed': 0
        }
    
    def load_file_offsets(self) -> Dict[str, int]:
        """加载文件读取偏移量"""
        try:
            if os.path.exists(OFFSET_STATE_FILE):
                with open(OFFSET_STATE_FILE, 'r') as f:
                    offsets = json.load(f)
                    logger.info(f"加载文件偏移量: {len(offsets)} 个文件")
                    return offsets
        except Exception as e:
            logger.warning(f"加载文件偏移量失败: {e}")
        return {}
    
    def save_file_offsets(self, offsets: Dict[str, int]):
        """保存文件读取偏移量"""
        try:
            with open(OFFSET_STATE_FILE, 'w') as f:
                json.dump(offsets, f, indent=2)
            logger.debug(f"保存文件偏移量: {len(offsets)} 个文件")
        except Exception as e:
            logger.error(f"保存文件偏移量失败: {e}")
    
    def save_state(self):
        """保存处理状态"""
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.debug("保存状态成功")
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    async def process_log_files_and_upload(self):
        """处理日志文件并实现真正的流式上传"""
        # 获取可用的日志文件
        log_files = self.log_reader.get_available_log_files()
        
        if not log_files:
            logger.info("没有找到日志文件")
            return
        
        logger.info(f"发现 {len(log_files)} 个日志文件")
        
        # 加载文件偏移量
        file_offsets = self.load_file_offsets()
        
        # 处理每个文件（包括已处理过的文件，以读取增量数据）
        for date, file_path in log_files:
            file_path_str = str(file_path)
            start_offset = file_offsets.get(file_path_str, 0)
            
            logger.info(f"处理日志文件: {file_path} (日期: {date.strftime('%Y-%m-%d')})")
            
            try:
                #  改进：流式处理 - 分块读取和上传
                await self.process_file_streaming(
                    file_path, file_path_str, start_offset, file_offsets
                )
                    
            except Exception as e:
                logger.error(f"❌ 处理文件失败 {file_path}: {e}", exc_info=True)
                # 保存当前进度
                self.ip_processor.save_pending_queue()
                #  改进：不要因为一个文件失败就退出，继续处理下一个
                logger.warning(f"跳过失败文件 {file_path}，继续处理下一个文件")
                continue
    
    async def process_file_streaming(self, file_path: Path, file_path_str: str, 
                                     start_offset: int, file_offsets: Dict[str, int]):
        """流式处理单个文件 - 边读边传（真正的分块处理）"""
        chunk_lines = 5000  #  改进：每次只读取5000行，真正分块
        total_processed = 0
        current_offset = start_offset
        last_saved_offset = start_offset
        
        logger.info(f"开始流式处理文件: {file_path}")
        
        while True:
            # 检查内存压力
            if self.ip_processor.check_memory_pressure():
                logger.warning(f"内存压力过大，暂停读取并强制上传")
                await self.force_upload_all()
            
            #  关键改进：每次只读取指定行数，真正分块
            batch_processed, new_offset = await self.log_reader.read_log_file(
                file_path, self.ip_processor, current_offset, max_lines=chunk_lines
            )
            
            if batch_processed == 0:
                # 没有新数据了
                logger.info(f"文件 {file_path.name} 无更多数据")
                break
            
            total_processed += batch_processed
            current_offset = new_offset
            
            logger.info(f"批次处理: {batch_processed} 行, 累计: {total_processed} 行, 当前偏移量: {current_offset}")
            
            #  关键改进：频繁上传，避免积压
            await self.upload_if_needed_aggressive()
            
            # 定期持久化待上传队列
            if self.ip_processor.should_persist():
                self.ip_processor.save_pending_queue()
            
            #  关键改进：只在上传成功后才保存偏移量
            stats = self.ip_processor.get_stats()
            if stats['new_ips_pending'] < MIN_UPLOAD_BATCH:
                # 待上传数据少，说明刚上传过，可以安全保存偏移量
                file_offsets[file_path_str] = current_offset
                self.save_file_offsets(file_offsets)
                self.state['total_processed'] += (current_offset - last_saved_offset)
                self.save_state()
                last_saved_offset = current_offset
                logger.debug(f"安全保存偏移量: {current_offset}")
        
        #  新增：文件处理完成后，上传剩余数据
        if total_processed > 0:
            logger.info(f"文件处理完成: {file_path}, 总共处理 {total_processed} 行")
            
            # 上传剩余的数据（即使没达到阈值）
            stats = self.ip_processor.get_stats()
            if stats['new_ips_pending'] > 0:
                logger.info(f"上传文件剩余的 {stats['new_ips_pending']} 条数据")
                await self.upload_new_ips()
                
                # 上传成功后保存最终偏移量
                stats_after = self.ip_processor.get_stats()
                if stats_after['new_ips_pending'] == 0:
                    file_offsets[file_path_str] = current_offset
                    self.save_file_offsets(file_offsets)
                    logger.info(f"✓ 文件 {file_path.name} 完全处理并上传成功")
    
    async def upload_if_needed(self):
        """检查是否有足够的IP需要上传，如果有则立即上传"""
        ip_stats = self.ip_processor.get_stats()
        pending_ips = ip_stats['new_ips_pending']
        
        # 如果待上传IP达到批次大小，立即上传
        if pending_ips >= BATCH_SIZE:
            logger.info(f"待上传IP已达到批次大小({pending_ips} >= {BATCH_SIZE})，开始上传")
            await self.upload_new_ips()
    
    async def upload_if_needed_aggressive(self):
        """更激进的上传策略 - 用于流式处理"""
        if self.upload_in_progress:
            return
        
        ip_stats = self.ip_processor.get_stats()
        pending_ips = ip_stats['new_ips_pending']
        
        #  改进：降低上传阈值，更频繁上传
        if pending_ips >= FORCE_UPLOAD_THRESHOLD:
            logger.info(f"达到强制上传阈值({pending_ips} >= {FORCE_UPLOAD_THRESHOLD})")
            await self.upload_new_ips()
        elif pending_ips >= MIN_UPLOAD_BATCH:
            # 即使没达到大批次，也尝试上传小批次
            logger.info(f"小批次上传({pending_ips} >= {MIN_UPLOAD_BATCH})")
            await self.upload_new_ips()
    
    async def force_upload_all(self):
        """强制上传所有待上传数据"""
        ip_stats = self.ip_processor.get_stats()
        pending_ips = ip_stats['new_ips_pending']
        
        if pending_ips == 0:
            return
        
        logger.warning(f"强制上传所有数据: {pending_ips} 条")
        
        while pending_ips > 0:
            await self.upload_new_ips()
            ip_stats = self.ip_processor.get_stats()
            new_pending = ip_stats['new_ips_pending']
            
            if new_pending >= pending_ips:
                # 没有减少，可能上传失败
                logger.error("上传失败，无法减少待上传队列")
                break
            
            pending_ips = new_pending
    
    async def upload_new_ips(self):
        """上传新发现的IP（改进版：持久化保护）"""
        if self.upload_in_progress:
            logger.debug("上传正在进行中，跳过")
            return
        
        self.upload_in_progress = True
        
        try:
            new_ips = self.ip_processor.get_new_ips_for_upload(BATCH_SIZE)
            
            if not new_ips:
                logger.debug("没有新IP需要上传")
                return
            
            logger.info(f"准备上传 {len(new_ips)} 个新IP")
            
            #  关键改进：上传前先持久化到磁盘
            self.ip_processor.save_pending_queue()
            
            # 上传IP数据
            success = await self.uploader.upload_ips(new_ips)
            
            if success:
                #  只在上传成功后才清理
                self.ip_processor.clear_uploaded_ips(len(new_ips))
                self.state['last_upload_time'] = datetime.now().isoformat()
                
                # 保存IP缓存和状态
                self.ip_processor.save_cache()
                self.ip_processor.save_pending_queue()  # 更新持久化队列
                self.save_state()
                
                logger.info(f"✓ 上传成功，累计上传: {self.uploader.upload_count} 个IP")
            else:
                #  改进：上传失败，数据已持久化，不会丢失
                logger.error(f"✗ 上传失败，数据已持久化到 {PENDING_QUEUE_FILE}，下次重启会恢复")
                # 不清理数据，保留在内存和磁盘中
        finally:
            self.upload_in_progress = False
    
    async def wait_for_server_online(self) -> bool:
        """
        等待服务器在线
        返回: True表示服务器在线，False表示达到最大重试次数后仍然离线
        """
        logger.info("检查服务器是否在线...")
        
        # 检查服务器是否在线
        is_online = await self.uploader.check_server_online()
        
        if is_online:
            # 服务器在线，重置离线计数器
            if self.server_offline_count > 0:
                logger.info(f" 服务器已恢复在线（之前离线 {self.server_offline_count} 次）")
            self.server_offline_count = 0
            return True
        
        # 服务器离线，增加计数器
        self.server_offline_count += 1
        
        # 计算等待时间（随着离线次数增加而增加等待时间，但有上限）
        if self.server_offline_count <= MAX_SERVER_CHECK_RETRIES:
            wait_time = SERVER_CHECK_INTERVAL
        else:
            # 超过最大重试次数后，使用更长的等待时间
            wait_time = SERVER_CHECK_INTERVAL * 2
        
        logger.warning(
            f" 服务器离线（第 {self.server_offline_count} 次检测），"
            f"将在 {wait_time} 秒后重试..."
        )
        
        await asyncio.sleep(wait_time)
        return False
    
    async def run_once(self):
        """执行一次完整的处理流程"""
        logger.info("-" * 80)
        logger.info("开始执行日志处理任务")
        
        try:
            # 1. 处理日志文件并边读边传
            await self.process_log_files_and_upload()
            
            # 2. 上传剩余的IP（如果有的话）
            await self.upload_new_ips()
            
            # 3. 显示统计信息
            self.print_stats()
            
        except Exception as e:
            logger.error(f"处理任务异常: {e}")
        
        logger.info("任务执行完成")
    
    async def run_forever(self):
        """持续运行处理器"""
        logger.info("=" * 80)
        logger.info("异步日志处理器启动")
        logger.info("=" * 80)
        logger.info(f"目标服务器: {API_ENDPOINT}")
        logger.info(f"僵尸网络类型: {BOTNET_TYPE}")
        logger.info(f"日志目录: {LOG_DIR}")
        logger.info(f"文件模式: {LOG_FILE_PATTERN}")
        logger.info(f"处理间隔: {UPLOAD_INTERVAL} 秒")
        logger.info(f"批量大小: {BATCH_SIZE} 个IP")
        logger.info(f"服务器检查间隔: {SERVER_CHECK_INTERVAL} 秒")
        logger.info("=" * 80)
        
        try:
            while True:
                # 1. 先检查服务器是否在线
                server_online = await self.wait_for_server_online()
                
                if not server_online:
                    # 服务器离线，跳过本次处理，继续等待
                    continue
                
                # 2. 服务器在线，执行正常的处理流程
                await self.run_once()
                
                # 3. 等待下次执行
                logger.info(f"等待 {UPLOAD_INTERVAL} 秒后执行下次处理...")
                await asyncio.sleep(UPLOAD_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("\n收到中断信号，正在退出...")
        except Exception as e:
            logger.error(f"处理器异常: {e}")
        finally:
            # 清理资源
            await self.uploader.close_session()
            
            # 最终统计
            logger.info("=" * 80)
            logger.info("处理器已停止")
            self.print_stats()
            logger.info("=" * 80)
    
    def print_stats(self):
        """打印统计信息（增强版 - 更详细的监控）"""
        ip_stats = self.ip_processor.get_stats()
        
        logger.info("=" * 80)
        logger.info(" 处理统计报告")
        logger.info("=" * 80)
        
        # 基础统计
        logger.info(" 数据处理:")
        logger.info(f"  ├─ 已处理行数: {ip_stats['processed_lines']:,}")
        logger.info(f"  ├─ 日内重复IP: {ip_stats['duplicate_count']:,}")
        logger.info(f"  ├─ 全局重复IP: {ip_stats.get('global_duplicate_count', 0):,}")
        logger.info(f"  └─ 唯一IP总数: {ip_stats.get('unique_ips_total', 0):,}")
        
        # 上传统计
        logger.info("")
        logger.info(" 上传状态:")
        logger.info(f"  ├─ 待上传IP数: {ip_stats['new_ips_pending']:,}")
        logger.info(f"  ├─ 已缓存IP数: {ip_stats['cached_ips']:,}")
        logger.info(f"  ├─ 累计上传数: {self.uploader.upload_count:,}")
        logger.info(f"  └─ 失败次数: {self.uploader.error_count}")
        
        # 去重效率
        if ip_stats['processed_lines'] > 0:
            total_duplicates = ip_stats['duplicate_count'] + ip_stats.get('global_duplicate_count', 0)
            dedup_rate = (total_duplicates / ip_stats['processed_lines']) * 100
            logger.info("")
            logger.info(" 去重效率:")
            logger.info(f"  └─ 去重率: {dedup_rate:.1f}% ({total_duplicates:,} / {ip_stats['processed_lines']:,})")
        
        # 内存和磁盘状态
        logger.info("")
        logger.info(" 存储状态:")
        
        # 持久化队列检查
        if os.path.exists(PENDING_QUEUE_FILE):
            try:
                queue_size = os.path.getsize(PENDING_QUEUE_FILE) / 1024 / 1024
                logger.info(f"  ├─ 队列文件: {queue_size:.2f} MB")
            except:
                logger.info(f"  ├─ 队列文件: 存在")
        else:
            logger.info(f"  ├─ 队列文件: 无")
        
        # 不完整行缓存
        incomplete_count = len(self.log_reader.incomplete_lines)
        if incomplete_count > 0:
            logger.info(f"  ├─ 不完整行: {incomplete_count} 个文件")
        
        # 文件缓存
        if self.log_reader.file_cache:
            logger.info(f"  └─ 文件缓存: {len(self.log_reader.file_cache)} 个文件")
        
        # 内存压力告警
        logger.info("")
        if ip_stats['new_ips_pending'] > FORCE_UPLOAD_THRESHOLD:
            logger.warning(f"  内存压力警告: 待上传数据 {ip_stats['new_ips_pending']:,} 超过阈值 {FORCE_UPLOAD_THRESHOLD:,}")
        elif ip_stats['new_ips_pending'] > MIN_UPLOAD_BATCH:
            logger.info(f"ℹ  待上传数据: {ip_stats['new_ips_pending']:,} 条 (正常范围)")
        else:
            logger.info(f"✓  待上传数据: {ip_stats['new_ips_pending']:,} 条 (健康)")
        
        logger.info("=" * 80)


# ============================================================
# 命令行模式
# ============================================================

async def test_connection():
    """测试连接"""
    print("测试连接到本地服务器...")
    print(f"目标: {API_ENDPOINT}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            status_url = f"http://{LOCAL_SERVER_HOST}:{LOCAL_SERVER_PORT}/api/upload-status"
            
            async with session.get(status_url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f" 连接成功!")
                    print(f"服务器状态: {data.get('api_status', 'unknown')}")
                    print(f"服务器时间: {data.get('timestamp', 'unknown')}")
                    return True
                else:
                    print(f" 连接失败: HTTP {response.status}")
                    return False
                    
    except Exception as e:
        print(f" 连接失败: {e}")
        return False


async def test_upload():
    """测试上传功能"""
    print("\n测试上传功能...")
    
    # 模拟IP数据
    test_ip_data = [{
        'ip': '1.2.3.4',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'botnet_type': BOTNET_TYPE,
        'timestamp': datetime.now().isoformat()
    }]
    
    uploader = RemoteUploader()
    success = await uploader.upload_ips(test_ip_data)
    await uploader.close_session()
    
    if success:
        print(" 上传测试成功!")
        return True
    else:
        print(" 上传测试失败!")
        return False


async def test_log_processing():
    """测试日志处理功能"""
    print("\n测试日志处理功能...")
    
    processor = AsyncLogProcessor()
    
    # 检查日志文件
    log_files = processor.log_reader.get_available_log_files()
    if not log_files:
        print(" 没有找到日志文件")
        print(f"请检查日志目录: {LOG_DIR}")
        print(f"文件模式: {LOG_FILE_PATTERN}")
        return False
    
    print(f" 找到 {len(log_files)} 个日志文件")
    for date, path in log_files:
        file_size = path.stat().st_size if path.exists() else 0
        print(f"  {date.strftime('%Y-%m-%d')}: {path} ({file_size:,} bytes)")
    
    return True


async def main_async():
    """异步主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            # 测试模式
            print("=" * 80)
            print("  远端上传器 - 测试模式")
            print("=" * 80)
            
            # 测试连接
            conn_ok = await test_connection()
            if not conn_ok:
                print("\n请检查:")
                print("  1. LOCAL_SERVER_HOST 是否正确？")
                print("  2. 本地服务器是否运行？")
                print("  3. 防火墙是否开放端口？")
                sys.exit(1)
            
            # 测试上传
            upload_ok = await test_upload()
            if not upload_ok:
                print("\n请检查:")
                print("  1. API_KEY 是否正确？")
                print("  2. 远端IP是否在白名单中？")
                sys.exit(1)
            
            # 测试日志处理
            log_ok = await test_log_processing()
            if not log_ok:
                print("\n请检查:")
                print("  1. LOG_DIR 路径是否正确？")
                print("  2. 日志文件是否存在？")
                print("  3. LOG_FILE_PATTERN 模式是否正确？")
                sys.exit(1)
            
            print("\n 所有测试通过！可以运行正式模式")
            print(f"\n启动命令: python {sys.argv[0]}")
            
        elif command == "once":
            # 单次执行
            processor = AsyncLogProcessor()
            await processor.run_once()
            await processor.uploader.close_session()
            
        else:
            print(f"未知命令: {command}")
            print(f"用法:")
            print(f"  python {sys.argv[0]}       - 持续运行")
            print(f"  python {sys.argv[0]} test  - 测试连接")
            print(f"  python {sys.argv[0]} once  - 单次执行")
    else:
        # 持续运行模式
        processor = AsyncLogProcessor()
        await processor.run_forever()


def main():
    """主函数"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()





