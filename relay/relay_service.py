#!/usr/bin/env python3
"""
中转服务主协调器
协调数据拉取、存储、推送和IP切换
"""

import os
import sys
import json
import logging
import time
import signal
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# 导入本地模块
from data_storage import DataStorage
from data_puller import DataPuller
from data_pusher import DataPusher
from ip_changer_adapter import IPChangerAdapter
from config_loader import load_config, validate_config

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('relay_service.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RelayService:
    """中转服务协调器"""
    
    def __init__(self, config_file: str = 'relay_config.json'):
        """
        初始化中转服务
        
        Args:
            config_file: 配置文件路径
        """
        self.config = self._load_config(config_file)
        self.running = False
        self.paused = False  # IP切换时暂停标志
        
        # 初始化各模块
        self.storage = DataStorage(
            db_file=self.config.get('storage', {}).get('db_file', './relay_cache.db'),
            retention_days=self.config.get('storage', {}).get('retention_days', 7)
        )
        
        self.puller = DataPuller(self.config.get('puller', {}))
        self.pusher = DataPusher(self.config.get('pusher', {}))
        
        # 初始化IP切换适配器（传入暂停/恢复回调）
        self.ip_changer = IPChangerAdapter(
            config=self.config.get('ip_change', {}),
            pause_callback=self.pause,
            resume_callback=self.resume
        )
        
        # 统计信息
        self.stats = {
            'total_pulled': 0,
            'total_pushed': 0,
            'total_failed': 0,
            'cycles': 0,
            'start_time': None,
            'last_pull_time': None,
            'last_push_time': None
        }
        
        # 循环配置
        self.pull_interval = self.config.get('intervals', {}).get('pull', 10)
        self.push_interval = self.config.get('intervals', {}).get('push', 5)
        self.cleanup_interval = self.config.get('intervals', {}).get('cleanup', 3600)
        self.retry_interval = self.config.get('intervals', {}).get('retry', 300)
        
        self.last_cleanup = datetime.now()
        self.last_retry = datetime.now()
        
        logger.info("=" * 70)
        logger.info("中转服务初始化完成")
        logger.info("=" * 70)
        logger.info(f"C2服务器数量: {len(self.puller.c2_servers)}")
        logger.info(f"平台地址: {self.pusher.platform_url}")
        logger.info(f"中转ID: {self.pusher.relay_id}")
        logger.info(f"数据保留: {self.storage.retention_days} 天")
        logger.info(f"拉取间隔: {self.pull_interval} 秒")
        logger.info(f"推送间隔: {self.push_interval} 秒")
        logger.info("=" * 70)
    
    def _load_config(self, config_file: str) -> Dict:
        """加载配置文件（支持环境变量覆盖）"""
        try:
            config = load_config(config_file)
            
            # 验证配置
            if not validate_config(config):
                logger.error("配置验证失败，请检查配置")
                sys.exit(1)
            
            return config
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            sys.exit(1)
    
    def pull_cycle(self):
        """数据拉取循环"""
        if self.paused:
            logger.debug("服务已暂停，跳过拉取")
            return
        
        logger.info("\n" + "=" * 70)
        logger.info(f"开始拉取循环 - {datetime.now()}")
        logger.info("=" * 70)
        
        # 从所有C2服务器拉取数据
        pull_results = self.puller.pull_from_all_servers()
        
        if not pull_results:
            logger.info("无C2服务器返回数据")
            return
        
        # 保存数据到本地存储
        total_saved = 0
        for result in pull_results:
            server_config = result['server_config']
            data = result['data']
            records = data.get('data', [])
            
            if records:
                saved_count = self.storage.save_pulled_data(
                    records,
                    c2_server=data.get('server_id')
                )
                total_saved += saved_count
                
                # 确认C2删除（仅当保存成功）
                if saved_count == len(records):
                    self.puller.confirm_pull(server_config, saved_count)
                else:
                    logger.warning(f"部分数据保存失败，不确认C2删除")
        
        self.stats['total_pulled'] += total_saved
        self.stats['last_pull_time'] = datetime.now()
        
        logger.info(f"拉取循环完成: 共保存 {total_saved} 条记录")
    
    def push_cycle(self):
        """数据推送循环"""
        if self.paused:
            logger.debug("服务已暂停，跳过推送")
            return
        
        logger.info("\n" + "=" * 70)
        logger.info(f"开始推送循环 - {datetime.now()}")
        logger.info("=" * 70)
        
        # 获取待推送数据
        records, record_ids = self.storage.get_pending_data(
            limit=self.config.get('pusher', {}).get('batch_size', 1000)
        )
        
        if not records:
            logger.info("无待推送数据")
            return
        
        # 按botnet_type分组
        grouped = {}
        record_id_map = {}  # botnet_type -> record_ids
        
        for i, record in enumerate(records):
            botnet_type = record.get('botnet_type', 'unknown')
            if botnet_type not in grouped:
                grouped[botnet_type] = []
                record_id_map[botnet_type] = []
            grouped[botnet_type].append(record)
            record_id_map[botnet_type].append(record_ids[i])
        
        logger.info(f"按类型分组: {', '.join([f'{k}({len(v)})' for k, v in grouped.items()])}")
        
        # 推送到平台
        push_results = self.pusher.push_grouped_data(grouped)
        
        # 更新数据状态
        total_pushed = 0
        total_failed = 0
        
        for botnet_type, success in push_results.items():
            ids = record_id_map[botnet_type]
            if success:
                self.storage.mark_as_pushed(ids)
                total_pushed += len(ids)
            else:
                self.storage.mark_as_failed(ids)
                total_failed += len(ids)
        
        self.stats['total_pushed'] += total_pushed
        self.stats['total_failed'] += total_failed
        self.stats['last_push_time'] = datetime.now()
        
        logger.info(f"推送循环完成: 成功 {total_pushed} 条, 失败 {total_failed} 条")
    
    def maintenance_cycle(self):
        """维护循环：清理过期数据、重试失败数据"""
        now = datetime.now()
        
        # 清理过期数据
        if (now - self.last_cleanup).total_seconds() >= self.cleanup_interval:
            logger.info("执行数据清理...")
            deleted = self.storage.cleanup_old_data()
            self.last_cleanup = now
        
        # 重试失败数据
        if (now - self.last_retry).total_seconds() >= self.retry_interval:
            logger.info("重试失败数据...")
            retried = self.storage.retry_failed_data(
                max_retries=self.config.get('pusher', {}).get('max_retries', 3)
            )
            self.last_retry = now
    
    def print_statistics(self):
        """打印统计信息"""
        db_stats = self.storage.get_statistics()
        ip_stats = self.ip_changer.get_stats()
        
        logger.info("\n" + "-" * 70)
        logger.info("服务统计")
        logger.info("-" * 70)
        logger.info(f"运行周期: {self.stats['cycles']}")
        logger.info(f"总拉取: {self.stats['total_pulled']} 条")
        logger.info(f"总推送: {self.stats['total_pushed']} 条")
        logger.info(f"总失败: {self.stats['total_failed']} 条")
        logger.info(f"缓存待推送: {db_stats['pending']} 条")
        logger.info(f"缓存已推送: {db_stats['pushed']} 条")
        logger.info(f"缓存失败: {db_stats['failed']} 条")
        
        if self.stats['start_time']:
            uptime = datetime.now() - self.stats['start_time']
            logger.info(f"运行时间: {uptime}")
        
        # IP切换统计
        if ip_stats['enabled']:
            logger.info(f"IP切换次数: {ip_stats['total_changes']}")
            logger.info(f"当前IP: {ip_stats.get('current_ip', 'N/A')}")
            if ip_stats['last_change_time']:
                logger.info(f"上次切换: {ip_stats['last_change_time']}")
        
        logger.info("-" * 70)
    
    def pause(self):
        """暂停服务（IP切换时）"""
        self.paused = True
        logger.warning("⏸️  服务已暂停（IP切换中）")
    
    def resume(self):
        """恢复服务"""
        self.paused = False
        logger.info("▶️  服务已恢复")
    
    def run(self):
        """运行中转服务主循环"""
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        logger.info("\n" + "=" * 70)
        logger.info("中转服务启动")
        logger.info("=" * 70)
        
        # 启动IP切换器
        self.ip_changer.start()
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        last_pull = datetime.now() - timedelta(seconds=self.pull_interval)
        last_push = datetime.now() - timedelta(seconds=self.push_interval)
        
        try:
            while self.running:
                now = datetime.now()
                self.stats['cycles'] += 1
                
                # 拉取数据
                if (now - last_pull).total_seconds() >= self.pull_interval:
                    try:
                        self.pull_cycle()
                        last_pull = now
                    except Exception as e:
                        logger.error(f"拉取循环异常: {e}", exc_info=True)
                
                # 推送数据
                if (now - last_push).total_seconds() >= self.push_interval:
                    try:
                        self.push_cycle()
                        last_push = now
                    except Exception as e:
                        logger.error(f"推送循环异常: {e}", exc_info=True)
                
                # 维护任务
                try:
                    self.maintenance_cycle()
                except Exception as e:
                    logger.error(f"维护循环异常: {e}", exc_info=True)
                
                # 打印统计
                if self.stats['cycles'] % 10 == 0:
                    self.print_statistics()
                
                # 短暂休眠
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\n收到中断信号")
        finally:
            self.stop()
    
    def stop(self):
        """停止服务"""
        self.running = False
        
        # 停止IP切换器
        self.ip_changer.stop()
        
        logger.info("\n" + "=" * 70)
        logger.info("中转服务停止")
        logger.info("=" * 70)
        self.print_statistics()
        logger.info("再见！")
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"\n收到信号 {signum}")
        self.stop()
        sys.exit(0)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="中转服务器")
    parser.add_argument('--config', default='relay_config.json',
                       help='配置文件路径')
    args = parser.parse_args()
    
    try:
        service = RelayService(config_file=args.config)
        service.run()
    except Exception as e:
        logger.error(f"服务异常: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
