#!/usr/bin/env python3
"""检查并创建缺失的僵尸网络数据表"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pymysql
from config import DB_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_create_tables():
    """检查所有僵尸网络类型的表，创建缺失的表"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 获取所有已注册的僵尸网络类型
        cursor.execute("SELECT name, display_name FROM botnet_types")
        botnets = cursor.fetchall()
        
        logger.info(f"找到 {len(botnets)} 个已注册的僵尸网络类型")
        
        for bot in botnets:
            name = bot['name']
            display_name = bot.get('display_name', name)
            logger.info(f"\n检查僵尸网络: {name} ({display_name})")
            
            # 定义需要的4个表
            tables_needed = {
                f'china_botnet_{name}': '中国地区统计表',
                f'global_botnet_{name}': '全球统计表',
                f'botnet_nodes_{name}': '节点表',
                f'botnet_communications_{name}': '通信记录表'
            }
            
            # 检查每个表是否存在
            missing_tables = []
            for table_name, description in tables_needed.items():
                cursor.execute("""
                    SELECT COUNT(*) as cnt
                    FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = %s
                """, (DB_CONFIG['database'], table_name))
                
                exists = cursor.fetchone()['cnt'] > 0
                if exists:
                    logger.info(f"  ✓ {table_name} ({description}) 存在")
                else:
                    logger.warning(f"  ✗ {table_name} ({description}) 缺失")
                    missing_tables.append(table_name)
            
            # 如果有缺失的表，创建它们
            if missing_tables:
                logger.info(f"\n开始为 {name} 创建缺失的表...")
                create_missing_tables(cursor, name, missing_tables)
                conn.commit()
                logger.info(f"✓ 成功为 {name} 创建所有缺失的表")
            else:
                logger.info(f"  ✓ {name} 的所有表都已存在")
        
        logger.info("\n所有僵尸网络表检查完成！")
        
    except Exception as e:
        logger.error(f"发生错误: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def create_missing_tables(cursor, bot_name, missing_tables):
    """为指定僵尸网络创建缺失的表"""
    
    china_table = f"china_botnet_{bot_name}"
    global_table = f"global_botnet_{bot_name}"
    node_table = f"botnet_nodes_{bot_name}"
    communication_table = f"botnet_communications_{bot_name}"
    
    # 创建中国区域统计表
    if china_table in missing_tables:
        logger.info(f"  创建 {china_table}...")
        cursor.execute(f"""
            CREATE TABLE {china_table} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                province VARCHAR(50) NOT NULL,
                municipality VARCHAR(50) NOT NULL,
                infected_num INT DEFAULT 0 COMMENT '感染数量（节点数）',
                communication_count INT DEFAULT 0 COMMENT '通信总次数',
                created_at TIMESTAMP NULL DEFAULT NULL COMMENT '该地区第一个节点的创建时间',
                updated_at TIMESTAMP NULL DEFAULT NULL COMMENT '该地区最新节点的更新时间',
                UNIQUE KEY idx_location (province, municipality),
                INDEX idx_province (province),
                INDEX idx_infected_num (infected_num),
                INDEX idx_communication_count (communication_count),
                INDEX idx_created_at (created_at),
                INDEX idx_updated_at (updated_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
            COMMENT='中国地区僵尸网络统计表(按省市)'
        """)
    
    # 创建全球统计表
    if global_table in missing_tables:
        logger.info(f"  创建 {global_table}...")
        cursor.execute(f"""
            CREATE TABLE {global_table} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                country VARCHAR(100) NOT NULL,
                infected_num INT DEFAULT 0 COMMENT '感染数量（节点数）',
                communication_count INT DEFAULT 0 COMMENT '通信总次数',
                created_at TIMESTAMP NULL DEFAULT NULL COMMENT '该国家第一个节点的创建时间',
                updated_at TIMESTAMP NULL DEFAULT NULL COMMENT '该国家最新节点的更新时间',
                UNIQUE KEY idx_country (country),
                INDEX idx_infected_num (infected_num),
                INDEX idx_communication_count (communication_count),
                INDEX idx_created_at (created_at),
                INDEX idx_updated_at (updated_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
            COMMENT='全球僵尸网络统计表(按国家)'
        """)
    
    # 创建节点表
    if node_table in missing_tables:
        logger.info(f"  创建 {node_table}...")
        cursor.execute(f"""
            CREATE TABLE {node_table} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip VARCHAR(15) NOT NULL COMMENT '节点IP地址',
                longitude FLOAT COMMENT '经度',
                latitude FLOAT COMMENT '纬度',
                country VARCHAR(50) COMMENT '国家',
                province VARCHAR(50) COMMENT '省份',
                city VARCHAR(50) COMMENT '城市',
                continent VARCHAR(50) COMMENT '洲',
                isp VARCHAR(255) COMMENT 'ISP运营商',
                asn VARCHAR(50) COMMENT 'AS号',
                status ENUM('active', 'inactive') DEFAULT 'active' COMMENT '节点状态',
                first_seen TIMESTAMP NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
                last_seen TIMESTAMP NULL DEFAULT NULL COMMENT '最后通信时间（日志时间）',
                communication_count INT DEFAULT 0 COMMENT '通信次数',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
                is_china BOOLEAN DEFAULT FALSE COMMENT '是否为中国节点',
                INDEX idx_ip (ip),
                INDEX idx_location (country, province, city),
                INDEX idx_status (status),
                INDEX idx_first_seen (first_seen),
                INDEX idx_last_seen (last_seen),
                INDEX idx_communication_count (communication_count),
                INDEX idx_is_china (is_china),
                UNIQUE KEY idx_unique_ip (ip)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
            COMMENT='僵尸网络节点基本信息表（汇总）'
        """)
    
    # 创建通信记录表
    if communication_table in missing_tables:
        logger.info(f"  创建 {communication_table}...")
        cursor.execute(f"""
            CREATE TABLE {communication_table} (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                node_id INT NOT NULL COMMENT '关联的节点ID',
                ip VARCHAR(15) NOT NULL COMMENT '节点IP',
                communication_time TIMESTAMP NOT NULL COMMENT '通信时间（日志时间）',
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '接收时间',
                longitude FLOAT COMMENT '经度',
                latitude FLOAT COMMENT '纬度',
                country VARCHAR(50) COMMENT '国家',
                province VARCHAR(50) COMMENT '省份',
                city VARCHAR(50) COMMENT '城市',
                continent VARCHAR(50) COMMENT '洲',
                isp VARCHAR(255) COMMENT 'ISP运营商',
                asn VARCHAR(50) COMMENT 'AS号',
                event_type VARCHAR(50) COMMENT '事件类型',
                status VARCHAR(50) DEFAULT 'active' COMMENT '通信状态',
                is_china BOOLEAN DEFAULT FALSE COMMENT '是否为中国节点',
                INDEX idx_node_id (node_id),
                INDEX idx_ip (ip),
                INDEX idx_communication_time (communication_time),
                INDEX idx_received_at (received_at),
                INDEX idx_location (country, province, city),
                INDEX idx_is_china (is_china),
                INDEX idx_composite (ip, communication_time),
                FOREIGN KEY (node_id) REFERENCES {node_table}(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
            COMMENT='僵尸网络节点通信记录表'
        """)

if __name__ == "__main__":
    check_and_create_tables()
