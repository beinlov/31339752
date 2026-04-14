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
                    botnet_type TEXT NOT NULL,
                    ip TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT,
                    source TEXT,
                    raw_data TEXT,
                    pulled_at TEXT NOT NULL,
                    pushed_at TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    c2_server TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON data_records(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_botnet_status ON data_records(botnet_type, status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON data_records(created_at)")
            
            # 统计表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    date TEXT PRIMARY KEY,
                    total_pulled INTEGER DEFAULT 0,
                    total_pushed INTEGER DEFAULT 0,
                    total_failed INTEGER DEFAULT 0,
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
                                botnet_type, ip, timestamp, event_type, 
                                source, raw_data, pulled_at, c2_server, status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                        """, (
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
    
    def get_pending_data(self, botnet_type: str = None, limit: int = 1000) -> Tuple[List[Dict], List[int]]:
        """获取待推送的数据"""
        with self.lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                if botnet_type:
                    cursor.execute("""
                        SELECT id, raw_data FROM data_records 
                        WHERE status = 'pending' AND botnet_type = ?
                        ORDER BY created_at ASC LIMIT ?
                    """, (botnet_type, limit))
                else:
                    cursor.execute("""
                        SELECT id, raw_data FROM data_records 
                        WHERE status = 'pending'
                        ORDER BY created_at ASC LIMIT ?
                    """, (limit,))
                
                rows = cursor.fetchall()
                
                if not rows:
                    return [], []
                
                record_ids = [row[0] for row in rows]
                records = [json.loads(row[1]) for row in rows]
                
                return records, record_ids
    
    def mark_as_pushed(self, record_ids: List[int]) -> int:
        """标记数据为已推送"""
        if not record_ids:
            return 0
        
        with self.lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                pushed_at = datetime.now().isoformat()
                
                placeholders = ','.join('?' * len(record_ids))
                cursor.execute(f"""
                    UPDATE data_records 
                    SET status = 'pushed', pushed_at = ?
                    WHERE id IN ({placeholders})
                """, [pushed_at] + record_ids)
                
                updated = cursor.rowcount
                conn.commit()
                
                self._update_stats(cursor, 'total_pushed', updated)
                conn.commit()
                
                logger.info(f"标记已推送: {updated} 条")
                return updated
    
    def mark_as_failed(self, record_ids: List[int]) -> int:
        """标记数据推送失败"""
        if not record_ids:
            return 0
        
        with self.lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                placeholders = ','.join('?' * len(record_ids))
                cursor.execute(f"""
                    UPDATE data_records 
                    SET status = 'failed', retry_count = retry_count + 1
                    WHERE id IN ({placeholders})
                """, record_ids)
                
                updated = cursor.rowcount
                conn.commit()
                
                self._update_stats(cursor, 'total_failed', updated)
                conn.commit()
                
                logger.info(f"标记失败: {updated} 条")
                return updated
    
    def retry_failed_data(self, max_retries: int = 3) -> int:
        """重试失败的数据"""
        with self.lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE data_records 
                    SET status = 'pending'
                    WHERE status = 'failed' AND retry_count < ?
                """, (max_retries,))
                
                updated = cursor.rowcount
                conn.commit()
                
                if updated > 0:
                    logger.info(f"重试失败数据: {updated} 条")
                
                return updated
    
    def cleanup_old_data(self) -> int:
        """清理过期数据"""
        cutoff_date = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
        
        with self.lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM data_records 
                    WHERE created_at < ? AND status = 'pushed'
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
            
            cursor.execute("SELECT COUNT(*) FROM data_records WHERE status = 'pushed'")
            pushed_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM data_records WHERE status = 'failed'")
            failed_count = cursor.fetchone()[0]
            
            # 今日统计
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT * FROM statistics WHERE date = ?", (today,))
            row = cursor.fetchone()
            
            today_stats = {
                'pulled': row[1] if row else 0,
                'pushed': row[2] if row else 0,
                'failed': row[3] if row else 0
            }
            
            return {
                'total_records': total_records,
                'pending': pending_count,
                'pushed': pushed_count,
                'failed': failed_count,
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
