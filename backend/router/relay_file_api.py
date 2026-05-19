# -*- coding: utf-8 -*-
"""
中继节点文件API模块 - 基于文件系统的命令下发和状态读取

工作原理:
1. 平台通过SSH/SMB/HTTP将命令文件写入中继位置的 commands/ 目录
2. 平台定时读取中继位置 status/ 目录的状态文件
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import paramiko
import json
import os
import time
import logging
from datetime import datetime
from config import TCP_RST_CONFIG
from router.suppression import get_db_connection

router = APIRouter()
logger = logging.getLogger(__name__)

class TcpSynAttackRequest(BaseModel):
    """TCP SYN洪水攻击请求"""
    target_ip: str
    target_port: int
    capture_interface: Optional[str] = None
    inject_interface: Optional[str] = None

class RelayFileManager:
    """中继文件管理器 - 通过SSH/SFTP操作远程文件"""
    
    def __init__(self, host: str, port: int, username: str, password: str, share_path: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.share_path = share_path
        
    def _get_sftp_client(self):
        """获取SFTP客户端"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host, port=self.port, username=self.username, password=self.password)
        return ssh.open_sftp(), ssh
        
    def write_command(self, attack_id: str, command_data: dict) -> bool:
        """写入命令文件到中继位置"""
        try:
            sftp, ssh = self._get_sftp_client()
            
            # 命令文件路径
            remote_file = f"{self.share_path}/commands/{attack_id}_{int(datetime.now().timestamp())}.json"
            
            # 写入命令
            with sftp.open(remote_file, 'w') as f:
                f.write(json.dumps(command_data, indent=2, ensure_ascii=False))
                
            logger.info(f"命令文件已写入: {remote_file}")
            
            sftp.close()
            ssh.close()
            return True
            
        except Exception as e:
            logger.error(f"写入命令文件失败: {e}")
            return False
            
    def read_status(self, attack_id: str) -> Optional[dict]:
        """读取攻击状态文件"""
        try:
            sftp, ssh = self._get_sftp_client()
            
            # 状态文件路径
            status_file = f"{self.share_path}/status/{attack_id}_status.json"
            attack_file = f"{self.share_path}/status/{attack_id}_attack.json"
            
            result = {}
            
            # 读取连接状态
            try:
                with sftp.open(status_file, 'r') as f:
                    result['connections'] = json.load(f)
            except FileNotFoundError:
                result['connections'] = None
                
            # 读取攻击状态
            try:
                with sftp.open(attack_file, 'r') as f:
                    result['attack'] = json.load(f)
            except FileNotFoundError:
                result['attack'] = None
                
            sftp.close()
            ssh.close()
            
            return result if result.get('connections') or result.get('attack') else None
            
        except Exception as e:
            logger.error(f"读取状态文件失败: {e}")
            return None
            
    def list_all_status(self) -> List[dict]:
        """列出所有状态文件"""
        try:
            sftp, ssh = self._get_sftp_client()
            
            status_dir = f"{self.share_path}/status"
            files = sftp.listdir(status_dir)
            
            all_status = []
            for filename in files:
                if filename.endswith('_status.json'):
                    try:
                        with sftp.open(f"{status_dir}/{filename}", 'r') as f:
                            all_status.append(json.load(f))
                    except Exception as e:
                        logger.error(f"读取文件 {filename} 失败: {e}")
                        
            sftp.close()
            ssh.close()
            
            return all_status
            
        except Exception as e:
            logger.error(f"列出状态文件失败: {e}")
            return []

# 全局文件管理器实例
relay_manager = None

def init_relay_manager():
    """初始化中继文件管理器"""
    global relay_manager
    try:
        relay_manager = RelayFileManager(
            host=TCP_RST_CONFIG['host'],
            port=TCP_RST_CONFIG.get('port', 22),
            username=TCP_RST_CONFIG['username'],
            password=TCP_RST_CONFIG['password'],
            share_path=TCP_RST_CONFIG['share_path']
        )
        logger.info("TCP RST攻击中继文件管理器初始化成功")
    except KeyError as e:
        logger.error(f"配置缺少必要字段: {e}")
    except Exception as e:
        logger.error(f"初始化中继文件管理器失败: {e}")

@router.post("/relay-file/attack/start")
async def start_attack_via_file(request: TcpSynAttackRequest):
    """通过文件下发启动攻击命令"""
    if not relay_manager:
        raise HTTPException(status_code=500, detail="中继文件管理器未初始化")
        
    try:
        attack_id = f"tcp-syn-{int(datetime.now().timestamp())}"
        task_id = f"tcp-rst_{request.target_ip}_{request.target_port}_{int(datetime.now().timestamp())}"
        
        command_data = {
            'type': 'start_attack',
            'attack_id': attack_id,
            'target_ip': request.target_ip,
            'target_port': request.target_port,
            'capture_interface': request.capture_interface,
            'inject_interface': request.inject_interface,
            'timestamp': datetime.now().isoformat()
        }
        
        # 保存到数据库
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tcp_rst_task 
                (task_id, attack_id, target_ip, target_port, capture_interface, inject_interface, status, start_time)
                VALUES (%s, %s, %s, %s, %s, %s, 'running', NOW())
            """, (task_id, attack_id, request.target_ip, request.target_port, 
                  request.capture_interface, request.inject_interface))
            conn.commit()
            logger.info(f"TCP RST攻击任务已保存到数据库: {task_id}")
        except Exception as db_error:
            logger.error(f"保存任务到数据库失败: {db_error}")
            conn.rollback()
        finally:
            conn.close()
        
        # 写入命令文件到中继节点
        success = relay_manager.write_command(attack_id, command_data)
        
        if success:
            return {
                'status': 'success',
                'message': '攻击命令已下发',
                'attack_id': attack_id,
                'task_id': task_id
            }
        else:
            raise HTTPException(status_code=500, detail="写入命令文件失败")
            
    except Exception as e:
        logger.error(f"下发攻击命令失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/relay-file/attack/stop")
async def stop_attack_via_file(attack_id: str):
    """通过文件下发停止攻击命令"""
    if not relay_manager:
        raise HTTPException(status_code=500, detail="中继文件管理器未初始化")
        
    try:
        # 更新数据库状态
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tcp_rst_task
                SET status = 'stopped', stop_time = NOW()
                WHERE attack_id = %s AND status = 'running'
            """, (attack_id,))
            conn.commit()
            logger.info(f"TCP RST攻击任务已更新为stopped: {attack_id}")
        except Exception as db_error:
            logger.error(f"更新任务状态失败: {db_error}")
            conn.rollback()
        finally:
            conn.close()
        
        # 写入停止命令到中继节点
        command_data = {
            'type': 'stop_attack',
            'attack_id': attack_id,
            'timestamp': datetime.now().isoformat()
        }
        
        success = relay_manager.write_command(attack_id, command_data)
        
        if success:
            return {
                'status': 'success',
                'message': '停止命令已下发',
                'attack_id': attack_id
            }
        else:
            raise HTTPException(status_code=500, detail="写入命令文件失败")
            
    except Exception as e:
        logger.error(f"下发停止命令失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/relay-file/attack/{attack_id}/status")
async def get_attack_status_from_file(attack_id: str):
    """从文件读取攻击状态"""
    if not relay_manager:
        raise HTTPException(status_code=500, detail="中继文件管理器未初始化")
        
    try:
        status = relay_manager.read_status(attack_id)
        
        if status:
            return {
                'status': 'success',
                'data': status
            }
        else:
            return {
                'status': 'not_found',
                'message': '状态文件不存在或尚未生成'
            }
            
    except Exception as e:
        logger.error(f"读取状态文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/relay-file/status/all")
async def get_all_status_from_file():
    """读取所有攻击状态"""
    if not relay_manager:
        raise HTTPException(status_code=500, detail="中继文件管理器未初始化")
        
    try:
        all_status = relay_manager.list_all_status()
        
        return {
            'status': 'success',
            'data': all_status,
            'count': len(all_status)
        }
            
    except Exception as e:
        logger.error(f"读取所有状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/relay-file/health")
async def check_relay_connection():
    """检查中继连接健康状态"""
    if not relay_manager:
        return {
            'status': 'error',
            'message': '中继文件管理器未初始化'
        }
        
    try:
        # 尝试连接并列出目录
        sftp, ssh = relay_manager._get_sftp_client()
        files = sftp.listdir(relay_manager.share_path)
        sftp.close()
        ssh.close()
        
        return {
            'status': 'healthy',
            'message': '中继连接正常',
            'share_path': relay_manager.share_path,
            'files_count': len(files)
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'中继连接异常: {str(e)}'
        }

class DeployProgress(BaseModel):
    """部署进度"""
    step: str
    status: str  # running, success, error
    message: str
    timestamp: str

@router.post("/relay-file/deploy")
async def deploy_relay_node():
    """一键部署中继节点服务
    
    自动执行：
    1. 创建目录结构
    2. 上传脚本文件
    3. 安装依赖
    4. 设置权限
    5. 启动服务
    """
    if not relay_manager:
        raise HTTPException(status_code=500, detail="中继文件管理器未初始化，请检查config.py配置")
    
    progress_log = []
    
    def log_progress(step: str, status: str, message: str):
        progress_log.append({
            'step': step,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        logger.info(f"[部署] {step}: {message}")
    
    try:
        # 建立SSH连接
        log_progress("连接SSH", "running", f"正在连接到 {relay_manager.host}:{relay_manager.port}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            relay_manager.host,
            port=relay_manager.port,
            username=relay_manager.username,
            password=relay_manager.password,
            timeout=10
        )
        log_progress("连接SSH", "success", "SSH连接成功")
        
        # 步骤1: 创建目录结构
        log_progress("创建目录", "running", "正在创建中继节点目录...")
        commands = [
            "mkdir -p /opt/relay_scripts",
            "mkdir -p /opt/relay_share/commands",
            "mkdir -p /opt/relay_share/status",
            "mkdir -p /opt/relay_share/processed",
            f"chown -R {relay_manager.username}:{relay_manager.username} /opt/relay_scripts",
            f"chown -R {relay_manager.username}:{relay_manager.username} /opt/relay_share"
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(f"sudo {cmd}")
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error_msg = stderr.read().decode('utf-8')
                log_progress("创建目录", "error", f"命令失败: {cmd}, 错误: {error_msg}")
                raise Exception(f"创建目录失败: {error_msg}")
        
        log_progress("创建目录", "success", "目录结构创建成功")
        
        # 步骤2: 上传脚本文件
        log_progress("上传脚本", "running", "正在上传攻击脚本...")
        sftp = ssh.open_sftp()
        
        # 获取本地脚本路径
        script_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'suppression_scripts')
        files_to_upload = [
            ('relay_node_file_monitor.py', '/opt/relay_scripts/relay_node_file_monitor.py'),
            ('tcp_rst.py', '/opt/relay_scripts/tcp_rst.py')
        ]
        
        for local_file, remote_file in files_to_upload:
            local_path = os.path.join(script_dir, local_file)
            if not os.path.exists(local_path):
                log_progress("上传脚本", "error", f"本地文件不存在: {local_path}")
                raise Exception(f"本地文件不存在: {local_path}")
            
            sftp.put(local_path, remote_file)
            log_progress("上传脚本", "running", f"已上传: {local_file}")
        
        sftp.close()
        log_progress("上传脚本", "success", "脚本文件上传成功")
        
        # 步骤3: 安装依赖
        log_progress("安装依赖", "running", "正在安装Python依赖包...")
        
        # 检查并安装pip
        stdin, stdout, stderr = ssh.exec_command("which pip3")
        if stdout.channel.recv_exit_status() != 0:
            log_progress("安装依赖", "running", "pip3未安装，正在安装...")
            ssh.exec_command("sudo apt-get update && sudo apt-get install -y python3-pip")
        
        # 安装Python包
        install_cmd = "pip3 install watchdog scapy --user"
        stdin, stdout, stderr = ssh.exec_command(install_cmd)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error_msg = stderr.read().decode('utf-8')
            log_progress("安装依赖", "warning", f"pip安装可能有警告: {error_msg[:200]}")
        
        log_progress("安装依赖", "success", "Python依赖安装成功")
        
        # 步骤4: 设置网络权限
        log_progress("设置权限", "running", "正在设置网络抓包权限...")
        
        cap_cmd = "sudo setcap cap_net_raw,cap_net_admin=eip $(which python3)"
        stdin, stdout, stderr = ssh.exec_command(cap_cmd)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error_msg = stderr.read().decode('utf-8')
            log_progress("设置权限", "warning", f"权限设置警告: {error_msg[:200]}")
        else:
            log_progress("设置权限", "success", "网络权限设置成功")
        
        # 步骤5: 获取网络接口
        log_progress("检测接口", "running", "正在检测网络接口...")
        stdin, stdout, stderr = ssh.exec_command("ip -o link show | awk -F': ' '{print $2}' | grep -v lo | head -1")
        interface = stdout.read().decode('utf-8').strip()
        if not interface:
            interface = "eth0"  # 默认值
            log_progress("检测接口", "warning", f"无法检测接口，使用默认: {interface}")
        else:
            log_progress("检测接口", "success", f"检测到网络接口: {interface}")
        
        # 步骤6: 创建systemd服务文件
        log_progress("创建服务", "running", "正在创建systemd服务...")
        
        service_content = f"""[Unit]
Description=TCP RST Relay Node File Monitor Service
After=network.target

[Service]
Type=simple
User={relay_manager.username}
Group={relay_manager.username}
WorkingDirectory=/opt/relay_scripts
ExecStart=/usr/bin/python3 /opt/relay_scripts/relay_node_file_monitor.py --share-path /opt/relay_share --interface {interface}
Restart=always
RestartSec=10
StandardOutput=append:/opt/relay_scripts/service.log
StandardError=append:/opt/relay_scripts/service.log

[Install]
WantedBy=multi-user.target
"""
        
        # 写入服务文件
        stdin, stdout, stderr = ssh.exec_command("sudo tee /etc/systemd/system/relay-node.service")
        stdin.write(service_content)
        stdin.channel.shutdown_write()
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0:
            log_progress("创建服务", "warning", "服务文件创建可能有问题，将尝试手动启动")
        else:
            log_progress("创建服务", "success", "systemd服务文件创建成功")
            
            # 重载systemd
            ssh.exec_command("sudo systemctl daemon-reload")
            ssh.exec_command("sudo systemctl enable relay-node")
        
        # 步骤7: 启动服务
        log_progress("启动服务", "running", "正在启动中继节点服务...")
        
        # 先停止可能存在的旧进程
        ssh.exec_command("sudo pkill -f relay_node_file_monitor")
        time.sleep(1)
        
        # 尝试通过systemd启动
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl start relay-node")
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0:
            # systemd启动失败，尝试手动启动
            log_progress("启动服务", "running", "systemd启动失败，尝试手动启动...")
            start_cmd = f"nohup python3 /opt/relay_scripts/relay_node_file_monitor.py --share-path /opt/relay_share --interface {interface} > /opt/relay_scripts/service.log 2>&1 &"
            ssh.exec_command(start_cmd)
            time.sleep(2)
        
        # 检查服务是否运行
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep relay_node_file_monitor | grep -v grep")
        output = stdout.read().decode('utf-8')
        
        if "relay_node_file_monitor" in output:
            log_progress("启动服务", "success", f"中继节点服务启动成功！使用接口: {interface}")
        else:
            log_progress("启动服务", "error", "服务启动失败，请检查日志")
        
        # 步骤8: 验证部署
        log_progress("验证部署", "running", "正在验证部署...")
        time.sleep(2)
        
        # 检查目录
        stdin, stdout, stderr = ssh.exec_command("ls -la /opt/relay_share/")
        dir_output = stdout.read().decode('utf-8')
        
        if "commands" in dir_output and "status" in dir_output:
            log_progress("验证部署", "success", "目录结构验证通过")
        else:
            log_progress("验证部署", "warning", "目录结构可能不完整")
        
        ssh.close()
        
        log_progress("部署完成", "success", f"✅ 中继节点部署成功！服务器: {relay_manager.host}, 接口: {interface}")
        
        return {
            'status': 'success',
            'message': '中继节点部署成功',
            'interface': interface,
            'logs': progress_log
        }
        
    except paramiko.AuthenticationException:
        log_progress("连接SSH", "error", "SSH认证失败，请检查用户名和密码")
        return {
            'status': 'error',
            'message': 'SSH认证失败',
            'logs': progress_log
        }
    except paramiko.SSHException as e:
        log_progress("SSH错误", "error", f"SSH连接错误: {str(e)}")
        return {
            'status': 'error',
            'message': f'SSH错误: {str(e)}',
            'logs': progress_log
        }
    except Exception as e:
        log_progress("未知错误", "error", f"部署失败: {str(e)}")
        logger.exception("部署中继节点失败")
        return {
            'status': 'error',
            'message': str(e),
            'logs': progress_log
        }

@router.get("/relay-file/status")
async def get_relay_node_status():
    """获取中继节点运行状态"""
    if not relay_manager:
        raise HTTPException(status_code=500, detail="中继文件管理器未初始化")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            relay_manager.host,
            port=relay_manager.port,
            username=relay_manager.username,
            password=relay_manager.password,
            timeout=5
        )
        
        # 检查进程
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep relay_node_file_monitor | grep -v grep")
        process_output = stdout.read().decode('utf-8')
        is_running = "relay_node_file_monitor" in process_output
        
        # 获取网络接口
        stdin, stdout, stderr = ssh.exec_command("ip -o link show | awk -F': ' '{print $2}' | grep -v lo")
        interfaces = stdout.read().decode('utf-8').strip().split('\n')
        
        # 检查目录
        stdin, stdout, stderr = ssh.exec_command("test -d /opt/relay_scripts && test -d /opt/relay_share && echo 'exists' || echo 'not_exists'")
        dirs_exist = stdout.read().decode('utf-8').strip() == 'exists'
        
        ssh.close()
        
        return {
            'status': 'success',
            'data': {
                'is_running': is_running,
                'is_deployed': dirs_exist,
                'available_interfaces': interfaces,
                'host': relay_manager.host,
                'share_path': relay_manager.share_path
            }
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }
