"""
日志处理器性能监控脚本
用于监控数据库写入性能和识别瓶颈
"""
import time
import logging
import threading
from datetime import datetime, timedelta
from collections import deque
import pymysql

# 可选的性能监控依赖
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, db_config: dict, monitor_interval: int = 30):
        self.db_config = db_config
        self.monitor_interval = monitor_interval
        self.running = False

        # 性能指标
        self.flush_times = deque(maxlen=100)  # 最近100次flush时间
        self.db_connection_times = deque(maxlen=100)  # 数据库连接时间
        self.insert_times = deque(maxlen=100)  # 插入时间

        # 系统资源监控
        self.cpu_usage = deque(maxlen=60)  # 最近60次CPU使用率
        self.memory_usage = deque(maxlen=60)  # 内存使用率

    def start_monitoring(self):
        """开始监控"""
        self.running = True
        monitor_thread = threading.Thread(target=self._monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        logger.info("Performance monitoring stopped")

    def record_flush_time(self, duration: float):
        """记录flush时间"""
        self.flush_times.append(duration)

    def record_db_connection_time(self, duration: float):
        """记录数据库连接时间"""
        self.db_connection_times.append(duration)

    def record_insert_time(self, duration: float):
        """记录插入时间"""
        self.insert_times.append(duration)

    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 监控系统资源（如果可用）
                if PSUTIL_AVAILABLE:
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory_percent = psutil.virtual_memory().percent

                    self.cpu_usage.append(cpu_percent)
                    self.memory_usage.append(memory_percent)

                # 监控数据库连接
                self._check_db_performance()

                # 生成性能报告
                if len(self.flush_times) > 0:
                    self._generate_performance_report()

                time.sleep(self.monitor_interval)

            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                time.sleep(5)

    def _check_db_performance(self):
        """检查数据库性能"""
        try:
            start_time = time.time()
            conn = pymysql.connect(**self.db_config)
            connection_time = time.time() - start_time

            self.record_db_connection_time(connection_time)

            # 检查数据库状态
            cursor = conn.cursor()
            cursor.execute("SHOW PROCESSLIST")
            processes = cursor.fetchall()

            # 统计连接数
            active_connections = len(processes)

            cursor.close()
            conn.close()

            if connection_time > 1.0:  # 连接时间超过1秒
                logger.warning(f"Slow database connection: {connection_time:.2f}s")

            if active_connections > 50:  # 连接数过多
                logger.warning(f"High database connections: {active_connections}")

        except Exception as e:
            logger.error(f"Error checking database performance: {e}")

    def _generate_performance_report(self):
        """生成性能报告"""
        try:
            # 计算平均值
            avg_flush_time = sum(self.flush_times) / len(self.flush_times)
            avg_connection_time = sum(self.db_connection_times) / len(
                self.db_connection_times) if self.db_connection_times else 0
            avg_insert_time = sum(self.insert_times) / len(self.insert_times) if self.insert_times else 0

            # 计算最大值
            max_flush_time = max(self.flush_times) if self.flush_times else 0
            max_connection_time = max(self.db_connection_times) if self.db_connection_times else 0

            # 系统资源
            avg_cpu = sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
            avg_memory = sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0

            # 检查性能问题
            issues = []
            if avg_flush_time > 2.0:
                issues.append(f"High average flush time: {avg_flush_time:.2f}s")

            if max_flush_time > 5.0:
                issues.append(f"Very slow flush detected: {max_flush_time:.2f}s")

            if avg_connection_time > 0.5:
                issues.append(f"Slow database connections: {avg_connection_time:.2f}s")

            if avg_cpu > 80:
                issues.append(f"High CPU usage: {avg_cpu:.1f}%")

            if avg_memory > 85:
                issues.append(f"High memory usage: {avg_memory:.1f}%")

            # 记录报告
            logger.info("=" * 60)
            logger.info("PERFORMANCE REPORT")
            logger.info("=" * 60)
            logger.info(f"Average flush time: {avg_flush_time:.2f}s")
            logger.info(f"Max flush time: {max_flush_time:.2f}s")
            logger.info(f"Average DB connection time: {avg_connection_time:.3f}s")
            logger.info(f"Average insert time: {avg_insert_time:.3f}s")
            logger.info(f"CPU usage: {avg_cpu:.1f}%")
            logger.info(f"Memory usage: {avg_memory:.1f}%")

            if issues:
                logger.warning("PERFORMANCE ISSUES DETECTED:")
                for issue in issues:
                    logger.warning(f"- {issue}")
            else:
                logger.info("No performance issues detected")

            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Error generating performance report: {e}")


class TimedDBWriter:
    """带性能监控的数据库写入器装饰器"""

    def __init__(self, db_writer, performance_monitor: PerformanceMonitor):
        self.db_writer = db_writer
        self.monitor = performance_monitor

        # 代理所有属性
        for attr in dir(db_writer):
            if not attr.startswith('_') and not hasattr(self, attr):
                setattr(self, attr, getattr(db_writer, attr))

    async def flush(self, force: bool = False):
        """带性能监控的flush方法"""
        start_time = time.time()

        try:
            result = await self.db_writer.flush(force)
            flush_time = time.time() - start_time
            self.monitor.record_flush_time(flush_time)

            if flush_time > 2.0:
                logger.warning(f"[{self.db_writer.botnet_type}] Slow flush detected: {flush_time:.2f}s")

            return result

        except Exception as e:
            flush_time = time.time() - start_time
            self.monitor.record_flush_time(flush_time)
            logger.error(f"[{self.db_writer.botnet_type}] Flush failed after {flush_time:.2f}s: {e}")
            raise


def create_monitored_writer(botnet_type: str, db_config: dict, batch_size: int = 500):
    """创建带性能监控的数据库写入器"""
    from .db_writer import BotnetDBWriter

    # 创建性能监控器
    monitor = PerformanceMonitor(db_config)
    monitor.start_monitoring()

    # 创建优化的写入器（现在已经包含所有优化功能和内置监控）
    writer = BotnetDBWriter(
        botnet_type, 
        db_config, 
        batch_size, 
        use_connection_pool=True,
        enable_monitoring=True
    )

    # 包装为带监控的写入器
    monitored_writer = TimedDBWriter(writer, monitor)

    return monitored_writer, monitor
