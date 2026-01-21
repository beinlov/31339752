"""
数据清理工具
删除已归档的旧数据，释放数据库存储空间
"""
import pymysql
import logging
import time
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG
from scripts.data_retention_config import (
    BOTNET_TYPES, HOT_DATA_DAYS, CLEANUP_BATCH_SIZE,
    CLEANUP_DELAY_SECONDS, MAX_DELETE_PER_RUN,
    REQUIRE_ARCHIVE_BEFORE_DELETE
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/var/log/botnet/cleaner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataCleaner:
    """数据清理器"""
    
    def __init__(self, db_config: Dict, dry_run: bool = False):
        """
        初始化数据清理器
        
        Args:
            db_config: 数据库配置
            dry_run: 是否为演练模式（不实际删除数据）
        """
        self.db_config = db_config
        self.dry_run = dry_run
        self.deleted_count = 0
    
    def connect_db(self):
        """建立数据库连接"""
        return pymysql.connect(**self.db_config)
    
    def cleanup_communications(
        self, 
        botnet_type: str,
        before_date: datetime,
        archived_only: bool = True
    ) -> int:
        """
        清理通信记录表的旧数据
        
        Args:
            botnet_type: 僵尸网络类型
            before_date: 删除此日期之前的数据
            archived_only: 是否仅删除已标记为archived的数据
            
        Returns:
            删除的记录数
        """
        table_name = f"botnet_communications_{botnet_type}"
        
        logger.info(f"{'='*60}")
        logger.info(f"开始清理 {table_name}")
        logger.info(f"删除 {before_date.date()} 之前的数据")
        logger.info(f"仅删除已归档: {archived_only}")
        logger.info(f"演练模式: {self.dry_run}")
        logger.info(f"{'='*60}")
        
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            
            # 1. 检查表是否存在archived字段
            has_archived_column = self._check_archived_column(cursor, table_name)
            
            # 2. 先统计要删除的记录数
            count_query = f"""
                SELECT COUNT(*) as count
                FROM {table_name}
                WHERE communication_time < %s
            """
            
            if archived_only and has_archived_column:
                count_query += " AND archived = 1"
            
            cursor.execute(count_query, [before_date])
            total_to_delete = cursor.fetchone()[0]
            
            if total_to_delete == 0:
                logger.info(f"没有需要删除的数据")
                conn.close()
                return 0
            
            logger.info(f"预计删除 {total_to_delete} 条记录")
            
            # 3. 如果是演练模式，直接返回
            if self.dry_run:
                logger.info(f"[演练模式] 将删除 {total_to_delete} 条记录（未实际执行）")
                conn.close()
                return total_to_delete
            
            # 4. 安全检查：如果需要归档但没有archived列，拒绝删除
            if REQUIRE_ARCHIVE_BEFORE_DELETE and not has_archived_column:
                logger.warning(f"表 {table_name} 没有archived字段，拒绝删除")
                logger.warning(f"请先运行归档脚本或添加archived字段")
                conn.close()
                return 0
            
            # 5. 分批删除数据
            deleted_count = self._delete_in_batches(
                cursor, 
                table_name,
                before_date,
                archived_only and has_archived_column,
                total_to_delete
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ 清理完成: 已删除 {deleted_count} 条记录")
            
            self.deleted_count += deleted_count
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理失败: {e}", exc_info=True)
            return 0
    
    def _check_archived_column(self, cursor, table_name: str) -> bool:
        """检查表是否有archived字段"""
        try:
            cursor.execute(f"""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = %s
                AND COLUMN_NAME = 'archived'
            """, [table_name])
            
            result = cursor.fetchone()
            has_column = result is not None
            
            if not has_column:
                logger.warning(f"表 {table_name} 没有 'archived' 字段")
            
            return has_column
            
        except Exception as e:
            logger.error(f"检查字段失败: {e}")
            return False
    
    def _delete_in_batches(
        self,
        cursor,
        table_name: str,
        before_date: datetime,
        archived_only: bool,
        total_to_delete: int
    ) -> int:
        """
        分批删除数据，避免长时间锁表
        
        Args:
            cursor: 数据库游标
            table_name: 表名
            before_date: 删除此日期之前的数据
            archived_only: 是否仅删除已归档数据
            total_to_delete: 总共需要删除的记录数
            
        Returns:
            实际删除的记录数
        """
        total_deleted = 0
        batch_count = 0
        max_batches = (MAX_DELETE_PER_RUN + CLEANUP_BATCH_SIZE - 1) // CLEANUP_BATCH_SIZE
        
        while total_deleted < total_to_delete and batch_count < max_batches:
            # 构建删除语句
            delete_query = f"""
                DELETE FROM {table_name}
                WHERE communication_time < %s
            """
            
            if archived_only:
                delete_query += " AND archived = 1"
            
            delete_query += f" LIMIT {CLEANUP_BATCH_SIZE}"
            
            # 执行删除
            start_time = time.time()
            cursor.execute(delete_query, [before_date])
            deleted_in_batch = cursor.rowcount
            duration = time.time() - start_time
            
            if deleted_in_batch == 0:
                break
            
            total_deleted += deleted_in_batch
            batch_count += 1
            
            # 输出进度
            progress = (total_deleted / total_to_delete) * 100
            logger.info(
                f"批次 {batch_count}: 删除 {deleted_in_batch} 条, "
                f"累计 {total_deleted}/{total_to_delete} ({progress:.1f}%), "
                f"耗时 {duration:.2f}s"
            )
            
            # 批次间延迟，避免过载
            if CLEANUP_DELAY_SECONDS > 0 and deleted_in_batch == CLEANUP_BATCH_SIZE:
                time.sleep(CLEANUP_DELAY_SECONDS)
            
            # 达到单次运行上限
            if total_deleted >= MAX_DELETE_PER_RUN:
                logger.warning(f"达到单次删除上限 {MAX_DELETE_PER_RUN}，停止删除")
                logger.warning(f"剩余 {total_to_delete - total_deleted} 条记录未删除")
                break
        
        return total_deleted
    
    def cleanup_old_data(self, days: int = None):
        """
        清理所有僵尸网络的旧数据
        
        Args:
            days: 删除多少天之前的数据（默认使用HOT_DATA_DAYS）
        """
        if days is None:
            days = HOT_DATA_DAYS
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"开始清理旧数据")
        logger.info(f"删除 {cutoff_date.date()} 之前的数据")
        logger.info(f"{'='*60}\n")
        
        summary = {
            'total_deleted': 0,
            'by_botnet': {}
        }
        
        for botnet_type in BOTNET_TYPES:
            deleted = self.cleanup_communications(
                botnet_type,
                cutoff_date,
                archived_only=REQUIRE_ARCHIVE_BEFORE_DELETE
            )
            
            summary['total_deleted'] += deleted
            summary['by_botnet'][botnet_type] = deleted
        
        # 输出清理摘要
        logger.info(f"\n{'='*60}")
        logger.info(f"清理摘要")
        logger.info(f"{'='*60}")
        logger.info(f"总删除记录数: {summary['total_deleted']}")
        
        for botnet_type, count in summary['by_botnet'].items():
            if count > 0:
                logger.info(f"  - {botnet_type}: {count} 条")
        
        return summary
    
    def add_archived_column(self, botnet_type: str):
        """
        为通信记录表添加archived字段
        
        Args:
            botnet_type: 僵尸网络类型
        """
        table_name = f"botnet_communications_{botnet_type}"
        
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            
            # 检查字段是否存在
            if self._check_archived_column(cursor, table_name):
                logger.info(f"{table_name} 已有archived字段")
                conn.close()
                return
            
            # 添加字段
            logger.info(f"为 {table_name} 添加archived字段...")
            cursor.execute(f"""
                ALTER TABLE {table_name}
                ADD COLUMN archived TINYINT(1) DEFAULT 0 COMMENT '是否已归档'
            """)
            
            # 添加索引
            cursor.execute(f"""
                ALTER TABLE {table_name}
                ADD INDEX idx_archived (archived)
            """)
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ 字段添加成功")
            
        except Exception as e:
            logger.error(f"添加字段失败: {e}")
    
    def mark_as_archived(
        self,
        botnet_type: str,
        start_date: datetime,
        end_date: datetime
    ):
        """
        标记数据为已归档
        
        Args:
            botnet_type: 僵尸网络类型
            start_date: 开始日期
            end_date: 结束日期
        """
        table_name = f"botnet_communications_{botnet_type}"
        
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            
            # 确保有archived字段
            if not self._check_archived_column(cursor, table_name):
                logger.error(f"表没有archived字段，请先添加")
                conn.close()
                return
            
            # 标记为已归档
            update_query = f"""
                UPDATE {table_name}
                SET archived = 1
                WHERE communication_time >= %s
                AND communication_time < %s
                AND archived = 0
            """
            
            cursor.execute(update_query, [start_date, end_date])
            updated_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"标记 {updated_count} 条记录为已归档")
            
        except Exception as e:
            logger.error(f"标记失败: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据清理工具')
    parser.add_argument(
        '--mode',
        choices=['auto', 'custom', 'add-column', 'mark-archived'],
        default='auto',
        help='清理模式'
    )
    parser.add_argument(
        '--days',
        type=int,
        help='删除多少天之前的数据'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='演练模式，不实际删除数据'
    )
    parser.add_argument(
        '--botnet-type',
        help='指定僵尸网络类型'
    )
    
    args = parser.parse_args()
    
    cleaner = DataCleaner(DB_CONFIG, dry_run=args.dry_run)
    
    if args.mode == 'auto':
        # 自动清理
        cleaner.cleanup_old_data(days=args.days)
    elif args.mode == 'custom':
        # 自定义清理
        if not args.botnet_type or not args.days:
            print("错误: custom模式需要 --botnet-type 和 --days 参数")
            return
        
        cutoff_date = datetime.now() - timedelta(days=args.days)
        cleaner.cleanup_communications(
            args.botnet_type,
            cutoff_date,
            archived_only=REQUIRE_ARCHIVE_BEFORE_DELETE
        )
    elif args.mode == 'add-column':
        # 为所有表添加archived字段
        for botnet_type in BOTNET_TYPES:
            cleaner.add_archived_column(botnet_type)
    elif args.mode == 'mark-archived':
        # 标记数据为已归档（用于迁移）
        if not args.botnet_type:
            print("错误: 需要 --botnet-type 参数")
            return
        
        # 标记30天之前的数据为已归档
        end_date = datetime.now() - timedelta(days=30)
        start_date = datetime(2000, 1, 1)  # 从很早开始
        
        cleaner.mark_as_archived(args.botnet_type, start_date, end_date)


if __name__ == "__main__":
    main()
