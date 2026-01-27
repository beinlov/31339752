"""
数据库表结构统一定义
所有僵尸网络相关的表结构都在这里定义，确保db_writer和router使用相同的DDL
"""

# ==================== 节点表结构 ====================
NODE_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS {table_name} (
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
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    updated_at TIMESTAMP NULL DEFAULT NULL COMMENT '记录更新时间',
    is_china BOOLEAN DEFAULT FALSE COMMENT '是否为中国节点',
    INDEX idx_ip (ip),
    INDEX idx_location (country, province, city),
    INDEX idx_status (status),
    INDEX idx_first_seen (first_seen),
    INDEX idx_last_seen (last_seen),
    INDEX idx_communication_count (communication_count),
    INDEX idx_is_china (is_china),
    UNIQUE KEY idx_unique_ip (ip)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='僵尸网络节点基本信息表（汇总）'
"""

# ==================== 通信记录表结构 ====================
COMMUNICATION_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS {table_name} (
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
    UNIQUE KEY idx_unique_communication (ip, communication_time) COMMENT '唯一约束：防止重复数据',
    INDEX idx_node_id (node_id),
    INDEX idx_communication_time (communication_time) COMMENT '时间范围查询',
    INDEX idx_location (country, province, city) COMMENT '地理位置查询',
    CONSTRAINT fk_node_{botnet_type} FOREIGN KEY (node_id) REFERENCES {node_table}(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='僵尸网络节点通信记录表（优化版：唯一约束+外键约束RESTRICT）'
"""

# ==================== 中国地区统计表结构 ====================
CHINA_BOTNET_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS {table_name} (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='中国地区僵尸网络统计表(按省市)'
"""

# ==================== 全球统计表结构 ====================
GLOBAL_BOTNET_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS {table_name} (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='全球僵尸网络统计表(按国家)'
"""


def get_node_table_ddl(botnet_type: str) -> str:
    """获取节点表的DDL语句"""
    table_name = f"botnet_nodes_{botnet_type}"
    return NODE_TABLE_SCHEMA.format(table_name=table_name)


def get_communication_table_ddl(botnet_type: str, node_table: str = None) -> str:
    """获取通信记录表的DDL语句"""
    table_name = f"botnet_communications_{botnet_type}"
    if node_table is None:
        node_table = f"botnet_nodes_{botnet_type}"
    
    return COMMUNICATION_TABLE_SCHEMA.format(
        table_name=table_name,
        node_table=node_table,
        botnet_type=botnet_type
    )


def get_china_botnet_table_ddl(botnet_type: str) -> str:
    """获取中国地区统计表的DDL语句"""
    table_name = f"china_botnet_{botnet_type}"
    return CHINA_BOTNET_TABLE_SCHEMA.format(table_name=table_name)


def get_global_botnet_table_ddl(botnet_type: str) -> str:
    """获取全球统计表的DDL语句"""
    table_name = f"global_botnet_{botnet_type}"
    return GLOBAL_BOTNET_TABLE_SCHEMA.format(table_name=table_name)
