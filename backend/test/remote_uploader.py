#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
远端日志上传脚本
部署在远端蜜罐服务器上，定期收集日志并上传到本地服务器
"""

import requests
import time
import os
import sys
from datetime import datetime
from typing import List, Optional
import logging

# ============================================================
# 配置区域 - 请根据实际情况修改
# ============================================================

# 本地服务器配置
LOCAL_SERVER_HOST = "your-local-server-ip"  # 修改为本地服务器的公网IP或域名
LOCAL_SERVER_PORT = 8000
API_ENDPOINT = f"http://{LOCAL_SERVER_HOST}:{LOCAL_SERVER_PORT}/api/upload-logs"

# API密钥（必须与本地服务器的config.py中的API_KEY一致）
API_KEY = "your-secret-api-key-change-this-in-production"

# 僵尸网络类型（根据实际蜜罐类型修改）
BOTNET_TYPE = "mozi"  # 可选: asruex, mozi, andromeda, moobot, ramnit, leethozer

# 日志文件路径（远端蜜罐生成的日志文件）
LOG_FILE_PATH = "/var/log/honeypot/botnet.log"  # 修改为实际日志路径

# 上传配置
UPLOAD_INTERVAL = 300  # 上传间隔（秒），默认5分钟
BATCH_SIZE = 1000      # 每次上传的最大行数
MAX_RETRIES = 3        # 上传失败重试次数
RETRY_DELAY = 30       # 重试延迟（秒）

# 状态文件（记录已上传的行数，避免重复上传）
STATE_FILE = "/tmp/uploader_state.txt"

# ============================================================
# 日志配置
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/remote_uploader.log')
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# 核心功能
# ============================================================

class LogUploader:
    """日志上传器"""
    
    def __init__(self):
        self.last_position = self.load_state()
        self.upload_count = 0
        self.error_count = 0
        
    def load_state(self) -> int:
        """加载上次上传的位置"""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    position = int(f.read().strip())
                    logger.info(f"加载状态: 上次上传位置 {position}")
                    return position
        except Exception as e:
            logger.warning(f"加载状态失败: {e}，从头开始")
        return 0
    
    def save_state(self, position: int):
        """保存当前上传位置"""
        try:
            with open(STATE_FILE, 'w') as f:
                f.write(str(position))
            logger.debug(f"保存状态: 位置 {position}")
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    def read_new_logs(self) -> Optional[List[str]]:
        """读取新增的日志行"""
        try:
            if not os.path.exists(LOG_FILE_PATH):
                logger.warning(f"日志文件不存在: {LOG_FILE_PATH}")
                return None
            
            with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
                # 跳到上次读取的位置
                f.seek(self.last_position)
                
                # 读取新行
                new_lines = []
                for line in f:
                    line = line.strip()
                    if line:  # 跳过空行
                        new_lines.append(line)
                    
                    # 限制批量大小
                    if len(new_lines) >= BATCH_SIZE:
                        break
                
                # 更新位置
                new_position = f.tell()
                
                if new_lines:
                    logger.info(f"读取到 {len(new_lines)} 条新日志")
                    return new_lines, new_position
                else:
                    logger.debug("没有新日志")
                    return None, self.last_position
                    
        except Exception as e:
            logger.error(f"读取日志失败: {e}")
            return None, self.last_position
    
    def upload_logs(self, logs: List[str]) -> bool:
        """上传日志到本地服务器"""
        if not logs:
            return True
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        }
        
        data = {
            "botnet_type": BOTNET_TYPE,
            "logs": logs,
            "source_ip": self.get_local_ip()
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"上传 {len(logs)} 条日志 (尝试 {attempt + 1}/{MAX_RETRIES})")
                
                response = requests.post(
                    API_ENDPOINT,
                    json=data,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ 上传成功: {result['received_count']} 条")
                    self.upload_count += result['received_count']
                    return True
                    
                elif response.status_code == 401:
                    logger.error("❌ 认证失败: API密钥无效")
                    return False
                    
                elif response.status_code == 403:
                    logger.error("❌ 权限不足: IP未在白名单中")
                    return False
                    
                else:
                    logger.warning(f"⚠️ 上传失败 (HTTP {response.status_code}): {response.text}")
                    
            except requests.exceptions.ConnectionError:
                logger.warning(f"⚠️ 连接失败，{RETRY_DELAY}秒后重试...")
                
            except requests.exceptions.Timeout:
                logger.warning(f"⚠️ 请求超时，{RETRY_DELAY}秒后重试...")
                
            except Exception as e:
                logger.error(f"⚠️ 上传异常: {e}")
            
            # 重试延迟
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
        
        # 所有重试都失败
        logger.error(f"❌ 上传失败: 已重试 {MAX_RETRIES} 次")
        self.error_count += 1
        return False
    
    def get_local_ip(self) -> str:
        """获取本机IP"""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "unknown"
    
    def run_once(self):
        """执行一次上传任务"""
        logger.info("-" * 60)
        logger.info("开始执行上传任务")
        
        # 读取新日志
        result = self.read_new_logs()
        if result is None:
            return
        
        logs, new_position = result
        
        if not logs:
            logger.info("没有新日志需要上传")
            return
        
        # 上传日志
        success = self.upload_logs(logs)
        
        if success:
            # 更新位置
            self.last_position = new_position
            self.save_state(new_position)
            logger.info(f"任务完成，累计上传: {self.upload_count} 条")
        else:
            logger.error("上传失败，位置不更新，下次将重试")
    
    def run_forever(self):
        """持续运行"""
        logger.info("=" * 60)
        logger.info("远端日志上传器启动")
        logger.info("=" * 60)
        logger.info(f"目标服务器: {API_ENDPOINT}")
        logger.info(f"僵尸网络类型: {BOTNET_TYPE}")
        logger.info(f"日志文件: {LOG_FILE_PATH}")
        logger.info(f"上传间隔: {UPLOAD_INTERVAL} 秒")
        logger.info(f"批量大小: {BATCH_SIZE} 条")
        logger.info("=" * 60)
        
        while True:
            try:
                self.run_once()
            except KeyboardInterrupt:
                logger.info("\n收到中断信号，正在退出...")
                break
            except Exception as e:
                logger.error(f"任务执行异常: {e}")
                self.error_count += 1
            
            # 等待下次执行
            logger.info(f"等待 {UPLOAD_INTERVAL} 秒后执行下次上传...")
            time.sleep(UPLOAD_INTERVAL)
        
        # 退出统计
        logger.info("=" * 60)
        logger.info("上传器已停止")
        logger.info(f"累计上传: {self.upload_count} 条")
        logger.info(f"错误次数: {self.error_count}")
        logger.info("=" * 60)


# ============================================================
# 命令行模式
# ============================================================

def test_connection():
    """测试连接"""
    print("测试连接到本地服务器...")
    print(f"目标: {API_ENDPOINT}")
    
    try:
        status_url = f"http://{LOCAL_SERVER_HOST}:{LOCAL_SERVER_PORT}/api/upload-status"
        response = requests.get(status_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 连接成功!")
            print(f"服务器状态: {data['api_status']}")
            print(f"服务器时间: {data['timestamp']}")
            return True
        else:
            print(f"❌ 连接失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


def test_upload():
    """测试上传一条日志"""
    print("\n测试上传功能...")
    
    test_log = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},1.2.3.4,test,remote_upload_test"
    
    uploader = LogUploader()
    success = uploader.upload_logs([test_log])
    
    if success:
        print("✅ 上传测试成功!")
        return True
    else:
        print("❌ 上传测试失败!")
        return False


def main():
    """主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            # 测试模式
            print("=" * 60)
            print("  远端上传器 - 测试模式")
            print("=" * 60)
            
            # 测试连接
            conn_ok = test_connection()
            if not conn_ok:
                print("\n请检查:")
                print("  1. LOCAL_SERVER_HOST 是否正确？")
                print("  2. 本地服务器是否运行？")
                print("  3. 防火墙是否开放端口？")
                sys.exit(1)
            
            # 测试上传
            upload_ok = test_upload()
            if not upload_ok:
                print("\n请检查:")
                print("  1. API_KEY 是否正确？")
                print("  2. 远端IP是否在白名单中？")
                sys.exit(1)
            
            print("\n🎉 所有测试通过！可以运行正式模式")
            print(f"\n启动命令: python {sys.argv[0]}")
            
        elif command == "once":
            # 单次执行
            uploader = LogUploader()
            uploader.run_once()
            
        else:
            print(f"未知命令: {command}")
            print(f"用法:")
            print(f"  python {sys.argv[0]}       - 持续运行")
            print(f"  python {sys.argv[0]} test  - 测试连接")
            print(f"  python {sys.argv[0]} once  - 单次执行")
    else:
        # 持续运行模式
        uploader = LogUploader()
        uploader.run_forever()


if __name__ == "__main__":
    main()





