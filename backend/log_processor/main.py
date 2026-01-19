"""
统一日志处理主程序
处理所有僵尸网络的日志数据
"""
import sys
import os
import asyncio
import logging
import signal
import time
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    BOTNET_CONFIG, DB_CONFIG, DB_BATCH_SIZE, 
    DB_COMMIT_INTERVAL, POSITION_STATE_FILE,
    LOG_PROCESSOR_LOG_FILE, C2_ENDPOINTS, ENABLE_REMOTE_PULLING,
    QUEUE_MODE_ENABLED,  # 队列模式开关
    INTERNAL_WORKER_CONFIG  # 内置Worker配置
)
from log_processor.parser import LogParser
from log_processor.enricher import IPEnricher
from log_processor.db_writer import BotnetDBWriter
from log_processor.performance_monitor import create_monitored_writer
from log_processor.watcher import BotnetLogWatcher
from log_processor.remote_puller import RemotePuller
from typing import List, Dict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_PROCESSOR_LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 导入Redis队列（用于解耦数据处理）
# 从log_processor.task_queue导入，所有配置从config.py读取
task_queue = None
USE_QUEUE_FOR_PULLING = False

if QUEUE_MODE_ENABLED:
    try:
        from log_processor.task_queue import task_queue
        if task_queue is not None:
            USE_QUEUE_FOR_PULLING = True
            logger.info("[队列模式] 已启用 - 数据将通过Redis队列异步处理")
            logger.info("[队列模式] 所有配置从 config.py 读取")
            
            # 检查内置Worker配置
            if INTERNAL_WORKER_CONFIG.get('enabled', True):
                worker_count = INTERNAL_WORKER_CONFIG.get('worker_count', 1)
                logger.info(f"[内置Worker] 已启用 - 将启动 {worker_count} 个Worker协程")
            else:
                logger.warning("[内置Worker] 已禁用 - 数据将推送到队列但无Worker处理")
                logger.warning("[内置Worker] 请启动独立的worker.py或在config.py中启用内置Worker")
        else:
            logger.warning("[队列模式] TaskQueue初始化失败，降级为直接处理模式")
    except ImportError as e:
        logger.warning(f"[队列模式] 无法导入task_queue: {e}")
        logger.warning("[队列模式] 降级为直接处理模式")
else:
    logger.info("[直接模式] 队列模式已禁用 - 数据将直接同步处理")
    logger.info("[直接模式] 可在 config.py 中设置 QUEUE_MODE_ENABLED = True 启用队列模式")


class BotnetLogProcessor:
    """僵尸网络日志处理器"""
    
    def __init__(self):
        """初始化日志处理器"""
        self.parsers = {}
        self.enricher = IPEnricher(
            cache_size=10000,
            cache_ttl=86400,
            max_concurrent=20  # 限制并发为20，防止数据库连接耗尽
        )
        self.writers = {}
        self.monitors = {}  # 性能监控器
        self.watcher = None
        self.remote_puller = None  # 远程拉取器
        self.remote_puller_task = None  # 拉取任务
        self.running = False
        
        # 内置Worker相关
        self.internal_workers = []  # 内置Worker协程列表
        self.internal_worker_tasks = []  # Worker任务列表
        
        # 统计信息
        self.stats = {
            'total_lines': 0,
            'processed_lines': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        # 初始化各个僵尸网络的处理器
        # 性能优化选项
        USE_PERFORMANCE_MONITORING = True  # 设置为True启用性能监控
        USE_CONNECTION_POOL = True  # 设置为True使用连接池
        
        for botnet_type, config in BOTNET_CONFIG.items():
            if config.get('enabled', True):
                # 创建解析器
                self.parsers[botnet_type] = LogParser(
                    botnet_type, 
                    config.get('important_events', [])
                )
                
                # 创建写入器
                if USE_PERFORMANCE_MONITORING:
                    # 使用带性能监控的写入器
                    self.writers[botnet_type], self.monitors[botnet_type] = create_monitored_writer(
                        botnet_type, DB_CONFIG, DB_BATCH_SIZE
                    )
                else:
                    # 使用标准写入器（包含所有优化功能）
                    self.writers[botnet_type] = BotnetDBWriter(
                        botnet_type, DB_CONFIG, DB_BATCH_SIZE, 
                        use_connection_pool=USE_CONNECTION_POOL,
                        enable_monitoring=True
                    )
                
        logger.info(f"Initialized processors for {len(self.parsers)} botnet types")
        
        # 初始化远程拉取器（如果启用）
        logger.info(f"检查远程拉取配置: ENABLE_REMOTE_PULLING={ENABLE_REMOTE_PULLING}")
        if ENABLE_REMOTE_PULLING:
            try:
                logger.info(f"准备初始化远程拉取器，C2端点数量: {len(C2_ENDPOINTS)}")
                self.remote_puller = RemotePuller(C2_ENDPOINTS, self)
                logger.info(f"[OK] 远程拉取器已初始化（{len([c for c in C2_ENDPOINTS if c.get('enabled')])} 个C2端点）")
            except Exception as e:
                logger.error(f"远程拉取器初始化失败: {e}", exc_info=True)
                self.remote_puller = None
        else:
            logger.warning("⚠️  远程拉取功能未启用")
        
    async def process_api_data(self, botnet_type: str, ip_data: List[Dict]):
        """
        处理来自API的结构化IP数据（支持队列模式和直接处理模式）
        
        Args:
            botnet_type: 僵尸网络类型
            ip_data: 结构化IP数据列表
        """
        if botnet_type not in self.writers:
            logger.warning(f"Unknown botnet type: {botnet_type}")
            return
        
        # ===== 模式1: 使用Redis队列（推荐，不阻塞） =====
        if USE_QUEUE_FOR_PULLING and task_queue:
            try:
                task_id = task_queue.push_task(
                    botnet_type=botnet_type,
                    ip_data=ip_data,
                    client_ip='log_processor'  # 标识来源
                )
                queue_len = task_queue.get_queue_length()
                logger.info(
                    f"[{botnet_type}] 已推送 {len(ip_data)} 条数据到队列，"
                    f"任务ID: {task_id}, 队列长度: {queue_len}"
                )
                return  # 立即返回，由Worker异步处理
            except Exception as e:
                logger.error(f"[{botnet_type}] 推送到队列失败: {e}，降级为直接处理")
                # 降级到直接处理模式
        
        # ===== 模式2: 直接处理（会占用资源，可能影响前端） =====
        writer = self.writers[botnet_type]
        logger.info(f"[{botnet_type}] 收到 {len(ip_data)} 个IP，开始直接处理...")
        
        # 批量处理IP查询和数据库写入
        processed_count = 0
        error_count = 0
        start_time = datetime.now()
        
        # === 性能监控：IP增强阶段 ===
        enrich_start = datetime.now()
        
        # 使用gather并发查询IP信息（已有Semaphore控制并发上限）
        ip_query_tasks = []
        for ip_item in ip_data:
            ip_query_tasks.append(self.enricher.enrich(ip_item['ip']))
        
        # 并发查询所有IP的地理位置信息
        ip_infos = await asyncio.gather(*ip_query_tasks, return_exceptions=True)
        
        enrich_time = (datetime.now() - enrich_start).total_seconds()
        enrich_stats = self.enricher.get_stats()
        logger.info(
            f"[{botnet_type}] IP增强完成: {len(ip_data)}条 用时{enrich_time:.2f}秒 ({len(ip_data)/enrich_time:.0f} IP/秒) "
            f"缓存命中率{enrich_stats['total_cache_hit_rate']}"
        )
        
        # 将查询结果与IP数据配对并写入
        for ip_item, ip_info in zip(ip_data, ip_infos):
            try:
                # 如果查询出错，使用默认值
                if isinstance(ip_info, Exception):
                    logger.warning(f"IP查询失败 {ip_item['ip']}: {ip_info}")
                    ip_info = {
                        'country': '未知',
                        'province': '',
                        'city': '',
                        'longitude': 0,
                        'latitude': 0,
                        'continent': '',
                        'isp': '',
                        'asn': '',
                        'is_china': False
                    }
                
                # 构造parsed_data格式
                parsed_data = {
                    'ip': ip_item['ip'],
                    'timestamp': datetime.fromisoformat(ip_item['timestamp']) if isinstance(ip_item['timestamp'], str) else ip_item['timestamp'],
                    'event_type': 'remote_upload',
                    'source': 'remote_uploader',
                    'date': ip_item.get('date', datetime.now().strftime('%Y-%m-%d')),
                    'botnet_type': ip_item.get('botnet_type', botnet_type)
                }
                
                # 写入数据库缓冲区（不立即刷新）
                writer.add_node(parsed_data, ip_info)
                
                processed_count += 1
                self.stats['processed_lines'] += 1
                
            except Exception as e:
                logger.error(f"处理API数据失败 [{botnet_type}] {ip_item.get('ip', 'unknown')}: {e}")
                error_count += 1
                self.stats['errors'] += 1
        
        # === 性能监控：数据库写入阶段 ===
        db_start = datetime.now()
        
        # 批量刷新到数据库（提高效率）
        try:
            await writer.flush(force=True)
            
            db_time = (datetime.now() - db_start).total_seconds()
            total_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"[OK] [{botnet_type}] API数据处理完成: "
                f"成功 {processed_count}, 失败 {error_count}, "
                f"总用时 {total_time:.2f}秒 ({processed_count/total_time:.0f} IP/秒) | "
                f"IP增强 {enrich_time:.2f}秒({enrich_time/total_time*100:.1f}%) "
                f"DB写入 {db_time:.2f}秒({db_time/total_time*100:.1f}%)"
            )
        except Exception as e:
            logger.error(f"[ERROR] [{botnet_type}] 数据库刷新失败: {e}")

    async def process_log_line(self, botnet_type: str, line: str):
        """
        处理单行日志
        
        Args:
            botnet_type: 僵尸网络类型
            line: 日志行内容
        """
        try:
            self.stats['total_lines'] += 1
            
            # 获取解析器
            parser = self.parsers.get(botnet_type)
            if not parser:
                logger.warning(f"No parser found for botnet type: {botnet_type}")
                return
                
            # 解析日志
            parsed_data = parser.parse_line(line)
            if not parsed_data:
                return
                
            # 检查是否需要保存
            if not parser.should_save_to_db(parsed_data):
                return
                
            # 增强IP信息
            ip = parsed_data['ip']
            ip_info = await self.enricher.enrich(ip)
            
            # 写入数据库
            writer = self.writers.get(botnet_type)
            if writer:
                writer.add_node(parsed_data, ip_info)
                
            self.stats['processed_lines'] += 1
            
            # 定期刷新
            if self.stats['processed_lines'] % DB_BATCH_SIZE == 0:
                await self._flush_all_writers()
                
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error processing log line: {e}, line: {line[:100]}")
            
    async def _flush_all_writers(self):
        """刷新所有写入器"""
        for botnet_type, writer in self.writers.items():
            try:
                await writer.flush(force=True)
            except Exception as e:
                logger.error(f"Error flushing writer for {botnet_type}: {e}")
                
    async def _periodic_flush(self):
        """定期刷新任务"""
        while self.running:
            await asyncio.sleep(DB_COMMIT_INTERVAL)
            logger.info("Periodic flush triggered")
            await self._flush_all_writers()
            self._print_stats()
            
    async def _internal_worker_process_task(self, worker_id: int):
        """内置Worker协程 - 从队列获取并处理任务"""
        logger.info(f"[内置Worker-{worker_id}] 启动")
        
        # 获取配置
        queue_timeout = INTERNAL_WORKER_CONFIG.get('queue_timeout', 1)
        db_batch_size = INTERNAL_WORKER_CONFIG.get('db_batch_size', 100)
        max_retries = INTERNAL_WORKER_CONFIG.get('max_retries', 3)
        retry_delay = INTERNAL_WORKER_CONFIG.get('retry_delay', 5)
        
        retry_count = 0
        
        while self.running:
            try:
                # 从队列获取任务（在线程池中运行，避免阻塞事件循环）
                loop = asyncio.get_event_loop()
                task = await loop.run_in_executor(None, task_queue.pop_task, queue_timeout)
                
                if task:
                    retry_count = 0  # 成功获取任务，重置重试计数
                    
                    # 处理任务
                    task_id = task.get('task_id', 'unknown')
                    botnet_type = task.get('botnet_type', 'unknown')
                    ip_data = task.get('ip_data', [])
                    client_ip = task.get('client_ip', 'unknown')
                    
                    logger.info(f"[内置Worker-{worker_id}] 开始处理任务: {task_id}, {len(ip_data)} 条IP")
                    
                    start_time = datetime.now()
                    
                    try:
                        # 获取或创建写入器
                        writer = self.writers.get(botnet_type)
                        if not writer:
                            logger.warning(f"[内置Worker-{worker_id}] 未找到{botnet_type}的writer，跳过任务")
                            continue
                        
                        # 记录批次开始
                        writer.start_batch(client_ip, len(ip_data))
                        
                        # 处理每个IP
                        processed_count = 0
                        error_count = 0
                        
                        for ip_item in ip_data:
                            try:
                                # 构造parsed_data
                                parsed_data = {
                                    'ip': ip_item['ip'],
                                    'timestamp': datetime.fromisoformat(ip_item['timestamp'].replace('Z', '+00:00')),
                                    'event_type': 'remote_upload',
                                    'source': 'remote_uploader',
                                    'date': ip_item.get('date', datetime.now().strftime('%Y-%m-%d')),
                                    'botnet_type': ip_item.get('botnet_type', botnet_type)
                                }
                                
                                # IP富化（使用主程序的enricher）
                                ip_info = await self.enricher.enrich(ip_item['ip'])
                                
                                # 写入数据库
                                writer.add_node(parsed_data, ip_info)
                                processed_count += 1
                                
                            except Exception as e:
                                logger.error(f"[内置Worker-{worker_id}] 处理IP失败 {ip_item.get('ip')}: {e}")
                                error_count += 1
                        
                        # 强制刷新
                        await writer.flush(force=True)
                        
                        elapsed = (datetime.now() - start_time).total_seconds()
                        stats = writer.get_stats()
                        
                        logger.info(
                            f"[内置Worker-{worker_id}] 任务完成: {task_id} | "
                            f"处理 {processed_count}, 错误 {error_count}, "
                            f"写入 {stats.get('total_written', 0)}, 重复 {stats.get('duplicate_count', 0)} | "
                            f"耗时 {elapsed:.2f}秒"
                        )
                        
                    except Exception as e:
                        logger.error(f"[内置Worker-{worker_id}] 任务处理失败: {task_id} - {e}", exc_info=True)
                
            except KeyboardInterrupt:
                logger.info(f"[内置Worker-{worker_id}] 收到停止信号")
                break
            except Exception as e:
                # 导入redis异常
                try:
                    import redis
                    if isinstance(e, redis.TimeoutError):
                        if not self.running:
                            logger.info(f"[内置Worker-{worker_id}] Redis超时，准备退出")
                            break
                        logger.debug(f"[内置Worker-{worker_id}] Redis超时（正常）")
                        await asyncio.sleep(0.1)
                        continue
                    elif isinstance(e, redis.ConnectionError):
                        retry_count += 1
                        logger.error(f"[内置Worker-{worker_id}] Redis连接错误 (尝试 {retry_count}/{max_retries}): {e}")
                        
                        if retry_count >= max_retries:
                            logger.error(f"[内置Worker-{worker_id}] Redis连接失败次数过多，停止Worker")
                            break
                        
                        logger.info(f"[内置Worker-{worker_id}] 等待{retry_delay}秒后重试...")
                        await asyncio.sleep(retry_delay)
                        continue
                except ImportError:
                    pass
                
                logger.error(f"[内置Worker-{worker_id}] 错误: {e}", exc_info=True)
                await asyncio.sleep(1)
        
        logger.info(f"[内置Worker-{worker_id}] 已停止")
    
    def _print_stats(self):
        """打印统计信息"""
        logger.info("=== 统计信息 ===")
        logger.info(f"总行数: {self.stats['total_lines']}")
        logger.info(f"处理行数: {self.stats['processed_lines']}")
        logger.info(f"错误数: {self.stats['errors']}")
        logger.info(f"运行时间: {datetime.now() - self.stats['start_time']}")
        
        # 打印各个写入器的统计
        for botnet_type, writer in self.writers.items():
            stats = writer.get_stats()
            logger.info(f"[{botnet_type}] 写入: {stats['total_written']}, 重复: {stats['duplicate_count']}, 缓冲: {stats['buffer_size']}")
            
        # 打印IP增强器统计
        enricher_stats = self.enricher.get_stats()
        logger.info(f"IP查询: {enricher_stats['total_queries']}, L1命中率: {enricher_stats['l1_hit_rate']}, L2命中率: {enricher_stats['l2_hit_rate']}, 总命中率: {enricher_stats['total_cache_hit_rate']}")
        
        # 打印远程拉取器统计（如果启用）
        if self.remote_puller:
            puller_stats = self.remote_puller.get_stats()
            logger.info(f"远程拉取: 总计 {puller_stats['total_pulled']}, 已保存 {puller_stats['total_saved']}, 错误 {puller_stats['error_count']}")
            if puller_stats['last_pull_time']:
                logger.info(f"最后拉取: {puller_stats['last_pull_time']}")
        
        # 打印内置Worker统计
        if self.internal_worker_tasks:
            logger.info(f"内置Worker: {len(self.internal_worker_tasks)} 个协程运行中")
    
    def generate_performance_reports(self):
        """生成所有写入器的性能报告"""
        reports = []
        for botnet_type, writer in self.writers.items():
            if hasattr(writer, 'generate_performance_report'):
                report = writer.generate_performance_report()
                reports.append(report)
                logger.info(report)
        return reports
    
    def get_performance_summary(self):
        """获取性能摘要"""
        summary = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'writers': {}
        }
        
        for botnet_type, writer in self.writers.items():
            if hasattr(writer, 'get_performance_stats'):
                summary['writers'][botnet_type] = writer.get_performance_stats()
        
        return summary
        
    def start(self):
        """启动日志处理服务"""
        logger.info("=" * 60)
        logger.info("Starting Botnet Log Processor")
        logger.info("=" * 60)
        
        self.running = True
        
        # 创建事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 创建日志监控器,传入事件循环
            self.watcher = BotnetLogWatcher(
                BOTNET_CONFIG,
                self.process_log_line,
                POSITION_STATE_FILE,
                loop  # 传入事件循环
            )
            
            # 启动监控
            self.watcher.start()
            
            # 处理已存在的日志文件 - 在事件循环中运行
            loop.run_until_complete(self.watcher.process_existing_logs())
            
            # 启动定期刷新任务
            loop.create_task(self._periodic_flush())
            
            # 启动远程拉取任务（如果启用）
            if self.remote_puller:
                logger.info("正在启动远程拉取任务...")
                logger.info(f"远程拉取器对象: {self.remote_puller}")
                logger.info(f"C2端点数量: {len([c for c in C2_ENDPOINTS if c.get('enabled')])}")
                self.remote_puller_task = loop.create_task(self.remote_puller.run())
                logger.info(f"[OK] 远程拉取任务已启动，任务对象: {self.remote_puller_task}")
            else:
                logger.warning("⚠️  远程拉取器未初始化，跳过启动")
            
            # 启动内置Worker协程（如果启用）
            if USE_QUEUE_FOR_PULLING and INTERNAL_WORKER_CONFIG.get('enabled', True):
                worker_count = INTERNAL_WORKER_CONFIG.get('worker_count', 1)
                logger.info(f"正在启动 {worker_count} 个内置Worker协程...")
                
                for i in range(worker_count):
                    worker_id = i + 1
                    worker_task = loop.create_task(self._internal_worker_process_task(worker_id))
                    self.internal_worker_tasks.append(worker_task)
                    logger.info(f"[OK] 内置Worker-{worker_id} 已启动")
                
                logger.info(f"[OK] 所有内置Worker已启动 (共 {worker_count} 个)")
            
            logger.info("Botnet Log Processor is running. Press Ctrl+C to stop.")
            
            # 保持运行
            loop.run_forever()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            # 执行异步停止
            if self.running:
                loop.run_until_complete(self._async_stop())
        finally:
            if not loop.is_closed():
                loop.close()
            
    async def _async_stop(self):
        """异步停止服务"""
        logger.info("Stopping Botnet Log Processor...")
        
        self.running = False
        
        # 停止内置Worker协程
        if self.internal_worker_tasks:
            logger.info(f"正在停止 {len(self.internal_worker_tasks)} 个内置Worker协程...")
            for task in self.internal_worker_tasks:
                if not task.done():
                    task.cancel()
            
            # 等待所有Worker停止
            results = await asyncio.gather(*self.internal_worker_tasks, return_exceptions=True)
            stopped_count = sum(1 for r in results if isinstance(r, asyncio.CancelledError) or r is None)
            logger.info(f"内置Worker已停止: {stopped_count}/{len(self.internal_worker_tasks)}")
        
        # 停止远程拉取任务
        if self.remote_puller_task and not self.remote_puller_task.done():
            logger.info("正在停止远程拉取任务...")
            self.remote_puller_task.cancel()
            try:
                await self.remote_puller_task
            except asyncio.CancelledError:
                logger.info("远程拉取任务已停止")
        
        # 停止监控
        if self.watcher:
            self.watcher.stop()
            
        # 最后刷新一次
        await self._flush_all_writers()
        
        # 打印最终统计
        self._print_stats()
        
        logger.info("Botnet Log Processor stopped")
    
    def stop(self):
        """停止服务（同步版本，仅设置标志）"""
        logger.info("Stop signal received, setting flag...")
        self.running = False
        
        # 停止监控（立即）
        if self.watcher:
            self.watcher.stop()
        
        # 停止事件循环
        try:
            loop = asyncio.get_event_loop()
            if loop and loop.is_running():
                # 在事件循环中安排异步停止
                asyncio.ensure_future(self._async_stop())
                # 延迟停止事件循环，让 _async_stop 有时间执行
                loop.call_later(0.5, loop.stop)
        except Exception as e:
            logger.error(f"Error stopping loop: {e}")


# 全局处理器实例（用于API调用）
_global_processor = None

def get_processor():
    """获取全局处理器实例"""
    global _global_processor
    if _global_processor is None:
        _global_processor = BotnetLogProcessor()
    return _global_processor

def signal_handler(sig, frame):
    """信号处理器"""
    logger.info("Signal received, initiating graceful shutdown...")
    global _global_processor
    if _global_processor:
        _global_processor.stop()
    # 不立即 sys.exit，让事件循环优雅关闭


def main():
    """主函数"""
    # 输出 Python 版本信息
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    logger.info(f"Python 版本: {python_version}")
    if sys.version_info < (3, 9):
        logger.warning("检测到 Python < 3.9，使用 run_in_executor 代替 asyncio.to_thread")
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建并启动处理器
    global _global_processor
    _global_processor = BotnetLogProcessor()
    _global_processor.start()


if __name__ == "__main__":
    main()

