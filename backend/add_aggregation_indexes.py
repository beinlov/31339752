#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为聚合优化添加索引
解决聚合器慢的问题
"""

import pymysql
import logging
from config import DB_CONFIG, BOTNET_TYPES

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def add_aggregation_indexes():
    """为所有僵尸网络表添加聚合所需的索引"""
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        logger.info("=" * 60)
        logger.info("开始为聚合器添加优化索引")
        logger.info("=" * 60)
        
        for botnet_type in BOTNET_TYPES:
            node_table = f"botnet_nodes_{botnet_type}"
            
            # 检查表是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (DB_CONFIG['database'], node_table))
            
            if cursor.fetchone()[0] == 0:
                logger.info(f"[{botnet_type}] 表 {node_table} 不存在，跳过")
                continue
            
            logger.info(f"\n[{botnet_type}] 检查表 {node_table}...")
            
            # 检查现有索引
            cursor.execute(f"SHOW INDEX FROM {node_table}")
            existing_indexes = {row[2] for row in cursor.fetchall()}
            
            logger.info(f"  现有索引: {', '.join(existing_indexes) if existing_indexes else '无'}")
            
            # 需要添加的索引
            indexes_to_add = []
            
            # 1. country索引（聚合器最重要的索引）
            if 'idx_country' not in existing_indexes:
                indexes_to_add.append(('idx_country', 'country'))
                logger.info("  [需要] idx_country (country) - 用于WHERE country='中国'")
            
            # 2. province索引（用于GROUP BY）
            if 'idx_province' not in existing_indexes:
                indexes_to_add.append(('idx_province', 'province'))
                logger.info("  [需要] idx_province (province) - 用于GROUP BY province")
            
            # 3. city索引（用于GROUP BY）
            if 'idx_city' not in existing_indexes:
                indexes_to_add.append(('idx_city', 'city'))
                logger.info("  [需要] idx_city (city) - 用于GROUP BY city")
            
            # 4. 复合索引：country + province + city（最优化）
            if 'idx_country_province_city' not in existing_indexes:
                indexes_to_add.append(('idx_country_province_city', 'country, province, city'))
                logger.info("  [需要] idx_country_province_city - 用于聚合查询")
            
            # 5. updated_at索引（用于增量聚合）
            if 'idx_updated_at' not in existing_indexes:
                indexes_to_add.append(('idx_updated_at', 'updated_at'))
                logger.info("  [需要] idx_updated_at - 用于增量聚合")
            
            if not indexes_to_add:
                logger.info(f"  ✓ 所有索引已存在")
                continue
            
            # 添加索引
            logger.info(f"\n  开始添加 {len(indexes_to_add)} 个索引...")
            
            for idx_name, idx_columns in indexes_to_add:
                try:
                    logger.info(f"    添加 {idx_name}...")
                    cursor.execute(f"""
                        CREATE INDEX {idx_name} ON {node_table}({idx_columns})
                    """)
                    logger.info(f"    ✓ {idx_name} 添加成功")
                except pymysql.err.OperationalError as e:
                    if 'Duplicate key name' in str(e):
                        logger.info(f"    - {idx_name} 已存在，跳过")
                    else:
                        logger.error(f"    ✗ {idx_name} 添加失败: {e}")
            
            conn.commit()
            logger.info(f"  ✓ [{botnet_type}] 索引优化完成")
        
        logger.info("\n" + "=" * 60)
        logger.info("索引添加完成！")
        logger.info("=" * 60)
        logger.info("\n预期性能提升:")
        logger.info("  - WHERE country='中国': 从全表扫描 → 索引扫描 (100x)")
        logger.info("  - GROUP BY province, city: 从慢速分组 → 快速分组 (10x)")
        logger.info("  - 聚合总耗时: 预计从 几分钟 → 几秒钟")
        logger.info("\n建议:")
        logger.info("  - 重启聚合器以应用优化")
        logger.info("  - 观察日志中的 '耗时 X秒' 信息")
        logger.info("")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"添加索引失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    add_aggregation_indexes()
