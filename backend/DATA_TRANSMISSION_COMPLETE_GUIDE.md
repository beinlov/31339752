# 数据传输系统完整指南

**版本**: v2.0  
**更新日期**: 2026-01-14  
**适用环境**: C2服务器 + 平台服务器

---

## 📋 目录

1. [系统架构概览](#系统架构概览)
2. [数据传输模式](#数据传输模式)
3. [C2端配置详解](#c2端配置详解)
4. [平台端配置详解](#平台端配置详解)
5. [启动步骤](#启动步骤)
6. [参数索引](#参数索引)
7. [故障排查](#故障排查)

---

## 系统架构概览

### 组件关系图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          C2服务器                                    │
│  ┌────────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │  日志文件目录   │───→│ BackgroundLog│───→│  SQLite缓存        │  │
│  │  /log/*.log    │    │  Reader      │    │  /tmp/c2_data_      │  │
│  │                │    │              │    │  cache.db           │  │
│  └────────────────┘    └─────────────┘    └─────────────────────┘  │
│                                                     │                │
│                                                     ↓                │
│                                            ┌─────────────────────┐  │
│                                            │  HTTP API           │  │
│                                            │  :8080/api/pull     │  │
│                                            └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                                     │
                                  HTTP拉取（每5分钟） │
                                                     ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         平台服务器                                   │
│  ┌─────────────────────┐                                            │
│  │  RemotePuller       │                                            │
│  │  (remote_puller.py) │                                            │
│  └─────────────────────┘                                            │
│            │                                                         │
│            ↓ 模式选择                                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      数据处理模式                            │   │
│  │  ┌──────────────┐              ┌──────────────┐             │   │
│  │  │  队列模式    │              │  直接模式    │             │   │
│  │  │  (推荐)     │              │  (简单)     │             │   │
│  │  └──────────────┘              └──────────────┘             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│            │                                │                       │
│            ↓                                ↓                       │
│  ┌─────────────────┐            ┌─────────────────────────┐       │
│  │  Redis队列      │            │  直接处理流程            │       │
│  │  (异步缓冲)     │            │  1. IP富化              │       │
│  └─────────────────┘            │  2. 数据库写入          │       │
│            │                    └─────────────────────────┘       │
│            ↓                                │                       │
│  ┌─────────────────┐                        │                       │
│  │  Worker进程     │                        │                       │
│  │  (worker.py)    │                        │                       │
│  │  1. IP富化      │                        │                       │
│  │  2. 数据库写入  │                        │                       │
│  └─────────────────┘                        │                       │
│            │                                │                       │
│            └────────────────┬───────────────┘                       │
│                             ↓                                       │
│                    ┌─────────────────┐                              │
│                    │  MySQL数据库    │                              │
│                    │  botnet_        │                              │
│                    │  communications │                              │
│                    └─────────────────┘                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 数据传输模式

### 模式对比总览

| 特性 | 模式1: 队列模式 | 模式2: 直接模式 |
|------|----------------|----------------|
| **Redis依赖** | ✅ 需要 | ❌ 不需要 |
| **Worker进程** | ✅ 需要 | ❌ 不需要 |
| **性能** | 高（异步并发） | 中（同步串行） |
| **复杂度** | 高 | 低 |
| **可靠性** | 高（持久化队列） | 中（内存处理） |
| **失败重试** | ✅ 支持 | ❌ 不支持 |
| **适用场景** | 生产环境、大数据量 | 测试环境、小数据量 |
| **并发处理** | ✅ 支持多Worker | ❌ 单线程 |
| **监控能力** | 强（队列监控） | 弱 |

---

### 模式1: 队列模式（生产推荐）

#### 🎯 工作原理

```
数据流：
C2日志 → SQLite → HTTP API → RemotePuller → Redis队列 → Worker → IP富化 → 数据库

时间线：
┌──────────────────────────────────────────────────────────────────┐
│ T+0s   : RemotePuller拉取1000条数据                              │
│ T+0.1s : 推送到Redis队列，立即返回（不阻塞）                     │
│ T+0.1s : RemotePuller继续下一轮拉取                              │
│ ------- 异步分界线 -------                                        │
│ T+1s   : Worker从队列取出任务                                     │
│ T+2s   : Worker完成IP富化（1000个IP）                            │
│ T+3s   : Worker写入数据库                                         │
│ T+3s   : Worker继续处理下一个任务                                 │
└──────────────────────────────────────────────────────────────────┘
```

#### 🔧 启用条件

```python
# 文件: backend/log_processor/main.py:40-48

try:
    from task_queue import task_queue
    USE_QUEUE_FOR_PULLING = True  # ← 队列模式启用
    logger.info("[配置] 日志处理器将使用Redis队列进行异步处理")
except ImportError:
    task_queue = None
    USE_QUEUE_FOR_PULLING = False
    logger.warning("[配置] task_queue未找到，将直接处理数据")
```

**启用条件**:
1. ✅ `backend/task_queue.py` 文件存在
2. ✅ Redis服务运行（默认localhost:6379）
3. ✅ Worker进程启动

#### 📝 关键代码逻辑

```python
# 文件: backend/log_processor/main.py:130-142

if USE_QUEUE_FOR_PULLING and task_queue:
    try:
        # 推送到Redis队列
        task_id = task_queue.push_task(
            botnet_type=botnet_type,
            ip_data=ip_data,
            client_ip='log_processor'
        )
        logger.info(f"[{botnet_type}] 已推送 {len(ip_data)} 条数据到队列")
        return  # ← 立即返回，不执行后续逻辑
    except Exception as e:
        logger.error(f"推送失败: {e}，降级为直接处理")
        # 继续执行直接处理逻辑
```

#### ⚙️ 相关配置参数

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `REDIS_HOST` | `backend/task_queue.py` | `'localhost'` | Redis服务器地址 |
| `REDIS_PORT` | `backend/task_queue.py` | `6379` | Redis端口 |
| `REDIS_DB` | `backend/task_queue.py` | `0` | Redis数据库编号 |
| `QUEUE_NAME` | `backend/task_queue.py` | `'botnet:task_queue'` | 队列键名 |
| `MAX_RETRIES` | `backend/worker.py` | `3` | 任务失败重试次数 |

#### 🚀 启动步骤

```bash
# 1. 确保Redis运行
redis-cli ping
# 应返回: PONG

# 2. 启动主程序（日志处理器）
cd backend/log_processor
python main.py &

# 3. 启动Worker（关键！）
cd backend
python worker.py &

# 4. 可选：启动多个Worker并发处理
python worker.py &
python worker.py &
python worker.py &
```

#### 📊 监控命令

```bash
# 查看队列长度
redis-cli LLEN botnet:task_queue

# 查看队列中的任务
redis-cli LRANGE botnet:task_queue 0 10

# 实时监控队列
watch -n 1 'redis-cli LLEN botnet:task_queue'

# 查看Worker日志
tail -f logs/worker.log
```

#### ⚠️  注意事项

1. **必须启动Worker**: 数据只会在Worker中处理
2. **队列积压**: 如果Worker不运行，队列会无限增长
3. **Redis持久化**: 配置Redis的AOF/RDB防止数据丢失
4. **Worker数量**: 根据CPU核心数和数据量调整

---

### 模式2: 直接模式（测试推荐）

#### 🎯 工作原理

```
数据流：
C2日志 → SQLite → HTTP API → RemotePuller → IP富化 → 数据库
                                          ↑
                                    直接处理（阻塞）

时间线：
┌──────────────────────────────────────────────────────────────────┐
│ T+0s   : RemotePuller拉取1000条数据                              │
│ T+0.1s : 开始IP富化（阻塞）                                       │
│ T+5s   : IP富化完成                                               │
│ T+6s   : 写入数据库                                               │
│ T+6s   : 本次处理完成，继续下一轮拉取                             │
└──────────────────────────────────────────────────────────────────┘
```

#### 🔧 启用条件

```python
# 自动启用条件：
# 1. task_queue.py 不存在
# 2. Redis连接失败
# 3. 队列推送失败后降级
```

**启用方法**:
```bash
# 方法1: 删除/重命名task_queue.py
mv backend/task_queue.py backend/task_queue.py.bak

# 方法2: 停止Redis服务
redis-cli shutdown

# 重启日志处理器
pkill -f main.py && python backend/log_processor/main.py
```

#### 📝 关键代码逻辑

```python
# 文件: backend/log_processor/main.py:147-232

# ===== 模式2: 直接处理 =====
writer = self.writers[botnet_type]
logger.info(f"[{botnet_type}] 收到 {len(ip_data)} 个IP，开始直接处理...")

# 1. IP富化阶段
ip_query_tasks = []
for ip_item in ip_data:
    ip_query_tasks.append(self.enricher.enrich(ip_item['ip']))

ip_infos = await asyncio.gather(*ip_query_tasks, return_exceptions=True)
logger.info(f"[{botnet_type}] IP增强完成: {len(ip_data)}条")

# 2. 数据库写入阶段
for ip_item, ip_info in zip(ip_data, ip_infos):
    parsed_data = {
        'ip': ip_item['ip'],
        'timestamp': ip_item['timestamp'],
        # ... 其他字段
    }
    writer.add_node(parsed_data, ip_info)

# 3. 强制刷新到数据库
await writer.flush(force=True)
logger.info(f"[{botnet_type}] 写入: {processed_count}, 重复: {error_count}")
```

#### ⚙️ 相关配置参数

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `DB_BATCH_SIZE` | `backend/config.py` | `1000` | 数据库批量写入大小 |
| `DB_COMMIT_INTERVAL` | `backend/config.py` | `60` | 自动提交间隔（秒） |
| `IP_ENRICHER_SEMAPHORE` | `backend/config.py` | `50` | IP查询并发上限 |

#### 🚀 启动步骤

```bash
# 1. 确保task_queue.py不存在（或Redis不可用）
ls backend/task_queue.py
# 应报错: No such file or directory

# 2. 启动日志处理器
cd backend/log_processor
python main.py

# 3. 查看日志确认模式
tail -f ../../logs/log_processor.log
# 应看到: [WARNING] task_queue未找到，将直接处理数据
```

#### 📊 监控命令

```bash
# 查看日志处理器日志
tail -f logs/log_processor.log | grep "IP增强完成\|写入:"

# 查看数据库写入
mysql -u root -p botnet -e "
SELECT 
    COUNT(*) as count,
    MAX(received_at) as latest
FROM botnet_communications_test
WHERE received_at > NOW() - INTERVAL 5 MINUTE;
"
```

#### ⚠️  注意事项

1. **性能**: 处理大量数据时会阻塞主程序
2. **无重试**: 失败的任务不会自动重试
3. **单线程**: 无法并发处理多个批次
4. **适用场景**: 测试环境、数据量<10万/天

---

## C2端配置详解

### 配置文件位置

```
backend/remote/config.json
```

### 完整配置示例

```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 8080
    },
    "botnet": {
        "botnet_type": "test",
        "log_dir": "/home/ubuntu/log",
        "log_file_pattern": "test_{date}.log"
    },
    "cache": {
        "db_path": "/tmp/c2_data_cache.db",
        "max_cache_size": 100000
    },
    "api": {
        "api_key": "your-secret-api-key-here-change-in-production",
        "enable_auth": true
    }
}
```

### 参数详解

#### 1. server（HTTP服务器配置）

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `host` | string | `"0.0.0.0"` | 监听地址（0.0.0.0=所有网卡） |
| `port` | int | `8080` | 监听端口 |

**修改示例**:
```json
{
    "server": {
        "host": "127.0.0.1",  // 仅本地访问
        "port": 9090          // 修改端口
    }
}
```

#### 2. botnet（僵尸网络配置）⭐

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `botnet_type` | string | ✅ | 僵尸网络类型（决定数据写入哪个表） |
| `log_dir` | string | ✅ | 日志文件目录（绝对路径） |
| `log_file_pattern` | string | ✅ | 日志文件名模式 |

**botnet_type说明**:
- **作用**: 决定数据写入的表名
  - `"test"` → `botnet_communications_test`
  - `"ramnit"` → `botnet_communications_ramnit`
- **允许值**: `asruex`, `mozi`, `andromeda`, `moobot`, `ramnit`, `leethozer`, `test`
- **⚠️  注意**: 必须与平台端的ALLOWED_BOTNET_TYPES匹配

**log_file_pattern说明**:
- **支持的占位符**:
  - `{date}`: 日期格式，支持 `YYYYMMDD` 或 `YYYY-MM-DD`
  - `{datetime}`: 小时格式（兼容旧版）
- **示例**:
  - `"test_{date}.log"` → `test_20260114.log` 或 `test_2026-01-14.log`
  - `"ramnit_{date}.log"` → `ramnit_20260114.log`

**修改示例**:
```json
{
    "botnet": {
        "botnet_type": "ramnit",              // 修改为ramnit
        "log_dir": "/var/log/ramnit",         // 修改日志目录
        "log_file_pattern": "ramnit_{date}.log"  // 修改文件模式
    }
}
```

#### 3. cache（SQLite缓存配置）

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `db_path` | string | `/tmp/c2_data_cache.db` | SQLite数据库路径 |
| `max_cache_size` | int | `100000` | 最大缓存记录数 |

**说明**:
- **db_path**: 缓存数据库的存储位置
  - 使用`/tmp`：重启会丢失（适合测试）
  - 使用持久目录：数据保留（适合生产）
- **max_cache_size**: 缓存超过此值会触发清理

**修改示例**:
```json
{
    "cache": {
        "db_path": "/data/c2_cache.db",  // 持久化存储
        "max_cache_size": 500000         // 增加缓存上限
    }
}
```

#### 4. api（API安全配置）

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `api_key` | string | `"your-secret..."` | API密钥 |
| `enable_auth` | bool | `true` | 是否启用认证 |

**⚠️  安全建议**:
1. 生产环境必须修改默认API密钥
2. 使用强密码（建议32位随机字符串）
3. 定期轮换API密钥
4. 配置HTTPS（防止密钥泄露）

**修改示例**:
```json
{
    "api": {
        "api_key": "a9f3b2e1c4d5e6f7a8b9c0d1e2f3a4b5",  // 生成随机密钥
        "enable_auth": true
    }
}
```

### C2端高级配置（在backend/config.py中）

#### 日志回溯配置

```python
# 文件: backend/config.py:310-318

C2_LOG_LOOKBACK_CONFIG = {
    'mode': 'unlimited',  # 'unlimited': 无限回溯, 'limited': 限制天数
    'max_days': 90,       # limited模式下的最大回溯天数
    'description': '无限回溯模式：C2端会读取所有未处理的历史日志文件'
}
```

**mode参数**:
- `'unlimited'`: 读取所有历史日志文件（推荐）
  - 适用：平台长时间停运后恢复
  - 行为：扫描log_dir中所有匹配的日志文件
- `'limited'`: 只回溯指定天数
  - 适用：限制内存使用
  - 行为：只读取最近max_days天的日志

**修改方法**:
```python
# 修改为限制90天
C2_LOG_LOOKBACK_CONFIG = {
    'mode': 'limited',
    'max_days': 90,
}
```

---

## 平台端配置详解

### 配置文件位置

```
backend/config.py
```

### 核心配置参数

#### 1. C2端点配置⭐

```python
# 文件: backend/config.py:233-271

C2_ENDPOINTS = [
    {
        'name': 'test',                  # 端点名称（用于日志）
        'url': 'http://192.168.1.100:8080',  # C2服务器地址
        'api_key': 'your-secret-api-key',    # 必须与C2端一致
        'enabled': True,                  # 是否启用此端点
        'pull_interval': 300,             # 拉取间隔（秒），300=5分钟
        'pull_limit': 1000,               # 每次拉取的最大记录数
        'timeout': 30,                    # HTTP请求超时（秒）
        'verify_ssl': False,              # 是否验证SSL证书
    }
]
```

**参数详解**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `name` | string | ✅ | - | 端点标识符，用于日志和状态跟踪 |
| `url` | string | ✅ | - | C2服务器完整URL（含协议和端口） |
| `api_key` | string | ✅ | - | **必须与C2端config.json中一致** |
| `enabled` | bool | ❌ | `true` | 是否启用此端点 |
| `pull_interval` | int | ❌ | `300` | 拉取间隔（秒） |
| `pull_limit` | int | ❌ | `1000` | 每次拉取记录数 |
| `timeout` | int | ❌ | `30` | HTTP超时 |
| `verify_ssl` | bool | ❌ | `false` | SSL证书验证 |

**配置示例（多个C2端点）**:
```python
C2_ENDPOINTS = [
    {
        'name': 'test_cn',
        'url': 'http://192.168.1.100:8080',
        'api_key': 'key-cn-001',
        'enabled': True,
        'pull_interval': 180,  # 3分钟拉取一次
    },
    {
        'name': 'test_us',
        'url': 'http://10.0.0.50:8080',
        'api_key': 'key-us-002',
        'enabled': True,
        'pull_interval': 300,  # 5分钟拉取一次
    },
    {
        'name': 'ramnit_main',
        'url': 'https://c2.example.com:8443',
        'api_key': 'key-ramnit-main',
        'enabled': False,  # 临时禁用
        'verify_ssl': True,
    }
]
```

#### 2. 数据库配置

```python
# 文件: backend/config.py:17-27

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'botnet',
    'charset': 'utf8mb4'
}
```

#### 3. IP富化配置

```python
# 文件: backend/config.py:173-204

# Redis缓存配置（L2缓存）
IP_CACHE_REDIS_CONFIG = {
    'enabled': True,           # 是否启用Redis缓存
    'host': 'localhost',
    'port': 6379,
    'db': 1,
    'ttl': 604800,            # 7天（秒）
    'key_prefix': 'ip_cache:'
}

# IP富化重试配置
IP_ENRICHMENT_RETRY_CONFIG = {
    'max_retries': 3,          # 最大重试次数
    'retry_delay': 1.0,        # 初始延迟（秒）
    'backoff_factor': 2.0,     # 指数退避因子
    'max_delay': 10.0          # 最大延迟（秒）
}

# IP查询限流配置
IP_QUERY_RATE_LIMIT = {
    'max_concurrent': 50,      # 最大并发查询数
    'timeout': 10.0            # 单次查询超时（秒）
}
```

#### 4. 批量写入配置

```python
# 文件: backend/config.py:206-216

DB_BATCH_SIZE = 1000           # 批量写入大小
DB_COMMIT_INTERVAL = 60        # 自动提交间隔（秒）
DB_STATISTICS_INTERVAL = 300   # 统计输出间隔（秒）
```

#### 5. 背压控制配置

```python
# 文件: backend/config.py:289-301

BACKPRESSURE_CONFIG = {
    'enabled': True,
    'high_watermark': 10000,   # 队列高水位（暂停拉取）
    'low_watermark': 5000,     # 队列低水位（恢复拉取）
    'check_interval': 10,      # 检查间隔（秒）
}
```

---

## 启动步骤

### 完整启动流程（队列模式）

#### 步骤1: 准备环境

```bash
# 1. 启动Redis
redis-server &

# 2. 启动MySQL
systemctl start mysql

# 3. 检查服务状态
redis-cli ping  # 应返回PONG
mysql -u root -p -e "SELECT 1"  # 应返回1
```

#### 步骤2: 配置C2端

```bash
# 1. 编辑C2配置
vim backend/remote/config.json

# 2. 关键配置检查
{
    "botnet": {
        "botnet_type": "test",  # ← 确认类型
        "log_dir": "/home/ubuntu/log",  # ← 确认路径存在
        "log_file_pattern": "test_{date}.log"
    },
    "api": {
        "api_key": "your-secret-key"  # ← 记住这个key
    }
}
```

#### 步骤3: 启动C2服务

```bash
# 在C2服务器上
cd backend/remote
python3 c2_data_server.py &

# 查看日志
tail -f /var/log/c2_data_server.log

# 期望输出:
# [INFO] HTTP服务器启动: http://0.0.0.0:8080
# [INFO] 无限回溯模式：将读取所有历史日志文件
# [INFO] 读取日志文件: test_2026-01-14.log
```

#### 步骤4: 配置平台端

```bash
# 1. 编辑平台配置
vim backend/config.py

# 2. 关键配置检查
C2_ENDPOINTS = [
    {
        'name': 'test',
        'url': 'http://C2_SERVER_IP:8080',  # ← C2服务器IP
        'api_key': 'your-secret-key',  # ← 与C2端一致！
        'enabled': True,
    }
]

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',  # ← 确认数据库密码
    'database': 'botnet'
}
```

#### 步骤5: 启动平台端

```bash
# 1. 启动日志处理器
cd backend/log_processor
python main.py &

# 2. 启动Worker（队列模式必须！）
cd backend
python worker.py &

# 3. 查看日志
tail -f ../logs/log_processor.log
tail -f ../logs/worker.log
```

#### 步骤6: 验证运行

```bash
# 1. 检查进程
ps aux | grep -E "(main.py|worker.py|c2_data_server.py)"

# 2. 检查队列
redis-cli LLEN botnet:task_queue

# 3. 检查数据
python backend/scripts/check_test_data.py

# 4. 查看日志
tail -f logs/log_processor.log | grep "test"
```

---

### 快速启动流程（直接模式）

#### 步骤1-3: 同队列模式

#### 步骤4: 禁用队列

```bash
# 禁用task_queue
mv backend/task_queue.py backend/task_queue.py.bak
```

#### 步骤5: 启动平台端

```bash
# 只需启动日志处理器（无需Worker）
cd backend/log_processor
python main.py &

# 查看日志
tail -f ../../logs/log_processor.log

# 期望看到:
# [WARNING] task_queue未找到，将直接处理数据
# [INFO] [test] 收到 1000 个IP，开始直接处理...
```

---

## 参数索引

### 按功能分类

#### A. 数据拉取参数

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `pull_interval` | `config.py` C2_ENDPOINTS | `300` | 拉取间隔（秒） |
| `pull_limit` | `config.py` C2_ENDPOINTS | `1000` | 每次拉取记录数 |
| `timeout` | `config.py` C2_ENDPOINTS | `30` | HTTP超时 |
| `ENABLE_REMOTE_PULLING` | `config.py` | `True` | 是否启用远程拉取 |

#### B. 缓存参数

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `db_path` | `remote/config.json` cache | `/tmp/c2_data_cache.db` | SQLite路径 |
| `max_cache_size` | `remote/config.json` cache | `100000` | C2端最大缓存 |
| `IP_CACHE_SIZE` | `config.py` | `10000` | L1缓存大小 |
| `IP_CACHE_TTL` | `config.py` | `3600` | L1缓存TTL |
| `IP_CACHE_REDIS_CONFIG` | `config.py` | - | L2 Redis缓存 |

#### C. 数据库参数

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `DB_CONFIG` | `config.py` | - | 数据库连接配置 |
| `DB_BATCH_SIZE` | `config.py` | `1000` | 批量写入大小 |
| `DB_COMMIT_INTERVAL` | `config.py` | `60` | 自动提交间隔 |

#### D. 性能参数

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `max_concurrent` | `config.py` IP_QUERY_RATE_LIMIT | `50` | IP查询并发数 |
| `high_watermark` | `config.py` BACKPRESSURE_CONFIG | `10000` | 背压高水位 |
| `low_watermark` | `config.py` BACKPRESSURE_CONFIG | `5000` | 背压低水位 |

#### E. 安全参数

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `api_key` | `remote/config.json` | - | C2端API密钥 |
| `api_key` | `config.py` C2_ENDPOINTS | - | 平台端API密钥 |
| `enable_auth` | `remote/config.json` | `true` | 是否启用认证 |
| `verify_ssl` | `config.py` C2_ENDPOINTS | `false` | SSL验证 |

---

## 故障排查

### 问题1: 数据拉取成功但未写入数据库

**症状**:
```
[INFO] 远程拉取: 总计 1000, 已保存 1000, 错误 0
[INFO] [test] 写入: 0, 重复: 0, 缓冲: 0
```

**原因**: 队列模式已启用但Worker未运行

**解决**:
```bash
# 方案1: 启动Worker
python backend/worker.py

# 方案2: 禁用队列模式
mv backend/task_queue.py backend/task_queue.py.bak
pkill -f main.py && python backend/log_processor/main.py
```

**诊断脚本**:
```bash
python backend/scripts/diagnose_queue.py
```

---

### 问题2: C2端无法读取日志文件

**症状**:
```
[INFO] 无限回溯模式：将读取所有历史日志文件
[DEBUG] 无法解析文件日期: test_2026-01-14.log
```

**原因**: 文件名格式与log_file_pattern不匹配

**解决**:
```json
// 文件: backend/remote/config.json
{
    "botnet": {
        "log_file_pattern": "test_{date}.log"  // 支持YYYYMMDD和YYYY-MM-DD
    }
}
```

---

### 问题3: API认证失败

**症状**:
```
[ERROR] 认证失败，请检查 API Key
```

**原因**: 平台端和C2端的api_key不一致

**解决**:
```bash
# 1. 检查C2端
cat backend/remote/config.json | grep api_key

# 2. 检查平台端
grep "api_key" backend/config.py

# 3. 确保两者一致
```

---

### 问题4: 数据写到了错误的表

**症状**: test数据在ramnit表中

**原因**: C2端botnet_type配置错误

**解决**:
```json
// 文件: backend/remote/config.json
{
    "botnet": {
        "botnet_type": "test"  // ← 确保正确
    }
}
```

---

## 附录

### A. 目录结构

```
backend/
├── config.py                    # 平台端主配置
├── log_processor/
│   ├── main.py                  # 日志处理器主程序
│   ├── remote_puller.py         # 远程拉取器
│   ├── enricher.py              # IP富化器
│   └── db_writer.py             # 数据库写入器
├── remote/
│   ├── config.json              # C2端配置文件
│   └── c2_data_server.py        # C2端服务器
├── worker.py                    # Worker进程
├── task_queue.py                # Redis队列封装
└── scripts/
    ├── check_test_data.py       # 数据检查脚本
    └── diagnose_queue.py        # 队列诊断脚本
```

### B. 端口占用

| 服务 | 默认端口 | 说明 |
|------|---------|------|
| C2 HTTP | 8080 | C2服务器API端口 |
| MySQL | 3306 | 数据库 |
| Redis | 6379 | 队列和缓存 |

### C. 日志位置

| 日志 | 位置 | 说明 |
|------|------|------|
| C2端日志 | `/var/log/c2_data_server.log` | C2服务器日志 |
| 平台端日志 | `logs/log_processor.log` | 日志处理器 |
| Worker日志 | `logs/worker.log` | Worker进程 |

---

**文档版本**: v2.0  
**最后更新**: 2026-01-14  
**维护者**: System Admin
