#!/usr/bin/env python3
"""
C2端数据服务器 - 独立版本（不依赖 remote_uploader.py）
提供HTTP接口供服务器拉取数据

部署：只需要这一个文件 + config.json
"""

import asyncio
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from aiohttp import web
import aiofiles

# ============================================================
# 先初始化日志
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# 然后加载配置
# ============================================================

def load_config(config_file: str = "config.json") -> Dict:
    """加载配置文件"""
    default_config = {
        "botnet": {
            "botnet_type": "ramnit",
            "log_dir": "/home/ubuntu/logs",
            "log_file_pattern": "ramnit_{datetime}.log"
        }
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                logger.info(f"加载配置文件: {config_file}")
                return config
        except Exception as e:
            logger.error(f"加载配置失败: {e}，使用默认配置")
            return default_config
    else:
        logger.warning(f"配置文件不存在: {config_file}，使用默认配置")
        return default_config

# 加载配置
CONFIG = load_config()
BOTNET_TYPE = CONFIG["botnet"]["botnet_type"]
LOG_DIR = Path(CONFIG["botnet"]["log_dir"])
LOG_FILE_PATTERN = CONFIG["botnet"]["log_file_pattern"]

# HTTP服务器配置
HTTP_HOST = os.environ.get("C2_HTTP_HOST", "0.0.0.0")
HTTP_PORT = int(os.environ.get("C2_HTTP_PORT", "8888"))
API_KEY = os.environ.get("C2_API_KEY", "your-secret-api-key-here")

# 数据缓存配置
MAX_CACHED_RECORDS = 10000
CACHE_FILE = "/tmp/c2_data_cache.json"

# IP解析正则
IP_REGEX = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')

# ============================================================
# 通用工具类
# ============================================================

class LogReader:
    """日志文件读取器"""
    
    def __init__(self, log_dir: Path, file_pattern: str):
        self.log_dir = log_dir
        self.file_pattern = file_pattern
    
    async def get_available_log_files(self, hours_back: int = 48) -> List[Tuple[datetime, Path]]:
        """获取可用的日志文件列表（只返回上一小时及更早的文件）"""
        files = []
        now = datetime.now()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        earliest_time = now - timedelta(hours=hours_back)
        
        if not self.log_dir.exists():
            logger.warning(f"日志目录不存在: {self.log_dir}")
            return files
        
        # 支持 {datetime} 格式（按小时）
        if '{datetime}' in self.file_pattern:
            pattern_parts = self.file_pattern.split('{datetime}')
            if len(pattern_parts) == 2:
                prefix, suffix = pattern_parts
                glob_pattern = f"{prefix}*{suffix}"
                
                for file_path in self.log_dir.glob(glob_pattern):
                    if file_path.is_file():
                        try:
                            filename = file_path.name
                            datetime_str = filename[len(prefix):-len(suffix)] if suffix else filename[len(prefix):]
                            file_datetime = datetime.strptime(datetime_str, '%Y-%m-%d_%H')
                            
                            # 只处理上一小时及更早的文件（跳过当前小时）
                            if earliest_time <= file_datetime < current_hour:
                                files.append((file_datetime, file_path))
                        except ValueError:
                            continue
        
        # 支持 {date} 格式（按天）
        elif '{date}' in self.file_pattern:
            pattern_parts = self.file_pattern.split('{date}')
            if len(pattern_parts) == 2:
                prefix, suffix = pattern_parts
                glob_pattern = f"{prefix}*{suffix}"
                
                for file_path in self.log_dir.glob(glob_pattern):
                    if file_path.is_file():
                        try:
                            filename = file_path.name
                            date_str = filename[len(prefix):-len(suffix)] if suffix else filename[len(prefix):]
                            file_date = datetime.strptime(date_str, '%Y-%m-%d')
                            files.append((file_date, file_path))
                        except ValueError:
                            continue
        
        return sorted(files, key=lambda x: x[0])


class IPProcessor:
    """IP地址处理器"""
    
    def __init__(self, botnet_type: str):
        self.botnet_type = botnet_type
    
    def normalize_ip(self, ip: str) -> Optional[str]:
        """规范化IP地址（去除前导零）并验证"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return None
            
            normalized_parts = []
            for part in parts:
                num = int(part)  # 自动去除前导零
                if num < 0 or num > 255:
                    return None
                normalized_parts.append(str(num))
            
            normalized_ip = '.'.join(normalized_parts)
            
            # 过滤私有IP
            if normalized_ip.startswith(('127.', '10.', '192.168.', '169.254.')):
                return None
            if normalized_ip.startswith('172.'):
                second_octet = int(normalized_parts[1])
                if 16 <= second_octet <= 31:
                    return None
            
            return normalized_ip
        except:
            return None
    
    def extract_ip_and_timestamp_from_line(self, line: str, file_path: Path = None) -> Optional[Dict]:
        """从日志行提取IP和时间戳"""
        try:
            # 尝试解析时间戳
            log_time = None
            timestamp_source = "parsed"
            
            # 常见时间格式
            time_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
            ]
            
            # 从行首提取时间戳
            if len(line) >= 19:
                potential_timestamp = line[:19]
                for fmt in time_formats:
                    try:
                        log_time = datetime.strptime(potential_timestamp, fmt)
                        break
                    except:
                        continue
            
            # 如果无法解析，使用文件修改时间
            if not log_time and file_path and file_path.exists():
                log_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                timestamp_source = "file_mtime"
            
            # 最后使用当前时间
            if not log_time:
                log_time = datetime.now()
                timestamp_source = "fallback_now"
            
            # 提取IP地址
            ips = IP_REGEX.findall(line)
            if ips:
                for ip in ips:
                    normalized_ip = self.normalize_ip(ip)
                    if normalized_ip:
                        return {
                            'ip': normalized_ip,
                            'raw_ip': ip if ip != normalized_ip else None,
                            'timestamp': log_time.isoformat(),
                            'timestamp_source': timestamp_source,
                            'date': log_time.strftime('%Y-%m-%d'),
                            'log_hour': log_time.strftime('%Y-%m-%d_%H'),
                            'botnet_type': self.botnet_type
                        }
            
            return None
        except Exception as e:
            return None


# ============================================================
# 数据缓存管理器
# ============================================================

class DataCache:
    """数据缓存管理器"""
    
    def __init__(self, cache_file: str = CACHE_FILE):
        self.cache_file = cache_file
        self.records: List[Dict] = []
        self.total_generated = 0
        self.total_pulled = 0
        self.load_cache()
    
    def load_cache(self):
        """加载缓存"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    self.records = data.get('records', [])
                    self.total_generated = data.get('total_generated', 0)
                    self.total_pulled = data.get('total_pulled', 0)
                logger.info(f"加载缓存: {len(self.records)} 条待拉取记录")
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
    
    def save_cache(self):
        """保存缓存"""
        try:
            data = {
                'updated_at': datetime.now().isoformat(),
                'total_generated': self.total_generated,
                'total_pulled': self.total_pulled,
                'records': self.records
            }
            temp_file = self.cache_file + ".tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            os.replace(temp_file, self.cache_file)
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    def add_records(self, records: List[Dict]):
        """添加新记录"""
        self.records.extend(records)
        self.total_generated += len(records)
        
        # 限制缓存大小
        if len(self.records) > MAX_CACHED_RECORDS:
            self.records = self.records[-MAX_CACHED_RECORDS:]
            logger.warning(f"缓存已满，保留最新的 {MAX_CACHED_RECORDS} 条")
    
    def get_records(self, count: int = 1000) -> List[Dict]:
        """获取记录"""
        if not self.records:
            return []
        
        result = self.records[:count]
        return result
    
    def confirm_pulled(self, count: int):
        """确认已拉取"""
        if count > 0:
            self.records = self.records[count:]
            self.total_pulled += count
            logger.info(f"确认拉取 {count} 条，剩余: {len(self.records)} 条")
            self.save_cache()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'cached_records': len(self.records),
            'total_generated': self.total_generated,
            'total_pulled': self.total_pulled,
            'cache_full': len(self.records) >= MAX_CACHED_RECORDS
        }


# 全局数据缓存
data_cache = DataCache()

# ============================================================
# 后台日志读取任务
# ============================================================

class BackgroundLogReader:
    """后台日志读取器"""
    
    def __init__(self, cache: DataCache):
        self.cache = cache
        self.log_reader = LogReader(LOG_DIR, LOG_FILE_PATTERN)
        self.ip_processor = IPProcessor(BOTNET_TYPE)
        self.running = False
        self.read_interval = 60
        self.processed_files = set()
        
        logger.info(f"初始化日志读取器:")
        logger.info(f"  - 日志目录: {LOG_DIR}")
        logger.info(f"  - 文件模式: {LOG_FILE_PATTERN}")
        logger.info(f"  - 僵尸网络: {BOTNET_TYPE}")
    
    async def run(self):
        """运行后台读取任务"""
        self.running = True
        logger.info("后台日志读取任务启动")
        
        while self.running:
            try:
                await self.read_logs()
                await asyncio.sleep(self.read_interval)
            except Exception as e:
                logger.error(f"读取日志异常: {e}", exc_info=True)
                await asyncio.sleep(10)
    
    async def read_logs(self):
        """读取日志文件"""
        try:
            log_files = await self.log_reader.get_available_log_files(hours_back=48)
            
            if not log_files:
                logger.debug("没有可读取的日志文件")
                return
            
            logger.debug(f"发现 {len(log_files)} 个可处理的日志文件")
            
            new_records = []
            files_read = 0
            
            log_files.sort(key=lambda x: x[0], reverse=True)
            
            for file_datetime, file_path in log_files:
                file_key = str(file_path)
                
                if file_key in self.processed_files:
                    continue
                
                logger.info(f"读取日志文件: {file_path.name}")
                
                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        line_count = 0
                        ip_count = 0
                        
                        async for line in f:
                            line_count += 1
                            line = line.strip()
                            
                            if not line:
                                continue
                            
                            ip_data = self.ip_processor.extract_ip_and_timestamp_from_line(line, file_path)
                            
                            if ip_data:
                                new_records.append(ip_data)
                                ip_count += 1
                            
                            if len(new_records) >= 5000:
                                break
                        
                        logger.info(f"  ✓ 文件处理完成: 读取{line_count}行，提取{ip_count}个IP")
                    
                    self.processed_files.add(file_key)
                    files_read += 1
                    
                    if files_read >= 10 or len(new_records) >= 5000:
                        break
                
                except Exception as e:
                    logger.error(f"读取文件 {file_path} 失败: {e}")
                    continue
            
            if new_records:
                self.cache.add_records(new_records)
                self.cache.save_cache()
                logger.info(f"✅ 新增 {len(new_records)} 条记录，当前缓存: {len(self.cache.records)} 条")
            
            # 清理已处理文件列表
            if len(self.processed_files) > 100:
                recent_files = sorted(log_files, key=lambda x: x[0], reverse=True)[:50]
                recent_file_keys = {str(f[1]) for f in recent_files}
                self.processed_files = self.processed_files & recent_file_keys
        
        except Exception as e:
            logger.error(f"读取日志失败: {e}", exc_info=True)
    
    def stop(self):
        """停止后台任务"""
        self.running = False


background_reader = None

# ============================================================
# HTTP接口
# ============================================================

def check_auth(request: web.Request) -> bool:
    """检查认证"""
    auth_header = request.headers.get('Authorization', '')
    
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        return token == API_KEY
    
    api_key = request.headers.get('X-API-Key', '')
    return api_key == API_KEY


async def handle_pull(request: web.Request) -> web.Response:
    """处理数据拉取请求"""
    if not check_auth(request):
        return web.json_response({'error': 'Unauthorized'}, status=401)
    
    try:
        params = request.rel_url.query
        # 支持 limit 和 count 参数（兼容性）
        limit = int(params.get('limit', params.get('count', 1000)))
        limit = min(limit, 5000)  # 限制最大拉取数量
        
        # 支持 confirm 参数（拉取后自动确认删除）
        auto_confirm = params.get('confirm', '').lower() == 'true'
        
        records = data_cache.get_records(limit)
        
        # 如果启用了自动确认，拉取后立即删除
        if auto_confirm and records:
            data_cache.confirm_pulled(len(records))
            logger.info(f"拉取请求: 返回并确认 {len(records)} 条记录")
        else:
            logger.info(f"拉取请求: 返回 {len(records)} 条记录（未确认）")
        
        response_data = {
            'success': True,
            'count': len(records),
            'data': records,  # 使用 'data' 字段（匹配本地拉取器）
            'records': records,  # 保留兼容性
            'stats': data_cache.get_stats()
        }
        
        return web.json_response(response_data)
    
    except Exception as e:
        logger.error(f"拉取失败: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def handle_confirm(request: web.Request) -> web.Response:
    """处理确认拉取请求"""
    if not check_auth(request):
        return web.json_response({'error': 'Unauthorized'}, status=401)
    
    try:
        data = await request.json()
        count = data.get('count', 0)
        data_cache.confirm_pulled(count)
        
        return web.json_response({
            'success': True,
            'message': f'已确认 {count} 条'
        })
    
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def handle_stats(request: web.Request) -> web.Response:
    """处理统计请求"""
    stats = data_cache.get_stats()
    return web.json_response(stats)


async def handle_health(request: web.Request) -> web.Response:
    """健康检查"""
    return web.json_response({'status': 'ok', 'service': 'c2-data-server'})


# ============================================================
# 应用启动和清理
# ============================================================

async def on_startup(app):
    """应用启动时执行"""
    global background_reader
    background_reader = BackgroundLogReader(data_cache)
    app['background_task'] = asyncio.create_task(background_reader.run())


async def on_cleanup(app):
    """应用清理时执行"""
    global background_reader
    if background_reader:
        background_reader.stop()
    
    if 'background_task' in app:
        app['background_task'].cancel()
        try:
            await app['background_task']
        except asyncio.CancelledError:
            pass


def create_app() -> web.Application:
    """创建应用"""
    app = web.Application()
    
    # 支持两种路径：/api/pull 和 /pull（兼容性）
    app.router.add_get('/api/pull', handle_pull)
    app.router.add_get('/pull', handle_pull)
    app.router.add_post('/api/confirm', handle_confirm)
    app.router.add_post('/confirm', handle_confirm)
    app.router.add_get('/api/stats', handle_stats)
    app.router.add_get('/stats', handle_stats)
    app.router.add_get('/health', handle_health)
    app.router.add_get('/api/health', handle_health)
    
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    
    return app


def main():
    """主函数"""
    logger.info("="*60)
    logger.info("C2端数据服务器启动（独立版本）")
    logger.info(f"HTTP服务: http://{HTTP_HOST}:{HTTP_PORT}")
    logger.info(f"日志目录: {LOG_DIR}")
    logger.info(f"僵尸网络类型: {BOTNET_TYPE}")
    logger.info("="*60)
    
    if API_KEY == "your-secret-api-key-here":
        logger.warning("⚠️  警告: 使用默认API Key，请设置环境变量 C2_API_KEY")
    
    app = create_app()
    web.run_app(app, host=HTTP_HOST, port=HTTP_PORT)


if __name__ == '__main__':
    main()
