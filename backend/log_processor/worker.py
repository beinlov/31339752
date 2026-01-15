# -*- coding: utf-8 -*-
"""
⚠️  已废弃 - DEPRECATED ⚠️

此文件已被废弃，Worker功能已集成到 main.py 中。

【新架构】:
- Worker功能已内置在 backend/log_processor/main.py 中
- 只需启动 main.py，无需单独启动 worker.py
- 所有配置在 config.py 的 INTERNAL_WORKER_CONFIG 中

【如何使用新架构】:
1. 确保 config.py 中 INTERNAL_WORKER_CONFIG['enabled'] = True
2. 运行: python backend/log_processor/main.py
3. 内置Worker会自动启动，无需额外操作

【何时使用此文件】:
- 仅在需要独立Worker进程时使用（极少数情况）
- 或临时禁用内置Worker时作为备用方案

【详细文档】:
- 参见: backend/INTERNAL_WORKER_MIGRATION.md

════════════════════════════════════════════════════════

独立Worker进程 - 从Redis队列消费任务并处理
完全独立于Web服务，不影响前端响应

重构说明：
- 所有配置参数从 backend/config.py 读取
- 支持通过环境变量覆盖配置
- 移动到log_processor目录，便于模块化管理
"""

import asyncio
import logging
import signal
import sys
import os
import redis
from datetime import datetime
from pathlib import Path

# 添加父目录到path，确保可以导入config
sys.path.insert(0, str(Path(__file__).parent.parent))

from log_processor.task_queue import task_queue
from log_processor.enricher import IPEnricher
from log_processor.db_writer import BotnetDBWriter
from config import DB_CONFIG, WORKER_CONFIG, QUEUE_MODE_ENABLED

# 配置日志
log_file = WORKER_CONFIG.get('log_file', 'logs/worker.log')
log_level = getattr(logging, WORKER_CONFIG.get('log_level', 'INFO'))

# 确保日志目录存在
log_dir = os.path.dirname(log_file)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BotnetWorker:
    """僵尸网络数据处理Worker"""
    
    def __init__(self, worker_id: int = 1):
        """
        初始化Worker
        
        Args:
            worker_id: Worker编号（用于日志标识）
        """
        self.worker_id = worker_id
        self.running = False
        
        # 从config读取配置
        enricher_concurrent = WORKER_CONFIG.get('enricher_concurrent', 20)
        enricher_cache_size = WORKER_CONFIG.get('enricher_cache_size', 10000)
        enricher_cache_ttl = WORKER_CONFIG.get('enricher_cache_ttl', 86400)
        
        self.enricher = IPEnricher(
            cache_size=enricher_cache_size,
            cache_ttl=enricher_cache_ttl,
            max_concurrent=enricher_concurrent
        )
        
        # 从config读取重试配置
        self.max_retries = WORKER_CONFIG.get('max_retries', 3)
        self.retry_delay = WORKER_CONFIG.get('retry_delay', 5)
        self.queue_timeout = WORKER_CONFIG.get('queue_timeout', 1)
        self.db_batch_size = WORKER_CONFIG.get('db_batch_size', 100)
        
        logger.info(f"[Worker-{self.worker_id}] 初始化完成")
        logger.info(f"[Worker-{self.worker_id}] 配置: 富化并发={enricher_concurrent}, "
                   f"缓存={enricher_cache_size}, DB批量={self.db_batch_size}")
        
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
        
        logger.info(f"[Worker-{self.worker_id}] 开始处理任务: {task_id}, {len(ip_data)} 条IP")
        
        start_time = datetime.now()
        
        try:
            # 创建数据库写入器
            writer = BotnetDBWriter(
                botnet_type,
                DB_CONFIG,
                batch_size=self.db_batch_size,
                use_connection_pool=True,
                enable_monitoring=True
            )
            
            # 记录批次开始
            writer.start_batch(client_ip, len(ip_data))
            
            # 处理每个IP数据
            processed_count = 0
            error_count = 0
            
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
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"[Worker-{self.worker_id}] 处理IP失败 {ip_item.get('ip')}: {e}")
                    error_count += 1
            
            # 强制刷新写入器
            await writer.flush(force=True)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # 获取写入器统计
            stats = writer.get_stats()
            
            logger.info(
                f"[Worker-{self.worker_id}] 任务完成: {task_id} | "
                f"处理 {processed_count}, 错误 {error_count}, "
                f"写入 {stats.get('total_written', 0)}, 重复 {stats.get('duplicate_count', 0)} | "
                f"耗时 {elapsed:.2f}秒"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"[Worker-{self.worker_id}] 任务处理失败: {task_id} - {e}", exc_info=True)
            return False
    
    async def run(self):
        """运行Worker主循环"""
        self.running = True
        
        # 检查队列模式是否启用
        if not QUEUE_MODE_ENABLED:
            logger.error(f"[Worker-{self.worker_id}] 队列模式未启用！")
            logger.error(f"[Worker-{self.worker_id}] 请在config.py中设置 QUEUE_MODE_ENABLED = True")
            return
        
        # 检查task_queue是否可用
        if task_queue is None:
            logger.error(f"[Worker-{self.worker_id}] TaskQueue未初始化！")
            logger.error(f"[Worker-{self.worker_id}] 请检查Redis连接配置")
            return
        
        # 启动前检查Redis连接
        logger.info(f"[Worker-{self.worker_id}] 检查Redis连接...")
        if not task_queue.test_connection():
            logger.error(f"[Worker-{self.worker_id}] Redis连接失败！请确保Redis已启动")
            logger.error(f"[Worker-{self.worker_id}] 启动Redis: redis-server")
            logger.error(f"[Worker-{self.worker_id}] 检查配置: {task_queue.redis_client.connection_pool.connection_kwargs}")
            return
        
        logger.info(f"[Worker-{self.worker_id}] 启动成功，等待任务...")
        logger.info(f"[Worker-{self.worker_id}] 队列名称: {task_queue.queue_name}")
        logger.info(f"[Worker-{self.worker_id}] 检查队列长度: {task_queue.get_queue_length()}")
        
        retry_count = 0
        
        while self.running:
            try:
                # 从队列获取任务（阻塞timeout秒，避免CPU空转）
                task = task_queue.pop_task(timeout=self.queue_timeout)
                
                if task:
                    success = await self.process_task(task)
                    retry_count = 0  # 成功处理后重置重试计数
                    
                    if not success:
                        logger.warning(f"[Worker-{self.worker_id}] 任务处理失败，但不重试")
                    
            except KeyboardInterrupt:
                logger.info(f"[Worker-{self.worker_id}] 收到停止信号...")
                self.running = False
                break
            except redis.TimeoutError as e:
                # Redis超时（通常是Ctrl+C中断时发生）
                if not self.running:
                    logger.info(f"[Worker-{self.worker_id}] Redis超时，准备退出")
                    break
                logger.warning(f"[Worker-{self.worker_id}] Redis超时: {e}")
                await asyncio.sleep(1)
            except redis.ConnectionError as e:
                retry_count += 1
                logger.error(f"[Worker-{self.worker_id}] Redis连接错误 (尝试 {retry_count}/{self.max_retries}): {e}")
                
                if retry_count >= self.max_retries:
                    logger.error(f"[Worker-{self.worker_id}] Redis连接失败次数过多，停止Worker")
                    logger.error(f"[Worker-{self.worker_id}] 请检查Redis是否运行")
                    break
                
                logger.info(f"[Worker-{self.worker_id}] 等待{self.retry_delay}秒后重试...")
                await asyncio.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"[Worker-{self.worker_id}] 错误: {e}", exc_info=True)
                await asyncio.sleep(1)
        
        logger.info(f"[Worker-{self.worker_id}] 已停止")
    
    def stop(self):
        """停止Worker"""
        logger.info(f"[Worker-{self.worker_id}] 准备停止...")
        self.running = False


async def main(worker_id: int = 1):
    """
    主函数
    
    Args:
        worker_id: Worker编号
    """
    worker = BotnetWorker(worker_id=worker_id)
    
    # 信号处理
    def signal_handler(sig, frame):
        logger.info(f"收到信号 {sig}，准备停止Worker-{worker_id}...")
        worker.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 运行Worker
    await worker.run()


if __name__ == '__main__':
    # 支持命令行参数指定Worker ID
    worker_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    logger.info("=" * 80)
    logger.info(f"Botnet数据处理Worker - Worker #{worker_id}")
    logger.info("=" * 80)
    logger.info(f"队列模式: {'启用' if QUEUE_MODE_ENABLED else '禁用'}")
    logger.info(f"Redis配置: 从 config.py 加载")
    logger.info(f"Worker配置: 从 config.py 加载")
    logger.info("=" * 80)
    
    try:
        asyncio.run(main(worker_id))
    except KeyboardInterrupt:
        logger.info(f"Worker-{worker_id} 已停止")
