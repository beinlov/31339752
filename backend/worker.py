# -*- coding: utf-8 -*-
"""
独立Worker进程 - 从Redis队列消费任务并处理
完全独立于Web服务，不影响前端响应
"""

import asyncio
import logging
import signal
import sys
import redis
from datetime import datetime

from task_queue import task_queue
from log_processor.enricher import IPEnricher
from log_processor.db_writer import BotnetDBWriter
from config import DB_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BotnetWorker:
    """僵尸网络数据处理Worker"""
    
    def __init__(self):
        """初始化Worker"""
        self.running = False
        self.enricher = IPEnricher(
            cache_size=10000,
            cache_ttl=86400,
            max_concurrent=20
        )
        
    async def process_task(self, task: dict):
        """
        处理单个任务
        
        Args:
            task: 任务字典
        """
        task_id = task['task_id']
        botnet_type = task['botnet_type']
        ip_data = task['ip_data']
        client_ip = task['client_ip']
        
        logger.info(f"[Worker] 开始处理任务: {task_id}, {len(ip_data)} 条IP")
        
        start_time = datetime.now()
        
        try:
            # 创建数据库写入器
            writer = BotnetDBWriter(
                botnet_type,
                DB_CONFIG,
                batch_size=100,
                use_connection_pool=True,
                enable_monitoring=True
            )
            
            # 记录批次开始
            writer.start_batch(client_ip, len(ip_data))
            
            # 处理每个IP数据
            for ip_item in ip_data:
                try:
                    # 构造parsed_data格式
                    parsed_data = {
                        'ip': ip_item['ip'],
                        'timestamp': datetime.fromisoformat(ip_item['timestamp'].replace('Z', '+00:00')),
                        'event_type': 'remote_upload',
                        'source': 'remote_uploader',
                        'date': ip_item.get('date', datetime.now().strftime('%Y-%m-%d')),
                        'botnet_type': ip_item.get('botnet_type', botnet_type)
                    }
                    
                    # IP地理位置增强
                    ip_info = await self.enricher.enrich(ip_item['ip'])
                    
                    # 写入数据库
                    writer.add_node(parsed_data, ip_info)
                    
                except Exception as e:
                    logger.error(f"[Worker] 处理IP失败 {ip_item.get('ip')}: {e}")
            
            # 强制刷新写入器
            await writer.flush(force=True)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"[Worker] 任务完成: {task_id} | "
                f"成功 {writer.processed_count}, 重复 {writer.duplicate_count}, "
                f"写入 {writer.total_written} | 耗时 {elapsed:.2f}秒"
            )
            
        except Exception as e:
            logger.error(f"[Worker] 任务处理失败: {task_id} - {e}", exc_info=True)
    
    async def run(self):
        """运行Worker主循环"""
        self.running = True
        
        # 启动前检查Redis连接
        logger.info("[Worker] 检查Redis连接...")
        if not task_queue.test_connection():
            logger.error("[Worker] Redis连接失败！请确保Redis已启动")
            logger.error("[Worker] 启动Redis: redis-server")
            return
        
        logger.info("[Worker] 启动成功，等待任务...")
        
        retry_count = 0
        max_retries = 3
        
        while self.running:
            try:
                # 从队列获取任务（阻塞1秒，避免CPU空转）
                task = task_queue.pop_task(timeout=1)
                
                if task:
                    await self.process_task(task)
                    retry_count = 0  # 成功处理后重置重试计数
                    
            except KeyboardInterrupt:
                logger.info("[Worker] 收到停止信号...")
                break
            except redis.ConnectionError as e:
                retry_count += 1
                logger.error(f"[Worker] Redis连接错误 (尝试 {retry_count}/{max_retries}): {e}")
                
                if retry_count >= max_retries:
                    logger.error("[Worker] Redis连接失败次数过多，停止Worker")
                    logger.error("[Worker] 请检查Redis是否运行: netstat -ano | find \":6379\"")
                    break
                
                logger.info(f"[Worker] 等待5秒后重试...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"[Worker] 错误: {e}", exc_info=True)
                await asyncio.sleep(1)
        
        logger.info("[Worker] 已停止")
    
    def stop(self):
        """停止Worker"""
        self.running = False


async def main():
    """主函数"""
    worker = BotnetWorker()
    
    # 信号处理
    def signal_handler(sig, frame):
        logger.info(f"收到信号 {sig}，准备停止...")
        worker.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 运行Worker
    await worker.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker已停止")
