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
            with open(config_file, 'r', encoding='utf-8') as f:
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
# 兼容旧配置
LOG_DIR = Path(CONFIG["botnet"]["log_dir"])
LOG_FILE_PATTERN = CONFIG["botnet"]["log_file_pattern"]
# 加载日志源配置（过滤掉注释项）
LOG_SOURCES = {k: v for k, v in CONFIG.get("log_sources", {}).items() if not k.startswith('_')}

# HTTP服务器配置
HTTP_HOST = os.environ.get("C2_HTTP_HOST", CONFIG.get("http_server", {}).get("host", "0.0.0.0"))
HTTP_PORT = int(os.environ.get("C2_HTTP_PORT", CONFIG.get("http_server", {}).get("port", 8888)))
# 优先从环境变量读取，其次从config.json，最后使用默认值
API_KEY = os.environ.get("C2_API_KEY", CONFIG.get("http_server", {}).get("api_key", "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"))

# 数据缓存配置（改用SQLite持久化）
CACHE_CONFIG = CONFIG.get("cache", {})
MAX_CACHED_RECORDS = CACHE_CONFIG.get("max_cached_records", 10000)
CACHE_DB_FILE = CACHE_CONFIG.get("db_file", "./c2_data_cache.db")
CACHE_RETENTION_DAYS = CACHE_CONFIG.get("retention_days", 7)


# 序列ID配置（用于断点续传）
SEQ_ID_START = 1  # 序列ID起始值

# IP解析正则
IP_REGEX = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')

class BackpressureController:
    """
    背压控制器 - 根据缓存量动态调整读取行为
    
    策略：
    1. 缓存 >= 高水位线 → 暂停读取（返回0）
    2. 缓存 <= 低水位线 → 全速读取（返回max_batch）
    3. 缓存在中间       → 线性缩放读取量
    """
    
    def __init__(self, config: Dict):
        """
        Args:
            config: 配置字典，包含：
                - max_cached_records: 最大缓存记录数（硬限制）
                - high_watermark: 高水位线（暂停读取阈值）
                - low_watermark: 低水位线（全速读取阈值）
                - read_batch_size: 基础读取批量大小
                - adaptive_read: 是否启用自适应读取（默认True）
        """
        self.max_cached = config.get('max_cached_records', 10000)
        self.high_watermark = config.get('high_watermark', int(self.max_cached * 0.8))
        self.low_watermark = config.get('low_watermark', int(self.max_cached * 0.2))
        self.read_batch_size = config.get('read_batch_size', 5000)
        self.adaptive_read = config.get('adaptive_read', True)
        
        # 统计信息
        self.total_paused = 0
        self.total_throttled = 0
        self.total_full_speed = 0
        
        logger.info(f"背压控制器初始化:")
        logger.info(f"  - 最大缓存: {self.max_cached} 条")
        logger.info(f"  - 高水位线: {self.high_watermark} 条 ({self.high_watermark/self.max_cached*100:.0f}%)")
        logger.info(f"  - 低水位线: {self.low_watermark} 条 ({self.low_watermark/self.max_cached*100:.0f}%)")
        logger.info(f"  - 基础读取量: {self.read_batch_size} 条")
        logger.info(f"  - 自适应模式: {'启用' if self.adaptive_read else '禁用'}")
    
    def calculate_read_size(self, current_cached: int) -> Tuple[int, str]:
        """
        计算本次应该读取的记录数
        
        Args:
            current_cached: 当前缓存的记录数
        
        Returns:
            (read_size, reason) - 读取数量和原因
        """
        if not self.adaptive_read:
            # 简单模式：超过最大值就不读
            if current_cached >= self.max_cached:
                self.total_paused += 1
                return 0, f"缓存已满({current_cached}/{self.max_cached})"
            else:
                self.total_full_speed += 1
                return self.read_batch_size, "正常读取"
        
        # 自适应模式
        if current_cached >= self.high_watermark:
            # 高水位：暂停读取
            self.total_paused += 1
            return 0, f"背压暂停({current_cached}/{self.high_watermark})"
        
        elif current_cached <= self.low_watermark:
            # 低水位：全速读取
            self.total_full_speed += 1
            return self.read_batch_size, f"全速读取({current_cached}/{self.low_watermark})"
        
        else:
            # 中间水位：线性缩放
            # 计算缩放因子：从低水位的100%到高水位的0%
            available_range = self.high_watermark - self.low_watermark
            current_offset = current_cached - self.low_watermark
            scale_factor = 1.0 - (current_offset / available_range)
            
            read_size = int(self.read_batch_size * scale_factor)
            read_size = max(100, read_size)  # 至少读100条
            
            self.total_throttled += 1
            return read_size, f"节流读取(缓存{current_cached}条,速度{scale_factor*100:.0f}%)"
    
    def should_skip_read(self, current_cached: int) -> Tuple[bool, str]:
        """
        判断是否应该跳过本次读取
        
        Returns:
            (should_skip, reason)
        """
        read_size, reason = self.calculate_read_size(current_cached)
        return read_size == 0, reason
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_decisions = self.total_paused + self.total_throttled + self.total_full_speed
        
        if total_decisions == 0:
            return {
                'total_decisions': 0,
                'paused_rate': '0%',
                'throttled_rate': '0%',
                'full_speed_rate': '0%'
            }
        
        return {
            'total_decisions': total_decisions,
            'paused_count': self.total_paused,
            'throttled_count': self.total_throttled,
            'full_speed_count': self.total_full_speed,
            'paused_rate': f"{self.total_paused/total_decisions*100:.1f}%",
            'throttled_rate': f"{self.total_throttled/total_decisions*100:.1f}%",
            'full_speed_rate': f"{self.total_full_speed/total_decisions*100:.1f}%"
        }
    
    def log_stats(self):
        """输出统计信息"""
        stats = self.get_stats()
        if stats['total_decisions'] > 0:
            logger.info(f"📊 背压统计: 暂停{stats['paused_rate']}, 节流{stats['throttled_rate']}, 全速{stats['full_speed_rate']}")

# ============================================================
# 通用工具类
# ============================================================

class LogReader:
    """日志文件读取器"""
    
    def __init__(self, log_dir: Path, file_pattern: str, line_parser_config: Dict = None):
        self.log_dir = log_dir
        self.file_pattern = file_pattern
        self.line_parser_config = line_parser_config or {}
        
        # 编译正则表达式（如果提供）
        if self.line_parser_config.get('type') == 'regex':
            pattern = self.line_parser_config.get('pattern')
            if pattern:
                self.regex_pattern = re.compile(pattern)
            else:
                self.regex_pattern = None
        else:
            self.regex_pattern = None
    
    async def get_available_log_files(self, days_back: int = None, include_current: bool = True) -> List[Tuple[datetime, Path]]:
        """
        获取可用的日志文件列表
        
        Args:
            days_back: 回溯天数，None表示无限回溯（读取所有历史文件）
            include_current: 是否包含当前的文件（正在写入的）
        """
        files = []
        now = datetime.now()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        
        # 确定最早时间
        if days_back is None:
            # 无限回溯：使用一个很早的时间
            earliest_time = datetime(2000, 1, 1)
            logger.info("无限回溯模式：将读取所有历史日志文件")
        else:
            earliest_time = now - timedelta(days=days_back)
            logger.info(f"限制回溯模式：回溯{days_back}天")
        
        if not self.log_dir.exists():
            logger.warning(f"日志目录不存在: {self.log_dir}")
            return files
        
        # 支持 {date} 格式（按天）- 推荐
        if '{date}' in self.file_pattern:
            pattern_parts = self.file_pattern.split('{date}')
            if len(pattern_parts) == 2:
                prefix, suffix = pattern_parts
                glob_pattern = f"{prefix}*{suffix}"
                
                for file_path in self.log_dir.glob(glob_pattern):
                    if file_path.is_file():
                        try:
                            filename = file_path.name
                            date_str = filename[len(prefix):-len(suffix)] if suffix else filename[len(prefix):]
                            
                            # 尝试多种日期格式
                            file_date = None
                            for date_format in ['%Y%m%d', '%Y-%m-%d']:
                                try:
                                    file_date = datetime.strptime(date_str, date_format)
                                    break
                                except ValueError:
                                    continue
                            
                            if file_date is None:
                                logger.debug(f"无法解析文件日期: {filename}, 日期字符串: {date_str}")
                                continue
                            
                            # 根据配置决定是否包含当天的文件
                            current_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
                            
                            if include_current:
                                # 实时模式：包括当天的文件
                                if earliest_time.date() <= file_date.date() <= now.date():
                                    files.append((file_date, file_path))
                                    logger.debug(f"添加日志文件: {filename}, 日期: {file_date.date()}")
                            else:
                                # 保守模式：只处理昨天及更早的文件
                                if earliest_time.date() <= file_date.date() < current_day.date():
                                    files.append((file_date, file_path))
                                    logger.debug(f"添加日志文件: {filename}, 日期: {file_date.date()}")
                        except Exception as e:
                            logger.warning(f"处理文件 {filename} 时出错: {e}")
                            continue
        
        # 支持 {datetime} 格式（按小时）- 兼容旧格式
        elif '{datetime}' in self.file_pattern:
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
                            
                            # 根据配置决定是否包含当前小时的文件
                            if include_current:
                                # 实时模式：包含当前小时的文件
                                if earliest_time <= file_datetime <= now:
                                    files.append((file_datetime, file_path))
                            else:
                                # 保守模式：只处理上一小时及更早的文件
                                current_hour = now.replace(minute=0, second=0, microsecond=0)
                                if earliest_time <= file_datetime < current_hour:
                                    files.append((file_datetime, file_path))
                        except ValueError as e:
                            logger.debug(f"无法解析文件日期: {filename}, 错误: {e}")
                            continue
        
        return sorted(files, key=lambda x: x[0])
    
    def parse_line(self, line: str) -> Optional[Tuple[str, datetime]]:
        """
        解析日志行，提取IP和时间戳
        
        Returns:
            (ip, timestamp) 或 None
        """
        if not self.regex_pattern:
            # 无正则配置，返回None
            return None
        
        try:
            match = self.regex_pattern.search(line)
            if not match:
                return None
            
            # 提取时间戳
            ts_group = self.line_parser_config.get('timestamp_group', 1)
            timestamp_str = match.group(ts_group)
            ts_format = self.line_parser_config.get('timestamp_format', '%Y-%m-%d %H:%M:%S')
            log_time = datetime.strptime(timestamp_str, ts_format)
            
            # 提取IP
            ip_group = self.line_parser_config.get('ip_group', 2)
            ip = match.group(ip_group)
            
            return (ip, log_time)
        except Exception as e:
            logger.debug(f"解析行失败: {e}, line: {line[:100]}")
            return None


class DatabaseReader:
    """数据库日志读取器（支持SQLite）"""
    
    def __init__(self, db_path: Path, db_config: Dict, field_mapping: Dict):
        self.db_path = db_path
        self.db_config = db_config
        self.field_mapping = field_mapping
        self.last_position = 0
        self.position_file = './db_positions.json'
        self._load_position()
        
    def _load_position(self):
        """加载上次读取位置"""
        try:
            if os.path.exists(self.position_file):
                with open(self.position_file, 'r') as f:
                    positions = json.load(f)
                    self.last_position = positions.get(str(self.db_path), 0)
                    logger.info(f"数据库 {self.db_path.name} 从位置 {self.last_position} 继续")
        except Exception as e:
            logger.warning(f"加载数据库位置失败: {e}")
    
    def _save_position(self):
        """保存当前读取位置"""
        try:
            positions = {}
            if os.path.exists(self.position_file):
                with open(self.position_file, 'r') as f:
                    positions = json.load(f)
            positions[str(self.db_path)] = self.last_position
            with open(self.position_file, 'w') as f:
                json.dump(positions, f)
        except Exception as e:
            logger.error(f"保存数据库位置失败: {e}")
    
    def read_records(self, limit: int = 1000) -> List[Dict]:
        """从数据库读取记录"""
        records = []
        try:
            if not self.db_path.exists():
                logger.warning(f"数据库文件不存在: {self.db_path}")
                return records
            
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 执行查询（使用配置的SQL）
            query = self.db_config.get('query')
            if not query:
                # 默认查询
                table = self.db_config.get('table', 'logs')
                position_field = self.db_config.get('position_field', 'id')
                ip_field = self.field_mapping['ip_field']
                ts_field = self.field_mapping['timestamp_field']
                query = f"SELECT {ip_field}, {ts_field}, {position_field} FROM {table} WHERE {position_field} > ? ORDER BY {position_field} ASC LIMIT ?"
            
            cursor.execute(query, (self.last_position, limit))
            rows = cursor.fetchall()
            
            ip_field = self.field_mapping['ip_field']
            ts_field = self.field_mapping['timestamp_field']
            ts_format = self.field_mapping.get('timestamp_format', '%Y-%m-%dT%H:%M:%S')
            position_field = self.db_config.get('position_field', 'id')
            
            for row in rows:
                try:
                    # 提取IP
                    ip = row[ip_field]
                    # 提取时间戳
                    timestamp_str = row[ts_field]
                    
                    # 解析时间戳
                    try:
                        log_time = datetime.strptime(timestamp_str, ts_format)
                    except:
                        # 如果解析失败，尝试ISO格式
                        log_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # 更新位置
                    if position_field in row.keys():
                        self.last_position = max(self.last_position, row[position_field])
                    
                    records.append({
                        'ip': ip,
                        'timestamp': log_time.isoformat(),
                        'date': log_time.strftime('%Y-%m-%d'),
                        'log_hour': log_time.strftime('%Y-%m-%d_%H'),
                    })
                except Exception as e:
                    logger.warning(f"解析数据库记录失败: {e}, row: {dict(row)}")
                    continue
            
            conn.close()
            
            if records:
                self._save_position()
                logger.info(f"从数据库读取 {len(records)} 条记录，位置: {self.last_position}")
            
        except Exception as e:
            logger.error(f"读取数据库失败: {e}", exc_info=True)
        
        return records


class IPProcessor:
    """IP地址处理器"""
    
    def __init__(self, botnet_type: str, log_type: str = "online", field_mapping: Dict = None):
        self.botnet_type = botnet_type
        self.log_type = log_type
    
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
                            'botnet_type': self.botnet_type,
                            'log_type': self.log_type
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
        self.last_seq_id = 0  # 初始化序列ID
        self.init_database()
        self.load_stats()
    
    def init_database(self):
        """初始化SQLite数据库"""
        try:
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            # 创建表结构（新增seq_id字段）
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    seq_id INTEGER NOT NULL UNIQUE,
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
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_seq_id ON cache(seq_id)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_pulled ON cache(pulled)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON cache(created_at)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)')
            
            # 创建统计表（新增last_seq_id字段）
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    total_generated INTEGER DEFAULT 0,
                    total_pulled INTEGER DEFAULT 0,
                    last_seq_id INTEGER DEFAULT 0,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 初始化统计
            self.conn.execute('INSERT OR IGNORE INTO stats (id, total_generated, total_pulled, last_seq_id) VALUES (1, 0, 0, 0)')
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
                # sqlite3.Row不支持.get()方法，使用try-except
                try:
                    self.last_seq_id = row['last_seq_id']
                except (KeyError, IndexError):
                    self.last_seq_id = 0
            
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
                    last_seq_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            ''', (self.total_generated, self.total_pulled, self.last_seq_id))
            self.conn.commit()
        except Exception as e:
            logger.error(f"保存统计数据失败: {e}")
    
    def add_records(self, records: List[Dict]):
        """添加新记录（使用批量插入，自动分配seq_id）"""
        try:
            added_count = 0
            duplicate_count = 0
            for record in records:
                try:
                    # 自动分配seq_id
                    self.last_seq_id += 1
                    seq_id = self.last_seq_id
                    
                    # 在数据中添加seq_id
                    record['seq_id'] = seq_id
                    
                    self.conn.execute('''
                        INSERT INTO cache (seq_id, ip, timestamp, data, pulled)
                        VALUES (?, ?, ?, ?, 0)
                    ''', (seq_id, record['ip'], record['timestamp'], json.dumps(record)))
                    added_count += 1
                except sqlite3.IntegrityError:
                    # 重复记录，跳过（但seq_id已增加，保证单调）
                    pass
                    duplicate_count += 1
            
            self.conn.commit()
            self.total_generated += added_count
            self.save_stats()

            # 输出统计信息
            if duplicate_count > 0:
                logger.info(f"数据写入: 新增 {added_count} 条，重复 {duplicate_count} 条")

            # 检查是否超过最大缓存，如果超过则警告
            cursor = self.conn.execute('SELECT COUNT(*) as count FROM cache WHERE pulled = 0')
            unpulled_count = cursor.fetchone()['count']
            if unpulled_count > MAX_CACHED_RECORDS:
                logger.warning(f"缓存已超限：{unpulled_count} 条，请尽快拉取")
            
        except Exception as e:
            logger.error(f"添加记录失败: {e}")
            self.conn.rollback()
    
    def get_records(self, count: int = 1000, since_seq: Optional[int] = None, since_ts: Optional[str] = None) -> List[Dict]:
        """
        获取未拉取的记录（支持序列ID + 时间戳双游标）
        
        Args:
            count: 最大返回数量
            since_seq: 只返回此序列ID之后的记录（优先使用）
            since_ts: 只返回此时间之后的记录（ISO格式，备用）
        
        Returns:
            记录列表
        """
        try:
            # 优先使用seq_id游标（最可靠）
            if since_seq is not None:
                cursor = self.conn.execute('''
                    SELECT id, seq_id, data FROM cache 
                    WHERE pulled = 0 AND seq_id > ?
                    ORDER BY seq_id ASC
                    LIMIT ?
                ''', (since_seq, count))
            # 其次使用时间戳游标（使用>=支持重叠窗口）
            elif since_ts:
                cursor = self.conn.execute('''
                    SELECT id, seq_id, data FROM cache 
                    WHERE pulled = 0 AND timestamp >= ?
                    ORDER BY seq_id ASC
                    LIMIT ?
                ''', (since_ts, count))
            # 默认从头开始拉取
            else:
                cursor = self.conn.execute('''
                    SELECT id, seq_id, data FROM cache 
                    WHERE pulled = 0
                    ORDER BY seq_id ASC
                    LIMIT ?
                ''', (count,))
            
            rows = cursor.fetchall()
            records = []
            for row in rows:
                data = json.loads(row['data'])
                data['_cache_id'] = row['id']  # 附加缓存ID用于确认
                data['_seq_id'] = row['seq_id']  # 附加序列ID
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

class BackgroundLogReader:
    
    def __init__(self, cache: DataCache):
        self.cache = cache
        self.running = False
        self.file_positions = {}  # {file_path: last_read_position}
        self.positions_file = './c2_file_positions.json'
        self.file_positions = self._load_file_positions()
        
        # 从配置读取参数
        processing_config = CONFIG.get('processing', {})
        self.read_interval = processing_config.get('read_interval', 60)
        self.max_files_per_read = processing_config.get('max_files_per_read', 10)
        
        # 初始化背压控制器
        self.backpressure = BackpressureController(CACHE_CONFIG)
        self.stats_counter = 0  # 用于定期输出统计
        
        # 加载回溯配置
        try:
            from config import C2_LOG_LOOKBACK_CONFIG
            self.lookback_config = C2_LOG_LOOKBACK_CONFIG
            logger.info(f"回溯配置: {C2_LOG_LOOKBACK_CONFIG['mode']}")
        except ImportError:
            self.lookback_config = {'mode': 'unlimited', 'max_days': 90}
            logger.warning("无法加载回溯配置，使用默认值（无限回溯）")
        
        # ========== 初始化日志源（支持多种日志类型） ==========
        self.log_sources = {}  # {log_type: (reader, processor, db_reader)}
        
        # 如果有新配置log_sources，优先使用
        if LOG_SOURCES:
            logger.info("=" * 60)
            logger.info("初始化多日志源模式:")
            for log_type, source_config in LOG_SOURCES.items():
                if not source_config.get('enabled', False):
                    logger.info(f"  ⊗ {log_type}: 已禁用")
                    continue
                
                storage_type = source_config.get('storage_type')
                log_type_name = source_config.get('log_type', log_type)
                
                try:
                    if storage_type == 'file':
                        # 文件日志源
                        path = Path(source_config['path'])
                        
                        # 判断path是文件还是目录
                        if path.is_file() or not path.exists():
                            # 单个文件 - 特殊处理
                            log_dir = path.parent
                            file_pattern = path.name
                        else:
                            # 目录
                            log_dir = path
                            file_pattern = source_config.get('file_pattern', '*.log')
                        
                        line_parser_config = source_config.get('field_mapping', {}).get('line_parser', {})
                        reader = LogReader(log_dir, file_pattern, line_parser_config)
                        processor = IPProcessor(BOTNET_TYPE, log_type_name)
                        self.log_sources[log_type_name] = ('file', reader, processor, None)
                        logger.info(f"  ✓ {log_type_name} (文件): {path}")
                    
                    elif storage_type == 'database':
                        # 数据库日志源
                        db_path = Path(source_config['path'])
                        db_config = source_config.get('db_config', {})
                        field_mapping = source_config.get('field_mapping', {})
                        
                        db_reader = DatabaseReader(db_path, db_config, field_mapping)
                        processor = IPProcessor(BOTNET_TYPE, log_type_name)
                        self.log_sources[log_type_name] = ('database', None, processor, db_reader)
                        logger.info(f"  ✓ {log_type_name} (数据库): {db_path}")
                    
                except Exception as e:
                    logger.error(f"  ✗ {log_type}: 初始化失败 - {e}")
            
            logger.info("=" * 60)
        else:
            # 兼容旧配置（单一日志源）
            logger.info("使用兼容模式（单一日志源）:")
            self.log_reader = LogReader(LOG_DIR, LOG_FILE_PATTERN)
            self.ip_processor = IPProcessor(BOTNET_TYPE, "online")
            logger.info(f"  - 日志目录: {LOG_DIR}")
            logger.info(f"  - 文件模式: {LOG_FILE_PATTERN}")
            logger.info(f"  - 僵尸网络: {BOTNET_TYPE}")
        
        logger.info(f"读取间隔: {self.read_interval}秒")
        logger.info(f"位置记录: {len(self.file_positions)} 个文件")
    
    def _load_file_positions(self) -> Dict[str, int]:
        """从文件加载已读取位置"""
        try:
            if os.path.exists(self.positions_file):
                with open(self.positions_file, 'r') as f:
                    positions = json.load(f)
                    logger.info(f"已加载 {len(positions)} 个文件的读取位置")
                    return positions
        except Exception as e:
            logger.warning(f"加载文件位置失败: {e}，将从头开始读取")
        return {}
    
    def _save_file_positions(self):
        """保存文件读取位置"""
        try:
            with open(self.positions_file, 'w') as f:
                json.dump(self.file_positions, f, indent=2)
            logger.debug(f"已保存 {len(self.file_positions)} 个文件的读取位置")
        except Exception as e:
            logger.error(f"保存文件位置失败: {e}")
    
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
    
    async def read_logs_multi_source(self, read_limit: int):
        """读取多个日志源（支持文件和数据库）"""
        all_records = []
        
        for log_type, (storage_type, file_reader, processor, db_reader) in self.log_sources.items():
            try:
                if storage_type == 'database':
                    # 从数据库读取
                    records = db_reader.read_records(limit=min(read_limit - len(all_records), 1000))
                    for record in records:
                        record['botnet_type'] = BOTNET_TYPE
                        record['log_type'] = log_type
                        # 标准化IP
                        ip = record.get('ip')
                        if ip:
                            normalized_ip = processor.normalize_ip(ip)
                            if normalized_ip:
                                record['ip'] = normalized_ip
                                all_records.append(record)
                    
                    logger.info(f"  [{log_type}] 数据库读取 {len(records)} 条")
                
                elif storage_type == 'file':
                    # 从文件读取
                    if file_reader.regex_pattern:
                        # 使用新的正则解析逻辑
                        records = await self._read_file_with_regex(file_reader, processor, log_type, read_limit - len(all_records))
                        all_records.extend(records)
                    else:
                        # 使用原有的IP提取逻辑
                        records = await self._read_file_legacy(file_reader, processor, log_type, read_limit - len(all_records))
                        all_records.extend(records)
                
                # 检查是否达到限制
                if len(all_records) >= read_limit:
                    break
            
            except Exception as e:
                logger.error(f"读取日志源 {log_type} 失败: {e}", exc_info=True)
        
        # 添加到缓存
        if all_records:
            self.cache.add_records(all_records)
            stats = self.cache.get_stats()
            logger.info(f"📦 提取 {len(all_records)} 条 → 当前缓存: {stats['cached_records']} 条")
            
            # 保存文件位置
            self._save_file_positions()
            
            # 每10次输出一次背压统计
            self.stats_counter += 1
            if self.stats_counter % 10 == 0:
                self.backpressure.log_stats()
        else:
            logger.debug("本次未提取到新数据")
    
    async def _read_file_with_regex(self, reader: LogReader, processor: IPProcessor, log_type: str, limit: int) -> List[Dict]:
        """使用正则表达式读取文件"""
        records = []
        
        # 获取该日志源的单个文件
        log_files = await reader.get_available_log_files(days_back=None, include_current=True)
        
        for file_datetime, file_path in log_files:
            if len(records) >= limit:
                break
            
            file_key = str(file_path)
            last_position = self.file_positions.get(file_key, 0)
            
            try:
                file_size = file_path.stat().st_size
                if last_position >= file_size and file_size > 0:
                    continue
                
                async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    await f.seek(last_position)
                    line_count = 0
                    
                    async for line in f:
                        line_count += 1
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 使用正则解析
                        result = reader.parse_line(line)
                        if result:
                            ip, log_time = result
                            normalized_ip = processor.normalize_ip(ip)
                            if normalized_ip:
                                records.append({
                                    'ip': normalized_ip,
                                    'timestamp': log_time.isoformat(),
                                    'date': log_time.strftime('%Y-%m-%d'),
                                    'log_hour': log_time.strftime('%Y-%m-%d_%H'),
                                    'botnet_type': BOTNET_TYPE,
                                    'log_type': log_type
                                })
                        
                        if len(records) >= limit:
                            break
                    
                    current_position = await f.tell()
                    self.file_positions[file_key] = current_position
                    
                    if line_count > 0:
                        logger.info(f"  [{log_type}] {file_path.name}: 读取{line_count}行, 提取{len(records)}个IP")
            
            except Exception as e:
                logger.error(f"读取文件 {file_path} 失败: {e}")
        
        return records
    
    async def _read_file_legacy(self, reader: LogReader, processor: IPProcessor, log_type: str, limit: int) -> List[Dict]:
        """使用传统IP正则读取文件"""
        # 兼容旧逻辑，暂时返回空
        return []
    
    async def read_logs(self):
        """读取日志文件（支持多日志源+无限回溯+增量读取+背压控制）"""
        try:
            # ========== 背压控制检查 ==========
            stats = self.cache.get_stats()
            current_cached = stats['cached_records']
            
            # 检查是否应该跳过读取
            should_skip, reason = self.backpressure.should_skip_read(current_cached)
            
            if should_skip:
                logger.info(f"⏸️  跳过本次读取: {reason}")
                return
            
            # 计算本次应该读取的数量
            read_limit, read_reason = self.backpressure.calculate_read_size(current_cached)
            logger.info(f"📖 开始读取: {read_reason}, 限制 {read_limit} 条")
            
            # 如果有多日志源配置，使用新逻辑
            if self.log_sources:
                await self.read_logs_multi_source(read_limit)
                return

            # 确定回溯天数（兼容旧配置）
            if self.lookback_config['mode'] == 'unlimited':
                days_back = None  # 无限回溯
            else:
                days_back = self.lookback_config['max_days']
            
            # 获取可用的日志文件（按配置回溯）
            log_files = await self.log_reader.get_available_log_files(
                days_back=days_back,
                include_current=True
            )
            
            if not log_files:
                logger.debug("没有可读取的日志文件")
                return
            
            logger.debug(f"发现 {len(log_files)} 个可处理的日志文件")
            
            new_records = []
            files_read = 0
            
            # 按时间排序（从旧到新，确保顺序读取）
            log_files.sort(key=lambda x: x[0])
            
            for file_datetime, file_path in log_files:
                file_key = str(file_path)
                
                # 获取上次读取的位置
                last_position = self.file_positions.get(file_key, 0)
                
                logger.info(f"读取日志文件: {file_path.name} (从位置 {last_position} 继续)")
                
                try:
                    file_size = file_path.stat().st_size
                    
                    # 检查文件是否已读完
                    if last_position >= file_size and file_size > 0:
                        logger.debug(f"  文件已读完，跳过: {file_path.name}")
                        files_read += 1
                        continue

                    async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        # 跳到上次读取的位置
                        await f.seek(last_position)
                        
                        line_count = 0
                        ip_count = 0
                        file_exhausted = False  # 标记文件是否读完

                        async for line in f:
                            line_count += 1
                            line = line.strip()
                            
                            if not line:
                                continue
                            
                            ip_data = self.ip_processor.extract_ip_and_timestamp_from_line(line, file_path)
                            
                            if ip_data:
                                new_records.append(ip_data)
                                ip_count += 1
                            # 限制单次读取量，避免内存占用过多
                            if len(new_records) >= 5000:
                                break
                            # 使用背压控制器计算的限制量
                            if len(new_records) >= read_limit:
                                logger.debug(f"  达到读取限制({read_limit}条)，中断当前文件")
                                break
                        else:
                            # 正常遍历结束（没有break），说明文件读完了
                            file_exhausted = True
                        
                        # 保存当前读取位置
                        current_position = await f.tell()
                        self.file_positions[file_key] = current_position
                        
                        if line_count > 0:
                            logger.info(f"  文件处理: 新读{line_count}行，提取{ip_count}个IP，位置:{last_position}→{current_position}")
                            status = "读完" if file_exhausted else "未完"
                            logger.info(f"  文件处理: 新读{line_count}行，提取{ip_count}个IP，位置:{last_position}→{current_position} [{status}]")
                        else:
                            logger.debug(f"  文件无新内容: {file_path.name}")
                    
                    files_read += 1

                    # 达到读取限制时停止
                    if len(new_records) >= read_limit:
                        logger.info(f"达到读取限制: 已读{files_read}个文件，提取{len(new_records)}条")
                        break
                    
                    # 达到文件数限制时停止
                    if files_read >= self.max_files_per_read:
                        logger.info(f"达到文件数限制: 已读{files_read}个文件")
                        break
                
                except Exception as e:
                    logger.error(f"读取文件 {file_path} 失败: {e}")
                    continue
            
            if new_records:
                self.cache.add_records(new_records)
                stats = self.cache.get_stats()
                logger.info(f"新增 {len(new_records)} 条记录，当前缓存: {stats['cached_records']} 条")
                new_stats = self.cache.get_stats()
                logger.info(f"📦 提取 {len(new_records)} 条 → 当前缓存: {new_stats['cached_records']} 条")
                
                # 保存文件位置
                self._save_file_positions()
                
                # 每10次输出一次背压统计
                self.stats_counter += 1
                if self.stats_counter % 10 == 0:
                    self.backpressure.log_stats()
            else:
                logger.debug("本次未提取到新数据")
            
            # 清理过期的文件位置记录（保留最近30天的）
            if len(self.file_positions) > 100:
                recent_file_keys = {str(f[1]) for f in log_files[-100:]}
                self.file_positions = {k: v for k, v in self.file_positions.items() if k in recent_file_keys}
                self._save_file_positions()
        
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
    - since_seq: 只拉取此序列ID之后的数据（优先使用，最可靠）
    - since_ts: 只拉取此时间之后的数据（备用，支持重叠窗口）
    - since: 兼容旧版本，等同于since_ts
    - confirm: 是否自动确认删除（默认false，不建议使用true）
    """
    if not check_auth(request):
        return web.json_response({'error': 'Unauthorized'}, status=401)
    
    try:
        params = request.rel_url.query
        
        # 支持 limit 和 count 参数（兼容性）
        limit = int(params.get('limit', params.get('count', 1000)))
        limit = min(limit, 5000)  # 限制最大拉取数量
        
        # 支持序列ID游标（优先）
        since_seq = params.get('since_seq', None)
        if since_seq is not None:
            since_seq = int(since_seq)
        
        # 支持时间戳游标（备用）
        since_ts = params.get('since_ts', params.get('since', None))
        
        # 支持 confirm 参数（默认false，推荐使用两阶段确认）
        auto_confirm = params.get('confirm', 'false').lower() == 'true'
        
        # 拉取记录
        records = data_cache.get_records(limit, since_seq, since_ts)
        
        # 如果启用了自动确认（不推荐）
        if auto_confirm and records:
            data_cache.confirm_pulled(len(records))
            logger.info(f"拉取请求: 返回并确认 {len(records)} 条记录（自动确认模式）")
        else:
            logger.info(f"拉取请求: 返回 {len(records)} 条记录（未确认，等待服务器确认）")
        
        # 获取当前批次最大seq_id（用于断点续传）
        max_seq_id = max([r.get('_seq_id', 0) for r in records]) if records else 0
        
        # 获取缓存中的全局最大seq_id（用于检测C2端重置）
        cursor = data_cache.conn.execute('SELECT MAX(seq_id) as global_max_seq FROM cache')
        row = cursor.fetchone()
        global_max_seq_id = row['global_max_seq'] if row and row['global_max_seq'] is not None else 0
        
        response_data = {
            'success': True,
            'count': len(records),
            'data': records,  # 使用 'data' 字段（匹配本地拉取器）
            'records': records,  # 保留兼容性
            'max_seq_id': max_seq_id,  # 当前批次最大序列ID
            'global_max_seq_id': global_max_seq_id,  # 缓存中的全局最大序列ID（用于检测重置）
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
    """处理统计请求（包含背压统计）"""
    stats = data_cache.get_stats()
    
    # 添加背压统计
    if background_reader and background_reader.backpressure:
        stats['backpressure_stats'] = background_reader.backpressure.get_stats()
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
