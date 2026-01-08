"""
单个僵尸网络类型的数据库迁移脚本
从单表设计迁移到双表设计（节点表 + 通信记录表）

使用方法:
    python migrate_single_botnet.py <botnet_type>
    
例如:
    python migrate_single_botnet.py asruex
"""

import sys
import pymysql
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'botnet',
    'charset': 'utf8mb4'
}


def migrate_botnet(botnet_type):
    """迁移单个僵尸网络类型的数据库"""
    
    logger.info(f"=" * 60)
    logger.info(f"开始迁移僵尸网络: {botnet_type}")
    logger.info(f"=" * 60)
    
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        node_table = f"botnet_nodes_{botnet_type}"
        communication_table = f"botnet_communications_{botnet_type}"
        china_table = f"china_botnet_{botnet_type}"
        global_table = f"global_botnet_{botnet_type}"
        
        # ============================================
        # Step 1: 检查节点表是否存在
        # ============================================
        logger.info(f"Step 1: 检查节点表 {node_table} 是否存在...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], node_table))
        
        if cursor.fetchone()[0] == 0:
            logger.error(f"节点表 {node_table} 不存在！")
            return False
        
        logger.info("✓ 节点表存在")
        
        # ============================================
        # Step 2: 创建通信记录表
        # ============================================
        logger.info(f"Step 2: 创建通信记录表 {communication_table}...")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {communication_table} (
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
                INDEX idx_composite (ip, communication_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
            COMMENT='僵尸网络节点通信记录表'
        """)
        logger.info(f"✓ 通信记录表 {communication_table} 创建完成")
        
        # ============================================
        # Step 3: 修改节点表结构
        # ============================================
        logger.info(f"Step 3: 修改节点表结构...")
        
        # 检查字段存在性
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = %s
        """, (DB_CONFIG['database'], node_table))
        
        existing_columns = {row[0] for row in cursor.fetchall()}
        logger.info(f"现有字段: {existing_columns}")
        
        # 重命名 active_time 为 first_seen
        if 'active_time' in existing_columns and 'first_seen' not in existing_columns:
            logger.info("重命名 active_time -> first_seen...")
            cursor.execute(f"""
                ALTER TABLE {node_table} 
                CHANGE COLUMN active_time first_seen TIMESTAMP NULL DEFAULT NULL 
                COMMENT '首次发现时间（日志时间）'
            """)
            logger.info("✓ active_time 已重命名为 first_seen")
        
        # 重命名 updated_at 为 last_seen（临时）
        if 'updated_at' in existing_columns and 'last_seen' not in existing_columns:
            logger.info("重命名 updated_at -> last_seen...")
            cursor.execute(f"""
                ALTER TABLE {node_table} 
                CHANGE COLUMN updated_at last_seen TIMESTAMP NULL DEFAULT NULL 
                COMMENT '最后通信时间（日志时间）'
            """)
            logger.info("✓ updated_at 已重命名为 last_seen")
        
        # 添加 updated_at 字段（自动更新时间）
        if 'updated_at' not in existing_columns:
            logger.info("添加 updated_at 字段...")
            cursor.execute(f"""
                ALTER TABLE {node_table} 
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP 
                COMMENT '记录更新时间'
            """)
            logger.info("✓ updated_at 字段已添加")
        
        # 添加 communication_count 字段
        if 'communication_count' not in existing_columns:
            logger.info("添加 communication_count 字段...")
            cursor.execute(f"""
                ALTER TABLE {node_table}
                ADD COLUMN communication_count INT DEFAULT 0 COMMENT '通信次数'
            """)
            logger.info("✓ communication_count 字段已添加")
        
        # 添加索引
        logger.info("添加索引...")
        try:
            cursor.execute(f"ALTER TABLE {node_table} ADD INDEX idx_first_seen (first_seen)")
        except:
            pass
        try:
            cursor.execute(f"ALTER TABLE {node_table} ADD INDEX idx_last_seen (last_seen)")
        except:
            pass
        try:
            cursor.execute(f"ALTER TABLE {node_table} ADD INDEX idx_communication_count (communication_count)")
        except:
            pass
        
        logger.info("✓ 节点表结构修改完成")
        
        # ============================================
        # Step 4: 迁移历史数据
        # ============================================
        logger.info(f"Step 4: 迁移历史数据...")
        
        # 查询节点表数据量
        cursor.execute(f"SELECT COUNT(*) FROM {node_table}")
        node_count = cursor.fetchone()[0]
        logger.info(f"节点表共有 {node_count} 条记录")
        
        if node_count > 0:
            # 迁移第一次通信记录（使用 first_seen）
            logger.info("迁移第一次通信记录...")
            cursor.execute(f"""
                INSERT INTO {communication_table} 
                (node_id, ip, communication_time, received_at, longitude, latitude, 
                 country, province, city, continent, isp, asn, status, is_china)
                SELECT 
                    id, 
                    ip, 
                    COALESCE(first_seen, created_time) as communication_time,
                    created_time as received_at,
                    longitude, 
                    latitude,
                    country, 
                    province, 
                    city, 
                    continent, 
                    isp, 
                    asn, 
                    status, 
                    is_china
                FROM {node_table}
                WHERE first_seen IS NOT NULL OR created_time IS NOT NULL
            """)
            first_count = cursor.rowcount
            logger.info(f"✓ 已迁移 {first_count} 条第一次通信记录")
            
            # 迁移最后一次通信记录（使用 last_seen，如果与 first_seen 不同）
            logger.info("迁移最后一次通信记录...")
            cursor.execute(f"""
                INSERT INTO {communication_table} 
                (node_id, ip, communication_time, received_at, longitude, latitude, 
                 country, province, city, continent, isp, asn, status, is_china)
                SELECT 
                    id, 
                    ip, 
                    last_seen as communication_time,
                    created_time as received_at,
                    longitude, 
                    latitude,
                    country, 
                    province, 
                    city, 
                    continent, 
                    isp, 
                    asn, 
                    status, 
                    is_china
                FROM {node_table}
                WHERE last_seen IS NOT NULL 
                  AND (first_seen IS NULL OR last_seen != first_seen)
                  AND last_seen > COALESCE(first_seen, '1970-01-01')
            """)
            last_count = cursor.rowcount
            logger.info(f"✓ 已迁移 {last_count} 条最后一次通信记录")
            
            # 更新节点表的通信次数
            logger.info("更新节点通信次数统计...")
            cursor.execute(f"""
                UPDATE {node_table} n
                SET communication_count = (
                    SELECT COUNT(*) 
                    FROM {communication_table} c 
                    WHERE c.node_id = n.id
                )
            """)
            logger.info("✓ 节点通信次数统计已更新")
        
        # ============================================
        # Step 5: 更新统计表结构
        # ============================================
        logger.info(f"Step 5: 更新统计表结构...")
        
        # 检查统计表是否存在
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name IN (%s, %s)
        """, (DB_CONFIG['database'], china_table, global_table))
        
        existing_stat_tables = [row[0] for row in cursor.fetchall()]
        
        # 为中国统计表添加 communication_count
        if china_table in existing_stat_tables:
            cursor.execute(f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = 'communication_count'
            """, (DB_CONFIG['database'], china_table))
            
            if not cursor.fetchone():
                logger.info(f"为 {china_table} 添加 communication_count 字段...")
                cursor.execute(f"""
                    ALTER TABLE {china_table} 
                    ADD COLUMN communication_count INT DEFAULT 0 COMMENT '通信总次数'
                """)
                logger.info(f"✓ {china_table} 已添加 communication_count 字段")
        
        # 为全球统计表添加 communication_count
        if global_table in existing_stat_tables:
            cursor.execute(f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = 'communication_count'
            """, (DB_CONFIG['database'], global_table))
            
            if not cursor.fetchone():
                logger.info(f"为 {global_table} 添加 communication_count 字段...")
                cursor.execute(f"""
                    ALTER TABLE {global_table} 
                    ADD COLUMN communication_count INT DEFAULT 0 COMMENT '通信总次数'
                """)
                logger.info(f"✓ {global_table} 已添加 communication_count 字段")
        
        # ============================================
        # Step 6: 数据验证
        # ============================================
        logger.info(f"Step 6: 数据验证...")
        
        # 验证节点数量
        cursor.execute(f"SELECT COUNT(*) FROM {node_table}")
        node_count = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT COUNT(*) FROM {communication_table}")
        comm_count = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT COUNT(*) FROM {node_table} WHERE communication_count > 0")
        node_with_comm = cursor.fetchone()[0]
        
        logger.info(f"节点表记录数: {node_count}")
        logger.info(f"通信记录表记录数: {comm_count}")
        logger.info(f"有通信记录的节点数: {node_with_comm}")
        
        # 验证数据一致性
        cursor.execute(f"""
            SELECT 
                n.ip,
                n.communication_count as node_count,
                COUNT(c.id) as actual_count
            FROM {node_table} n
            LEFT JOIN {communication_table} c ON n.id = c.node_id
            GROUP BY n.id, n.ip, n.communication_count
            HAVING node_count != COUNT(c.id)
            LIMIT 5
        """)
        
        inconsistent = cursor.fetchall()
        if inconsistent:
            logger.warning(f"发现 {len(inconsistent)} 个数据不一致的节点:")
            for row in inconsistent:
                logger.warning(f"  IP: {row[0]}, 节点表计数: {row[1]}, 实际计数: {row[2]}")
        else:
            logger.info("✓ 数据一致性验证通过")
        
        # 提交事务
        conn.commit()
        logger.info("=" * 60)
        logger.info(f"✓ 僵尸网络 {botnet_type} 迁移完成！")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()


def main():
    if len(sys.argv) < 2:
        print("使用方法: python migrate_single_botnet.py <botnet_type>")
        print("例如: python migrate_single_botnet.py asruex")
        print("\n可用的僵尸网络类型:")
        print("  - asruex")
        print("  - mozi")
        print("  - andromeda")
        print("  - moobot")
        print("  - ramnit")
        print("  - leethozer")
        sys.exit(1)
    
    botnet_type = sys.argv[1]
    
    # 确认操作
    print(f"\n{'='*60}")
    print(f"即将迁移僵尸网络: {botnet_type}")
    print(f"数据库: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"{'='*60}")
    confirm = input("\n是否继续？(yes/no): ")
    
    if confirm.lower() != 'yes':
        print("操作已取消")
        sys.exit(0)
    
    # 执行迁移
    success = migrate_botnet(botnet_type)
    
    if success:
        print("\n✓ 迁移成功完成！")
        sys.exit(0)
    else:
        print("\n✗ 迁移失败！")
        sys.exit(1)


if __name__ == '__main__':
    main()
