#!/usr/bin/env python3
"""
数据存储模块
负责本地SQLite数据库的数据缓存和管理
支持7天数据保留，保证数据传输的完整性
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class DataStorage:
    """本地数据存储管理器"""
    
    def __init__(self, db_file: str = "./relay_cache.db", retention_days: int = 7):
        self.db_file = db_file
        self.retention_days = retention_days
        self.lock = threading.Lock()
        self._init_database()
        logger.info(f"数据存储初始化: {db_file}, 保留{retention_days}天")
    
    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # 数据记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    seq_id INTEGER,
                    botnet_type TEXT NOT NULL,
                    ip TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT,
                    source TEXT,
                    raw_data TEXT,
                    pulled_at TEXT NOT NULL,
                    pulled_by_platform_at TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    c2_server TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON data_records(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_seq_id ON data_records(seq_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_botnet_status ON data_records(botnet_type, status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON data_records(created_at)")
            
            # 统计表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    date TEXT PRIMARY KEY,
                    total_pulled INTEGER DEFAULT 0,
                    total_served INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL
                )
            """)
            
            conn.commit()
            logger.info("数据库初始化完成")
    
    def save_pulled_data(self, records: List[Dict], c2_server: str = None) -> int:
        """保存从C2拉取的数据"""
        if not records:
            return 0
        
        with self.lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                pulled_at = datetime.now().isoformat()
                saved_count = 0
                
                for record in records:
                    try:
                        cursor.execute("""
                            INSERT INTO data_records (
                                seq_id, botnet_type, ip, timestamp, event_type, 
                                source, raw_data, pulled_at, c2_server, status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                        """, (
                            record.get('seq_id'),
                            record.get('botnet_type', 'unknown'),
                            record.get('ip', ''),
                            record.get('timestamp', ''),
                            record.get('event_type', ''),
                            record.get('source', ''),
                            json.dumps(record, ensure_ascii=False),
                            pulled_at,
                            c2_server
                        ))
                        saved_count += 1
                    except Exception as e:
                        logger.error(f"保存记录失败: {e}")
                
                conn.commit()
                self._update_stats(cursor, 'total_pulled', saved_count)
                conn.commit()
                
                logger.info(f"保存数据: {saved_count}/{len(records)} 条")
                return saved_count
    
    def get_pending_data(self, limit: int = 1000, since_seq: int = None) -> Tuple[List[Dict], int]:
        """
        获取待提供给平台的数据
        
        Args:
            limit: 最大返回数量
            since_seq: 起始序列号（断点续传）
            
        Returns:
            (数据列表, 最大序列号)
        """
        with self.lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                if since_seq is not None:
                    cursor.execute("""
                        SELECT id, seq_id, raw_data FROM data_records 
                        WHERE status = 'pending' AND seq_id > ?
                        ORDER BY seq_id ASC LIMIT ?
                    """, (since_seq, limit))
                else:
                    cursor.execute("""
                        SELECT id, seq_id, raw_data FROM data_records 
                        WHERE status = 'pending'
                        ORDER BY seq_id ASC LIMIT ?
                    """, (limit,))
                
                rows = cursor.fetchall()
                
                if not rows:
                    return [], 0
                
                records = []
                max_seq_id = 0
                
                for row in rows:
                    record_data = json.loads(row[2])
                    # 添加序列号
                    record_data['seq_id'] = row[1]
                    records.append(record_data)
                    
                    if row[1] and row[1] > max_seq_id:
                        max_seq_id = row[1]
                
                return records, max_seq_id
    
    def mark_as_served(self, count: int) -> int:
        """
        标记数据为已提供给平台
        
        Args:
            count: 确认的记录数
            
        Returns:
            更新的记录数
        """
        if count <= 0:
            return 0
        
        with self.lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                served_at = datetime.now().isoformat()
                
                # 标记最早的count条pending记录为served
                cursor.execute("""
                    UPDATE data_records 
                    SET status = 'served', pulled_by_platform_at = ?
                    WHERE id IN (
                        SELECT id FROM data_records 
                        WHERE status = 'pending'
                        ORDER BY seq_id ASC
                        LIMIT ?
                    )
                """, (served_at, count))
                
                updated = cursor.rowcount
                conn.commit()
                
                self._update_stats(cursor, 'total_served', updated)
                conn.commit()
                
                logger.info(f"标记已提供: {updated} 条")
                return updated
    
    def cleanup_old_data(self) -> int:
        """清理过期数据"""
        cutoff_date = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
        
        with self.lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM data_records 
                    WHERE created_at < ? AND status = 'served'
                """, (cutoff_date,))
                
                deleted = cursor.rowcount
                conn.commit()
                
                if deleted > 0:
                    logger.info(f"清理过期数据: {deleted} 条")
                
                return deleted
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # 总计数
            cursor.execute("SELECT COUNT(*) FROM data_records")
            total_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM data_records WHERE status = 'pending'")
            pending_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM data_records WHERE status = 'served'")
            served_count = cursor.fetchone()[0]
            
            # 获取最大和最小seq_id
            cursor.execute("SELECT MIN(seq_id), MAX(seq_id) FROM data_records WHERE status = 'pending'")
            row = cursor.fetchone()
            min_seq = row[0] if row[0] else 0
            max_seq = row[1] if row[1] else 0
            
            # 今日统计
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT * FROM statistics WHERE date = ?", (today,))
            row = cursor.fetchone()
            
            today_stats = {
                'pulled': row[1] if row else 0,
                'served': row[2] if row else 0
            }
            
            return {
                'total_records': total_records,
                'pending': pending_count,
                'served': served_count,
                'seq_range': {
                    'min': min_seq,
                    'max': max_seq
                },
                'today': today_stats
            }
    
    def _update_stats(self, cursor, field: str, increment: int):
        """更新统计数据"""
        today = datetime.now().strftime('%Y-%m-%d')
        now = datetime.now().isoformat()
        
        cursor.execute(f"""
            INSERT INTO statistics (date, {field}, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
            {field} = {field} + ?,
            updated_at = ?
        """, (today, increment, now, increment, now))
