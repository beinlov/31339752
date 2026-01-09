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
import sqlite3
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
HTTP_HOST = os.environ.get("C2_HTTP_HOST", CONFIG.get("http_server", {}).get("host", "0.0.0.0"))
HTTP_PORT = int(os.environ.get("C2_HTTP_PORT", CONFIG.get("http_server", {}).get("port", 8888)))
# 优先从环境变量读取，其次从config.json，最后使用默认值
API_KEY = os.environ.get("C2_API_KEY", CONFIG.get("http_server", {}).get("api_key", "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"))

# 数据缓存配置（改用SQLite持久化）
MAX_CACHED_RECORDS = 10000
CACHE_DB_FILE = "/tmp/c2_data_cache.db"  # SQLite数据库文件
CACHE_RETENTION_DAYS = 7  # 已拉取数据保留7天后自动清理

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
    """数据缓存管理器 - 使用SQLite持久化存储"""
    
    def __init__(self, db_file: str = CACHE_DB_FILE):
        self.db_file = db_file
        self.conn = None
        self.total_generated = 0
        self.total_pulled = 0
        self.init_database()
        self.load_stats()
    
    def init_database(self):
        """初始化SQLite数据库"""
        try:
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            # 创建表结构
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data TEXT NOT NULL,
                    pulled INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    pulled_at TEXT,
                    UNIQUE(ip, timestamp)
                )
            ''')
            
            # 创建索引以提高查询性能
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_pulled ON cache(pulled)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON cache(created_at)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)')
            
            # 创建统计表
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    total_generated INTEGER DEFAULT 0,
                    total_pulled INTEGER DEFAULT 0,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 初始化统计
            self.conn.execute('INSERT OR IGNORE INTO stats (id, total_generated, total_pulled) VALUES (1, 0, 0)')
            self.conn.commit()
            
            logger.info(f"SQLite数据库初始化成功: {self.db_file}")
        except Exception as e:
            logger.error(f"SQLite数据库初始化失败: {e}")
            raise
    
    def load_stats(self):
        """加载统计数据"""
        try:
            cursor = self.conn.execute('SELECT * FROM stats WHERE id = 1')
            row = cursor.fetchone()
            if row:
                self.total_generated = row['total_generated']
                self.total_pulled = row['total_pulled']
            
            # 统计未拉取的记录数
            cursor = self.conn.execute('SELECT COUNT(*) as count FROM cache WHERE pulled = 0')
            unpulled_count = cursor.fetchone()['count']
            
            logger.info(f"加载缓存: {unpulled_count} 条未拉取记录")
        except Exception as e:
            logger.error(f"加载统计数据失败: {e}")
    
    def save_stats(self):
        """保存统计数据"""
        try:
            self.conn.execute('''
                UPDATE stats SET 
                    total_generated = ?,
                    total_pulled = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            ''', (self.total_generated, self.total_pulled))
            self.conn.commit()
        except Exception as e:
            logger.error(f"保存统计数据失败: {e}")
    
    def add_records(self, records: List[Dict]):
        """添加新记录（使用批量插入）"""
        try:
            added_count = 0
            for record in records:
                try:
                    self.conn.execute('''
                        INSERT INTO cache (ip, timestamp, data, pulled)
                        VALUES (?, ?, ?, 0)
                    ''', (record['ip'], record['timestamp'], json.dumps(record)))
                    added_count += 1
                except sqlite3.IntegrityError:
                    # 重复记录，跳过
                    pass
            
            self.conn.commit()
            self.total_generated += added_count
            self.save_stats()
            
            # 检查是否超过最大缓存，如果超过则警告
            cursor = self.conn.execute('SELECT COUNT(*) as count FROM cache WHERE pulled = 0')
            unpulled_count = cursor.fetchone()['count']
            if unpulled_count > MAX_CACHED_RECORDS:
                logger.warning(f"缓存已超限：{unpulled_count} 条，请尽快拉取")
            
        except Exception as e:
            logger.error(f"添加记录失败: {e}")
            self.conn.rollback()
    
    def get_records(self, count: int = 1000, since: Optional[str] = None) -> List[Dict]:
        """
        获取未拉取的记录
        
        Args:
            count: 最大返回数量
            since: 只返回此时间之后的记录（ISO格式）
        
        Returns:
            记录列表
        """
        try:
            if since:
                cursor = self.conn.execute('''
                    SELECT id, data FROM cache 
                    WHERE pulled = 0 AND timestamp > ?
                    ORDER BY created_at ASC
                    LIMIT ?
                ''', (since, count))
            else:
                cursor = self.conn.execute('''
                    SELECT id, data FROM cache 
                    WHERE pulled = 0
                    ORDER BY created_at ASC
                    LIMIT ?
                ''', (count,))
            
            rows = cursor.fetchall()
            records = []
            for row in rows:
                data = json.loads(row['data'])
                data['_cache_id'] = row['id']  # 附加缓存ID用于确认
                records.append(data)
            
            return records
        except Exception as e:
            logger.error(f"获取记录失败: {e}")
            return []
    
    def confirm_pulled(self, count: int):
        """
        确认已拉取（标记为已拉取，不立即删除）
        
        Args:
            count: 确认的记录数量
        """
        try:
            if count > 0:
                # 标记为已拉取
                self.conn.execute('''
                    UPDATE cache SET 
                        pulled = 1,
                        pulled_at = CURRENT_TIMESTAMP
                    WHERE id IN (
                        SELECT id FROM cache WHERE pulled = 0 
                        ORDER BY created_at ASC 
                        LIMIT ?
                    )
                ''', (count,))
                self.conn.commit()
                
                self.total_pulled += count
                self.save_stats()
                
                # 统计剩余未拉取记录
                cursor = self.conn.execute('SELECT COUNT(*) as count FROM cache WHERE pulled = 0')
                unpulled_count = cursor.fetchone()['count']
                
                logger.info(f"确认拉取 {count} 条，剩余: {unpulled_count} 条")
                
                # 清理旧的已拉取记录（保留7天）
                self.cleanup_old_records()
        except Exception as e:
            logger.error(f"确认拉取失败: {e}")
            self.conn.rollback()
    
    def cleanup_old_records(self):
        """清理过期的已拉取记录"""
        try:
            cursor = self.conn.execute('''
                DELETE FROM cache 
                WHERE pulled = 1 
                AND pulled_at < datetime('now', '-' || ? || ' days')
            ''', (CACHE_RETENTION_DAYS,))
            
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                self.conn.commit()
                logger.info(f"清理了 {deleted_count} 条过期记录")
        except Exception as e:
            logger.error(f"清理过期记录失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        try:
            cursor = self.conn.execute('SELECT COUNT(*) as count FROM cache WHERE pulled = 0')
            cached_records = cursor.fetchone()['count']
            
            cursor = self.conn.execute('SELECT COUNT(*) as count FROM cache WHERE pulled = 1')
            pulled_records = cursor.fetchone()['count']
            
            return {
                'cached_records': cached_records,
                'pulled_records': pulled_records,
                'total_generated': self.total_generated,
                'total_pulled': self.total_pulled,
                'cache_full': cached_records >= MAX_CACHED_RECORDS
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'cached_records': 0,
                'pulled_records': 0,
                'total_generated': self.total_generated,
                'total_pulled': self.total_pulled,
                'cache_full': False
            }
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")


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
                        
                        logger.info(f"  文件处理完成: 读取{line_count}行，提取{ip_count}个IP")
                    
                    self.processed_files.add(file_key)
                    files_read += 1
                    
                    if files_read >= 10 or len(new_records) >= 5000:
                        break
                
                except Exception as e:
                    logger.error(f"读取文件 {file_path} 失败: {e}")
                    continue
            
            if new_records:
                self.cache.add_records(new_records)
                # SQLite 自动持久化，无需手动保存
                stats = self.cache.get_stats()
                logger.info(f"新增 {len(new_records)} 条记录，当前缓存: {stats['cached_records']} 条")
            
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
        result = token == API_KEY
        if not result:
            logger.warning(f"认证失败 (Bearer): 收到 {token[:6]}***, 期望 {API_KEY[:6]}***")
        return result
    
    api_key = request.headers.get('X-API-Key', '')
    result = api_key == API_KEY
    if not result:
        logger.warning(f"认证失败 (X-API-Key): 收到 '{api_key[:6] if api_key else '(空)'}***', 期望 '{API_KEY[:6]}***'")
        logger.warning(f"收到Key长度: {len(api_key)}, 期望长度: {len(API_KEY)}")
    return result


async def handle_pull(request: web.Request) -> web.Response:
    """
    处理数据拉取请求
    
    支持参数：
    - limit: 最大拉取数量（默认1000）
    - since: 只拉取此时间之后的数据（断点续传）
    - confirm: 是否自动确认删除（默认false，不建议使用true）
    """
    if not check_auth(request):
        return web.json_response({'error': 'Unauthorized'}, status=401)
    
    try:
        params = request.rel_url.query
        
        # 支持 limit 和 count 参数（兼容性）
        limit = int(params.get('limit', params.get('count', 1000)))
        limit = min(limit, 5000)  # 限制最大拉取数量
        
        # 支持 since 参数（断点续传）
        since = params.get('since', None)
        
        # 支持 confirm 参数（默认false，推荐使用两阶段确认）
        auto_confirm = params.get('confirm', 'false').lower() == 'true'
        
        # 拉取记录
        records = data_cache.get_records(limit, since)
        
        # 如果启用了自动确认（不推荐）
        if auto_confirm and records:
            data_cache.confirm_pulled(len(records))
            logger.info(f"拉取请求: 返回并确认 {len(records)} 条记录（自动确认模式）")
        else:
            logger.info(f"拉取请求: 返回 {len(records)} 条记录（未确认，等待服务器确认）")
        
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
    logger.info(f"API Key长度: {len(API_KEY)}, 前6位: {API_KEY[:6]}***")
    logger.info("="*60)
    
    if API_KEY == "your-secret-api-key-here":
        logger.warning("⚠️  警告: 使用默认API Key，请设置环境变量 C2_API_KEY")
    elif API_KEY == "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4":
        logger.info("API Key已正确配置")
    
    app = create_app()
    web.run_app(app, host=HTTP_HOST, port=HTTP_PORT)


if __name__ == '__main__':
    main()
