# 代码修改指南

## 概述

本文档详细说明为了支持"记录节点全部通信信息"而需要进行的代码修改。

---

## 修改文件列表

1. ✅ **backend/log_processor/db_writer.py** - 核心修改
2. ✅ **backend/router/node.py** - 查询接口修改/新增
3. ✅ **backend/router/botnet.py** - 表创建逻辑修改
4. ⚠️ **backend/log_processor/stats_aggregator.py** - 统计逻辑可能需要调整

---

## 1. db_writer.py 修改详情

### 1.1 初始化方法修改

**位置**: `__init__()` 方法

**当前代码**:
```python
# 表名
self.node_table = f"botnet_nodes_{botnet_type}"
```

**修改为**:
```python
# 表名
self.node_table = f"botnet_nodes_{botnet_type}"
self.communication_table = f"botnet_communications_{botnet_type}"  # 新增
```

**同时移除去重相关的初始化**:
```python
# 去重相关 - 需要移除或注释
# self.processed_records = set()
# self.duplicate_count = 0
```

---

### 1.2 表创建方法修改

**位置**: `_ensure_tables_exist()` 方法（第449-488行）

**需要添加通信记录表的创建**:

```python
async def _ensure_tables_exist(self, cursor):
    """确保数据表存在并升级表结构"""
    try:
        # 1. 创建节点表（修改字段定义）
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.node_table} (
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
                last_seen TIMESTAMP NULL DEFAULT NULL COMMENT '最后一次通信时间（日志时间）',
                communication_count INT DEFAULT 0 COMMENT '通信次数',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
                is_china BOOLEAN DEFAULT FALSE COMMENT '是否为中国节点',
                INDEX idx_ip (ip),
                INDEX idx_location (country, province, city),
                INDEX idx_status (status),
                INDEX idx_first_seen (first_seen),
                INDEX idx_last_seen (last_seen),
                INDEX idx_is_china (is_china),
                INDEX idx_communication_count (communication_count),
                UNIQUE KEY idx_unique_ip (ip)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
            COMMENT='僵尸网络节点基本信息表（每个IP一条记录）'
        """)
        
        # 2. 创建通信记录表（新增）
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.communication_table} (
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
        
        # 3. 升级表结构（处理旧表迁移）
        await self._upgrade_table_structure(cursor)
        
        logger.info(f"[{self.botnet_type}] Tables ensured: {self.node_table}, {self.communication_table}")
        
    except Exception as e:
        logger.error(f"[{self.botnet_type}] Error ensuring tables exist: {e}")
        raise
```

---

### 1.3 数据添加方法修改

**位置**: `add_node()` 方法（第172-236行）

**关键修改**: 移除去重逻辑

**当前代码**:
```python
def add_node(self, log_data: Dict, ip_info: Dict) -> bool:
    try:
        self.received_count += 1
        
        # 生成记录唯一标识（用于去重）- 需要移除
        record_key = f"{log_data['ip']}|{log_data['timestamp']}|{log_data.get('event_type', '')}"
        
        # 检查是否已处理过（应用层去重）- 需要移除
        if record_key in self.processed_records:
            self.duplicate_count += 1
            logger.debug(f"[{self.botnet_type}] Skipping duplicate: {record_key}")
            return False
        
        # ... 构建节点数据 ...
        
        # 记录已处理 - 需要移除
        self.processed_records.add(record_key)
```

**修改为**:
```python
def add_node(self, log_data: Dict, ip_info: Dict) -> bool:
    """
    添加节点数据到缓冲区（不再去重，记录所有通信）
    
    Args:
        log_data: 日志数据
        ip_info: IP信息
        
    Returns:
        bool: True=成功添加, False=添加失败
    """
    try:
        self.received_count += 1
        
        # 构建节点数据（不再进行去重检查）
        node_data = {
            'ip': log_data['ip'],
            'timestamp': log_data['timestamp'],
            'event_type': log_data.get('event_type', ''),
            'country': ip_info.get('country', ''),
            'province': ip_info.get('province', ''),
            'city': ip_info.get('city', ''),
            'longitude': ip_info.get('longitude', 0),
            'latitude': ip_info.get('latitude', 0),
            'continent': ip_info.get('continent', ''),
            'isp': ip_info.get('isp', ''),
            'asn': ip_info.get('asn', ''),
            'status': 'active',
            'is_china': ip_info.get('is_china', False)
        }
        
        # 线程安全地添加到缓冲区
        with self.buffer_lock:
            self.node_buffer.append(node_data)
        
        self.processed_count += 1
        
        # 更新统计
        country = ip_info.get('country', '未知')
        self.global_stats[country] += 1
        
        if country == '中国':
            province = ip_info.get('province', '未知').rstrip('省')
            city = ip_info.get('city', '未知').rstrip('市')
            if city in ['北京', '天津', '上海', '重庆']:
                city = city
            self.china_stats[(province, city)] += 1
        
        return True
            
    except Exception as e:
        logger.error(f"[{self.botnet_type}] Error adding node: {e}")
        return False
```

---

### 1.4 数据插入方法修改（核心）

**位置**: `_insert_nodes()` 方法（第571-708行）

这是最关键的修改，需要改为双表插入逻辑。

**完整的新实现**:

```python
async def _insert_nodes(self, cursor, nodes: List[Dict]):
    """
    批量插入节点数据 - 双表设计
    
    1. 插入/更新节点表（维护节点汇总信息）
    2. 插入通信记录表（记录每次通信）
    
    Returns:
        int: 实际新插入的通信记录数量
    """
    if not nodes:
        return 0
        
    try:
        current_time = datetime.now()
        
        # ========================================
        # Step 1: 准备数据并解析时间戳
        # ========================================
        prepared_nodes = []
        for node in nodes:
            # 解析日志中的时间戳
            log_time = None
            timestamp_str = node.get('timestamp', '')
            
            if timestamp_str:
                try:
                    if isinstance(timestamp_str, str):
                        formats = [
                            '%Y-%m-%d %H:%M:%S',
                            '%Y/%m/%d %H:%M:%S',
                            '%Y-%m-%dT%H:%M:%S',
                        ]
                        
                        for fmt in formats:
                            try:
                                log_time = datetime.strptime(timestamp_str, fmt)
                                break
                            except ValueError:
                                continue
                        
                        if not log_time and 'T' in timestamp_str:
                            try:
                                clean_ts = timestamp_str.split('+')[0].split('Z')[0].split('.')[0]
                                log_time = datetime.strptime(clean_ts, '%Y-%m-%dT%H:%M:%S')
                            except Exception:
                                pass
                    
                    elif isinstance(timestamp_str, datetime):
                        log_time = timestamp_str
                
                except Exception as e:
                    logger.warning(f"[{self.botnet_type}] Failed to parse timestamp '{timestamp_str}': {e}")
            
            if not log_time:
                logger.warning(f"[{self.botnet_type}] No valid timestamp for IP {node['ip']}, using current time")
                log_time = current_time
            
            prepared_nodes.append({
                'node': node,
                'log_time': log_time
            })
        
        # ========================================
        # Step 2: 插入/更新节点表
        # ========================================
        node_sql = f"""
            INSERT INTO {self.node_table} 
            (ip, longitude, latitude, country, province, city, continent, isp, asn, 
             status, first_seen, last_seen, communication_count, is_china)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s)
            ON DUPLICATE KEY UPDATE
                longitude = VALUES(longitude),
                latitude = VALUES(latitude),
                country = VALUES(country),
                province = VALUES(province),
                city = VALUES(city),
                continent = VALUES(continent),
                isp = VALUES(isp),
                asn = VALUES(asn),
                status = VALUES(status),
                last_seen = CASE 
                    WHEN VALUES(last_seen) > last_seen OR last_seen IS NULL 
                    THEN VALUES(last_seen)
                    ELSE last_seen
                END,
                communication_count = communication_count + 1,
                is_china = VALUES(is_china)
        """
        
        node_values = []
        for item in prepared_nodes:
            node = item['node']
            log_time = item['log_time']
            
            node_values.append((
                node['ip'],
                node['longitude'],
                node['latitude'],
                node['country'],
                node['province'],
                node['city'],
                node['continent'],
                node['isp'],
                node['asn'],
                node['status'],
                log_time,  # first_seen
                log_time,  # last_seen
                node['is_china']
            ))
        
        cursor.executemany(node_sql, node_values)
        logger.debug(f"[{self.botnet_type}] Node table updated: {len(node_values)} records")
        
        # ========================================
        # Step 3: 获取node_id（通过IP查询）
        # ========================================
        ip_list = [item['node']['ip'] for item in prepared_nodes]
        placeholders = ','.join(['%s'] * len(ip_list))
        cursor.execute(
            f"SELECT id, ip FROM {self.node_table} WHERE ip IN ({placeholders})",
            ip_list
        )
        ip_to_node_id = {row[1]: row[0] for row in cursor.fetchall()}
        
        # ========================================
        # Step 4: 插入通信记录表
        # ========================================
        comm_sql = f"""
            INSERT INTO {self.communication_table}
            (node_id, ip, communication_time, longitude, latitude, country, province, 
             city, continent, isp, asn, event_type, status, is_china)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        comm_values = []
        for item in prepared_nodes:
            node = item['node']
            log_time = item['log_time']
            node_id = ip_to_node_id.get(node['ip'])
            
            if node_id is None:
                logger.error(f"[{self.botnet_type}] Cannot find node_id for IP: {node['ip']}")
                continue
            
            comm_values.append((
                node_id,
                node['ip'],
                log_time,
                node['longitude'],
                node['latitude'],
                node['country'],
                node['province'],
                node['city'],
                node['continent'],
                node['isp'],
                node['asn'],
                node.get('event_type', ''),
                node['status'],
                node['is_china']
            ))
        
        cursor.executemany(comm_sql, comm_values)
        rows_inserted = cursor.rowcount
        
        logger.debug(
            f"[{self.botnet_type}] Inserted {rows_inserted} communication records"
        )
        
        return rows_inserted
        
    except Exception as e:
        logger.error(f"[{self.botnet_type}] Error inserting nodes: {e}")
        raise
```

---

### 1.5 清理方法修改

**位置**: `get_statistics()` 方法

移除去重统计相关的代码：

```python
# 移除这些统计
# 'duplicate_count': self.duplicate_count,
# 'processed_records_count': len(self.processed_records),
```

---

## 2. node.py 修改详情

### 2.1 现有接口保持兼容

`/node-details` 接口继续返回节点表数据（汇总信息），基本不需要修改。

只需要确保查询的字段名是最新的：
- `active_time` → `first_seen`
- `updated_at` 现在表示记录更新时间，`last_seen` 表示最后通信时间

### 2.2 新增通信记录接口

在 `node.py` 中添加新的接口：

```python
@router.get("/node-communications")
async def get_node_communications(
    botnet_type: str,
    ip: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=10, le=1000)
):
    """
    获取节点的通信记录详情
    
    Args:
        botnet_type: 僵尸网络类型
        ip: 过滤特定IP（可选）
        start_time: 开始时间（可选，格式：YYYY-MM-DD HH:MM:SS）
        end_time: 结束时间（可选，格式：YYYY-MM-DD HH:MM:SS）
        page: 页码
        page_size: 每页数量
    
    Returns:
        {
            "total": 总记录数,
            "page": 当前页,
            "page_size": 每页数量,
            "communications": [通信记录列表]
        }
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        table_name = f"botnet_communications_{botnet_type}"
        
        # 检查表是否存在
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], table_name))
        
        if cursor.fetchone()['count'] == 0:
            raise HTTPException(
                status_code=404, 
                detail=f"Communication table for {botnet_type} not found"
            )
        
        # 构建查询条件
        where_clauses = []
        params = []
        
        if ip:
            where_clauses.append("ip = %s")
            params.append(ip)
        
        if start_time:
            where_clauses.append("communication_time >= %s")
            params.append(start_time)
        
        if end_time:
            where_clauses.append("communication_time <= %s")
            params.append(end_time)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) as total FROM {table_name} WHERE {where_sql}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']
        
        # 查询数据
        offset = (page - 1) * page_size
        data_sql = f"""
            SELECT 
                id,
                node_id,
                ip,
                communication_time,
                received_at,
                country,
                province,
                city,
                longitude,
                latitude,
                isp,
                asn,
                event_type,
                status,
                is_china
            FROM {table_name}
            WHERE {where_sql}
            ORDER BY communication_time DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_sql, params + [page_size, offset])
        communications = cursor.fetchall()
        
        # 格式化时间字段
        for comm in communications:
            if comm['communication_time']:
                comm['communication_time'] = comm['communication_time'].strftime('%Y-%m-%d %H:%M:%S')
            if comm['received_at']:
                comm['received_at'] = comm['received_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "communications": communications
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching communications: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@router.get("/node-communication-stats")
async def get_node_communication_stats(
    botnet_type: str,
    ip: str
):
    """
    获取单个节点的通信统计信息
    
    Returns:
        {
            "ip": IP地址,
            "total_communications": 总通信次数,
            "first_seen": 首次通信时间,
            "last_seen": 最后通信时间,
            "communication_timeline": [按天统计的通信次数]
        }
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        table_name = f"botnet_communications_{botnet_type}"
        
        # 基本统计
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_communications,
                MIN(communication_time) as first_seen,
                MAX(communication_time) as last_seen
            FROM {table_name}
            WHERE ip = %s
        """, (ip,))
        
        stats = cursor.fetchone()
        
        if stats['total_communications'] == 0:
            raise HTTPException(status_code=404, detail=f"No communications found for IP {ip}")
        
        # 按天统计
        cursor.execute(f"""
            SELECT 
                DATE(communication_time) as date,
                COUNT(*) as count
            FROM {table_name}
            WHERE ip = %s
            GROUP BY DATE(communication_time)
            ORDER BY date
        """, (ip,))
        
        timeline = cursor.fetchall()
        
        # 格式化时间
        if stats['first_seen']:
            stats['first_seen'] = stats['first_seen'].strftime('%Y-%m-%d %H:%M:%S')
        if stats['last_seen']:
            stats['last_seen'] = stats['last_seen'].strftime('%Y-%m-%d %H:%M:%S')
        
        for item in timeline:
            item['date'] = item['date'].strftime('%Y-%m-%d')
        
        return {
            "ip": ip,
            "total_communications": stats['total_communications'],
            "first_seen": stats['first_seen'],
            "last_seen": stats['last_seen'],
            "communication_timeline": timeline
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching communication stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
```

---

## 3. botnet.py 修改详情

**位置**: `ensure_botnet_table_exists()` 函数（第67-163行）

需要同步创建通信记录表，修改节点表字段定义：

```python
async def ensure_botnet_table_exists(bot_name: str):
    """确保僵尸网络数据表存在，如果不存在则创建"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        china_table = f"china_botnet_{bot_name}"
        global_table = f"global_botnet_{bot_name}"
        node_table = f"botnet_nodes_{bot_name}"
        communication_table = f"botnet_communications_{bot_name}"  # 新增

        # 检查表是否存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], china_table))
        
        if cursor.fetchone()[0] == 0:
            logger.info(f"Tables for {bot_name} do not exist, creating...")
            
            # 创建中国区域的僵尸网络表
            cursor.execute(f"""
                CREATE TABLE {china_table} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    province VARCHAR(50) NOT NULL,
                    municipality VARCHAR(50) NOT NULL,
                    infected_num INT DEFAULT 0 COMMENT '感染数量',
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
            
            # 创建全球僵尸网络表
            cursor.execute(f"""
                CREATE TABLE {global_table} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    country VARCHAR(100) NOT NULL,
                    infected_num INT DEFAULT 0 COMMENT '感染数量',
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
            
            # 创建节点表（修改字段定义）
            cursor.execute(f"""
                CREATE TABLE {node_table} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    ip VARCHAR(15) NOT NULL,
                    longitude FLOAT,
                    latitude FLOAT,
                    country VARCHAR(50),
                    province VARCHAR(50),
                    city VARCHAR(50),
                    continent VARCHAR(50),
                    isp VARCHAR(255),
                    asn VARCHAR(50),
                    status ENUM('active', 'inactive') DEFAULT 'active',
                    first_seen TIMESTAMP NULL DEFAULT NULL COMMENT '首次发现时间（日志时间）',
                    last_seen TIMESTAMP NULL DEFAULT NULL COMMENT '最后一次通信时间（日志时间）',
                    communication_count INT DEFAULT 0 COMMENT '通信次数',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
                    is_china BOOLEAN DEFAULT FALSE,
                    INDEX idx_ip (ip),
                    INDEX idx_location (country, province, city),
                    INDEX idx_status (status),
                    INDEX idx_first_seen (first_seen),
                    INDEX idx_last_seen (last_seen),
                    INDEX idx_communication_count (communication_count),
                    INDEX idx_is_china (is_china),
                    UNIQUE KEY idx_unique_ip (ip)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
                COMMENT='僵尸网络节点基本信息表（每个IP一条记录）'
            """)
            
            # 创建通信记录表（新增）
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
            
            conn.commit()
            logger.info(f"All tables for {bot_name} created successfully")
            
    except Exception as e:
        logger.error(f"Error ensuring table exists: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
```

---

## 4. 测试建议

### 4.1 单元测试

创建测试文件 `test_db_writer.py`:

```python
import pytest
from log_processor.db_writer import DatabaseWriter

def test_no_deduplication():
    """测试不再进行去重"""
    writer = DatabaseWriter('test', db_config, batch_size=10)
    
    # 相同的数据添加两次
    log_data = {'ip': '1.2.3.4', 'timestamp': '2024-01-01 12:00:00'}
    ip_info = {'country': 'China', 'province': '北京', 'city': '北京'}
    
    result1 = writer.add_node(log_data, ip_info)
    result2 = writer.add_node(log_data, ip_info)
    
    # 两次都应该返回True（不再去重）
    assert result1 == True
    assert result2 == True
    assert len(writer.node_buffer) == 2  # 缓冲区应该有两条记录

def test_communication_table_insert():
    """测试通信记录表插入"""
    # 具体测试逻辑
    pass
```

### 4.2 集成测试

1. 测试相同IP多次通信是否都被记录
2. 测试节点表的 `communication_count` 是否正确累加
3. 测试 `first_seen` 和 `last_seen` 是否正确更新
4. 测试通信记录查询接口

### 4.3 性能测试

```python
# 测试大量通信记录的插入性能
def test_bulk_insert_performance():
    import time
    
    writer = DatabaseWriter('test', db_config, batch_size=1000)
    
    # 生成10000条测试数据
    test_data = generate_test_data(10000)
    
    start = time.time()
    for data in test_data:
        writer.add_node(data['log'], data['ip_info'])
    
    writer.flush()
    end = time.time()
    
    print(f"插入10000条记录耗时: {end - start:.2f}秒")
    assert (end - start) < 10  # 应该在10秒内完成
```

---

## 5. 部署检查清单

### 部署前

- [ ] 备份生产数据库
- [ ] 在测试环境完整测试
- [ ] 验证迁移脚本无误
- [ ] 代码review通过
- [ ] 性能测试通过

### 部署步骤

1. [ ] 停止日志处理服务
2. [ ] 执行数据库迁移脚本
3. [ ] 验证表结构和数据
4. [ ] 部署新代码
5. [ ] 启动服务
6. [ ] 监控日志和性能
7. [ ] 验证功能正常

### 部署后

- [ ] 检查通信记录是否正常写入
- [ ] 验证节点统计是否准确
- [ ] 监控数据库性能
- [ ] 监控存储空间使用
- [ ] 验证查询接口返回正确

---

## 6. 回滚方案

如果部署后发现问题，执行回滚：

1. 停止服务
2. 恢复代码到旧版本
3. 恢复数据库备份（如果必要）
4. 重启服务

---

## 7. 常见问题

### Q1: 为什么不在通信记录表也使用唯一约束？

A: 因为需求是记录"全部通信"，同一个IP在同一时间可能有多次通信（虽然概率很小），使用唯一约束会导致数据丢失。

### Q2: 通信记录表会不会增长太快？

A: 会的。建议：
- 使用时间分区
- 定期归档旧数据
- 监控磁盘空间

### Q3: 查询性能会不会下降？

A: 节点表查询性能不会下降（甚至可能提升），通信记录表需要注意：
- 合理使用索引
- 限制查询时间范围
- 使用分页

### Q4: 如何验证数据迁移是否成功？

A: 执行以下查询：
```sql
-- 验证通信次数一致性
SELECT n.ip, n.communication_count, COUNT(c.id) as actual
FROM botnet_nodes_{type} n
LEFT JOIN botnet_communications_{type} c ON n.id = c.node_id
GROUP BY n.id
HAVING n.communication_count != COUNT(c.id);
```

应该返回空结果。

---

## 总结

主要修改点：
1. ✅ 移除所有去重逻辑
2. ✅ 双表插入（节点表 + 通信记录表）
3. ✅ 新增通信记录查询接口
4. ✅ 修改表字段定义

预期效果：
- 完整记录所有通信历史
- 保持查询性能
- 向后兼容现有接口
