"""
数据保留策略管理器
整合归档和清理功能，提供统一的定时任务入口
"""
import logging
import sys
import os
from datetime import datetime, timedelta
import json

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG
from scripts.data_archiver import DataArchiver
from scripts.data_cleaner import DataCleaner
from scripts.data_retention_config import (
    BOTNET_TYPES, HOT_DATA_DAYS, ENABLE_ARCHIVE, CLEANUP_ENABLED,
    validate_config
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/var/log/botnet/retention_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RetentionManager:
    """数据保留策略管理器"""
    
    def __init__(self, db_config, dry_run: bool = False):
        """
        初始化管理器
        
        Args:
            db_config: 数据库配置
            dry_run: 演练模式
        """
        self.db_config = db_config
        self.dry_run = dry_run
        self.archiver = DataArchiver(db_config)
        self.cleaner = DataCleaner(db_config, dry_run=dry_run)
        
        # 验证配置
        try:
            validate_config()
            logger.info("✅ 配置验证通过")
        except ValueError as e:
            logger.error(f"❌ 配置验证失败: {e}")
            raise
    
    def run_daily_maintenance(self):
        """
        执行每日数据维护任务
        
        流程：
        1. 归档上个月的数据
        2. 标记已归档数据
        3. 清理已归档的旧数据
        4. 生成维护报告
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"开始每日数据维护任务")
        logger.info(f"时间: {datetime.now()}")
        logger.info(f"演练模式: {self.dry_run}")
        logger.info(f"{'='*80}\n")
        
        report = {
            'start_time': datetime.now().isoformat(),
            'dry_run': self.dry_run,
            'archive_summary': None,
            'cleanup_summary': None,
            'errors': []
        }
        
        # 步骤1: 归档数据
        if ENABLE_ARCHIVE:
            logger.info("\n[步骤 1/3] 归档数据")
            logger.info("-" * 60)
            
            try:
                # 归档上个月的数据
                last_month = datetime.now() - timedelta(days=30)
                
                if not self.dry_run:
                    archive_summary = self.archiver.archive_old_data(months_ago=1)
                    report['archive_summary'] = archive_summary
                    logger.info(f"✅ 归档完成: {archive_summary['total_archived']} 条记录")
                else:
                    logger.info("[演练模式] 跳过实际归档")
                    
            except Exception as e:
                error_msg = f"归档失败: {e}"
                logger.error(error_msg, exc_info=True)
                report['errors'].append(error_msg)
        else:
            logger.info("[跳过] 归档功能未启用")
        
        # 步骤2: 标记已归档数据
        logger.info("\n[步骤 2/3] 标记已归档数据")
        logger.info("-" * 60)
        
        try:
            if not self.dry_run:
                cutoff_date = datetime.now() - timedelta(days=HOT_DATA_DAYS)
                start_of_time = datetime(2000, 1, 1)
                
                for botnet_type in BOTNET_TYPES:
                    self.cleaner.mark_as_archived(
                        botnet_type,
                        start_of_time,
                        cutoff_date
                    )
                
                logger.info("✅ 标记完成")
            else:
                logger.info("[演练模式] 跳过标记")
                
        except Exception as e:
            error_msg = f"标记失败: {e}"
            logger.error(error_msg, exc_info=True)
            report['errors'].append(error_msg)
        
        # 步骤3: 清理旧数据
        if CLEANUP_ENABLED:
            logger.info("\n[步骤 3/3] 清理旧数据")
            logger.info("-" * 60)
            
            try:
                cleanup_summary = self.cleaner.cleanup_old_data(days=HOT_DATA_DAYS)
                report['cleanup_summary'] = cleanup_summary
                
                if not self.dry_run:
                    logger.info(f"✅ 清理完成: {cleanup_summary['total_deleted']} 条记录")
                else:
                    logger.info(f"[演练模式] 预计清理: {cleanup_summary['total_deleted']} 条记录")
                    
            except Exception as e:
                error_msg = f"清理失败: {e}"
                logger.error(error_msg, exc_info=True)
                report['errors'].append(error_msg)
        else:
            logger.info("[跳过] 清理功能未启用")
        
        # 生成报告
        report['end_time'] = datetime.now().isoformat()
        report['duration_seconds'] = (
            datetime.fromisoformat(report['end_time']) - 
            datetime.fromisoformat(report['start_time'])
        ).total_seconds()
        
        self._save_report(report)
        self._print_summary(report)
        
        return report
    
    def _save_report(self, report: dict):
        """保存维护报告"""
        try:
            report_dir = '/var/log/botnet/reports'
            os.makedirs(report_dir, exist_ok=True)
            
            report_file = os.path.join(
                report_dir,
                f"retention_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"报告已保存: {report_file}")
            
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
    
    def _print_summary(self, report: dict):
        """打印维护摘要"""
        logger.info(f"\n{'='*80}")
        logger.info(f"维护任务完成")
        logger.info(f"{'='*80}")
        
        logger.info(f"开始时间: {report['start_time']}")
        logger.info(f"结束时间: {report['end_time']}")
        logger.info(f"总耗时: {report['duration_seconds']:.2f} 秒")
        
        if report.get('archive_summary'):
            summary = report['archive_summary']
            logger.info(f"\n归档统计:")
            logger.info(f"  - 总归档记录: {summary['total_archived']}")
            logger.info(f"  - 成功归档: {len(summary['successful_archives'])} 个僵尸网络")
        
        if report.get('cleanup_summary'):
            summary = report['cleanup_summary']
            logger.info(f"\n清理统计:")
            logger.info(f"  - 总删除记录: {summary['total_deleted']}")
            for botnet_type, count in summary['by_botnet'].items():
                if count > 0:
                    logger.info(f"    • {botnet_type}: {count} 条")
        
        if report['errors']:
            logger.warning(f"\n⚠️ 发生 {len(report['errors'])} 个错误:")
            for error in report['errors']:
                logger.warning(f"  - {error}")
        else:
            logger.info(f"\n✅ 所有任务成功完成，无错误")
        
        logger.info(f"\n{'='*80}\n")
    
    def initialize_tables(self):
        """
        初始化表结构
        为所有通信记录表添加archived字段
        """
        logger.info("初始化表结构...")
        
        for botnet_type in BOTNET_TYPES:
            self.cleaner.add_archived_column(botnet_type)
        
        logger.info("✅ 表结构初始化完成")
    
    def manual_archive(self, year: int, month: int):
        """
        手动归档指定月份的数据
        
        Args:
            year: 年份
            month: 月份
        """
        logger.info(f"手动归档 {year}年{month}月 的数据")
        
        for botnet_type in BOTNET_TYPES:
            self.archiver.archive_communications_by_month(
                botnet_type, year, month
            )
    
    def manual_cleanup(self, days: int):
        """
        手动清理指定天数之前的数据
        
        Args:
            days: 删除多少天之前的数据
        """
        logger.info(f"手动清理 {days} 天之前的数据")
        
        self.cleaner.cleanup_old_data(days=days)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据保留策略管理器')
    parser.add_argument(
        '--mode',
        choices=['daily', 'init', 'archive', 'cleanup'],
        default='daily',
        help='运行模式'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='演练模式，不实际修改数据'
    )
    parser.add_argument('--year', type=int, help='年份（归档模式）')
    parser.add_argument('--month', type=int, help='月份（归档模式）')
    parser.add_argument('--days', type=int, help='天数（清理模式）')
    
    args = parser.parse_args()
    
    try:
        manager = RetentionManager(DB_CONFIG, dry_run=args.dry_run)
        
        if args.mode == 'daily':
            # 每日维护任务
            manager.run_daily_maintenance()
        elif args.mode == 'init':
            # 初始化表结构
            manager.initialize_tables()
        elif args.mode == 'archive':
            # 手动归档
            if not args.year or not args.month:
                print("错误: archive模式需要 --year 和 --month 参数")
                return
            manager.manual_archive(args.year, args.month)
        elif args.mode == 'cleanup':
            # 手动清理
            if not args.days:
                print("错误: cleanup模式需要 --days 参数")
                return
            manager.manual_cleanup(args.days)
    
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
