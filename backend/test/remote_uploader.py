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
# 配置区域 - 请根据实际情况修改
# ============================================================

# 本地服务器配置
LOCAL_SERVER_HOST = "your-local-server-ip"  # 修改为本地服务器的公网IP或域名
LOCAL_SERVER_PORT = 8000

# API密钥（必须与本地服务器的config.py中的API_KEY一致）
API_KEY = "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"

# 僵尸网络类型（根据实际蜜罐类型修改）
BOTNET_TYPE = "ramnit"  # 可选: asruex, mozi, andromeda, moobot, ramnit, leethozer

# 日志文件配置（每日日志文件）
LOG_DIR = "/home/ubuntu"  # 日志文件目录
LOG_FILE_PATTERN = "ramnit_{date}.log"  # 日志文件命名模式，{date}会被替换为YYYY-MM-DD

# 处理配置
UPLOAD_INTERVAL = 300  # 上传间隔（秒），默认5分钟
BATCH_SIZE = 500       # 每次上传的最大IP数量
MAX_RETRIES = 3        # 上传失败重试次数
RETRY_DELAY = 30       # 重试延迟（秒）
READ_CHUNK_SIZE = 8192 # 文件读取块大小

# 状态文件（记录处理状态）
STATE_FILE = "/tmp/uploader_state.json"
DUPLICATE_CACHE_FILE = "/tmp/ip_cache.json"  # IP去重缓存文件

# IP缓存配置
CACHE_EXPIRE_DAYS = 7  # IP缓存过期天数

# API端点配置
API_ENDPOINT = "https://periotic-multifaced-christena.ngrok-free.dev"

# IP解析配置
IP_REGEX = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')  # IP地址正则表达式

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
    """异步日志读取器"""
    
    def __init__(self, log_dir: str, file_pattern: str):
        self.log_dir = Path(log_dir)
        self.file_pattern = file_pattern
        self.processed_files = set()
        
    def get_log_file_path(self, date: datetime) -> Path:
        """获取指定日期的日志文件路径"""
        date_str = date.strftime('%Y-%m-%d')
        filename = self.file_pattern.format(date=date_str)
        return self.log_dir / filename
    
    def get_available_log_files(self, days_back: int = 7) -> List[Tuple[datetime, Path]]:
        """获取可用的日志文件列表"""
        files = []
        today = datetime.now().date()
        
        for i in range(days_back + 1):
            date = datetime.combine(today - timedelta(days=i), datetime.min.time())
            file_path = self.get_log_file_path(date)
            
            if file_path.exists() and file_path.is_file():
                files.append((date, file_path))
                logger.debug(f"发现日志文件: {file_path}")
        
        return sorted(files, key=lambda x: x[0])  # 按日期排序
    
    async def read_log_file(self, file_path: Path, processor) -> int:
        """异步读取日志文件并交给处理器处理"""
        if not file_path.exists():
            logger.warning(f"日志文件不存在: {file_path}")
            return 0
        
        logger.info(f"开始读取日志文件: {file_path}")
        processed_lines = 0
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                buffer = ""
                
                while True:
                    chunk = await f.read(READ_CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    buffer += chunk
                    lines = buffer.split('\n')
                    buffer = lines[-1]  # 保留最后一个不完整的行
                    
                    # 处理完整的行
                    for line in lines[:-1]:
                        if line.strip():
                            await processor.process_line(line.strip())
                            processed_lines += 1
                            
                            # 每处理一定数量的行就让出控制权
                            if processed_lines % 1000 == 0:
                                await asyncio.sleep(0.001)
                
                # 处理最后一行
                if buffer.strip():
                    await processor.process_line(buffer.strip())
                    processed_lines += 1
        
        except Exception as e:
            logger.error(f"读取日志文件失败 {file_path}: {e}")
            return 0
        
        logger.info(f"完成读取日志文件: {file_path}, 处理了 {processed_lines} 行")
        return processed_lines


class IPProcessor:
    """IP处理器 - 负责解析、去重和缓存IP数据"""
    
    def __init__(self, botnet_type: str, cache_file: str):
        self.botnet_type = botnet_type
        self.cache_file = cache_file
        self.ip_cache: Set[str] = set()
        self.daily_ips: Dict[str, Set[str]] = defaultdict(set)  # 按日期分组的IP
        self.daily_ips_with_time: Dict[str, List[Dict]] = defaultdict(list)  # 包含时间戳的IP数据
        self.processed_count = 0
        self.duplicate_count = 0
        self.load_cache()
    
    def load_cache(self):
        """加载IP缓存（仅用于统计，不用于去重）"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # 加载所有历史IP（用于统计显示）
                self.ip_cache = set()
                for ip_data in cache_data.get('ips', []):
                    self.ip_cache.add(ip_data['ip'])
                
                logger.info(f"加载IP缓存: {len(self.ip_cache)} 个IP（仅统计用）")
        except Exception as e:
            logger.warning(f"加载IP缓存失败: {e}")
            self.ip_cache = set()
    
    def save_cache(self):
        """保存IP缓存"""
        try:
            cache_data = {
                'updated_at': datetime.now().isoformat(),
                'ips': [
                    {
                        'ip': ip,
                        'timestamp': datetime.now().isoformat()
                    }
                    for ip in self.ip_cache
                ]
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.debug(f"保存IP缓存: {len(self.ip_cache)} 个IP")
        except Exception as e:
            logger.error(f"保存IP缓存失败: {e}")
    
    async def process_line(self, line: str):
        """处理单行日志，提取IP地址和时间戳"""
        self.processed_count += 1
        
        # 解析日志格式: 2025-11-12 10:32:32,125.162.162.237
        ip_data = self.extract_ip_and_timestamp_from_line(line)
        
        if ip_data and self.is_valid_ip(ip_data['ip']):
            ip = ip_data['ip']
            log_date = ip_data['date']
            
            # 只在同一天内去重，跨日期的重复IP仍需要上传以更新updated_at
            if ip in self.daily_ips[log_date]:
                self.duplicate_count += 1
            else:
                # 添加到当日集合（包含完整的IP数据）
                if log_date not in self.daily_ips_with_time:
                    self.daily_ips_with_time[log_date] = []
                
                self.daily_ips_with_time[log_date].append(ip_data)
                self.daily_ips[log_date].add(ip)
                
                # 更新全局缓存（用于统计，但不用于去重判断）
                self.ip_cache.add(ip)
    
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
        """获取需要上传的新IP数据（包含真实时间戳）"""
        all_new_ips = []
        
        # 优先使用包含时间戳的数据
        for date, ip_data_list in self.daily_ips_with_time.items():
            all_new_ips.extend(ip_data_list)
        
        # 如果没有时间戳数据，回退到旧格式（兼容性）
        if not all_new_ips:
            for date, ips in self.daily_ips.items():
                for ip in ips:
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
        """获取处理统计"""
        total_new_ips = sum(len(ips) for ips in self.daily_ips.values())
        return {
            'processed_lines': self.processed_count,
            'duplicate_count': self.duplicate_count,
            'cached_ips': len(self.ip_cache),
            'new_ips_pending': total_new_ips
        }


class RemoteUploader:
    """远端上传器 - 负责将处理后的数据上传到本地服务器"""
    
    def __init__(self):
        self.upload_count = 0
        self.error_count = 0
        self.session = None
    
    async def create_session(self):
        """创建HTTP会话"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close_session(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            self.session = None
    
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
                        logger.info(f"✅ 上传成功: {result.get('received_count', len(ip_data))} 个IP")
                        self.upload_count += result.get('received_count', len(ip_data))
                        return True
                        
                    elif response.status == 401:
                        logger.error("❌ 认证失败: API密钥无效")
                        return False
                        
                    elif response.status == 403:
                        logger.error("❌ 权限不足: IP未在白名单中")
                        return False
                        
                    else:
                        error_text = await response.text()
                        logger.warning(f"⚠️ 上传失败 (HTTP {response.status}): {error_text}")
                        
            except aiohttp.ClientError as e:
                logger.warning(f"⚠️ 网络错误: {e}")
                
            except Exception as e:
                logger.error(f"⚠️ 上传异常: {e}")
            
            # 重试延迟
            if attempt < MAX_RETRIES - 1:
                logger.info(f"等待 {RETRY_DELAY} 秒后重试...")
                await asyncio.sleep(RETRY_DELAY)
        
        # 所有重试都失败
        logger.error(f"❌ 上传失败: 已重试 {MAX_RETRIES} 次")
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
    """异步日志处理器 - 协调LogReader、IPProcessor和RemoteUploader"""
    
    def __init__(self):
        self.log_reader = LogReader(LOG_DIR, LOG_FILE_PATTERN)
        self.ip_processor = IPProcessor(BOTNET_TYPE, DUPLICATE_CACHE_FILE)
        self.uploader = RemoteUploader()
        self.state = self.load_state()
    
    def load_state(self) -> Dict:
        """加载处理状态"""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                    logger.info(f"加载状态: 已处理文件 {len(state.get('processed_files', []))} 个")
                    return state
        except Exception as e:
            logger.warning(f"加载状态失败: {e}")
        
        return {
            'processed_files': [],
            'last_upload_time': None,
            'total_processed': 0
        }
    
    def save_state(self):
        """保存处理状态"""
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.debug("保存状态成功")
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    async def process_log_files(self):
        """处理日志文件"""
        # 获取可用的日志文件
        log_files = self.log_reader.get_available_log_files()
        
        if not log_files:
            logger.info("没有找到日志文件")
            return
        
        logger.info(f"发现 {len(log_files)} 个日志文件")
        
        # 过滤已处理的文件
        processed_files = set(self.state.get('processed_files', []))
        new_files = [(date, path) for date, path in log_files 
                    if str(path) not in processed_files]
        
        if not new_files:
            logger.info("所有日志文件都已处理")
            return
        
        logger.info(f"需要处理 {len(new_files)} 个新日志文件")
        
        # 异步处理每个文件
        for date, file_path in new_files:
            logger.info(f"处理日志文件: {file_path} (日期: {date.strftime('%Y-%m-%d')})")
            
            try:
                processed_lines = await self.log_reader.read_log_file(file_path, self.ip_processor)
                
                if processed_lines > 0:
                    # 标记文件为已处理
                    self.state['processed_files'].append(str(file_path))
                    self.state['total_processed'] += processed_lines
                    
                    logger.info(f"完成处理: {file_path}, 处理了 {processed_lines} 行")
                    
                    # 保存状态
                    self.save_state()
                    
            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {e}")
    
    async def upload_new_ips(self):
        """上传新发现的IP"""
        new_ips = self.ip_processor.get_new_ips_for_upload(BATCH_SIZE)
        
        if not new_ips:
            logger.info("没有新IP需要上传")
            return
        
        logger.info(f"准备上传 {len(new_ips)} 个新IP")
        
        # 上传IP数据
        success = await self.uploader.upload_ips(new_ips)
        
        if success:
            # 清理已上传的IP
            self.ip_processor.clear_uploaded_ips(len(new_ips))
            self.state['last_upload_time'] = datetime.now().isoformat()
            
            # 保存IP缓存和状态
            self.ip_processor.save_cache()
            self.save_state()
            
            logger.info(f"上传完成，累计上传: {self.uploader.upload_count} 个IP")
        else:
            logger.error("上传失败，IP数据将在下次重试")
    
    async def run_once(self):
        """执行一次完整的处理流程"""
        logger.info("-" * 80)
        logger.info("开始执行日志处理任务")
        
        try:
            # 1. 处理日志文件
            await self.process_log_files()
            
            # 2. 上传新IP
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
        logger.info("=" * 80)
        
        try:
            while True:
                await self.run_once()
                
                # 等待下次执行
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
        """打印统计信息"""
        ip_stats = self.ip_processor.get_stats()
        
        logger.info("📊 处理统计:")
        logger.info(f"  已处理行数: {ip_stats['processed_lines']:,}")
        logger.info(f"  重复IP数: {ip_stats['duplicate_count']:,}")
        logger.info(f"  缓存IP数: {ip_stats['cached_ips']:,}")
        logger.info(f"  待上传IP: {ip_stats['new_ips_pending']:,}")
        logger.info(f"  累计上传: {self.uploader.upload_count:,}")
        logger.info(f"  错误次数: {self.uploader.error_count}")


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
                    print(f"✅ 连接成功!")
                    print(f"服务器状态: {data.get('api_status', 'unknown')}")
                    print(f"服务器时间: {data.get('timestamp', 'unknown')}")
                    return True
                else:
                    print(f"❌ 连接失败: HTTP {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ 连接失败: {e}")
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
        print("✅ 上传测试成功!")
        return True
    else:
        print("❌ 上传测试失败!")
        return False


async def test_log_processing():
    """测试日志处理功能"""
    print("\n测试日志处理功能...")
    
    processor = AsyncLogProcessor()
    
    # 检查日志文件
    log_files = processor.log_reader.get_available_log_files()
    if not log_files:
        print("⚠️ 没有找到日志文件")
        print(f"请检查日志目录: {LOG_DIR}")
        print(f"文件模式: {LOG_FILE_PATTERN}")
        return False
    
    print(f"✅ 找到 {len(log_files)} 个日志文件")
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
            
            print("\n🎉 所有测试通过！可以运行正式模式")
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





