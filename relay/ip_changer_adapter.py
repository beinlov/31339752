#!/usr/bin/env python3
"""
IP切换适配器
将现有的changeip.py集成到relay服务中
支持暂停/恢复回调，与relay_service协调工作
"""

import os
import sys
import time
import logging
import threading
from typing import Callable, Optional

# 导入现有的changeip模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import changeip

logger = logging.getLogger(__name__)


class IPChangerAdapter:
    """IP切换适配器 - 封装changeip.py的功能"""
    
    def __init__(self, config: dict, pause_callback: Callable = None, resume_callback: Callable = None):
        """
        初始化IP切换适配器
        
        Args:
            config: IP切换配置
            pause_callback: IP切换前调用的暂停函数
            resume_callback: IP切换后调用的恢复函数
        """
        self.enabled = config.get('enabled', True)
        self.interval = config.get('change_interval', 600)  # 默认10分钟
        self.resume_delay = config.get('resume_delay', 30)
        
        # 回调函数
        self.pause_callback = pause_callback
        self.resume_callback = resume_callback
        
        # 运行状态
        self.running = False
        self.thread = None
        
        # 统计
        self.stats = {
            'total_changes': 0,
            'last_change_time': None,
            'current_ip': None,
            'errors': 0
        }
        
        logger.info("=" * 70)
        logger.info("IP切换适配器初始化")
        logger.info("=" * 70)
        logger.info(f"启用状态: {self.enabled}")
        logger.info(f"切换间隔: {self.interval} 秒")
        logger.info("=" * 70)
    
    def change_ip_with_callback(self):
        """执行IP切换（带回调）"""
        from datetime import datetime
        
        logger.info("\n" + "=" * 70)
        logger.info(f"开始IP切换流程 - {datetime.now()}")
        logger.info("=" * 70)
        
        try:
            # 1. 暂停服务
            if self.pause_callback:
                logger.info("暂停中转服务...")
                self.pause_callback()
            
            # 2. 等待AWS连通性
            changeip.wait_for_aws_connectivity()
            
            # 3. 获取新IP
            new_ip, allocation_id = changeip.get_new_ip()
            if not new_ip:
                logger.error("无法获取新IP，跳过本轮切换")
                if self.resume_callback:
                    self.resume_callback()
                return False
            
            # 4. 绑定IP
            changeip.associate_ip(new_ip, allocation_id)
            
            # 5. 更新OpenVPN配置并重启
            changeip.update_ovpn_config(new_ip)
            changeip.restart_openvpn()
            
            # 6. 等待网络恢复
            logger.info(f"等待网络恢复... ({self.resume_delay}秒)")
            time.sleep(self.resume_delay)
            changeip.wait_for_aws_connectivity()
            
            # 7. 恢复服务
            if self.resume_callback:
                logger.info("恢复中转服务...")
                self.resume_callback()
            
            # 8. 更新统计
            self.stats['total_changes'] += 1
            self.stats['last_change_time'] = datetime.now()
            self.stats['current_ip'] = new_ip
            
            logger.info("=" * 70)
            logger.info(f"✅ IP切换完成: {new_ip}")
            logger.info(f"总切换次数: {self.stats['total_changes']}")
            logger.info("=" * 70)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ IP切换异常: {e}", exc_info=True)
            self.stats['errors'] += 1
            
            # 确保恢复服务
            if self.resume_callback:
                self.resume_callback()
            
            return False
    
    def run_loop(self):
        """IP切换主循环"""
        logger.info("IP切换循环启动")
        
        # 初始化：获取现有EIP
        changeip.fetch_existing_eips()
        
        # 首次切换前等待
        logger.info(f"等待 {self.interval} 秒后开始首次IP切换...")
        
        while self.running:
            time.sleep(self.interval)
            
            if not self.running:
                break
            
            try:
                self.change_ip_with_callback()
            except Exception as e:
                logger.error(f"IP切换循环异常: {e}", exc_info=True)
                self.stats['errors'] += 1
        
        logger.info("IP切换循环停止")
    
    def start(self):
        """启动IP切换线程"""
        if not self.enabled:
            logger.info("IP切换功能未启用，跳过")
            return
        
        if self.running:
            logger.warning("IP切换线程已在运行")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self.run_loop, daemon=True)
        self.thread.start()
        
        logger.info("✅ IP切换线程已启动")
    
    def stop(self):
        """停止IP切换线程"""
        if not self.running:
            return
        
        logger.info("停止IP切换线程...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=10)
        
        logger.info("✅ IP切换线程已停止")
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            **self.stats,
            'running': self.running,
            'enabled': self.enabled,
            'eip_count': len(changeip.allocated_ips)
        }
