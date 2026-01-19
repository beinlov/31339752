"""
��ʬ����������ϲ��Թ���·��
�����˿���Դ���ġ�SYN��ˮ������IP/��������������Ъ�Զ�������
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

# ���suppression_scripts��Python·��
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'suppression_scripts'))

# ��������ִ����
from suppression_scripts.task_executor import (
    PortConsumeExecutor,
    SynFloodExecutor,
    stop_task as stop_task_process,
    get_running_tasks as get_running_task_processes
)

router = APIRouter()
logger = logging.getLogger(__name__)

# �����е�����洢
running_tasks = {}
task_lock = threading.Lock()
task_logs = {}
task_logs_lock = threading.Lock()

# ==================== ����ģ�� ====================

class PortConsumeRequest(BaseModel):
    """�˿���Դ��������"""
    ip: str = Field(..., description="Ŀ��IP��ַ")
    port: int = Field(..., ge=1, le=65535, description="Ŀ��˿�")
    threads: int = Field(100, ge=1, description="�߳���")


class SynFloodRequest(BaseModel):
    """SYN��ˮ��������"""
    ip: str = Field(..., description="Ŀ��IP��ַ")
    port: int = Field(..., ge=1, le=65535, description="Ŀ��˿�")
    threads: int = Field(50, ge=1, description="�߳���")
    duration: int = Field(60, ge=1, description="����ʱ��(��)")
    rate: int = Field(1000, ge=1, description="����(��/��)")


class IPBlacklistRequest(BaseModel):
    """IP����������"""
    ip: str = Field(..., description="IP��ַ", alias="ip_address")
    description: Optional[str] = Field(None, description="����")
    
    @validator('ip')
    def validate_ip(cls, v):
        """��֤IP��ַ��ʽ"""
        try:
            ipaddress.ip_address(v.strip())
            return v.strip()
        except ValueError:
            raise ValueError('IP��ַ��ʽ����ȷ')
    
    class Config:
        populate_by_name = True


class DomainBlacklistRequest(BaseModel):
    """��������������"""
    domain: str = Field(..., description="����")
    description: Optional[str] = Field(None, description="����")
    
    @validator('domain')
    def validate_domain(cls, v):
        """��֤������ʽ"""
        domain = v.strip().lower()
        if not domain or '.' not in domain:
            raise ValueError('������ʽ����ȷ')
        return domain


class PacketLossPolicyRequest(BaseModel):
    """������������"""
    ip: str = Field(..., description="Ŀ��IP��ַ", alias="ip_address")
    loss_rate: float = Field(..., ge=0.0, le=1.0, description="������(0.0-1.0)")
    description: Optional[str] = Field(None, description="����")
    
    class Config:
        populate_by_name = True


class PacketLossPolicyUpdate(BaseModel):
    """�������Ը�������"""
    loss_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="������")
    description: Optional[str] = Field(None, description="����")
    enabled: Optional[bool] = Field(None, description="�Ƿ�����")


# ==================== �������� ====================

def add_task_log(task_id: str, message: str, level: str = "INFO"):
    """���������־"""
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
        
        # �����ڴ�����־��������ౣ��100��
        if len(task_logs[task_id]) > 100:
            task_logs[task_id] = task_logs[task_id][-100:]


def update_task_status_callback(task_id: str, status: str, message: str):
    """
    ����״̬���»ص�����
    ���ڸ������ݿ��е�����״̬
    
    Args:
        task_id: ����ID
        status: ״̬
        message: ��Ϣ
    """
    try:
        add_task_log(task_id, message, "INFO" if status in ["������", "�����"] else "ERROR")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # �ж��������Ͳ����¶�Ӧ�ı�
        if task_id.startswith('port-consume'):
            if status in ["�����", "��ֹͣ", "����"]:
                cursor.execute("""
                    UPDATE port_consume_task
                    SET status = 'stopped', stop_time = NOW()
                    WHERE task_id = %s
                """, (task_id,))
        elif task_id.startswith('syn-flood'):
            if status in ["�����", "��ֹͣ", "����"]:
                cursor.execute("""
                    UPDATE syn_flood_task
                    SET status = 'stopped', stop_time = NOW()
                    WHERE task_id = %s
                """, (task_id,))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"��������״̬ʧ��: {e}")


def get_task_logs(task_id: str = None, limit: int = 50) -> List[Dict]:
    """��ȡ������־"""
    with task_logs_lock:
        if task_id:
            logs = task_logs.get(task_id, [])
            return logs[-limit:]
        else:
            # ���������������־
            all_logs = []
            for tid, logs in task_logs.items():
                all_logs.extend(logs[-limit:])
            all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
            return all_logs[:limit]


# ==================== ���ݿ������ʹ��MySQL�� ====================

from config import DB_CONFIG
import pymysql

def get_db_connection():
    """��ȡ���ݿ�����"""
    return pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def init_suppression_tables():
    """��ʼ�����������ر�"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # IP��������
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_blacklist (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip_address VARCHAR(45) UNIQUE NOT NULL,
                description VARCHAR(200),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_ip (ip_address)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # ������������
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS domain_blacklist (
                id INT AUTO_INCREMENT PRIMARY KEY,
                domain VARCHAR(255) UNIQUE NOT NULL,
                description VARCHAR(200),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_domain (domain)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # �������Ա�
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
        
        # �˿���Դ���������
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
        
        # SYN��ˮ���������
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
        logger.info("����������ݿ���ʼ�����")
    except Exception as e:
        logger.error(f"��ʼ�����ݿ��ʧ��: {e}")
        conn.rollback()
    finally:
        conn.close()


# ��ʼ����
try:
    init_suppression_tables()
except Exception as e:
    logger.error(f"��ʼ��������ϱ�ʱ����: {e}")


# ==================== API·�� ====================

@router.get("/tasks")
async def get_tasks():
    """��ȡ���������б�"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # ��ȡ�˿���Դ��������
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
        
        # ��ȡSYN��ˮ��������
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
        all_tasks.sort(key=lambda x: x.get('start_time', ''), reverse=True)
        
        return {
            "status": "success",
            "data": all_tasks
        }
    except Exception as e:
        logger.error(f"��ȡ�����б�ʧ��: {e}")
        raise HTTPException(status_code=500, detail=f"��ȡ�����б�ʧ��: {str(e)}")
    finally:
        conn.close()


@router.post("/port-consume/start")
async def start_port_consume(request: PortConsumeRequest, background_tasks: BackgroundTasks):
    """����˿���Դ��������"""
    task_id = f"port-consume_{request.ip}_{request.port}_{int(datetime.now().timestamp())}"
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO port_consume_task (task_id, target_ip, target_port, threads, status)
            VALUES (%s, %s, %s, %s, 'running')
        """, (task_id, request.ip, request.port, request.threads))
        conn.commit()
        
        add_task_log(task_id, f"����˿���Դ��������: {request.ip}:{request.port}, �߳���: {request.threads}", "INFO")
        
        # ʵ������˿���Դ���Ĺ���
        try:
            executor = PortConsumeExecutor(task_id)
            executor.start(
                ip=request.ip,
                port=request.port,
                threads=request.threads,
                callback=update_task_status_callback
            )
            logger.info(f"�˿���Դ���Ĺ��������: {task_id}")
        except Exception as exec_error:
            logger.error(f"��������ű�ʧ��: {exec_error}")
            add_task_log(task_id, f"��������ű�ʧ��: {str(exec_error)}", "ERROR")
            # �������ݿ�״̬Ϊ����
            cursor.execute("""
                UPDATE port_consume_task
                SET status = 'error'
                WHERE task_id = %s
            """, (task_id,))
            conn.commit()
            raise
        
        return {
            "status": "success",
            "message": "���������",
            "task_id": task_id,
            "data": {
                "ip": request.ip,
                "port": request.port,
                "threads": request.threads
            }
        }
    except Exception as e:
        logger.error(f"����˿���Դ��������ʧ��: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"�������ʧ��: {str(e)}")
    finally:
        conn.close()


@router.post("/syn-flood/start")
async def start_syn_flood(request: SynFloodRequest):
    """���SYN��ˮ��������"""
    task_id = f"syn-flood_{request.ip}_{request.port}_{int(datetime.now().timestamp())}"
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO syn_flood_task (task_id, target_ip, target_port, threads, duration, rate, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'running')
        """, (task_id, request.ip, request.port, request.threads, request.duration, request.rate))
        conn.commit()
        
        add_task_log(task_id, f"���SYN��ˮ����: {request.ip}:{request.port}, ����{request.duration}��", "INFO")
        
        # ʵ�����SYN��ˮ����
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
            logger.info(f"SYN��ˮ���������: {task_id}")
        except Exception as exec_error:
            logger.error(f"��������ű�ʧ��: {exec_error}")
            add_task_log(task_id, f"��������ű�ʧ��: {str(exec_error)}", "ERROR")
            # �������ݿ�״̬Ϊ����
            cursor.execute("""
                UPDATE syn_flood_task
                SET status = 'error'
                WHERE task_id = %s
            """, (task_id,))
            conn.commit()
            raise
        
        return {
            "status": "success",
            "message": "SYN��ˮ�������������",
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
        logger.error(f"���SYN��ˮ��������ʧ��: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"�������ʧ��: {str(e)}")
    finally:
        conn.close()


@router.post("/task/{task_id}/stop")
async def stop_task(task_id: str):
    """ֹͣ����"""
    # ���ȳ���ֹͣʵ�����еĽ���
    process_stopped = False
    try:
        process_stopped = stop_task_process(task_id)
        if process_stopped:
            add_task_log(task_id, "���������ֹͣ", "INFO")
            logger.info(f"�ɹ�ֹͣ�������: {task_id}")
        else:
            logger.warning(f"������̲����ڻ���ֹͣ: {task_id}")
    except Exception as e:
        logger.error(f"ֹͣ�������ʱ����: {e}")
        add_task_log(task_id, f"ֹͣ����ʧ��: {str(e)}", "ERROR")
    
    # Ȼ��������ݿ�״̬
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # ���Ը��¶˿���Դ��������
        cursor.execute("""
            UPDATE port_consume_task
            SET status = 'stopped', stop_time = NOW()
            WHERE task_id = %s AND status = 'running'
        """, (task_id,))
        
        if cursor.rowcount == 0:
            # ���Ը���SYN��ˮ��������
            cursor.execute("""
                UPDATE syn_flood_task
                SET status = 'stopped', stop_time = NOW()
                WHERE task_id = %s AND status = 'running'
            """, (task_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            add_task_log(task_id, "������ֹͣ", "INFO")
            
            return {
                "status": "success",
                "message": "������ֹͣ"
            }
        else:
            return {
                "status": "error",
                "message": "���񲻴��ڻ���ֹͣ"
            }
    except Exception as e:
        logger.error(f"ֹͣ����ʧ��: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"ֹͣ����ʧ��: {str(e)}")
    finally:
        conn.close()


@router.get("/logs")
async def get_logs(limit: int = 100, task_id: Optional[str] = None):
    """��ȡ��־"""
    logs = get_task_logs(task_id, limit)
    return {
        "status": "success",
        "data": logs
    }


# ==================== IP������ ====================

@router.get("/blacklist/ip")
async def get_ip_blacklist():
    """��ȡIP�������б�"""
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
        logger.error(f"��ȡIP������ʧ��: {e}")
        raise HTTPException(status_code=500, detail=f"��ȡIP������ʧ��: {str(e)}")
    finally:
        conn.close()


@router.post("/blacklist/ip")
async def add_ip_blacklist(request: IPBlacklistRequest):
    """���IP��������"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ip_blacklist (ip_address, description)
            VALUES (%s, %s)
        """, (request.ip, request.description))
        conn.commit()
        
        return {
            "status": "success",
            "message": "IP����ӵ�������"
        }
    except pymysql.IntegrityError:
        return {
            "status": "error",
            "message": "��IP�Ѵ����ں�������"
        }
    except Exception as e:
        logger.error(f"���IP������ʧ��: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"���IP������ʧ��: {str(e)}")
    finally:
        conn.close()


@router.delete("/blacklist/ip/{ip_id}")
async def delete_ip_blacklist(ip_id: int):
    """ɾ��IP������"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ip_blacklist WHERE id = %s", (ip_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return {
                "status": "success",
                "message": "IP��ɾ��"
            }
        else:
            return {
                "status": "error",
                "message": "IP������"
            }
    except Exception as e:
        logger.error(f"ɾ��IP������ʧ��: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"ɾ��IP������ʧ��: {str(e)}")
    finally:
        conn.close()


# ==================== ���������� ====================

@router.get("/blacklist/domain")
async def get_domain_blacklist():
    """��ȡ�����������б�"""
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
        logger.error(f"��ȡ����������ʧ��: {e}")
        raise HTTPException(status_code=500, detail=f"��ȡ����������ʧ��: {str(e)}")
    finally:
        conn.close()


@router.post("/blacklist/domain")
async def add_domain_blacklist(request: DomainBlacklistRequest):
    """���������������"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO domain_blacklist (domain, description)
            VALUES (%s, %s)
        """, (request.domain, request.description))
        conn.commit()
        
        return {
            "status": "success",
            "message": "��������ӵ�������"
        }
    except pymysql.IntegrityError:
        return {
            "status": "error",
            "message": "�������Ѵ����ں�������"
        }
    except Exception as e:
        logger.error(f"�������������ʧ��: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"�������������ʧ��: {str(e)}")
    finally:
        conn.close()


@router.delete("/blacklist/domain/{domain_id}")
async def delete_domain_blacklist(domain_id: int):
    """ɾ������������"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM domain_blacklist WHERE id = %s", (domain_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return {
                "status": "success",
                "message": "������ɾ��"
            }
        else:
            return {
                "status": "error",
                "message": "����������"
            }
    except Exception as e:
        logger.error(f"ɾ������������ʧ��: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"ɾ������������ʧ��: {str(e)}")
    finally:
        conn.close()


# ==================== �������� ====================

@router.get("/packet-loss")
async def get_packet_loss_policies():
    """��ȡ���������б�"""
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
        logger.error(f"��ȡ��������ʧ��: {e}")
        raise HTTPException(status_code=500, detail=f"��ȡ��������ʧ��: {str(e)}")
    finally:
        conn.close()


@router.post("/packet-loss")
async def add_packet_loss_policy(request: PacketLossPolicyRequest):
    """��Ӷ�������"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO packet_loss_policy (ip_address, loss_rate, description)
            VALUES (%s, %s, %s)
        """, (request.ip, request.loss_rate, request.description))
        conn.commit()
        
        return {
            "status": "success",
            "message": "�������������"
        }
    except pymysql.IntegrityError:
        return {
            "status": "error",
            "message": "��IP�Ѵ��ڶ�������"
        }
    except Exception as e:
        logger.error(f"��Ӷ�������ʧ��: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"��Ӷ�������ʧ��: {str(e)}")
    finally:
        conn.close()


@router.put("/packet-loss/{policy_id}")
async def update_packet_loss_policy(policy_id: int, request: PacketLossPolicyUpdate):
    """���¶�������"""
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
        
        # ���Ǹ���updated_at�ֶ�
        updates.append("updated_at = NOW()")
        
        if not updates:
            return {
                "status": "error",
                "message": "û����Ҫ���µ��ֶ�"
            }
        
        params.append(policy_id)
        query = f"UPDATE packet_loss_policy SET {', '.join(updates)} WHERE id = %s"
        
        cursor.execute(query, params)
        conn.commit()
        
        if cursor.rowcount > 0:
            return {
                "status": "success",
                "message": "���������Ѹ���"
            }
        else:
            return {
                "status": "error",
                "message": "���Բ�����"
            }
    except Exception as e:
        logger.error(f"���¶�������ʧ��: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"���¶�������ʧ��: {str(e)}")
    finally:
        conn.close()


@router.delete("/packet-loss/{policy_id}")
async def delete_packet_loss_policy(policy_id: int):
    """ɾ����������"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM packet_loss_policy WHERE id = %s", (policy_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return {
                "status": "success",
                "message": "����������ɾ��"
            }
        else:
            return {
                "status": "error",
                "message": "���Բ�����"
            }
    except Exception as e:
        logger.error(f"ɾ����������ʧ��: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"ɾ����������ʧ��: {str(e)}")
    finally:
        conn.close()


# ==================== �����ӿڣ����ű�ʹ�ã� ====================

@router.get("/blacklist/ip/export", response_class=PlainTextResponse)
async def export_ip_blacklist():
    """
    ����IP�����������ı���ʽ����������ű�ʹ�ã�
    ���ظ�ʽ��ÿ��һ��IP��ַ
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT ip_address FROM ip_blacklist ORDER BY created_at DESC")
        items = cursor.fetchall()
        
        # ��ȡ����IP��ַ
        ip_addresses = [item['ip_address'] for item in items]
        
        # ���ش��ı���ʽ��ÿ��һ��IP
        return PlainTextResponse(content='\n'.join(ip_addresses), media_type="text/plain; charset=utf-8")
        
    except Exception as e:
        logger.error(f"����IP������ʧ��: {e}")
        raise HTTPException(status_code=500, detail=f"����IP������ʧ��: {str(e)}")
    finally:
        conn.close()


@router.get("/blacklist/domain/export", response_class=PlainTextResponse)
async def export_domain_blacklist():
    """
    �������������������ı���ʽ����������ű�ʹ�ã�
    ���ظ�ʽ��ÿ��һ������
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT domain FROM domain_blacklist ORDER BY created_at DESC")
        items = cursor.fetchall()
        
        # ��ȡ��������
        domains = [item['domain'] for item in items]
        
        # ���ش��ı���ʽ��ÿ��һ������
        return PlainTextResponse(content='\n'.join(domains), media_type="text/plain; charset=utf-8")
        
    except Exception as e:
        logger.error(f"��������������ʧ��: {e}")
        raise HTTPException(status_code=500, detail=f"��������������ʧ��: {str(e)}")
    finally:
        conn.close()


@router.get("/packet-loss/export")
async def export_packet_loss_policies():
    """
    �����������ԣ�JSON��ʽ����������ű�ʹ�ã�
    ���ظ�ʽ��{"ip1": 0.3, "ip2": 0.5}
    ֻ�������õĲ���
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # ֻ�������õĲ���
        cursor.execute("""
            SELECT ip_address, loss_rate
            FROM packet_loss_policy
            WHERE enabled = TRUE
            ORDER BY created_at DESC
        """)
        items = cursor.fetchall()
        
        # �����ֵ��ʽ {ip: loss_rate}
        policy_dict = {item['ip_address']: item['loss_rate'] for item in items}
        
        # ����JSON��ʽ
        return JSONResponse(content=policy_dict, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        logger.error(f"������������ʧ��: {e}")
        raise HTTPException(status_code=500, detail=f"������������ʧ��: {str(e)}")
    finally:
        conn.close()
