import pymysql
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from collections import defaultdict
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import os
from datetime import datetime
from pathlib import Path
import json
import asyncio
from typing import Optional
from config import DB_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Constants
LOG_DIR = "ashttpd/logdir"
STATE_FILE = "ashttpd/logdir/.monitor_state.json"

# Global variables
observer = None
is_monitoring = False

discriptions = {
    'b2': "蠕虫程序刚运行，首次请求验证C2有效性",
    'a0': "上传文件前请求，疑似建议服务器新建目录",
    'a1': "询问文件名是否可以删除",
    'a4': "POST文件",
    'a5': "蠕虫查命令列表，随后就用sid作为a3的param1参数来查询可以下载的命令文件名称列表",
    'a3': "客户端用param1查命令文件列表，然后客户端会再访问a7",
    'a7': "客户端下载文件后，客户端会再访问a6，可能是让服务器确认",
    'a6': "客户端a7下载后，用a6提示已经保存完成的",
    'a8': "询问文件名是否可以删除",
    'a9': "蠕虫查命令列表，下一步客户端会用b0来下载",
    'b0': "下载",
    'b1': "确认下载"
}

def parse(line):
    try:
        properties = line.strip().split(',')
        if len(properties) < 3:
            logger.warning(f"Invalid log line format: {line}")
            return None
            
        time, ip, status = properties[0], properties[1], properties[2]
        disc = ''
        command = ''
        
        if len(properties) >= 4:
            url = properties[3]
            if '?ql=' in url:
                command = url.split('?ql=')[-1][:2]  # Get the last 2 chars after ?ql=
                disc = discriptions.get(command, '')
                
        return {
            'ip': ip,
            'time': time,
            'status': status,
            'command': command,
            'disc': disc
        }
    except Exception as e:
        logger.error(f"Error parsing line: {line}, error: {e}")
        return None

class detail(BaseModel):
    ip: str
    time: str
    command: str
    description: str
    status: str

class AsruexLogHandler(FileSystemEventHandler):
    def __init__(self, db_config):
        self.db_config = db_config
        self.file_positions = self.load_state()
        self.ensure_table_exists()

    def load_state(self):
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return {}

    def save_state(self):
        try:
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            with open(STATE_FILE, 'w') as f:
                json.dump(self.file_positions, f)
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def ensure_table_exists(self):
        try:
            db = pymysql.connect(**self.db_config)
            cur = db.cursor()
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS asruex_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    log_time DATETIME,
                    ip VARCHAR(16),
                    status VARCHAR(50),
                    command VARCHAR(3),
                    description VARCHAR(200),
                    file_name VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_log_time (log_time),
                    INDEX idx_ip (ip),
                    INDEX idx_command (command)
                )
            """)
            db.commit()
        except Exception as e:
            logger.error(f"Error ensuring table exists: {e}")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'db' in locals():
                db.close()

    def process_file(self, filepath):
        try:
            db = pymysql.connect(**self.db_config)
            cur = db.cursor()
            
            # Get last position
            last_pos = self.file_positions.get(filepath, 0)
            
            with open(filepath, 'r') as file:
                file.seek(last_pos)
                new_lines = file.readlines()
                
                if new_lines:
                    logger.info(f"Processing {len(new_lines)} new lines from {filepath}")
                    
                    for line in new_lines:
                        parsed = parse(line)
                        if parsed:
                            try:
                                # Convert time string to datetime
                                log_time = datetime.strptime(parsed['time'], '%Y-%m-%d %H:%M:%S')
                                
                                cur.execute("""
                                    INSERT INTO asruex_logs 
                                    (log_time, ip, status, command, description, file_name)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, (
                                    log_time,
                                    parsed['ip'],
                                    parsed['status'],
                                    parsed['command'],
                                    parsed['disc'],
                                    os.path.basename(filepath)
                                ))
                            except Exception as e:
                                logger.error(f"Error inserting log entry: {e}")
                                continue
                    
                    db.commit()
                    self.file_positions[filepath] = file.tell()
                    self.save_state()
                    
        except Exception as e:
            logger.error(f"Error processing file {filepath}: {e}")
        finally:
            if 'cur' in locals():
                cur.close()
            if 'db' in locals():
                db.close()

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            logger.info(f"File modified: {event.src_path}")
            self.process_file(event.src_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            logger.info(f"New file created: {event.src_path}")
            self.process_file(event.src_path)

async def start_monitoring_task():
    global observer, is_monitoring
    
    try:
        if is_monitoring:
            return
            
        # Ensure log directory exists
        log_dir = Path(LOG_DIR)
        if not log_dir.exists():
            log_dir.mkdir(parents=True)
            logger.info(f"Created log directory: {LOG_DIR}")

        # Initialize handler and observer
        event_handler = AsruexLogHandler(DB_CONFIG)
        observer = Observer()
        observer.schedule(event_handler, str(log_dir), recursive=False)
        observer.start()
        is_monitoring = True
        logger.info(f"Started monitoring directory: {LOG_DIR}")

        # Only process the most recent file if it exists
        txt_files = list(log_dir.glob('*.txt'))
        if txt_files:
            latest_file = max(txt_files, key=os.path.getctime)
            logger.info(f"Processing latest file: {latest_file}")
            event_handler.process_file(str(latest_file))

    except Exception as e:
        logger.error(f"Error in monitoring task: {e}")
        if observer:
            observer.stop()
            observer = None
        is_monitoring = False
        raise

@router.get("/start-monitoring")
async def start_monitoring():
    try:
        # Start monitoring in background
        asyncio.create_task(start_monitoring_task())
        return JSONResponse(content={"status": "success", "message": "Started monitoring in background"})
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stop-monitoring")
async def stop_monitoring():
    global observer, is_monitoring
    try:
        if observer:
            observer.stop()
            observer.join()
            observer = None
        is_monitoring = False
        return JSONResponse(content={"status": "success", "message": "Stopped monitoring"})
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monitoring-status")
async def get_monitoring_status():
    return JSONResponse(content={"is_monitoring": is_monitoring})

@router.get("/logs")
async def get_logs(limit: int = 100, offset: int = 0):
    try:
        db = pymysql.connect(**DB_CONFIG)
        cur = db.cursor(pymysql.cursors.DictCursor)
        
        cur.execute("""
            SELECT * FROM asruex_logs 
            ORDER BY log_time DESC 
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        logs = cur.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        for log in logs:
            if log.get('log_time'):
                log['log_time'] = log['log_time'].strftime('%Y-%m-%d %H:%M:%S')
            if log.get('created_at'):
                log['created_at'] = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return JSONResponse(content=logs)
        
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals():
            cur.close()
        if 'db' in locals():
            db.close()

@router.get("/province-stats")
async def get_province_stats():
    try:
        db = pymysql.connect(**DB_CONFIG)
        cur = db.cursor(pymysql.cursors.DictCursor)
        
        # 从新表中获取省级统计数据
        cur.execute("""
            SELECT 
                province,
                SUM(infected_num) as total_infected,
                COUNT(DISTINCT municipality) as affected_cities,
                MAX(infected_num) as max_infected,
                AVG(infected_num) as avg_infected
            FROM china_botnet_asruex
            GROUP BY province
            ORDER BY total_infected DESC
        """)
        
        stats = cur.fetchall()
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Error fetching province stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals():
            cur.close()
        if 'db' in locals():
            db.close()

@router.get("/city-stats/{province}")
async def get_city_stats(province: str):
    try:
        db = pymysql.connect(**DB_CONFIG)
        cur = db.cursor(pymysql.cursors.DictCursor)
        
        # 从新表中获取城市级统计数据
        cur.execute("""
            SELECT 
                municipality,
                infected_num,
                created_at,
                updated_at
            FROM china_botnet_asruex
            WHERE province = %s
            ORDER BY infected_num DESC
        """, (province,))
        
        stats = cur.fetchall()
        
        # 转换datetime对象为字符串
        for stat in stats:
            if stat.get('created_at'):
                stat['created_at'] = stat['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if stat.get('updated_at'):
                stat['updated_at'] = stat['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
                
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Error fetching city stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals():
            cur.close()
        if 'db' in locals():
            db.close()

@router.post("/update-infected/{city}")
async def update_infected_count(city: str, infected_num: int):
    try:
        db = pymysql.connect(**DB_CONFIG)
        cur = db.cursor()
        
        # 更新指定城市的感染数
        cur.execute("""
            UPDATE china_botnet_asruex
            SET infected_num = %s
            WHERE municipality = %s
        """, (infected_num, city))
        
        db.commit()
        return JSONResponse(content={"status": "success", "message": f"Updated {city} infected count to {infected_num}"})
        
    except Exception as e:
        logger.error(f"Error updating infected count: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals():
            cur.close()
        if 'db' in locals():
            db.close() 