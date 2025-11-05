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

from log_processor.config import (
    BOTNET_CONFIG, DB_CONFIG, DB_BATCH_SIZE, 
    DB_COMMIT_INTERVAL, POSITION_STATE_FILE
)
from log_processor.parser import LogParser
from log_processor.enricher import IPEnricher
from log_processor.db_writer import BotnetDBWriter
from log_processor.watcher import BotnetLogWatcher

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log_processor.log'),
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
        for botnet_type, config in BOTNET_CONFIG.items():
            if config.get('enabled', True):
                # 创建解析器
                self.parsers[botnet_type] = LogParser(
                    botnet_type, 
                    config.get('important_events', [])
                )
                
                # 创建数据库写入器
                self.writers[botnet_type] = BotnetDBWriter(
                    botnet_type,
                    DB_CONFIG,
                    DB_BATCH_SIZE
                )
                
        logger.info(f"Initialized processors for {len(self.parsers)} botnet types")
        
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
        uptime = datetime.now() - self.stats['start_time']
        
        logger.info("=" * 60)
        logger.info("STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Uptime: {uptime}")
        logger.info(f"Total lines: {self.stats['total_lines']}")
        logger.info(f"Processed lines: {self.stats['processed_lines']}")
        logger.info(f"Errors: {self.stats['errors']}")
        
        # IP enricher统计
        enricher_stats = self.enricher.get_stats()
        logger.info(f"IP queries: {enricher_stats['total_queries']}")
        logger.info(f"Cache hit rate: {enricher_stats['cache_hit_rate']}")
        
        # 各僵尸网络统计（包含去重信息）
        for botnet_type, writer in self.writers.items():
            writer_stats = writer.get_stats()
            logger.info(f"[{botnet_type}] Written: {writer_stats['total_written']}, "
                       f"Duplicates: {writer_stats['duplicate_count']} ({writer_stats['duplicate_rate']}), "
                       f"Buffer: {writer_stats['buffer_size']}")
            
        logger.info("=" * 60)
        
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


def signal_handler(sig, frame):
    """信号处理器"""
    logger.info("Signal received, stopping...")
    sys.exit(0)


def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建并启动处理器
    processor = BotnetLogProcessor()
    processor.start()


if __name__ == "__main__":
    main()

