# -*- coding: utf-8 -*-
"""
Å®Î×¹¥»÷²âÊÔAPIÄ£¿é - »ùÓÚDocker»·¾³µÄDHTÅ®Î×¹¥»÷²âÊÔ
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict
import subprocess
import json
import os
import logging
import time
from datetime import datetime
from router.suppression import get_db_connection

router = APIRouter()
logger = logging.getLogger(__name__)

# Docker项目路径
DOCKER_PROJECT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 
    'suppression_scripts/docker-cluster-10 - 副本'
)

class SybilAttackRequest(BaseModel):
    """Å®Î×¹¥»÷²âÊÔÇëÇó"""
    attack_nodes_per_bucket: int = 8  # Ã¿¸öbucketµÄ¹¥»÷½ÚµãÊý
    test_type: str = "docker"  # docker | distributed
    target_node: str = "node-1"  # Ä¿±ê½ÚµãÃû³Æ
    description: Optional[str] = None


class DistributedSybilRequest(BaseModel):
    """·Ö²¼Ê½Å®Î×¹¥»÷ÅäÖÃ"""
    target_ip: str  # Ä¿±êIPµØÖ·
    target_port: int = 8000
    vps_list: List[Dict[str, str]]  # [{"ip": "45.76.123.10", "ssh_key": "..."}]
    total_servers: int = 10
    nodes_per_server: int = 26


def get_docker_compose_path():
    """»ñÈ¡docker-composeÎÄ¼þÂ·¾¶"""
    return os.path.join(DOCKER_PROJECT_PATH, 'docker-compose.yml')


def get_sybil_script_path():
    """»ñÈ¡Å®Î×¹¥»÷½Å±¾Â·¾¶"""
    return os.path.join(DOCKER_PROJECT_PATH, 'sybil.py')


def init_sybil_test_tables():
    """³õÊ¼»¯Å®Î×¹¥»÷²âÊÔÊý¾Ý¿â±í"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Å®Î×¹¥»÷²âÊÔÈÎÎñ±í
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sybil_attack_test (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id VARCHAR(100) UNIQUE NOT NULL,
                test_type VARCHAR(20) NOT NULL,
                target_node VARCHAR(100) NOT NULL,
                attack_nodes_count INT DEFAULT 256,
                status VARCHAR(20) DEFAULT 'preparing',
                description TEXT,
                docker_status JSON,
                attack_result JSON,
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                stop_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_task_id (task_id),
                INDEX idx_status (status),
                INDEX idx_test_type (test_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        conn.commit()
        logger.info("Å®Î×¹¥»÷²âÊÔ±í³õÊ¼»¯Íê³É")
    except Exception as e:
        logger.error(f"³õÊ¼»¯Å®Î×¹¥»÷²âÊÔ±íÊ§°Ü: {e}")
        conn.rollback()
    finally:
        conn.close()


# ³õÊ¼»¯±í
try:
    init_sybil_test_tables()
except Exception as e:
    logger.error(f"³õÊ¼»¯Å®Î×¹¥»÷²âÊÔÏµÍ³±íÊ±³ö´í: {e}")


@router.get("/test/tasks")
async def get_sybil_test_tasks():
    """»ñÈ¡Å®Î×¹¥»÷²âÊÔÈÎÎñÁÐ±í"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT task_id, test_type, target_node, attack_nodes_count, status,
                   description, docker_status, attack_result,
                   DATE_FORMAT(start_time, '%Y-%m-%d %H:%i:%s') as start_time,
                   DATE_FORMAT(stop_time, '%Y-%m-%d %H:%i:%s') as stop_time
            FROM sybil_attack_test
            ORDER BY start_time DESC
            LIMIT 50
        """)
        tasks = cursor.fetchall()
        
        # ½âÎöJSON×Ö¶Î
        for task in tasks:
            if task.get('docker_status'):
                task['docker_status'] = json.loads(task['docker_status'])
            if task.get('attack_result'):
                task['attack_result'] = json.loads(task['attack_result'])
        
        return {
            "status": "success",
            "data": tasks
        }
    except Exception as e:
        logger.error(f"»ñÈ¡Å®Î×¹¥»÷²âÊÔÈÎÎñÁÐ±íÊ§°Ü: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/test/docker/start")
async def start_docker_sybil_test(request: SybilAttackRequest, background_tasks: BackgroundTasks):
    """Æô¶¯Docker»·¾³µÄÅ®Î×¹¥»÷²âÊÔ"""
    task_id = f"sybil-docker_{int(time.time())}"
    
    # ±£´æÈÎÎñµ½Êý¾Ý¿â
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sybil_attack_test 
            (task_id, test_type, target_node, attack_nodes_count, status, description)
            VALUES (%s, %s, %s, %s, 'preparing', %s)
        """, (task_id, request.test_type, request.target_node, 
              request.attack_nodes_per_bucket * 32, request.description))
        conn.commit()
    except Exception as e:
        logger.error(f"±£´æÈÎÎñÊ§°Ü: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"±£´æÈÎÎñÊ§°Ü: {str(e)}")
    finally:
        conn.close()
    
    # ºóÌ¨ÈÎÎñÖ´ÐÐ
    background_tasks.add_task(run_docker_sybil_attack, task_id, request)
    
    return {
        "status": "success",
        "message": "Å®Î×¹¥»÷²âÊÔÒÑÆô¶¯",
        "task_id": task_id
    }


async def run_docker_sybil_attack(task_id: str, request: SybilAttackRequest):
    """Ö´ÐÐDockerÅ®Î×¹¥»÷²âÊÔ"""
    conn = get_db_connection()
    
    try:
        # ²½Öè0: Çå»ý¾ÉÈÝÆ÷(·ÀÖ¹¶Ë¿Ú³åÍ»)
        logger.info(f"[{task_id}] ²½Öè0: Çå»ý¾É»·¾³...")
        compose_file = get_docker_compose_path()
        try:
            subprocess.run(
                ["docker-compose", "-f", compose_file, "-p", "dht_test", "down"],
                cwd=DOCKER_PROJECT_PATH,
                capture_output=True,
                timeout=30
            )
            logger.info(f"[{task_id}] ¾É»·¾³ÒÑÇå»ð")
        except Exception as e:
            logger.warning(f"[{task_id}] Çå»ËÊ±³ö´í(¿ÉºöÂÔ): {e}")
        
        # ²½Öè1: Æô¶¯Docker»·¾³
        logger.info(f"[{task_id}] ²½Öè1: Æô¶¯DockerÍøÂç...")
        update_task_status(task_id, "starting_docker", {"step": "Æô¶¯DockerÈÝÆ÷"})
        
        result = subprocess.run(
            ["docker-compose", "-f", compose_file, "-p", "dht_test", "up", "-d"],
            cwd=DOCKER_PROJECT_PATH,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            raise Exception(f"Æô¶¯DockerÊ§°Ü: {result.stderr}")
        
        logger.info(f"[{task_id}] DockerÈÝÆ÷Æô¶¯³É¹¦")
        time.sleep(10)  # µÈ´ýÈÝÆ÷ÍêÈ«Æô¶¯
        
        # ²½Öè2: Ö´ÐÐÅ®Î×¹¥»÷
        logger.info(f"[{task_id}] ²½Öè2: Ö´ÐÐÅ®Î×¹¥»÷...")
        update_task_status(task_id, "attacking", {"step": "Ö´ÐÐÅ®Î×¹¥»÷"})
        
        attack_result = subprocess.run(
            ["docker", "exec", "attacker", "python3", "/app/sybil.py"],
            cwd=DOCKER_PROJECT_PATH,
            capture_output=True,
            text=True,
            timeout=150  # 脚本现在会在约110秒内自动完成
        )
        
        # 脚本已经包含了30秒的稳定等待时间，这里只需短暂等待
        logger.info(f"[{task_id}] ²½Öè3: ¹¥»÷ÍêÑé,×¼±¸Ñé½á¹û...")
        time.sleep(5)  # 短暂等待确保攻击完全生效
        
        # ²½Öè4: ÑéÖ¤¹¥»÷Ð§¹û
        logger.info(f"[{task_id}] ²½Öè4: ÑéÖ¤¹¥»÷Ð§¹û...")
        update_task_status(task_id, "verifying", {"step": "ÑéÖ¤¹¥»÷Ð§¹û"})
        
        verify_result = subprocess.run(
            ["docker", "exec", "node-2", "python3", "/app/verify_sybil_attack.py"],
            cwd=DOCKER_PROJECT_PATH,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # ½âÎöÑéÖ¤½á¹û - ¼ì²éÊÇ·ñº¬ÓÐ"Å®Î×¹¥»÷³É¹¦"»ò¸ßÕ¼±È
        attack_success = (
            "女巫攻击成功" in verify_result.stdout or
            "女巫节点占比: 100.0%" in verify_result.stdout or
            "女巫节点占比: 80.0%" in verify_result.stdout or
            ("疑似女巫节点数量:" in verify_result.stdout and 
             "合法节点数量: 0" in verify_result.stdout)
        )
        
        result_data = {
            "attack_success": attack_success,
            "verify_output": verify_result.stdout[:3000],  # 保存前3000字符，确保完整输出
            "attack_output": attack_result.stdout[:1500],  # 增加攻击输出长度
            "timestamp": datetime.now().isoformat()
        }
        
        # ¸üÐÂÈÎÎñ½á¹û
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sybil_attack_test
            SET status = 'completed', 
                attack_result = %s,
                stop_time = NOW()
            WHERE task_id = %s
        """, (json.dumps(result_data, ensure_ascii=False), task_id))
        conn.commit()
        
        logger.info(f"[{task_id}] Å®Î×¹¥»÷²âÊÔÍê³É£¬³É¹¦: {attack_success}")
        
    except subprocess.TimeoutExpired:
        logger.error(f"[{task_id}] Ö´ÐÐ³¬Ê±")
        update_task_status(task_id, "timeout", {"error": "Ö´ÐÐ³¬Ê±"})
    except Exception as e:
        logger.error(f"[{task_id}] Ö´ÐÐÊ§°Ü: {e}")
        update_task_status(task_id, "failed", {"error": str(e)})
    finally:
        conn.close()


@router.post("/test/docker/stop/{task_id}")
async def stop_docker_sybil_test(task_id: str):
    """Í£Ö¹DockerÅ®Î×¹¥»÷²âÊÔ"""
    try:
        compose_file = get_docker_compose_path()
        
        # Í£Ö¹²¢É¾³ýÈÝÆ÷
        result = subprocess.run(
            ["docker-compose", "-f", compose_file, "down"],
            cwd=DOCKER_PROJECT_PATH,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise Exception(f"Í£Ö¹DockerÊ§°Ü: {result.stderr}")
        
        # ¸üÐÂÊý¾Ý¿â×´Ì¬
        update_task_status(task_id, "stopped", {"manual_stop": True})
        
        return {
            "status": "success",
            "message": "Docker»·¾³ÒÑÍ£Ö¹"
        }
    except Exception as e:
        logger.error(f"Í£Ö¹Docker»·¾³Ê§°Ü: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/docker/status")
async def get_docker_status():
    """»ñÈ¡Docker»·¾³×´Ì¬"""
    try:
        # ¼ì²éÈÝÆ÷×´Ì¬
        result = subprocess.run(
            ["docker-compose", "-f", get_docker_compose_path(), "-p", "dht_test", "ps"],
            cwd=DOCKER_PROJECT_PATH,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        containers = []
        lines = result.stdout.split('\n')[2:]  # Ìø¹ý±íÍ·
        
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    containers.append({
                        "name": parts[0],
                        "status": parts[3] if len(parts) > 3 else "unknown"
                    })
        
        return {
            "status": "success",
            "containers": containers,
            "running": len([c for c in containers if "Up" in c.get("status", "")])
        }
    except Exception as e:
        logger.error(f"»ñÈ¡Docker×´Ì¬Ê§°Ü: {e}")
        return {
            "status": "error",
            "message": str(e),
            "containers": [],
            "running": 0
        }


@router.get("/test/docker/logs/{container}")
async def get_docker_logs(container: str, tail: int = 100):
    """»ñÈ¡DockerÈÝÆ÷ÈÕÖ¾"""
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", str(tail), container],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return {
            "status": "success",
            "container": container,
            "logs": result.stdout + result.stderr
        }
    except Exception as e:
        logger.error(f"»ñÈ¡ÈÝÆ÷ÈÕÖ¾Ê§°Ü: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/distributed/deploy")
async def deploy_distributed_sybil(request: DistributedSybilRequest):
    """²¿Êð·Ö²¼Ê½Å®Î×¹¥»÷µ½¶àÌ¨VPS"""
    task_id = f"sybil-distributed_{int(time.time())}"
    
    # ±£´æÈÎÎñ
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sybil_attack_test 
            (task_id, test_type, target_node, attack_nodes_count, status, description)
            VALUES (%s, 'distributed', %s, %s, 'deploying', %s)
        """, (task_id, request.target_ip, 
              request.nodes_per_server * request.total_servers,
              f"·Ö²¼Ê½¹¥»÷: {request.total_servers}Ì¨·þÎñÆ÷"))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    
    # Éú³É²¿ÊðÅäÖÃ
    deploy_config = {
        "task_id": task_id,
        "target_ip": request.target_ip,
        "target_port": request.target_port,
        "vps_list": request.vps_list,
        "total_servers": request.total_servers,
        "nodes_per_server": request.nodes_per_server
    }
    
    return {
        "status": "success",
        "message": "·Ö²¼Ê½²¿ÊðÅäÖÃÒÑÉú³É",
        "task_id": task_id,
        "deploy_config": deploy_config,
        "next_steps": [
            "1. ÔÚÃ¿Ì¨VPSÉÏ°²×°PythonºÍÒÀÀµ",
            "2. ÉÏ´«distributed_sybil.pyµ½VPS",
            "3. ÔÚÃ¿Ì¨VPSÉÏÖ´ÐÐ: python3 distributed_sybil.py <·þÎñÆ÷±àºÅ>",
            "4. Ê¹ÓÃÌá¹©µÄdeploy.sh½Å±¾×Ô¶¯»¯²¿Êð"
        ]
    }


def update_task_status(task_id: str, status: str, extra_data: dict = None):
    """¸üÐÂÈÎÎñ×´Ì¬"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if extra_data:
            cursor.execute("""
                UPDATE sybil_attack_test
                SET status = %s, docker_status = %s
                WHERE task_id = %s
            """, (status, json.dumps(extra_data, ensure_ascii=False), task_id))
        else:
            cursor.execute("""
                UPDATE sybil_attack_test
                SET status = %s
                WHERE task_id = %s
            """, (status, task_id))
        conn.commit()
    except Exception as e:
        logger.error(f"¸üÐÂÈÎÎñ×´Ì¬Ê§°Ü: {e}")
        conn.rollback()
    finally:
        conn.close()


@router.get("/test/analysis/{task_id}")
async def get_attack_analysis(task_id: str):
    """»ñÈ¡Å®Î×¹¥»÷Ð§¹û·ÖÎö"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT attack_result, docker_status, status
            FROM sybil_attack_test
            WHERE task_id = %s
        """, (task_id,))
        task = cursor.fetchone()
        
        if not task:
            raise HTTPException(status_code=404, detail="ÈÎÎñ²»´æÔÚ")
        
        result = {
            "task_id": task_id,
            "status": task['status'],
            "attack_result": json.loads(task['attack_result']) if task['attack_result'] else None,
            "docker_status": json.loads(task['docker_status']) if task['docker_status'] else None
        }
        
        return {
            "status": "success",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"»ñÈ¡¹¥»÷·ÖÎöÊ§°Ü: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.delete("/test/tasks/{task_id}")
async def delete_sybil_test_task(task_id: str):
    """删除单个女巫攻击测试任务"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 检查任务是否存在
        cursor.execute("SELECT status FROM sybil_attack_test WHERE task_id = %s", (task_id,))
        task = cursor.fetchone()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 如果任务正在运行，先停止Docker环境
        if task['status'] in ['preparing', 'starting_docker', 'attacking', 'verifying']:
            try:
                compose_file = get_docker_compose_path()
                subprocess.run(
                    ["docker-compose", "-f", compose_file, "-p", "dht_test", "down"],
                    cwd=DOCKER_PROJECT_PATH,
                    capture_output=True,
                    timeout=30
                )
            except Exception as e:
                logger.warning(f"停止Docker环境时出错: {e}")
        
        # 删除任务记录
        cursor.execute("DELETE FROM sybil_attack_test WHERE task_id = %s", (task_id,))
        conn.commit()
        
        logger.info(f"已删除测试任务: {task_id}")
        
        return {
            "status": "success",
            "message": "任务已删除",
            "task_id": task_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.delete("/test/tasks")
async def delete_all_sybil_test_tasks():
    """删除所有女巫攻击测试任务（清空历史）"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 先停止所有可能运行的Docker环境
        try:
            compose_file = get_docker_compose_path()
            subprocess.run(
                ["docker-compose", "-f", compose_file, "-p", "dht_test", "down"],
                cwd=DOCKER_PROJECT_PATH,
                capture_output=True,
                timeout=30
            )
        except Exception as e:
            logger.warning(f"停止Docker环境时出错: {e}")
        
        # 删除所有任务记录
        cursor.execute("DELETE FROM sybil_attack_test")
        deleted_count = cursor.rowcount
        conn.commit()
        
        logger.info(f"已删除所有测试任务，共 {deleted_count} 条")
        
        return {
            "status": "success",
            "message": f"已删除 {deleted_count} 个任务",
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"删除所有任务失败: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/test/docker/cleanup")
async def cleanup_docker_environment():
    """清理Docker测试环境（容器、网络、任务记录）"""
    try:
        cleanup_result = {
            "containers_removed": 0,
            "networks_removed": 0,
            "tasks_cleaned": 0,
            "errors": []
        }
        
        # 步骤1: 停止并删除所有Docker容器
        logger.info("开始清理Docker容器...")
        try:
            compose_file = get_docker_compose_path()
            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "-p", "dht_test", "down"],
                cwd=DOCKER_PROJECT_PATH,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("Docker Compose 容器清理成功")
                cleanup_result["containers_removed"] = 11  # 估计值
            else:
                cleanup_result["errors"].append(f"docker-compose down: {result.stderr}")
        except Exception as e:
            cleanup_result["errors"].append(f"清理容器失败: {str(e)}")
            logger.error(f"清理容器失败: {e}")
        
        # 步骤2: 强制删除所有DHT相关容器（兜底方案）
        try:
            # 查找所有相关容器
            ps_result = subprocess.run(
                ["docker", "ps", "-a", "--filter", "name=node-", "--filter", "name=attacker", "--format", "{{.ID}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if ps_result.stdout.strip():
                container_ids = ps_result.stdout.strip().split('\n')
                for cid in container_ids:
                    subprocess.run(["docker", "rm", "-f", cid], capture_output=True, timeout=10)
                    cleanup_result["containers_removed"] += 1
        except Exception as e:
            cleanup_result["errors"].append(f"强制删除容器失败: {str(e)}")
        
        # 步骤3: 清理Docker网络
        try:
            # 删除dht_test_dht_net网络
            net_result = subprocess.run(
                ["docker", "network", "rm", "dht_test_dht_net"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if net_result.returncode == 0:
                cleanup_result["networks_removed"] = 1
                logger.info("Docker网络已删除")
        except Exception as e:
            # 网络可能已经不存在，这不算错误
            logger.info(f"网络清理: {e}")
        
        # 步骤4: 清理数据库中的测试任务（可选，标记为已清理而不是删除）
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 将所有运行中或准备中的任务标记为已停止
            cursor.execute("""
                UPDATE sybil_attack_test
                SET status = 'cleaned', stop_time = NOW()
                WHERE status IN ('preparing', 'starting_docker', 'attacking', 'verifying')
            """)
            
            cleanup_result["tasks_cleaned"] = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"清理了 {cleanup_result['tasks_cleaned']} 个未完成的任务")
        except Exception as e:
            cleanup_result["errors"].append(f"清理任务记录失败: {str(e)}")
            logger.error(f"清理任务记录失败: {e}")
        
        # 返回清理结果
        return {
            "status": "success",
            "message": "环境清理完成",
            "details": cleanup_result
        }
        
    except Exception as e:
        logger.error(f"清理环境失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
