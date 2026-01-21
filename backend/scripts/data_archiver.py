"""
数据归档工具
将超过保留期的数据导出为压缩文件存储
"""
import pymysql
import pandas as pd
import logging
import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG
from scripts.data_retention_config import (
    BOTNET_TYPES, HOT_DATA_DAYS, WARM_DATA_DAYS,
    get_archive_path, ARCHIVE_FORMAT, ARCHIVE_COMPRESSION,
    VALIDATE_ARCHIVE_INTEGRITY, ARCHIVE_CHECKSUM_ALGORITHM
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/var/log/botnet/archiver.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataArchiver:
    """数据归档器"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.archived_count = 0
        self.archive_metadata = {}
    
    def connect_db(self):
        """建立数据库连接"""
        return pymysql.connect(**self.db_config)
    
    def archive_communications_by_month(
        self, 
        botnet_type: str, 
        year: int, 
        month: int
    ) -> Tuple[bool, str, int]:
        """
        按月归档通信记录
        
        Args:
            botnet_type: 僵尸网络类型
            year: 年份
            month: 月份
            
        Returns:
            (成功标志, 归档文件路径, 归档记录数)
        """
        table_name = f"botnet_communications_{botnet_type}"
        
        # 计算时间范围
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        logger.info(f"开始归档 {table_name} 数据: {start_date.date()} ~ {end_date.date()}")
        
        try:
            conn = self.connect_db()
            
            # 1. 查询数据
            query = f"""
                SELECT *
                FROM {table_name}
                WHERE communication_time >= %s
                AND communication_time < %s
                ORDER BY communication_time
            """
            
            df = pd.read_sql(query, conn, params=[start_date, end_date])
            conn.close()
            
            if df.empty:
                logger.info(f"没有需要归档的数据")
                return False, "", 0
            
            record_count = len(df)
            logger.info(f"读取到 {record_count} 条记录")
            
            # 2. 生成归档文件路径
            archive_file = get_archive_path(botnet_type, 'communications', year, month)
            
            # 3. 保存为指定格式
            if ARCHIVE_FORMAT == 'parquet':
                df.to_parquet(
                    archive_file, 
                    compression=ARCHIVE_COMPRESSION,
                    index=False
                )
            elif ARCHIVE_FORMAT == 'json':
                df.to_json(
                    archive_file + '.gz', 
                    orient='records',
                    compression='gzip'
                )
                archive_file = archive_file + '.gz'
            elif ARCHIVE_FORMAT == 'csv':
                df.to_csv(
                    archive_file + '.gz',
                    index=False,
                    compression='gzip'
                )
                archive_file = archive_file + '.gz'
            else:
                raise ValueError(f"不支持的归档格式: {ARCHIVE_FORMAT}")
            
            logger.info(f"归档文件已保存: {archive_file}")
            
            # 4. 验证归档完整性
            if VALIDATE_ARCHIVE_INTEGRITY:
                if not self._validate_archive(archive_file, record_count):
                    raise Exception("归档文件验证失败")
            
            # 5. 生成元数据
            metadata = {
                'botnet_type': botnet_type,
                'table_name': table_name,
                'year': year,
                'month': month,
                'record_count': record_count,
                'archive_file': archive_file,
                'archive_time': datetime.now().isoformat(),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'file_size': os.path.getsize(archive_file),
                'checksum': self._calculate_checksum(archive_file)
            }
            
            # 保存元数据
            metadata_file = archive_file + '.meta.json'
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ 归档完成: {record_count} 条记录 -> {archive_file}")
            
            self.archived_count += record_count
            self.archive_metadata[f"{botnet_type}_{year}{month:02d}"] = metadata
            
            return True, archive_file, record_count
            
        except Exception as e:
            logger.error(f"归档失败: {e}", exc_info=True)
            return False, "", 0
    
    def _validate_archive(self, archive_file: str, expected_count: int) -> bool:
        """
        验证归档文件完整性
        
        Args:
            archive_file: 归档文件路径
            expected_count: 预期记录数
            
        Returns:
            验证是否通过
        """
        try:
            if ARCHIVE_FORMAT == 'parquet':
                df = pd.read_parquet(archive_file)
            elif ARCHIVE_FORMAT == 'json':
                df = pd.read_json(archive_file, compression='gzip')
            elif ARCHIVE_FORMAT == 'csv':
                df = pd.read_csv(archive_file, compression='gzip')
            else:
                return False
            
            actual_count = len(df)
            if actual_count != expected_count:
                logger.error(f"记录数不匹配: 预期 {expected_count}, 实际 {actual_count}")
                return False
            
            logger.info(f"归档文件验证通过: {actual_count} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"归档文件验证失败: {e}")
            return False
    
    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        hash_func = hashlib.new(ARCHIVE_CHECKSUM_ALGORITHM)
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    def archive_old_data(self, months_ago: int = 1):
        """
        归档指定月份之前的数据
        
        Args:
            months_ago: 归档几个月之前的数据（默认1个月前）
        """
        target_date = datetime.now() - timedelta(days=30 * months_ago)
        year = target_date.year
        month = target_date.month
        
        logger.info(f"{'='*60}")
        logger.info(f"开始归档 {year}年{month}月 的数据")
        logger.info(f"{'='*60}")
        
        summary = {
            'total_archived': 0,
            'successful_archives': [],
            'failed_archives': []
        }
        
        for botnet_type in BOTNET_TYPES:
            success, archive_file, count = self.archive_communications_by_month(
                botnet_type, year, month
            )
            
            if success:
                summary['total_archived'] += count
                summary['successful_archives'].append({
                    'botnet_type': botnet_type,
                    'file': archive_file,
                    'count': count
                })
            else:
                summary['failed_archives'].append(botnet_type)
        
        # 输出归档摘要
        logger.info(f"\n{'='*60}")
        logger.info(f"归档摘要")
        logger.info(f"{'='*60}")
        logger.info(f"总归档记录数: {summary['total_archived']}")
        logger.info(f"成功归档: {len(summary['successful_archives'])} 个僵尸网络")
        logger.info(f"失败归档: {len(summary['failed_archives'])} 个僵尸网络")
        
        if summary['failed_archives']:
            logger.warning(f"失败列表: {', '.join(summary['failed_archives'])}")
        
        return summary
    
    def archive_range(self, start_year: int, start_month: int, end_year: int, end_month: int):
        """
        归档指定时间范围的数据
        
        Args:
            start_year: 开始年份
            start_month: 开始月份
            end_year: 结束年份
            end_month: 结束月份
        """
        current_year = start_year
        current_month = start_month
        
        total_archived = 0
        
        while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
            logger.info(f"\n归档 {current_year}-{current_month:02d}")
            
            for botnet_type in BOTNET_TYPES:
                success, _, count = self.archive_communications_by_month(
                    botnet_type, current_year, current_month
                )
                if success:
                    total_archived += count
            
            # 移动到下个月
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1
        
        logger.info(f"\n总计归档 {total_archived} 条记录")
        return total_archived


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据归档工具')
    parser.add_argument(
        '--mode',
        choices=['auto', 'month', 'range'],
        default='auto',
        help='归档模式: auto=自动归档上月数据, month=指定月份, range=时间范围'
    )
    parser.add_argument('--year', type=int, help='年份')
    parser.add_argument('--month', type=int, help='月份')
    parser.add_argument('--start-year', type=int, help='开始年份')
    parser.add_argument('--start-month', type=int, help='开始月份')
    parser.add_argument('--end-year', type=int, help='结束年份')
    parser.add_argument('--end-month', type=int, help='结束月份')
    
    args = parser.parse_args()
    
    archiver = DataArchiver(DB_CONFIG)
    
    if args.mode == 'auto':
        # 自动归档上个月的数据
        archiver.archive_old_data(months_ago=1)
    elif args.mode == 'month':
        # 归档指定月份
        if not args.year or not args.month:
            print("错误: --year 和 --month 参数必须提供")
            return
        
        for botnet_type in BOTNET_TYPES:
            archiver.archive_communications_by_month(
                botnet_type, args.year, args.month
            )
    elif args.mode == 'range':
        # 归档时间范围
        if not all([args.start_year, args.start_month, args.end_year, args.end_month]):
            print("错误: 必须提供 --start-year, --start-month, --end-year, --end-month")
            return
        
        archiver.archive_range(
            args.start_year, args.start_month,
            args.end_year, args.end_month
        )


if __name__ == "__main__":
    main()
