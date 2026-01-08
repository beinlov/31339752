"""
数据库写入器模块
负责将处理后的数据批量写入数据库
包含连接池、线程安全、高性能批量写入等优化功能
"""
import pymysql
import asyncio
import logging
from datetime import datetime
from typing import Dict, List
from collections import defaultdict, deque
from pymysql.cursors import DictCursor
import threading
import queue
import time

# 可选的性能监控依赖
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

logger = logging.getLogger(__name__)


class ConnectionPool:
    """简单的数据库连接池"""

    def __init__(self, db_config: Dict, pool_size: int = 5):
        self.db_config = db_config
        self.pool_size = pool_size
        self.pool = queue.Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        self._create_connections()

    def _create_connections(self):
        """创建连接池"""
        for _ in range(self.pool_size):
            try:
                conn = pymysql.connect(**self.db_config)
                self.pool.put(conn)
            except Exception as e:
                logger.error(f"Failed to create database connection: {e}")

    def get_connection(self):
        """获取连接"""
        try:
            # 尝试获取连接，超时5秒
            conn = self.pool.get(timeout=5)
            # 检查连接是否有效
            if not self._is_connection_valid(conn):
                conn = pymysql.connect(**self.db_config)
            return conn
        except queue.Empty:
            # 池中没有可用连接，创建新连接
            return pymysql.connect(**self.db_config)

    def return_connection(self, conn):
        """归还连接"""
        try:
            if self._is_connection_valid(conn):
                self.pool.put_nowait(conn)
            else:
                conn.close()
        except queue.Full:
            # 池已满，关闭连接
            conn.close()

    def _is_connection_valid(self, conn):
        """检查连接是否有效"""
        try:
            conn.ping(reconnect=False)
            return True
        except:
            return False

    def close_all(self):
        """关闭所有连接"""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except queue.Empty:
                break


class BotnetDBWriter:
    """僵尸网络数据库写入器（包含所有优化功能）"""

    def __init__(self, botnet_type: str, db_config: Dict, batch_size: int = 500, use_connection_pool: bool = True, enable_monitoring: bool = True):
        """
        初始化数据库写入器

        Args:
            botnet_type: 僵尸网络类型
            db_config: 数据库配置
            batch_size: 批量写入大小
            use_connection_pool: 是否使用连接池（默认True）
            enable_monitoring: 是否启用性能监控（默认True）
        """
        self.botnet_type = botnet_type
        self.db_config = db_config
        self.batch_size = batch_size
        self.use_connection_pool = use_connection_pool
        self.enable_monitoring = enable_monitoring

        # 连接池（如果启用）
        if use_connection_pool:
            self.connection_pool = ConnectionPool(db_config, pool_size=3)
        else:
            self.connection_pool = None

        # 缓冲区
        self.node_buffer = []
        self.buffer_lock = threading.Lock()

        # 统计信息
        self.total_written = 0
        self.last_flush_time = None
        self.table_created = False
        
        # 去重相关
        self.processed_records = set()
        self.duplicate_count = 0
        self.processed_count = 0  # 成功处理的数量
        self.received_count = 0   # 接收的总数量
        self.source_ip = None      # 来源IP
        self.batch_start_time = None  # 批次开始时间
        self.global_stats = defaultdict(int)  # 全球统计
        self.china_stats = defaultdict(int)   # 中国统计

        # 表名
        self.node_table = f"botnet_nodes_{botnet_type}"
        self.communication_table = f"botnet_communications_{botnet_type}"  # 新增通信记录表

        # 表创建状态缓存
        self.table_created = False
        self.china_table = f"china_botnet_{botnet_type}"
        self.global_table = f"global_botnet_{botnet_type}"

        # 性能监控（如果启用）
        if enable_monitoring:
            self.flush_times = deque(maxlen=100)  # 最近100次flush时间
            self.db_connection_times = deque(maxlen=100)  # 数据库连接时间
            self.insert_times = deque(maxlen=100)  # 插入时间
            self.cpu_usage = deque(maxlen=60)  # 最近60次CPU使用率
            self.memory_usage = deque(maxlen=60)  # 内存使用率
            self._start_system_monitoring()
        else:
            self.flush_times = None
            self.db_connection_times = None
            self.insert_times = None
            self.cpu_usage = None
            self.memory_usage = None
    
    def start_batch(self, source_ip: str, total_count: int):
        """
        开始一个新的批次处理
        
        Args:
            source_ip: 来源IP地址
            total_count: 总数据量
        """
        self.source_ip = source_ip
        self.batch_start_time = datetime.now()
        logger.info(
            f"[{self.botnet_type}] 收到来自 {source_ip} 的IP数据上传, "
            f"类型: {self.botnet_type}, 数量: {total_count}"
        )
        
    def add_node(self, log_data: Dict, ip_info: Dict) -> bool:
        """
        添加节点数据到缓冲区（不再去重，记录所有通信）
        
        Args:
            log_data: 日志数据
            ip_info: IP信息
            
        Returns:
            bool: True=成功添加, False=添加失败
        """
        try:
            self.received_count += 1
            
            # 构建节点数据（移除去重逻辑）
            node_data = {
                'ip': log_data['ip'],
                'timestamp': log_data['timestamp'],
                'event_type': log_data.get('event_type', ''),
                'country': ip_info.get('country', ''),
                'province': ip_info.get('province', ''),
                'city': ip_info.get('city', ''),
                'longitude': ip_info.get('longitude', 0),
                'latitude': ip_info.get('latitude', 0),
                'continent': ip_info.get('continent', ''),
                'isp': ip_info.get('isp', ''),
                'asn': ip_info.get('asn', ''),
                'status': 'active',
                'is_china': ip_info.get('is_china', False)
            }
            
            # 线程安全地添加到缓冲区
            with self.buffer_lock:
                self.node_buffer.append(node_data)
            
            self.processed_count += 1
            
            # 更新统计
            country = ip_info.get('country', '未知')
            self.global_stats[country] += 1
            
            if country == '中国':
                province = ip_info.get('province', '未知').rstrip('省')
                city = ip_info.get('city', '未知').rstrip('市')
                # 直辖市特殊处理
                if city in ['北京', '天津', '上海', '重庆']:
                    city = city  # 保持原样
                self.china_stats[(province, city)] += 1
            
            return True
                
        except Exception as e:
            logger.error(f"[{self.botnet_type}] Error adding node: {e}")
            return False
    
    def _start_system_monitoring(self):
        """启动系统资源监控"""
        if not self.enable_monitoring or not PSUTIL_AVAILABLE:
            if not PSUTIL_AVAILABLE:
                logger.warning(f"[{self.botnet_type}] psutil not available, system monitoring disabled")
            return
            
        def monitor_system():
            while self.enable_monitoring:
                try:
                    # 记录CPU和内存使用率
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory_percent = psutil.virtual_memory().percent
                    
                    self.cpu_usage.append(cpu_percent)
                    self.memory_usage.append(memory_percent)
                    
                    time.sleep(30)  # 每30秒监控一次
                except Exception as e:
                    logger.error(f"[{self.botnet_type}] System monitoring error: {e}")
                    time.sleep(30)
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    def _record_performance(self, operation: str, duration: float):
        """记录性能指标"""
        if not self.enable_monitoring:
            return
            
        if operation == 'flush' and self.flush_times is not None:
            self.flush_times.append(duration)
        elif operation == 'db_connection' and self.db_connection_times is not None:
            self.db_connection_times.append(duration)
        elif operation == 'insert' and self.insert_times is not None:
            self.insert_times.append(duration)
            
    async def flush(self, force: bool = False):
        """
        刷新缓冲区，写入数据库（优化版本）
        
        Args:
            force: 是否强制刷新（忽略batch_size检查）
        """
        flush_start_time = time.time()
        
        # 获取当前缓冲区数据
        with self.buffer_lock:
            if not force and len(self.node_buffer) < self.batch_size:
                return
                
            if not self.node_buffer:
                return
                
            # 复制缓冲区数据并清空
            nodes_to_write = self.node_buffer.copy()
            self.node_buffer.clear()
        
        conn = None
        try:
            # 从连接池获取连接或创建新连接
            conn_start_time = time.time()
            if self.use_connection_pool:
                conn = self.connection_pool.get_connection()
            else:
                conn = pymysql.connect(**self.db_config)
            conn_duration = time.time() - conn_start_time
            self._record_performance('db_connection', conn_duration)
            
            cursor = conn.cursor()
            
            # 确保表存在（只在第一次时检查）
            if not self.table_created:
                await self._ensure_tables_exist(cursor)
                self.table_created = True
            
            # 批量插入节点数据
            insert_start_time = time.time()
            await self._insert_nodes_batch(cursor, nodes_to_write)
            insert_duration = time.time() - insert_start_time
            self._record_performance('insert', insert_duration)
            
            # 提交事务
            conn.commit()
            
            self.total_written += len(nodes_to_write)
            
            # 输出详细的批量写入日志
            logger.info(
                f"[{self.botnet_type}] 批量写入 {len(nodes_to_write)} 条数据到数据库. "
                f"累计写入: {self.total_written}"
            )
            
            # 如果这是批次的最后一次flush（强制flush），输出完整统计
            if force and self.batch_start_time:
                duration = (datetime.now() - self.batch_start_time).total_seconds()
                logger.info(
                    f"[{self.botnet_type}] IP数据处理完成: "
                    f"接收 {self.received_count}, "
                    f"成功处理 {self.processed_count}, "
                    f"重复跳过 {self.duplicate_count}, "
                    f"写入数据库 {self.total_written}, "
                    f"耗时 {duration:.2f}s"
                )
            
            self.last_flush_time = datetime.now()
            
            # 记录flush性能
            flush_duration = time.time() - flush_start_time
            self._record_performance('flush', flush_duration)
            
        except Exception as e:
            logger.error(f"[{self.botnet_type}] Error flushing to database: {e}")
            if conn:
                conn.rollback()
            # 如果写入失败，将数据重新放回缓冲区
            with self.buffer_lock:
                self.node_buffer.extend(nodes_to_write)
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn:
                if self.use_connection_pool:
                    self.connection_pool.return_connection(conn)
                else:
                    conn.close()
                
    async def update_statistics(self):
        """更新统计表（带重试机制）"""
        if not self.china_stats and not self.global_stats:
            return
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            conn = None
            try:
                if self.use_connection_pool:
                    conn = self.connection_pool.get_connection()
                else:
                    conn = pymysql.connect(**self.db_config)
                cursor = conn.cursor()
                
                # 更新中国统计表
                if self.china_stats:
                    await self._update_china_stats(cursor)
                    
                # 更新全球统计表
                if self.global_stats:
                    await self._update_global_stats(cursor)
                    
                conn.commit()
                logger.info(f"[{self.botnet_type}] Statistics updated")
                
                # 清空统计缓冲
                self.china_stats.clear()
                self.global_stats.clear()
                break
                
            except pymysql.err.OperationalError as e:
                error_code = e.args[0] if e.args else 0
                if error_code in (2006, 2013) and attempt < max_retries - 1:
                    logger.warning(
                        f"[{self.botnet_type}] MySQL connection error in update_statistics "
                        f"(attempt {attempt + 1}/{max_retries}): {e}. Retrying..."
                    )
                    if conn:
                        try:
                            if self.use_connection_pool:
                                self.connection_pool.return_connection(conn)
                            else:
                                conn.close()
                        except:
                            pass
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    logger.error(f"[{self.botnet_type}] Error updating statistics: {e}")
                    if conn:
                        try:
                            conn.rollback()
                        except:
                            pass
                    break
                    
            except Exception as e:
                logger.error(f"[{self.botnet_type}] Error updating statistics: {e}")
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                break
                
            finally:
                if 'cursor' in locals():
                    try:
                        cursor.close()
                    except:
                        pass
                if conn:
                    try:
                        if self.use_connection_pool:
                            self.connection_pool.return_connection(conn)
                        else:
                            conn.close()
                    except:
                        pass
                
    async def _ensure_tables_exist(self, cursor):
        """确保数据表存在（双表设计：节点表+通信记录表）"""
        try:
            # 1. 创建节点表（汇总信息）
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.node_table} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    ip VARCHAR(15) NOT NULL COMMENT '节点IP地址',
                    longitude FLOAT COMMENT '经度',
                    latitude FLOAT COMMENT '纬度',
                    country VARCHAR(50) COMMENT '国家',
                    province VARCHAR(50) COMMENT '省份',
                    city VARCHAR(50) COMMENT '城市',
                    continent VARCHAR(50) COMMENT '洲',
                    isp VARCHAR(255) COMMENT 'ISP运营商',
                    asn VARCHAR(50) COMMENT 'AS号',
                    status ENUM('active', 'inactive') DEFAULT 'active' COMMENT '节点状态',
                    first_seen TIMESTAMP NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
                    last_seen TIMESTAMP NULL DEFAULT NULL COMMENT '最后通信时间（日志时间）',
                    communication_count INT DEFAULT 0 COMMENT '通信次数',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
                    is_china BOOLEAN DEFAULT FALSE COMMENT '是否为中国节点',
                    INDEX idx_ip (ip),
                    INDEX idx_location (country, province, city),
                    INDEX idx_status (status),
                    INDEX idx_first_seen (first_seen),
                    INDEX idx_last_seen (last_seen),
                    INDEX idx_communication_count (communication_count),
                    INDEX idx_is_china (is_china),
                    UNIQUE KEY idx_unique_ip (ip)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
                COMMENT='僵尸网络节点基本信息表（汇总）'
            """)
            
            # 2. 创建通信记录表（详细历史）
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.communication_table} (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    node_id INT NOT NULL COMMENT '关联的节点ID',
                    ip VARCHAR(15) NOT NULL COMMENT '节点IP',
                    communication_time TIMESTAMP NOT NULL COMMENT '通信时间（日志时间）',
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '接收时间',
                    longitude FLOAT COMMENT '经度',
                    latitude FLOAT COMMENT '纬度',
                    country VARCHAR(50) COMMENT '国家',
                    province VARCHAR(50) COMMENT '省份',
                    city VARCHAR(50) COMMENT '城市',
                    continent VARCHAR(50) COMMENT '洲',
                    isp VARCHAR(255) COMMENT 'ISP运营商',
                    asn VARCHAR(50) COMMENT 'AS号',
                    event_type VARCHAR(50) COMMENT '事件类型',
                    status VARCHAR(50) DEFAULT 'active' COMMENT '通信状态',
                    is_china BOOLEAN DEFAULT FALSE COMMENT '是否为中国节点',
                    INDEX idx_node_id (node_id),
                    INDEX idx_ip (ip),
                    INDEX idx_communication_time (communication_time),
                    INDEX idx_received_at (received_at),
                    INDEX idx_location (country, province, city),
                    INDEX idx_is_china (is_china),
                    INDEX idx_composite (ip, communication_time)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
                COMMENT='僵尸网络节点通信记录表'
            """)
            
            # 3. 升级表结构（处理旧表迁移）
            await self._upgrade_table_structure(cursor)
            
            logger.info(f"[{self.botnet_type}] Tables ensured: {self.node_table}, {self.communication_table}")
            
        except Exception as e:
            logger.error(f"[{self.botnet_type}] Error ensuring tables exist: {e}")
            raise
    
    async def _upgrade_table_structure(self, cursor):
        """升级表结构，重命名和添加字段"""
        try:
            # 检查字段存在性
            cursor.execute(f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = '{self.node_table}'
            """)
            
            existing_columns = {row[0] for row in cursor.fetchall()}
            
            # 旧字段到新字段的映射
            migrations = []
            
            # log_time -> active_time
            if 'log_time' in existing_columns and 'active_time' not in existing_columns:
                migrations.append(('log_time', 'active_time', "节点激活时间（日志中的时间）"))
            elif 'active_time' not in existing_columns:
                # 如果两个都不存在，直接添加新字段
                logger.info(f"[{self.botnet_type}] Adding active_time field")
                cursor.execute(f"""
                    ALTER TABLE {self.node_table} 
                    ADD COLUMN active_time TIMESTAMP NULL DEFAULT NULL 
                    COMMENT '节点激活时间（日志中的时间）' 
                    AFTER status
                """)
                cursor.execute(f"""
                    ALTER TABLE {self.node_table} 
                    ADD INDEX idx_active_time (active_time)
                """)
            
            # created_at -> created_time
            if 'created_at' in existing_columns and 'created_time' not in existing_columns:
                migrations.append(('created_at', 'created_time', "节点首次写入数据库的时间"))
            elif 'created_time' not in existing_columns:
                logger.info(f"[{self.botnet_type}] Adding created_time field")
                cursor.execute(f"""
                    ALTER TABLE {self.node_table} 
                    ADD COLUMN created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
                    COMMENT '节点首次写入数据库的时间'
                """)
                cursor.execute(f"""
                    ALTER TABLE {self.node_table} 
                    ADD INDEX idx_created_time (created_time)
                """)
            
            # 执行字段重命名
            for old_col, new_col, comment in migrations:
                logger.info(f"[{self.botnet_type}] Renaming {old_col} to {new_col}")
                cursor.execute(f"""
                    ALTER TABLE {self.node_table} 
                    CHANGE COLUMN {old_col} {new_col} TIMESTAMP NULL DEFAULT NULL 
                    COMMENT '{comment}'
                """)
            
            # 确保updated_at存在并且类型正确
            if 'updated_at' in existing_columns:
                # 修改updated_at的定义，移除ON UPDATE CURRENT_TIMESTAMP
                logger.info(f"[{self.botnet_type}] Modifying updated_at field")
                cursor.execute(f"""
                    ALTER TABLE {self.node_table} 
                    MODIFY COLUMN updated_at TIMESTAMP NULL DEFAULT NULL 
                    COMMENT '节点最新一次响应时间（日志中的时间）'
                """)
            
            # 删除旧的last_active字段（如果存在）
            if 'last_active' in existing_columns:
                logger.info(f"[{self.botnet_type}] Dropping last_active field")
                cursor.execute(f"""
                    ALTER TABLE {self.node_table} 
                    DROP COLUMN last_active
                """)
            
            logger.info(f"[{self.botnet_type}] Table structure upgrade completed")
                
        except Exception as e:
            logger.error(f"[{self.botnet_type}] Error upgrading table structure: {e}")
            raise
            
    async def _insert_nodes(self, cursor, nodes: List[Dict]):
        """
        批量插入节点数据（双表设计）
        委托给 _insert_nodes_batch 方法
        
        保留此方法以向后兼容
        """
        await self._insert_nodes_batch(cursor, nodes)
        return len(nodes)
            
    async def _update_china_stats(self, cursor):
        """更新中国统计表"""
        # 这里简化处理，直接从节点表重新统计
        # 实际应用中可以使用增量更新
        pass
        
    async def _update_global_stats(self, cursor):
        """更新全球统计表"""
        # 这里简化处理，直接从节点表重新统计
        # 实际应用中可以使用增量更新
        pass
        
    def get_stats(self) -> Dict:
        """获取统计信息（包含去重统计）"""
        total_processed = self.total_written + self.duplicate_count
        duplicate_rate = (self.duplicate_count / max(1, total_processed)) * 100
        
        return {
            'botnet_type': self.botnet_type,
            'total_written': self.total_written,
            'duplicate_count': self.duplicate_count,
            'duplicate_rate': f"{duplicate_rate:.2f}%",
            'buffer_size': len(self.node_buffer),
            'processed_cache_size': len(self.processed_records),
            'china_stats_size': len(self.china_stats),
            'global_stats_size': len(self.global_stats),
            'last_flush': self.last_flush_time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    async def get_accurate_stats(self) -> Dict:
        """获取准确的统计信息（通过查询数据库）"""
        try:
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 查询数据库中的实际记录数
            cursor.execute(f"SELECT COUNT(*) FROM {self.node_table}")
            actual_db_count = cursor.fetchone()[0]
            
            # 查询今天的记录数
            cursor.execute(f"""
                SELECT COUNT(*) FROM {self.node_table} 
                WHERE DATE(created_at) = CURDATE()
            """)
            today_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            # 计算准确的重复率
            total_processed = self.total_written + self.duplicate_count
            actual_duplicate_count = max(0, total_processed - actual_db_count)
            accurate_duplicate_rate = (actual_duplicate_count / max(1, total_processed)) * 100
            
            return {
                'botnet_type': self.botnet_type,
                'total_written': self.total_written,
                'duplicate_count': self.duplicate_count,
                'duplicate_rate': f"{(self.duplicate_count / max(1, total_processed)) * 100:.2f}%",
                'actual_db_count': actual_db_count,
                'today_count': today_count,
                'actual_duplicate_count': actual_duplicate_count,
                'accurate_duplicate_rate': f"{accurate_duplicate_rate:.2f}%",
                'buffer_size': len(self.node_buffer),
                'last_flush': self.last_flush_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"[{self.botnet_type}] Error getting accurate stats: {e}")
            return self.get_stats()  # 回退到基本统计
    
    async def _insert_nodes_batch(self, cursor, nodes: List[Dict]):
        """
        批量插入节点数据（双表设计）
        1. 插入/更新节点表（维护节点汇总信息）
        2. 插入通信记录表（记录每次通信）
        """
        if not nodes:
            return

        try:
            current_time = datetime.now()
            
            # ========================================
            # Step 1: 准备数据并解析时间戳
            # ========================================
            prepared_nodes = []
            for node in nodes:
                log_time = self._parse_timestamp(node.get('timestamp', ''), current_time)
                prepared_nodes.append({
                    'node': node,
                    'log_time': log_time
                })
            
            # ========================================
            # Step 2: 插入/更新节点表
            # ========================================
            node_sql = f"""
                INSERT INTO {self.node_table} 
                (ip, longitude, latitude, country, province, city, continent, isp, asn, 
                 status, first_seen, last_seen, communication_count, is_china)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s)
                ON DUPLICATE KEY UPDATE
                    longitude = VALUES(longitude),
                    latitude = VALUES(latitude),
                    country = VALUES(country),
                    province = VALUES(province),
                    city = VALUES(city),
                    continent = VALUES(continent),
                    isp = VALUES(isp),
                    asn = VALUES(asn),
                    status = VALUES(status),
                    last_seen = CASE 
                        WHEN VALUES(last_seen) > last_seen OR last_seen IS NULL 
                        THEN VALUES(last_seen)
                        ELSE last_seen
                    END,
                    communication_count = communication_count + 1,
                    is_china = VALUES(is_china)
            """
            
            node_values = []
            for item in prepared_nodes:
                node = item['node']
                log_time = item['log_time']
                
                node_values.append((
                    node['ip'],
                    node['longitude'],
                    node['latitude'],
                    node['country'],
                    node['province'],
                    node['city'],
                    node['continent'],
                    node['isp'],
                    node['asn'],
                    node['status'],
                    log_time,  # first_seen
                    log_time,  # last_seen
                    node['is_china']
                ))
            
            cursor.executemany(node_sql, node_values)
            logger.debug(f"[{self.botnet_type}] Node table updated: {len(node_values)} records")
            
            # ========================================
            # Step 3: 获取node_id（通过IP查询）
            # ========================================
            ip_list = [item['node']['ip'] for item in prepared_nodes]
            placeholders = ','.join(['%s'] * len(ip_list))
            cursor.execute(
                f"SELECT id, ip FROM {self.node_table} WHERE ip IN ({placeholders})",
                ip_list
            )
            ip_to_node_id = {row[1]: row[0] for row in cursor.fetchall()}
            
            # ========================================
            # Step 4: 插入通信记录表
            # ========================================
            comm_sql = f"""
                INSERT INTO {self.communication_table}
                (node_id, ip, communication_time, longitude, latitude, country, province, 
                 city, continent, isp, asn, event_type, status, is_china)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            comm_values = []
            for item in prepared_nodes:
                node = item['node']
                log_time = item['log_time']
                node_id = ip_to_node_id.get(node['ip'])
                
                if node_id is None:
                    logger.error(f"[{self.botnet_type}] Cannot find node_id for IP: {node['ip']}")
                    continue
                
                comm_values.append((
                    node_id,
                    node['ip'],
                    log_time,
                    node['longitude'],
                    node['latitude'],
                    node['country'],
                    node['province'],
                    node['city'],
                    node['continent'],
                    node['isp'],
                    node['asn'],
                    node.get('event_type', ''),
                    node['status'],
                    node['is_china']
                ))
            
            if comm_values:
                cursor.executemany(comm_sql, comm_values)
                rows_inserted = cursor.rowcount
                logger.debug(f"[{self.botnet_type}] Inserted {rows_inserted} communication records")
            
        except Exception as e:
            logger.error(f"[{self.botnet_type}] Error in batch insert: {e}")
            raise
    
    def _parse_timestamp(self, timestamp_str, current_time):
        """解析时间戳字符串"""
        log_time = None
        
        if timestamp_str:
            try:
                if isinstance(timestamp_str, str):
                    formats = [
                        '%Y-%m-%d %H:%M:%S',
                        '%Y/%m/%d %H:%M:%S',
                        '%Y-%m-%dT%H:%M:%S',
                    ]
                    
                    for fmt in formats:
                        try:
                            log_time = datetime.strptime(timestamp_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if not log_time and 'T' in timestamp_str:
                        try:
                            clean_ts = timestamp_str.split('+')[0].split('Z')[0].split('.')[0]
                            log_time = datetime.strptime(clean_ts, '%Y-%m-%dT%H:%M:%S')
                        except Exception:
                            pass
                
                elif isinstance(timestamp_str, datetime):
                    log_time = timestamp_str
            
            except Exception as e:
                logger.warning(f"[{self.botnet_type}] Failed to parse timestamp '{timestamp_str}': {e}")
        
        if not log_time:
            log_time = current_time
        
        return log_time
    
    def get_stats(self):
        """获取统计信息"""
        duplicate_rate = f"{(self.duplicate_count / max(1, self.total_written + self.duplicate_count)) * 100:.2f}%"

        with self.buffer_lock:
            buffer_size = len(self.node_buffer)

        stats = {
            'total_written': self.total_written,
            'duplicate_count': self.duplicate_count,
            'duplicate_rate': duplicate_rate,
            'buffer_size': buffer_size,
            'last_flush_time': self.last_flush_time
        }
        
        # 添加性能监控数据
        if self.enable_monitoring:
            stats.update(self.get_performance_stats())
            
        return stats
    
    def get_performance_stats(self):
        """获取性能统计信息"""
        if not self.enable_monitoring:
            return {}
            
        def safe_avg(deque_obj):
            return sum(deque_obj) / len(deque_obj) if deque_obj and len(deque_obj) > 0 else 0
            
        def safe_max(deque_obj):
            return max(deque_obj) if deque_obj and len(deque_obj) > 0 else 0
            
        def safe_min(deque_obj):
            return min(deque_obj) if deque_obj and len(deque_obj) > 0 else 0
        
        performance_stats = {}
        
        # Flush性能
        if self.flush_times:
            performance_stats['flush_performance'] = {
                'avg_time': f"{safe_avg(self.flush_times):.3f}s",
                'max_time': f"{safe_max(self.flush_times):.3f}s",
                'min_time': f"{safe_min(self.flush_times):.3f}s",
                'sample_count': len(self.flush_times)
            }
        
        # 数据库连接性能
        if self.db_connection_times:
            performance_stats['connection_performance'] = {
                'avg_time': f"{safe_avg(self.db_connection_times):.3f}s",
                'max_time': f"{safe_max(self.db_connection_times):.3f}s",
                'min_time': f"{safe_min(self.db_connection_times):.3f}s",
                'sample_count': len(self.db_connection_times)
            }
        
        # 插入性能
        if self.insert_times:
            performance_stats['insert_performance'] = {
                'avg_time': f"{safe_avg(self.insert_times):.3f}s",
                'max_time': f"{safe_max(self.insert_times):.3f}s",
                'min_time': f"{safe_min(self.insert_times):.3f}s",
                'sample_count': len(self.insert_times)
            }
        
        # 系统资源
        if self.cpu_usage:
            performance_stats['system_performance'] = {
                'avg_cpu': f"{safe_avg(self.cpu_usage):.1f}%",
                'max_cpu': f"{safe_max(self.cpu_usage):.1f}%",
                'avg_memory': f"{safe_avg(self.memory_usage):.1f}%",
                'max_memory': f"{safe_max(self.memory_usage):.1f}%"
            }
        
        return performance_stats
    
    def generate_performance_report(self):
        """生成性能报告"""
        if not self.enable_monitoring:
            return "Performance monitoring is disabled"
            
        stats = self.get_performance_stats()
        
        report = f"\n=== Performance Report for {self.botnet_type} ===\n"
        report += f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 基础统计
        report += f"Basic Stats:\n"
        report += f"  Total Written: {self.total_written}\n"
        report += f"  Duplicate Count: {self.duplicate_count}\n"
        report += f"  Buffer Size: {len(self.node_buffer)}\n\n"
        
        # 性能统计
        if 'flush_performance' in stats:
            fp = stats['flush_performance']
            report += f"Flush Performance:\n"
            report += f"  Average: {fp['avg_time']}\n"
            report += f"  Max: {fp['max_time']}\n"
            report += f"  Min: {fp['min_time']}\n"
            report += f"  Samples: {fp['sample_count']}\n\n"
        
        if 'connection_performance' in stats:
            cp = stats['connection_performance']
            report += f"Connection Performance:\n"
            report += f"  Average: {cp['avg_time']}\n"
            report += f"  Max: {cp['max_time']}\n"
            report += f"  Min: {cp['min_time']}\n"
            report += f"  Samples: {cp['sample_count']}\n\n"
        
        if 'insert_performance' in stats:
            ip = stats['insert_performance']
            report += f"Insert Performance:\n"
            report += f"  Average: {ip['avg_time']}\n"
            report += f"  Max: {ip['max_time']}\n"
            report += f"  Min: {ip['min_time']}\n"
            report += f"  Samples: {ip['sample_count']}\n\n"
        
        if 'system_performance' in stats:
            sp = stats['system_performance']
            report += f"System Performance:\n"
            report += f"  Average CPU: {sp['avg_cpu']}\n"
            report += f"  Max CPU: {sp['max_cpu']}\n"
            report += f"  Average Memory: {sp['avg_memory']}\n"
            report += f"  Max Memory: {sp['max_memory']}\n\n"
        
        return report

    def close(self):
        """关闭写入器"""
        # 最后刷新一次
        if self.node_buffer:
            asyncio.run(self.flush(force=True))

        # 关闭连接池
        if self.use_connection_pool and self.connection_pool:
            self.connection_pool.close_all()

        logger.info(f"[{self.botnet_type}] DB Writer closed")

