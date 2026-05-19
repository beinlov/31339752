#!/usr/bin/env python3
"""
UTG-Q-008 节点数据导入脚本
从 008.xlsx 读取IP数据，进行富化并写入数据库
"""
import sys
import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

try:
    import pandas as pd
    from openpyxl import load_workbook
except ImportError:
    print("缺少依赖包，正在安装...")
    os.system("pip3 install pandas openpyxl -q")
    import pandas as pd
    from openpyxl import load_workbook

from log_processor.enricher import IPEnricher
from log_processor.db_writer import BotnetDBWriter
from config import DB_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def import_utg_q_008(excel_file: str):
    """
    导入 UTG-Q-008 节点数据
    
    Args:
        excel_file: Excel文件路径
    """
    try:
        botnet_type = 'utg_q_008'
        
        logger.info(f"\n{'='*60}")
        logger.info(f"开始导入 UTG-Q-008 节点数据")
        logger.info(f"Excel文件: {excel_file}")
        logger.info(f"{'='*60}")
        
        # 检查文件是否存在
        if not os.path.exists(excel_file):
            logger.error(f"文件不存在: {excel_file}")
            return
        
        # 读取Excel文件
        logger.info("正在读取Excel文件...")
        df = pd.read_excel(excel_file)
        
        # 查找包含IP的列
        ip_column = None
        for col in df.columns:
            col_lower = str(col).lower()
            if 'ip' in col_lower or col_lower == 'ip':
                ip_column = col
                break
        
        if ip_column is None:
            # 如果没有找到IP列，尝试使用第一列
            ip_column = df.columns[0]
            logger.warning(f"未找到IP列，使用第一列: {ip_column}")
        
        # 提取IP地址并去重
        ips = df[ip_column].dropna().astype(str).unique().tolist()
        
        # 过滤无效IP
        valid_ips = []
        for ip in ips:
            ip = ip.strip()
            # 简单验证IP格式
            parts = ip.split('.')
            if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                valid_ips.append(ip)
            else:
                logger.debug(f"跳过无效IP: {ip}")
        
        logger.info(f"找到 {len(valid_ips)} 个有效IP")
        
        if not valid_ips:
            logger.warning("没有有效IP，退出")
            return
        
        # 创建IP富化器
        enricher = IPEnricher(
            cache_size=20000,
            cache_ttl=86400,
            max_concurrent=50
        )
        
        # 创建数据库写入器
        writer = BotnetDBWriter(botnet_type, DB_CONFIG, batch_size=500)
        
        # 当前时间作为所有记录的时间戳
        current_time = datetime.now()
        
        logger.info(f"开始处理 {len(valid_ips)} 个IP...")
        
        # 批量处理IP
        batch_size = 100
        processed_count = 0
        error_count = 0
        
        for i in range(0, len(valid_ips), batch_size):
            batch_ips = valid_ips[i:i + batch_size]
            
            # 并发富化IP信息
            tasks = [enricher.enrich(ip) for ip in batch_ips]
            ip_infos = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 写入数据库
            for ip, ip_info in zip(batch_ips, ip_infos):
                try:
                    # 如果富化失败，使用默认信息
                    if isinstance(ip_info, Exception):
                        logger.warning(f"IP富化失败 {ip}: {ip_info}")
                        ip_info = {
                            'ip': ip,
                            'country': '未知',
                            'province': '',
                            'city': '',
                            'isp': '',
                            'asn': '',
                            'longitude': 0.0,
                            'latitude': 0.0,
                            'continent': '',
                            'is_china': False
                        }
                    
                    # 构造日志数据格式
                    log_data = {
                        'ip': ip,
                        'timestamp': current_time,
                        'event_type': 'excel_import',
                        'source': 'excel_importer',
                        'date': current_time.strftime('%Y-%m-%d'),
                        'botnet_type': botnet_type
                    }
                    
                    # 写入数据库
                    writer.add_node(log_data, ip_info)
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"处理IP {ip} 失败: {e}")
                    error_count += 1
            
            # 显示进度
            progress = min(i + batch_size, len(valid_ips))
            logger.info(f"进度: {progress}/{len(valid_ips)} ({progress*100//len(valid_ips)}%)")
        
        # 强制刷新到数据库
        logger.info("正在写入数据库...")
        await writer.flush(force=True)
        
        # 显示统计信息
        stats = writer.get_stats()
        enricher_stats = enricher.get_stats()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"UTG-Q-008 导入完成")
        logger.info(f"{'='*60}")
        logger.info(f"总IP数: {len(valid_ips)}")
        logger.info(f"成功处理: {processed_count}")
        logger.info(f"处理失败: {error_count}")
        logger.info(f"写入节点数: {stats['total_written']}")
        logger.info(f"去重数量: {stats['duplicate_count']}")
        logger.info(f"去重率: {stats['duplicate_rate']}")
        logger.info(f"IP富化缓存命中率: {enricher_stats['total_cache_hit_rate']}")
        logger.info(f"{'='*60}\n")
        
    except Exception as e:
        logger.error(f"导入过程中发生错误: {e}", exc_info=True)


async def main():
    """主函数"""
    # Excel文件路径
    excel_file = os.path.join(os.path.dirname(__file__), '008.xlsx')
    
    # 执行导入
    await import_utg_q_008(excel_file)


if __name__ == '__main__':
    # 运行导入任务
    asyncio.run(main())
