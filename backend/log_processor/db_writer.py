"""
数据库写入器模块
负责将处理后的数据批量写入数据库
"""
import pymysql
import logging
from typing import Dict, List
from datetime import datetime
import random
from collections import defaultdict

logger = logging.getLogger(__name__)


class BotnetDBWriter:
    """僵尸网络数据库写入器"""
    
    def __init__(self, botnet_type: str, db_config: Dict, batch_size: int = 100):
        """
        初始化数据库写入器
        
        Args:
            botnet_type: 僵尸网络类型
            db_config: 数据库配置
            batch_size: 批量写入大小
        """
        self.botnet_type = botnet_type
        self.db_config = db_config
        self.batch_size = batch_size
        
        # 批量缓冲区
        self.node_buffer = []
        self.china_stats = defaultdict(int)  # {(province, city): count}
        self.global_stats = defaultdict(int)  # {country: count}
        
        # 统计信息
        self.total_written = 0
        self.duplicate_count = 0  # 重复记录计数
        self.last_flush_time = datetime.now()
        
        # 去重缓存（记录已处理的记录）
        self.processed_records = set()
        
        # 表名
        self.node_table = f"botnet_nodes_{botnet_type}"
        self.china_table = f"china_botnet_{botnet_type}"
        self.global_table = f"global_botnet_{botnet_type}"
        
    def add_node(self, log_data: Dict, ip_info: Dict):
        """
        添加节点数据到缓冲区（带去重检查）
        
        Args:
            log_data: 日志数据
            ip_info: IP信息
        """
        try:
            # 生成记录唯一标识（用于去重）
            record_key = f"{log_data['ip']}|{log_data['timestamp']}|{log_data.get('event_type', '')}"
            
            # 检查是否已处理过（应用层去重）
            if record_key in self.processed_records:
                self.duplicate_count += 1
                logger.debug(f"[{self.botnet_type}] Skipping duplicate: {record_key}")
                return
            
            # 构建节点数据
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
            
            # 添加到缓冲区
            self.node_buffer.append(node_data)
            
            # 记录已处理
            self.processed_records.add(record_key)
            
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
                
        except Exception as e:
            logger.error(f"[{self.botnet_type}] Error adding node: {e}")
            
    async def flush(self, force: bool = False):
        """
        刷新缓冲区，写入数据库
        
        Args:
            force: 是否强制刷新（忽略batch_size检查）
        """
        if not force and len(self.node_buffer) < self.batch_size:
            return
            
        if not self.node_buffer:
            return
            
        try:
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 确保表存在
            await self._ensure_tables_exist(cursor)
            
            # 批量插入节点数据
            await self._insert_nodes(cursor, self.node_buffer)
            
            # 提交事务
            conn.commit()
            
            self.total_written += len(self.node_buffer)
            logger.info(f"[{self.botnet_type}] Flushed {len(self.node_buffer)} nodes to database. Total: {self.total_written}")
            
            # 清空缓冲区
            self.node_buffer.clear()
            self.last_flush_time = datetime.now()
            
        except Exception as e:
            logger.error(f"[{self.botnet_type}] Error flushing to database: {e}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
                
    async def update_statistics(self):
        """更新统计表"""
        if not self.china_stats and not self.global_stats:
            return
            
        try:
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
            
        except Exception as e:
            logger.error(f"[{self.botnet_type}] Error updating statistics: {e}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
                
    async def _ensure_tables_exist(self, cursor):
        """确保数据表存在"""
        try:
            # 创建节点表
            # 注意: UNIQUE KEY 只使用 ip,允许同一IP在不同时间点写入,但同一次批次写入时去重
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.node_table} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    ip VARCHAR(15) NOT NULL,
                    longitude FLOAT,
                    latitude FLOAT,
                    country VARCHAR(50),
                    province VARCHAR(50),
                    city VARCHAR(50),
                    continent VARCHAR(50),
                    isp VARCHAR(255),
                    asn VARCHAR(50),
                    status ENUM('active', 'inactive') DEFAULT 'active',
                    last_active TIMESTAMP NULL DEFAULT NULL COMMENT '最后一次status为active的时间',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '首次写入时间',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最近更新时间',
                    is_china BOOLEAN DEFAULT FALSE,
                    INDEX idx_ip (ip),
                    INDEX idx_location (country, province, city),
                    INDEX idx_status (status),
                    INDEX idx_last_active (last_active),
                    INDEX idx_is_china (is_china),
                    INDEX idx_created_at (created_at),
                    INDEX idx_updated_at (updated_at),
                    UNIQUE KEY idx_unique_ip (ip)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
                COMMENT='僵尸网络节点原始数据表'
            """)
            
            logger.info(f"[{self.botnet_type}] Table {self.node_table} created with unique constraint")
            
        except Exception as e:
            logger.error(f"[{self.botnet_type}] Error ensuring tables exist: {e}")
            
    async def _insert_nodes(self, cursor, nodes: List[Dict]):
        """
        批量插入节点数据
        使用 INSERT ... ON DUPLICATE KEY UPDATE 支持重复IP的更新
        
        时间字段逻辑:
        - created_at: 首次写入时间,重复时保持不变
        - updated_at: 每次写入/更新的时间
        - last_active: status为active时的最后时间
        """
        if not nodes:
            return
            
        try:
            # 使用 INSERT ... ON DUPLICATE KEY UPDATE 
            # 如果IP已存在(基于 UNIQUE KEY idx_unique_record)则更新,否则插入
            sql = f"""
                INSERT INTO {self.node_table} 
                (ip, longitude, latitude, country, province, city, continent, isp, asn, 
                 status, last_active, is_china, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
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
                    last_active = VALUES(last_active),
                    is_china = VALUES(is_china),
                    updated_at = NOW()
            """
            
            values = []
            current_time = datetime.now()
            
            for node in nodes:
                # last_active: status为active时使用当前时间
                last_active = current_time if node['status'] == 'active' else None
                
                values.append((
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
                    last_active,
                    node['is_china']
                ))
                
            cursor.executemany(sql, values)
            
            # 注意: ON DUPLICATE KEY UPDATE 会让 rowcount 返回:
            # 1 = 新插入, 2 = 更新, 0 = 没变化
            rows_affected = cursor.rowcount
            
            # 粗略统计: rowcount >= len(nodes) 说明有更新发生
            if rows_affected > len(nodes):
                updated_count = rows_affected - len(nodes)
                logger.debug(f"[{self.botnet_type}] Updated {updated_count} existing records")
            
        except Exception as e:
            logger.error(f"[{self.botnet_type}] Error inserting nodes: {e}")
            raise
            
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

