#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
接管节点统计数据聚合器启动脚本
用于启动和管理数据聚合服务
"""

import os
import sys
import subprocess
import time
import signal
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'takeover_stats_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TakeoverStatsService:
    def __init__(self):
        self.process = None
        self.aggregator_script = project_root / 'stats_aggregator' / 'takeover_stats_aggregator.py'
        self.pid_file = project_root / 'logs' / 'takeover_stats_aggregator.pid'
        
    def start(self):
        """启动聚合服务"""
        if self.is_running():
            logger.warning("聚合服务已在运行")
            return False
            
        try:
            # 确保日志目录存在
            log_dir = project_root / 'logs'
            log_dir.mkdir(exist_ok=True)
            
            # 启动聚合进程
            cmd = [sys.executable, str(self.aggregator_script)]
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(project_root)
            )
            
            # 保存PID
            with open(self.pid_file, 'w') as f:
                f.write(str(self.process.pid))
            
            logger.info(f"聚合服务已启动，PID: {self.process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"启动聚合服务失败: {e}")
            return False
    
    def stop(self):
        """停止聚合服务"""
        try:
            if self.pid_file.exists():
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                try:
                    os.kill(pid, signal.SIGTERM)
                    logger.info(f"已发送停止信号到进程 {pid}")
                    
                    # 等待进程结束
                    time.sleep(2)
                    
                    # 检查进程是否还在运行
                    try:
                        os.kill(pid, 0)  # 检查进程是否存在
                        logger.warning(f"进程 {pid} 仍在运行，强制终止")
                        os.kill(pid, signal.SIGKILL)
                    except OSError:
                        pass  # 进程已结束
                        
                except OSError as e:
                    logger.warning(f"无法终止进程 {pid}: {e}")
                
                # 删除PID文件
                self.pid_file.unlink()
                
            logger.info("聚合服务已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止聚合服务失败: {e}")
            return False
    
    def restart(self):
        """重启聚合服务"""
        logger.info("重启聚合服务...")
        self.stop()
        time.sleep(1)
        return self.start()
    
    def is_running(self):
        """检查聚合服务是否正在运行"""
        if not self.pid_file.exists():
            return False
            
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # 检查进程是否存在
            os.kill(pid, 0)
            return True
            
        except (OSError, ValueError):
            # 进程不存在或PID文件损坏
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False
    
    def status(self):
        """获取服务状态"""
        if self.is_running():
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            logger.info(f"聚合服务正在运行，PID: {pid}")
            return True
        else:
            logger.info("聚合服务未运行")
            return False
    
    def run_once(self):
        """执行一次数据聚合"""
        try:
            cmd = [sys.executable, str(self.aggregator_script), '--once']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(project_root)
            )
            
            if result.returncode == 0:
                logger.info("单次数据聚合执行成功")
                if result.stdout:
                    logger.info(f"输出: {result.stdout}")
                return True
            else:
                logger.error(f"单次数据聚合执行失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"执行单次聚合失败: {e}")
            return False

def main():
    """主函数"""
    service = TakeoverStatsService()
    
    if len(sys.argv) < 2:
        print("用法: python start_takeover_stats_aggregator.py <command>")
        print("命令:")
        print("  start    - 启动聚合服务")
        print("  stop     - 停止聚合服务")
        print("  restart  - 重启聚合服务")
        print("  status   - 查看服务状态")
        print("  once     - 执行一次数据聚合")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        if service.start():
            print("聚合服务启动成功")
        else:
            print("聚合服务启动失败")
            sys.exit(1)
            
    elif command == 'stop':
        if service.stop():
            print("聚合服务停止成功")
        else:
            print("聚合服务停止失败")
            sys.exit(1)
            
    elif command == 'restart':
        if service.restart():
            print("聚合服务重启成功")
        else:
            print("聚合服务重启失败")
            sys.exit(1)
            
    elif command == 'status':
        service.status()
        
    elif command == 'once':
        if service.run_once():
            print("单次数据聚合执行成功")
        else:
            print("单次数据聚合执行失败")
            sys.exit(1)
            
    else:
        print(f"未知命令: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
