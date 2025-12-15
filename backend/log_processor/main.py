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
    LOG_PROCESSOR_LOG_FILE
)
from log_processor.parser import LogParser
from log_processor.enricher import IPEnricher
from log_processor.db_writer import BotnetDBWriter
from log_processor.performance_monitor import create_monitored_writer
from log_processor.watcher import BotnetLogWatcher
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


class BotnetLogProcessor:
    """僵尸网络日志处理器"""
    
    def __init__(self):
        """初始化日志处理器"""
        self.parsers = {}
        self.enricher = IPEnricher()
        self.writers = {}
        self.monitors = {}  # 性能监控器
        self.watcher = None
        self.running = False
        
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
        
    async def process_api_data(self, botnet_type: str, ip_data: List[Dict]):
        """
        处理来自API的结构化IP数据（异步非阻塞）
        
        Args:
            botnet_type: 僵尸网络类型
            ip_data: 结构化IP数据列表
        """
        if botnet_type not in self.writers:
            logger.warning(f"Unknown botnet type: {botnet_type}")
            return
            
        writer = self.writers[botnet_type]
        
        logger.info(f"[{botnet_type}] 收到 {len(ip_data)} 个IP，开始处理...")
        
        # 批量处理IP查询和数据库写入
        processed_count = 0
        error_count = 0
        start_time = datetime.now()
        
        # 使用gather并发查询IP信息（提高效率）
        ip_query_tasks = []
        for ip_item in ip_data:
            ip_query_tasks.append(self.enricher.enrich(ip_item['ip']))
        
        # 并发查询所有IP的地理位置信息
        ip_infos = await asyncio.gather(*ip_query_tasks, return_exceptions=True)
        
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
        
        # 批量刷新到数据库（提高效率）
        try:
            await writer.flush(force=True)
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"✅ [{botnet_type}] API数据处理完成: "
                f"成功 {processed_count}, 失败 {error_count}, "
                f"用时 {elapsed_time:.2f}秒 ({processed_count/elapsed_time:.0f} IP/秒)"
            )
        except Exception as e:
            logger.error(f"❌ [{botnet_type}] 数据库刷新失败: {e}")

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
        logger.info(f"IP查询: {enricher_stats['total_queries']}, 缓存命中率: {enricher_stats['cache_hit_rate']}")
    
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
            
            logger.info("Botnet Log Processor is running. Press Ctrl+C to stop.")
            
            # 保持运行
            loop.run_forever()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        finally:
            self.stop()
            loop.close()
            
    def stop(self):
        """停止服务"""
        logger.info("Stopping Botnet Log Processor...")
        
        self.running = False
        
        # 停止监控
        if self.watcher:
            self.watcher.stop()
            
        # 最后刷新一次
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._flush_all_writers())
        
        # 打印最终统计
        self._print_stats()
        
        logger.info("Botnet Log Processor stopped")


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
    logger.info("Signal received, stopping...")
    global _global_processor
    if _global_processor:
        _global_processor.stop()
    sys.exit(0)


def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建并启动处理器
    global _global_processor
    _global_processor = BotnetLogProcessor()
    _global_processor.start()


if __name__ == "__main__":
    main()

