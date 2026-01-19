# -*- coding: utf-8 -*-
"""
任务执行器模块
负责管理攻击脚本的启动、停止和监控
"""

import subprocess
import threading
import logging
import os
import sys
import signal
import psutil
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# 全局任务进程管理字典
task_processes: Dict[str, subprocess.Popen] = {}
task_threads: Dict[str, threading.Thread] = {}
task_lock = threading.Lock()


class TaskExecutor:
    """任务执行器基类"""
    
    def __init__(self, task_id: str, script_name: str):
        self.task_id = task_id
        self.script_name = script_name
        self.stopped_manually = False  # 标记是否手动停止
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.script_path = os.path.join(self.script_dir, script_name)
        self.process: Optional[subprocess.Popen] = None
        
    def start(self, *args, **kwargs):
        """启动任务"""
        raise NotImplementedError("子类必须实现start方法")
    
    def stop(self):
        """停止任务"""
        if self.process and self.process.poll() is None:
            try:
                # 标记为手动停止
                self.stopped_manually = True
                # 先尝试温柔地终止进程
                if sys.platform == 'win32':
                    self.process.terminate()
                else:
                    os.kill(self.process.pid, signal.SIGTERM)
                
                # 等待进程结束（最多等待5秒）
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # 强制杀死进程
                    self.process.kill()
                    self.process.wait()
                
                logger.info(f"任务 {self.task_id} 已停止")
                return True
            except Exception as e:
                logger.error(f"停止任务 {self.task_id} 失败: {e}")
                return False
        return False
    
    def is_running(self) -> bool:
        """检查任务是否正在运行"""
        return self.process is not None and self.process.poll() is None


class PortConsumeExecutor(TaskExecutor):
    """端口资源消耗攻击执行器"""
    
    def __init__(self, task_id: str):
        super().__init__(task_id, "port.py")
    
    def start(self, ip: str, port: int, threads: int = 100, callback=None):
        """
        启动端口资源消耗攻击
        
        Args:
            ip: 目标IP
            port: 目标端口
            threads: 线程数
            callback: 回调函数，用于更新任务状态
        """
        def run_task():
            try:
                logger.info(f"启动端口资源消耗攻击: {ip}:{port}, 线程数: {threads}")
                
                # 构建命令
                cmd = [
                    sys.executable,  # Python解释器
                    '-u',  # 无缓冲模式，确保实时输出
                    self.script_path,
                    str(ip),
                    str(port),
                    '-t', str(threads),  # 使用-t参数指定线程数
                    '-y'  # 自动确认，跳过交互式确认
                ]
                
                # 启动子进程
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    bufsize=1  # 行缓冲
                )
                
                with task_lock:
                    task_processes[self.task_id] = self.process
                
                if callback:
                    callback(self.task_id, "运行中", f"端口攻击任务已启动: {ip}:{port}")
                
                # 读取输出直到进程停止
                while self.process.poll() is None:
                    line = self.process.stdout.readline()
                    if line:
                        logger.info(f"[{self.task_id}] {line.strip()}")
                
                # 读取stderr获取错误信息
                stderr_output = self.process.stderr.read()
                if stderr_output:
                    logger.error(f"[{self.task_id}] 错误输出: {stderr_output}")
                
                # 检查返回码
                returncode = self.process.returncode
                if returncode == 0:
                    logger.info(f"任务 {self.task_id} 正常完成")
                    if callback:
                        callback(self.task_id, "已完成", "任务正常结束")
                elif self.stopped_manually:
                    # 手动停止，不显示异常
                    logger.info(f"任务 {self.task_id} 已停止")
                    if callback:
                        callback(self.task_id, "已停止", "任务已停止")
            except Exception as e:
                logger.error(f"执行任务 {self.task_id} 时出错: {e}")
                if callback:
                    callback(self.task_id, "错误", f"执行出错: {str(e)}")
            finally:
                with task_lock:
                    if self.task_id in task_processes:
                        del task_processes[self.task_id]
        
        # 在后台线程中运行任务
        thread = threading.Thread(target=run_task, daemon=True)
        thread.start()
        
        with task_lock:
            task_threads[self.task_id] = thread


class SynFloodExecutor(TaskExecutor):
    """SYN洪水攻击任务执行器"""
    
    def __init__(self, task_id: str):
        super().__init__(task_id, "stack.py")
    
    def start(self, ip: str, port: int, threads: int = 50, duration: int = 60, rate: int = 1000, callback=None):
        """
        启动SYN洪水攻击
        
        Args:
            ip: 目标IP
            port: 目标端口
            threads: 线程数
            duration: 持续时间（秒）
            rate: 速率（包/秒）
            callback: 回调函数
        """
        def run_task():
            try:
                logger.info(f"启动SYN洪水攻击: {ip}:{port}, 持续{duration}秒")
                
                cmd = [
                    sys.executable,
                    '-u',  # 无缓冲模式，确保实时输出
                    self.script_path,
                    str(ip),
                    str(port),
                    '-t', str(threads),  # 使用-t参数指定线程数
                    '--duration', str(duration),  # 使用--duration参数指定持续时间
                    '--rate', str(rate),  # 使用--rate参数指定速率
                    '-y'  # 自动确认，跳过交互式确认
                ]
                
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    bufsize=1  # 行缓冲
                )
                
                with task_lock:
                    task_processes[self.task_id] = self.process
                
                if callback:
                    callback(self.task_id, "运行中", f"SYN洪水攻击已启动: {ip}:{port}")
                
                # 读取输出
                while self.process.poll() is None:
                    line = self.process.stdout.readline()
                    if line:
                        logger.info(f"[{self.task_id}] {line.strip()}")
                
                # 读取stderr获取错误信息
                stderr_output = self.process.stderr.read()
                if stderr_output:
                    logger.error(f"[{self.task_id}] 错误输出: {stderr_output}")
                
                returncode = self.process.returncode
                if returncode == 0:
                    logger.info(f"任务 {self.task_id} 正常完成")
                    if callback:
                        callback(self.task_id, "已完成", "任务正常结束")
                elif self.stopped_manually:
                    # 手动停止，不显示异常
                    logger.info(f"任务 {self.task_id} 已停止")
                    if callback:
                        callback(self.task_id, "已停止", "任务已停止")

            except Exception as e:
                logger.error(f"执行任务 {self.task_id} 时出错: {e}")
                if callback:
                    callback(self.task_id, "错误", f"执行出错: {str(e)}")
            finally:
                with task_lock:
                    if self.task_id in task_processes:
                        del task_processes[self.task_id]
        
        thread = threading.Thread(target=run_task, daemon=True)
        thread.start()
        
        with task_lock:
            task_threads[self.task_id] = thread


def stop_task(task_id: str) -> bool:
    """
    停止指定任务
    
    Args:
        task_id: 任务ID
    
    Returns:
        bool: 是否成功停止
    """
    with task_lock:
        if task_id in task_processes:
            process = task_processes[task_id]
            try:
                if process.poll() is None:
                    # 进程还在运行，终止它
                    if sys.platform == 'win32':
                        process.terminate()
                    else:
                        os.kill(process.pid, signal.SIGTERM)
                    
                    # 等待进程结束
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    
                    logger.info(f"任务 {task_id} 已停止")
                    return True
            except Exception as e:
                logger.error(f"停止任务 {task_id} 失败: {e}")
                return False
            finally:
                del task_processes[task_id]
        else:
            logger.warning(f"任务 {task_id} 不存在或已停止")
            return False


def get_running_tasks() -> Dict[str, Dict]:
    """
    获取当前正在运行的任务
    
    Returns:
        Dict: 任务ID -> 任务信息
    """
    with task_lock:
        running = {}
        for task_id, process in list(task_processes.items()):
            if process.poll() is None:
                # 获取进程信息
                try:
                    p = psutil.Process(process.pid)
                    running[task_id] = {
                        'pid': process.pid,
                        'status': 'running',
                        'cpu_percent': p.cpu_percent(),
                        'memory_mb': p.memory_info().rss / 1024 / 1024
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    running[task_id] = {
                        'pid': process.pid,
                        'status': 'running'
                    }
            else:
                # 进程已结束，从字典中移除
                del task_processes[task_id]
        
        return running


def cleanup_finished_tasks():
    """清理已完成的任务"""
    with task_lock:
        finished = []
        for task_id, process in list(task_processes.items()):
            if process.poll() is not None:
                finished.append(task_id)
        
        for task_id in finished:
            del task_processes[task_id]
            logger.info(f"清理已结束任务: {task_id}")
