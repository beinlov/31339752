# -*- coding: utf-8 -*-
"""
抑制阻断路由模块
处理端口资源消耗、SYN洪水攻击、IP黑名单、域名黑名单、丢包策略等功能
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import subprocess
import threading
import logging
import psutil
import os
import sys
import ipaddress

# 将suppression_scripts添加到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'suppression_scripts'))

# 导入任务执行器
from suppression_scripts.task_executor import (
    PortConsumeExecutor,
    SynFloodExecutor,
    stop_task as stop_task_process,
    get_running_tasks as get_running_task_processes
)

router = APIRouter()
logger = logging.getLogger(__name__)

# 全局变量：内存中存储任务状态和日志
running_tasks = {}
task_lock = threading.Lock()
task_logs = {}
task_logs_lock = threading.Lock()

# ==================== 数据模型定义 ====================

class PortConsumeRequest(BaseModel):
    """端口资源消耗攻击请求模型"""
    ip: str = Field(..., description="目标IP地址")
    port: int = Field(..., ge=1, le=65535, description="目标端口")
    threads: int = Field(100, ge=1, le=50000, description="线程数")
    
    @validator('ip')
    def validate_ip(cls, v):
        """验证IP地址格式"""
        if not v or not v.strip():
            raise ValueError('IP地址不能为空')
        try:
            ipaddress.ip_address(v.strip())
            return v.strip()
        except ValueError:
            raise ValueError(f'IP地址格式不正确: {v}')
    
    @validator('port')
    def validate_port(cls, v):
        """验证端口号"""
        if not isinstance(v, int) or v < 1 or v > 65535:
            raise ValueError(f'端口号必须在1-65535之间: {v}')
        return v
    
    @validator('threads')
    def validate_threads(cls, v):
        """验证线程数"""
        if not isinstance(v, int) or v < 1:
            raise ValueError(f'线程数必须大于0: {v}')
        if v > 50000:
            raise ValueError(f'线程数不能超过50000: {v}')
        return v


class SynFloodRequest(BaseModel):
    """SYN洪水攻击请求模型"""
    ip: str = Field(..., description="目标IP地址")
    port: int = Field(..., ge=1, le=65535, description="目标端口")
    threads: int = Field(50, ge=1, le=1000, description="线程数")
    duration: int = Field(60, ge=1, le=3600, description="持续时间(秒)")
    rate: int = Field(1000, ge=1, le=100000, description="速率(包/秒)")
    
    @validator('ip')
    def validate_ip(cls, v):
        """验证IP地址格式"""
        if not v or not v.strip():
            raise ValueError('IP地址不能为空')
        try:
            ipaddress.ip_address(v.strip())
            return v.strip()
        except ValueError:
            raise ValueError(f'IP地址格式不正确: {v}')
    
    @validator('port')
    def validate_port(cls, v):
        """验证端口号"""
        if not isinstance(v, int) or v < 1 or v > 65535:
            raise ValueError(f'端口号必须在1-65535之间: {v}')
        return v
    
    @validator('threads')
    def validate_threads(cls, v):
        """验证线程数"""
        if not isinstance(v, int) or v < 1:
            raise ValueError(f'线程数必须大于0: {v}')
        if v > 1000:
            raise ValueError(f'SYN洪水攻击线程数不能超过1000: {v}')
        return v
    
    @validator('duration')
    def validate_duration(cls, v):
        """验证持续时间"""
        if not isinstance(v, int) or v < 1:
            raise ValueError(f'持续时间必须大于0秒: {v}')
        if v > 3600:
            raise ValueError(f'持续时间不能超过3600秒(1小时): {v}')
        return v
    
    @validator('rate')
    def validate_rate(cls, v):
        """验证速率"""
        if not isinstance(v, int) or v < 1:
            raise ValueError(f'速率必须大于0: {v}')
        if v > 100000:
            raise ValueError(f'速率不能超过100000包/秒: {v}')
        return v


class IPBlacklistRequest(BaseModel):
    """IP黑名单请求模型"""
    ip: str = Field(..., description="IP地址", alias="ip_address")
    description: Optional[str] = Field(None, description="描述信息")
    
    @validator('ip')
    def validate_ip(cls, v):
        """验证IP地址格式"""
        if not v or not v.strip():
            raise ValueError('IP地址不能为空')
        try:
            ipaddress.ip_address(v.strip())
            return v.strip()
        except ValueError:
            raise ValueError(f'IP地址格式不正确: {v}')
    
    class Config:
        populate_by_name = True


class DomainBlacklistRequest(BaseModel):
    """域名黑名单请求模型"""
    domain: str = Field(..., description="域名")
    description: Optional[str] = Field(None, description="描述信息")
    
    @validator('domain')
    def validate_domain(cls, v):
        """验证域名格式"""
        if not v or not v.strip():
            raise ValueError('域名不能为空')
        domain = v.strip().lower()
        if '.' not in domain:
            raise ValueError(f'域名格式不正确，必须包含点号: {domain}')
        # 简单的域名格式检查
        parts = domain.split('.')
        if len(parts) < 2:
            raise ValueError(f'域名格式不正确: {domain}')
        for part in parts:
            if not part or not part.replace('-', '').isalnum():
                raise ValueError(f'域名格式不正确: {domain}')
        return domain


class PacketLossPolicyRequest(BaseModel):
    """丢包策略请求模型"""
    ip: str = Field(..., description="目标IP地址", alias="ip_address")
    loss_rate: float = Field(..., ge=0.0, le=1.0, description="丢包率(0.0-1.0)")
    description: Optional[str] = Field(None, description="描述信息")
    enabled: bool = Field(True, description="是否启用")
    
    @validator('ip')
    def validate_ip(cls, v):
        """验证IP地址格式"""
        if not v or not v.strip():
            raise ValueError('IP地址不能为空')
        try:
            ipaddress.ip_address(v.strip())
            return v.strip()
        except ValueError:
            raise ValueError(f'IP地址格式不正确: {v}')
    
    @validator('loss_rate')
    def validate_loss_rate(cls, v):
        """验证丢包率"""
        if not isinstance(v, (int, float)):
            raise ValueError(f'丢包率必须是数字: {v}')
        if v < 0.0 or v > 1.0:
            raise ValueError(f'丢包率必须在0.0-1.0之间: {v}')
        return v
    
    class Config:
        populate_by_name = True


class PacketLossPolicyUpdate(BaseModel):
    """丢包策略更新模型"""
    loss_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="丢包率")
    description: Optional[str] = Field(None, description="描述信息")
    enabled: Optional[bool] = Field(None, description="是否启用")
    
    @validator('loss_rate')
    def validate_loss_rate(cls, v):
        """验证丢包率"""
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError(f'丢包率必须是数字: {v}')
            if v < 0.0 or v > 1.0:
                raise ValueError(f'丢包率必须在0.0-1.0之间: {v}')
        return v


# ====================  任务日志管理 ====================

def add_task_log(task_id: str, message: str, level: str = "INFO"):
    """添加任务日志"""
    with task_logs_lock:
        if task_id not in task_logs:
            task_logs[task_id] = []
        
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': level,
            'message': message,
            'task_id': task_id
        }
        task_logs[task_id].append(log_entry)
        
        # 内存中日志只保留最近100条
        if len(task_logs[task_id]) > 100:
            task_logs[task_id] = task_logs[task_id][-100:]


def update_task_status_callback(task_id: str, status: str, message: str):
    """
    任务状态更新回调函数
    用于更新数据库中的任务状态
    
    Args:
        task_id: 任务ID
        status: 任务状态
        message: 状态消息
    """
    try:
        add_task_log(task_id, message, "INFO" if status in ["运行中", "已完成"] else "ERROR")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 判断任务类型并更新对应的表
        if task_id.startswith('port-consume'):
            if status in ["已完成", "已停止", "错误"]:
                cursor.execute("""
                    UPDATE port_consume_task
                    SET status = 'stopped', stop_time = NOW()
                    WHERE task_id = %s
                """, (task_id,))
        elif task_id.startswith('syn-flood'):
            if status in ["已完成", "已停止", "错误"]:
                cursor.execute("""
                    UPDATE syn_flood_task
                    SET status = 'stopped', stop_time = NOW()
                    WHERE task_id = %s
                """, (task_id,))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"更新任务状态失败: {e}")


def get_task_logs(task_id: str = None, limit: int = 50) -> List[Dict]:
    """获取任务日志"""
    with task_logs_lock:
        if task_id:
            logs = task_logs.get(task_id, [])
            return logs[-limit:]
        else:
            # 返回所有任务的日志
            all_logs = []
            for tid, logs in task_logs.items():
                all_logs.extend(logs[-limit:])
            all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
            return all_logs[:limit]


# ==================== 数据库操作（使用MySQL） ====================

from config import DB_CONFIG
import pymysql

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def init_suppression_tables():
    """初始化抑制系统所需的数据库表"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # IP黑名单表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_blacklist (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip_address VARCHAR(45) UNIQUE NOT NULL,
                description VARCHAR(200),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_ip (ip_address)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # 域名黑名单表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS domain_blacklist (
                id INT AUTO_INCREMENT PRIMARY KEY,
                domain VARCHAR(255) UNIQUE NOT NULL,
                description VARCHAR(200),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_domain (domain)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # 丢包策略表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS packet_loss_policy (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip_address VARCHAR(45) UNIQUE NOT NULL,
                loss_rate FLOAT NOT NULL,
                description VARCHAR(200),
                enabled BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_ip (ip_address),
                INDEX idx_enabled (enabled)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # 端口资源消耗任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS port_consume_task (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id VARCHAR(100) UNIQUE NOT NULL,
                target_ip VARCHAR(45) NOT NULL,
                target_port INT NOT NULL,
                threads INT DEFAULT 100,
                status VARCHAR(20) DEFAULT 'running',
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                stop_time DATETIME,
                INDEX idx_task_id (task_id),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # SYN洪水攻击任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS syn_flood_task (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id VARCHAR(100) UNIQUE NOT NULL,
                target_ip VARCHAR(45) NOT NULL,
                target_port INT NOT NULL,
                threads INT DEFAULT 50,
                duration INT,
                rate INT,
                status VARCHAR(20) DEFAULT 'running',
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                stop_time DATETIME,
                INDEX idx_task_id (task_id),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        conn.commit()
        logger.info("数据库表初始化完成")
    except Exception as e:
        logger.error(f"初始化数据库失败: {e}")
        conn.rollback()
    finally:
        conn.close()


# 初始化数据库表
try:
    init_suppression_tables()
except Exception as e:
    logger.error(f"初始化抑制系统表时出错: {e}")


# ==================== API路由定义 ====================

@router.get("/tasks")
async def get_tasks():
    """获取任务列表"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 获取端口资源消耗任务
        cursor.execute("""
            SELECT task_id, target_ip as ip, target_port as port, threads,
                   status, DATE_FORMAT(start_time, '%Y-%m-%d %H:%i:%s') as start_time,
                   DATE_FORMAT(stop_time, '%Y-%m-%d %H:%i:%s') as stop_time,
                   'port-consume' as task_type
            FROM port_consume_task
            ORDER BY start_time DESC
            LIMIT 100
        """)
        port_tasks = cursor.fetchall()
        
        # 获取SYN洪水攻击任务
        cursor.execute("""
            SELECT task_id, target_ip as ip, target_port as port, threads, duration, rate,
                   status, DATE_FORMAT(start_time, '%Y-%m-%d %H:%i:%s') as start_time,
                   DATE_FORMAT(stop_time, '%Y-%m-%d %H:%i:%s') as stop_time,
                   'syn-flood' as task_type
            FROM syn_flood_task
            ORDER BY start_time DESC
            LIMIT 100
        """)
        syn_tasks = cursor.fetchall()
        
        all_tasks = port_tasks + syn_tasks
        # 排序时处理None值，None放在最后
        all_tasks.sort(key=lambda x: x.get('start_time') or '1900-01-01 00:00:00', reverse=True)
        
        return {
            "status": "success",
            "data": all_tasks
        }
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")
    finally:
        conn.close()


@router.post("/port-consume/start")
async def start_port_consume(request: PortConsumeRequest, background_tasks: BackgroundTasks):
    """启动端口资源消耗攻击"""
    task_id = f"port-consume_{request.ip}_{request.port}_{int(datetime.now().timestamp())}"
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO port_consume_task (task_id, target_ip, target_port, threads, status, start_time)
            VALUES (%s, %s, %s, %s, 'running', NOW())
        """, (task_id, request.ip, request.port, request.threads))
        conn.commit()
        
        add_task_log(task_id, f"启动端口资源消耗攻击: {request.ip}:{request.port}, 线程数: {request.threads}", "INFO")
        
        # 启动端口资源消耗攻击任务
        try:
            executor = PortConsumeExecutor(task_id)
            executor.start(
                ip=request.ip,
                port=request.port,
                threads=request.threads,
                callback=update_task_status_callback
            )
            logger.info(f"端口资源消耗攻击任务已创建: {task_id}")
        except Exception as exec_error:
            logger.error(f"执行端口资源消耗攻击任务失败: {exec_error}")
            add_task_log(task_id, f"执行端口资源消耗攻击任务失败: {str(exec_error)}", "ERROR")
            # 更新任务状态为错误
            cursor.execute("""
                UPDATE port_consume_task
                SET status = 'error'
                WHERE task_id = %s
            """, (task_id,))
            conn.commit()
            raise
        
        return {
            "status": "success",
            "message": "",
            "task_id": task_id,
            "data": {
                "ip": request.ip,
                "port": request.port,
                "threads": request.threads
            }
        }
    except Exception as e:
        logger.error(f"启动端口资源消耗攻击失败: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"启动端口资源消耗攻击失败: {str(e)}")
    finally:
        conn.close()


@router.post("/syn-flood/start")
async def start_syn_flood(request: SynFloodRequest, background_tasks: BackgroundTasks):
    """启动SYN洪水攻击"""
    task_id = f"syn-flood_{request.ip}_{request.port}_{int(datetime.now().timestamp())}"
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO syn_flood_task (task_id, target_ip, target_port, threads, duration, rate, status, start_time)
            VALUES (%s, %s, %s, %s, %s, %s, 'running', NOW())
        """, (task_id, request.ip, request.port, request.threads, request.duration, request.rate))
        conn.commit()
        
        add_task_log(task_id, f"启动SYN洪水攻击: {request.ip}:{request.port}, 持续时间: {request.duration} 秒", "INFO")
        
        # 启动SYN洪水攻击任务
        try:
            executor = SynFloodExecutor(task_id)
            executor.start(
                ip=request.ip,
                port=request.port,
                threads=request.threads,
                duration=request.duration,
                rate=request.rate,
                callback=update_task_status_callback
            )
            logger.info(f"SYN洪水攻击任务已创建: {task_id}")
        except Exception as exec_error:
            logger.error(f"执行SYN洪水攻击任务失败: {exec_error}")
            add_task_log(task_id, f"执行SYN洪水攻击任务失败: {str(exec_error)}", "ERROR")
            # 更新任务状态为错误
            cursor.execute("""
                UPDATE syn_flood_task
                SET status = 'error'
                WHERE task_id = %s
            """, (task_id,))
            conn.commit()
            raise
        
        return {
            "status": "success",
            "message": "SYN洪水攻击",
            "task_id": task_id,
            "data": {
                "ip": request.ip,
                "port": request.port,
                "threads": request.threads,
                "duration": request.duration,
                "rate": request.rate
            }
        }
    except Exception as e:
        logger.error(f"启动SYN洪水攻击失败: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"启动SYN洪水攻击失败: {str(e)}")
    finally:
        conn.close()


@router.post("/task/{task_id}/stop")
async def stop_task(task_id: str):
    """停止指定任务"""
    # 先尝试停止正在执行的进程
    process_stopped = False
    try:
        process_stopped = stop_task_process(task_id)
        if process_stopped:
            add_task_log(task_id, "任务已停止", "INFO")
            logger.info(f"成功停止任务: {task_id}")
        else:
            logger.warning(f"进程未找到或已停止: {task_id}")
    except Exception as e:
        logger.error(f"停止任务时出错: {e}")
        add_task_log(task_id, f"停止任务失败: {str(e)}", "ERROR")
    
    # 然后更新数据库状态
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 尝试更新端口资源消耗任务
        cursor.execute("""
            UPDATE port_consume_task
            SET status = 'stopped', stop_time = NOW()
            WHERE task_id = %s AND status = 'running'
        """, (task_id,))
        
        if cursor.rowcount == 0:
            # 尝试更新SYN洪水攻击任务
            cursor.execute("""
                UPDATE syn_flood_task
                SET status = 'stopped', stop_time = NOW()
                WHERE task_id = %s AND status = 'running'
            """, (task_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            add_task_log(task_id, "任务已停止", "INFO")
            
            return {
                "status": "success",
                "message": "任务已停止"
            }
        else:
            return {
                "status": "error",
                "message": "任务未找到或已停止"
            }
    except Exception as e:
        logger.error(f"停止任务失败: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"停止任务失败: {str(e)}")
    finally:
        conn.close()


@router.get("/logs")
async def get_logs(task_id: str = None, limit: int = 100):
    """获取任务执行日志"""
    logs = get_task_logs(task_id, limit)
    return {
        "status": "success",
        "data": logs
    }


# ==================== IP黑名单管理 ====================

@router.get("/blacklist/ip")
async def get_ip_blacklist():
    """获取IP黑名单列表"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, ip_address, description, 
                   DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at
            FROM ip_blacklist
            ORDER BY created_at DESC
        """)
        items = cursor.fetchall()
        
        return {
            "status": "success",
            "data": items
        }
    except Exception as e:
        logger.error(f"获取IP黑名单失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取IP黑名单失败: {str(e)}")
    finally:
        conn.close()


@router.post("/blacklist/ip")
async def add_ip_blacklist(request: IPBlacklistRequest):
    """添加IP到黑名单"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ip_blacklist (ip_address, description, created_at)
            VALUES (%s, %s, NOW())
        """, (request.ip, request.description))
        conn.commit()
        
        return {
            "status": "success",
            "message": "IP已成功添加到黑名单"
        }
    except pymysql.IntegrityError:
        return {
            "status": "error",
            "message": "该IP已存在于黑名单中"
        }
    except Exception as e:
        logger.error(f"添加IP黑名单失败: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"添加IP黑名单失败: {str(e)}")
    finally:
        conn.close()


@router.delete("/blacklist/ip/{ip_id}")
async def delete_ip_blacklist(ip_id: int):
    """删除IP黑名单条目"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ip_blacklist WHERE id = %s", (ip_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return {
                "status": "success",
                "message": "IP黑名单已删除"
            }
        else:
            return {
                "status": "error",
                "message": "IP黑名单条目不存在"
            }
    except Exception as e:
        logger.error(f"删除IP黑名单失败: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"删除IP黑名单失败: {str(e)}")
    finally:
        conn.close()


# ==================== 域名黑名单管理 ====================

@router.get("/blacklist/domain")
async def get_domain_blacklist():
    """获取域名黑名单列表"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, domain, description,
                   DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at
            FROM domain_blacklist
            ORDER BY created_at DESC
        """)
        items = cursor.fetchall()
        
        return {
            "status": "success",
            "data": items
        }
    except Exception as e:
        logger.error(f"获取域名黑名单失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取域名黑名单失败: {str(e)}")
    finally:
        conn.close()


@router.post("/blacklist/domain")
async def add_domain_blacklist(request: DomainBlacklistRequest):
    """添加域名到黑名单"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO domain_blacklist (domain, description, created_at)
            VALUES (%s, %s, NOW())
        """, (request.domain, request.description))
        conn.commit()
        
        return {
            "status": "success",
            "message": "域名已成功添加到黑名单"
        }
    except pymysql.IntegrityError:
        return {
            "status": "error",
            "message": "该域名已存在于黑名单中"
        }
    except Exception as e:
        logger.error(f"添加域名黑名单失败: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"添加域名黑名单失败: {str(e)}")
    finally:
        conn.close()


@router.delete("/blacklist/domain/{domain_id}")
async def delete_domain_blacklist(domain_id: int):
    """删除域名黑名单条目"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM domain_blacklist WHERE id = %s", (domain_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return {
                "status": "success",
                "message": "域名黑名单已删除"
            }
        else:
            return {
                "status": "error",
                "message": "域名黑名单条目不存在"
            }
    except Exception as e:
        logger.error(f"删除域名黑名单失败: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"删除域名黑名单失败: {str(e)}")
    finally:
        conn.close()


# ==================== 丢包策略管理 ====================

@router.get("/packet-loss")
async def get_packet_loss_policies():
    """获取丢包策略列表"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, ip_address, loss_rate, description, enabled,
                   DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                   DATE_FORMAT(updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
            FROM packet_loss_policy
            ORDER BY created_at DESC
        """)
        items = cursor.fetchall()
        
        return {
            "status": "success",
            "data": items
        }
    except Exception as e:
        logger.error(f"获取丢包策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取丢包策略失败: {str(e)}")
    finally:
        conn.close()


@router.post("/packet-loss")
async def add_packet_loss_policy(request: PacketLossPolicyRequest):
    """添加丢包策略"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO packet_loss_policy (ip_address, loss_rate, description, enabled, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (request.ip, request.loss_rate, request.description, request.enabled))
        conn.commit()
        
        return {
            "status": "success",
            "message": "丢包策略已成功添加"
        }
    except pymysql.IntegrityError:
        return {
            "status": "error",
            "message": "该IP已存在于丢包策略中"
        }
    except Exception as e:
        logger.error(f"添加丢包策略失败: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"添加丢包策略失败: {str(e)}")
    finally:
        conn.close()


@router.put("/packet-loss/{policy_id}")
async def update_packet_loss_policy(policy_id: int, request: PacketLossPolicyUpdate):
    """更新丢包策略"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if request.loss_rate is not None:
            updates.append("loss_rate = %s")
            params.append(request.loss_rate)
        
        if request.description is not None:
            updates.append("description = %s")
            params.append(request.description)
        
        if request.enabled is not None:
            updates.append("enabled = %s")
            params.append(request.enabled)
        
        # 总是更新updated_at字段
        updates.append("updated_at = NOW()")
        
        if not updates:
            return {
                "status": "error",
                "message": "没有需要更新的字段"
            }
        
        params.append(policy_id)
        query = f"UPDATE packet_loss_policy SET {', '.join(updates)} WHERE id = %s"
        
        cursor.execute(query, params)
        conn.commit()
        
        if cursor.rowcount > 0:
            return {
                "status": "success",
                "message": "丢包策略已更新"
            }
        else:
            return {
                "status": "error",
                "message": "丢包策略不存在"
            }
    except Exception as e:
        logger.error(f"更新丢包策略失败: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"更新丢包策略失败: {str(e)}")
    finally:
        conn.close()


@router.delete("/packet-loss/{policy_id}")
async def delete_packet_loss_policy(policy_id: int):
    """删除丢包策略"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM packet_loss_policy WHERE id = %s", (policy_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return {
                "status": "success",
                "message": "丢包策略已删除"
            }
        else:
            return {
                "status": "error",
                "message": "丢包策略不存在"
            }
    except Exception as e:
        logger.error(f"删除丢包策略失败: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"删除丢包策略失败: {str(e)}")
    finally:
        conn.close()


# ==================== 导出接口（供脚本使用） ====================

@router.get("/blacklist/ip/export", response_class=PlainTextResponse)
async def export_ip_blacklist():
    """
    导出IP黑名单为纯文本格式供脚本使用
    返回格式：每行一个IP地址
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT ip_address FROM ip_blacklist ORDER BY created_at DESC")
        items = cursor.fetchall()
        
        # 提取IP地址
        ip_addresses = [item['ip_address'] for item in items]
        
        # 返回纯文本格式，每行一个IP
        return PlainTextResponse(content='\n'.join(ip_addresses), media_type="text/plain; charset=utf-8")
        
    except Exception as e:
        logger.error(f"导出IP黑名单失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出IP黑名单失败: {str(e)}")
    finally:
        conn.close()


@router.get("/blacklist/domain/export", response_class=PlainTextResponse)
async def export_domain_blacklist():
    """
    导出域名黑名单为纯文本格式供脚本使用
    返回格式：每行一个域名
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT domain FROM domain_blacklist ORDER BY created_at DESC")
        items = cursor.fetchall()
        
        # 提取域名
        domains = [item['domain'] for item in items]
        
        # 返回纯文本格式，每行一个域名
        return PlainTextResponse(content='\n'.join(domains), media_type="text/plain; charset=utf-8")
        
    except Exception as e:
        logger.error(f"导出域名黑名单失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出域名黑名单失败: {str(e)}")
    finally:
        conn.close()


@router.get("/packet-loss/export")
async def export_packet_loss_policies():
    """
    导出丢包策略为JSON格式供脚本使用
    返回格式：{"ip1": 0.3, "ip2": 0.5}
    只返回启用的策略
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # 只查询启用的策略
        cursor.execute("""
            SELECT ip_address, loss_rate
            FROM packet_loss_policy
            WHERE enabled = TRUE
            ORDER BY created_at DESC
        """)
        items = cursor.fetchall()
        
        # 转换为字典格式 {ip: loss_rate}
        policy_dict = {item['ip_address']: item['loss_rate'] for item in items}
        
        # 返回JSON格式
        return JSONResponse(content=policy_dict, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        logger.error(f"导出丢包策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出丢包策略失败: {str(e)}")
    finally:
        conn.close()
