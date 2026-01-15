# 队列模式重构总结

**重构日期**: 2026-01-14  
**状态**: ✅ 完成

---

## 🎯 重构目标

1. ✅ 将队列模式相关代码整合到`log_processor`目录
2. ✅ 将所有配置参数集中到`config.py`
3. ✅ 最小化代码修改，保持向后兼容

---

## 📊 重构成果

### 文件变更

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `backend/config.py` | ✅ 新增配置 | 添加队列模式相关的所有配置参数 |
| `backend/log_processor/task_queue.py` | ✅ 新文件 | 从`config.py`读取配置的队列模块 |
| `backend/log_processor/worker.py` | ✅ 新文件 | 从`config.py`读取配置的Worker进程 |
| `backend/log_processor/main.py` | ✅ 修改 | 更新导入路径和模式检测逻辑 |
| `backend/task_queue.py` | ⚠️  待删除 | 旧文件，请删除或备份 |
| `backend/worker.py` | ⚠️  待删除 | 旧文件，请删除或备份 |

---

## 🆕 新增配置参数（config.py）

### 1. 队列模式开关

```python
# 一键启用/禁用队列模式
QUEUE_MODE_ENABLED = True  # True=队列模式, False=直接模式
```

**环境变量**: `export QUEUE_MODE_ENABLED=false`

---

### 2. Redis队列配置

```python
QUEUE_REDIS_CONFIG = {
    'host': 'localhost',              # Redis地址
    'port': 6379,                     # Redis端口
    'db': 0,                          # Redis数据库
    'password': None,                 # Redis密码（可选）
    'socket_connect_timeout': 5,
    'socket_timeout': 5,
    'retry_on_timeout': True,
    'health_check_interval': 30,
    'decode_responses': True,
}
```

**环境变量**:
- `QUEUE_REDIS_HOST`
- `QUEUE_REDIS_PORT`
- `QUEUE_REDIS_DB`
- `QUEUE_REDIS_PASSWORD`

---

### 3. 队列名称配置

```python
QUEUE_NAMES = {
    'ip_upload': 'botnet:ip_upload_queue',  # IP上传队列
    'task_queue': 'botnet:task_queue',      # 任务队列
}
```

**环境变量**:
- `QUEUE_NAME_IP_UPLOAD`
- `QUEUE_NAME_TASK`

---

### 4. Worker进程配置

```python
WORKER_CONFIG = {
    'worker_count': 1,                # Worker数量
    'enricher_concurrent': 20,        # IP查询并发数
    'enricher_cache_size': 10000,     # IP缓存大小
    'enricher_cache_ttl': 86400,      # IP缓存TTL（秒）
    'db_batch_size': 100,             # 批量写入大小
    'max_retries': 3,                 # 失败重试次数
    'retry_delay': 5,                 # 重试延迟（秒）
    'queue_timeout': 1,               # 队列拉取超时（秒）
    'log_level': 'INFO',              # 日志级别
    'log_file': 'logs/worker.log',    # 日志文件
}
```

**环境变量**:
- `WORKER_COUNT`
- `WORKER_ENRICHER_CONCURRENT`
- `WORKER_CACHE_SIZE`
- `WORKER_CACHE_TTL`
- `WORKER_DB_BATCH_SIZE`
- `WORKER_MAX_RETRIES`
- `WORKER_RETRY_DELAY`
- `WORKER_QUEUE_TIMEOUT`
- `WORKER_LOG_LEVEL`
- `WORKER_LOG_FILE`

---

## 🚀 使用方式

### 方式1: 修改config.py（推荐）

```python
# backend/config.py

# 启用队列模式（生产环境）
QUEUE_MODE_ENABLED = True

# 配置Redis连接
QUEUE_REDIS_CONFIG = {
    'host': '192.168.1.100',  # 修改为你的Redis地址
    'port': 6379,
    # ... 其他配置
}

# 配置Worker
WORKER_CONFIG = {
    'worker_count': 4,        # 启动4个Worker
    'enricher_concurrent': 50,# 每个Worker 50并发
    # ... 其他配置
}
```

---

### 方式2: 使用环境变量

```bash
# 启用队列模式
export QUEUE_MODE_ENABLED=true

# 配置Redis
export QUEUE_REDIS_HOST=192.168.1.100
export QUEUE_REDIS_PORT=6379

# 配置Worker
export WORKER_COUNT=4
export WORKER_ENRICHER_CONCURRENT=50

# 启动
python backend/log_processor/main.py
python backend/log_processor/worker.py
```

---

## 📂 新的目录结构

```
backend/
├── config.py                          ⭐ 所有配置集中在这里
│
├── log_processor/                     ⭐ 日志处理器模块
│   ├── main.py                       # 主程序
│   ├── task_queue.py                 # ✨ 队列模块（新）
│   ├── worker.py                     # ✨ Worker进程（新）
│   ├── enricher.py
│   ├── db_writer.py
│   ├── remote_puller.py
│   └── ...
│
├── task_queue.py                      ⚠️  旧文件（删除）
├── worker.py                          ⚠️  旧文件（删除）
└── ...
```

---

## 🔄 迁移步骤

### 1. 删除旧文件

```bash
cd backend
rm task_queue.py        # 或 mv task_queue.py task_queue.py.old
rm worker.py            # 或 mv worker.py worker.py.old
```

### 2. 配置队列模式

编辑 `backend/config.py`:

```python
# 启用或禁用队列模式
QUEUE_MODE_ENABLED = True  # 或 False

# 根据需要调整其他配置...
```

### 3. 重启服务

```bash
# 停止旧服务
pkill -f "python.*main.py"
pkill -f "python.*worker.py"

# 启动主程序
cd backend/log_processor
python main.py &

# 如果启用队列模式，启动Worker
python worker.py &
```

### 4. 验证

```bash
# 查看主程序日志
tail -f logs/log_processor.log

# 查看Worker日志（如果启用队列）
tail -f logs/worker.log

# 检查数据处理
python backend/scripts/check_test_data.py
```

---

## 💡 模式切换

### 启用队列模式

```python
# config.py
QUEUE_MODE_ENABLED = True
```

**启动**:
```bash
python backend/log_processor/main.py &   # 主程序
python backend/log_processor/worker.py &  # Worker（必须！）
```

**特点**:
- ✅ 异步处理，不阻塞
- ✅ 支持失败重试
- ✅ 可并发多个Worker
- ⚠️  需要Redis

---

### 禁用队列模式

```python
# config.py
QUEUE_MODE_ENABLED = False
```

**启动**:
```bash
python backend/log_processor/main.py &   # 仅主程序
# 无需Worker
```

**特点**:
- ✅ 简单，无需Redis
- ✅ 直接同步处理
- ⚠️  处理大量数据时可能阻塞
- ⚠️  不支持失败重试

---

## 📋 配置参数速查

### 常用配置

| 配置项 | 位置 | 默认值 | 环境变量 |
|--------|------|--------|----------|
| **队列模式开关** | `QUEUE_MODE_ENABLED` | `true` | `QUEUE_MODE_ENABLED` |
| **Redis地址** | `QUEUE_REDIS_CONFIG['host']` | `localhost` | `QUEUE_REDIS_HOST` |
| **Redis端口** | `QUEUE_REDIS_CONFIG['port']` | `6379` | `QUEUE_REDIS_PORT` |
| **Worker数量** | `WORKER_CONFIG['worker_count']` | `1` | `WORKER_COUNT` |
| **IP查询并发** | `WORKER_CONFIG['enricher_concurrent']` | `20` | `WORKER_ENRICHER_CONCURRENT` |

### 性能调优

| 场景 | 推荐配置 |
|------|---------|
| **高性能服务器** | `worker_count=4`, `enricher_concurrent=50` |
| **普通服务器** | `worker_count=2`, `enricher_concurrent=20` |
| **低配服务器** | `worker_count=1`, `enricher_concurrent=10` |
| **测试环境** | `QUEUE_MODE_ENABLED=False`（无需Redis） |

---

## 🐛 故障排查

### 问题：主程序无法导入task_queue

**症状**:
```
ModuleNotFoundError: No module named 'log_processor.task_queue'
```

**解决**:
```bash
# 检查文件是否存在
ls backend/log_processor/task_queue.py

# 如果不存在，说明文件未创建
```

---

### 问题：Worker无法连接Redis

**症状**:
```
[Worker-1] Redis连接失败
```

**解决**:
```bash
# 1. 检查Redis是否运行
redis-cli ping

# 2. 检查配置
grep "QUEUE_REDIS_CONFIG" backend/config.py

# 3. 启动Redis
redis-server
```

---

### 问题：数据未写入数据库

**症状**:
```
远程拉取: 总计 1000, 已保存 1000
[test] 写入: 0
```

**解决**:

1. **如果启用了队列模式** - 检查Worker是否运行:
```bash
ps aux | grep worker.py
# 如果没有，启动Worker
python backend/log_processor/worker.py &
```

2. **或者切换到直接模式**:
```python
# config.py
QUEUE_MODE_ENABLED = False
# 重启主程序
```

---

## 📖 相关文档

- **迁移指南**: `QUEUE_MODE_REFACTORING_GUIDE.md` - 详细的迁移步骤
- **数据传输指南**: `DATA_TRANSMISSION_COMPLETE_GUIDE.md` - 完整的数据传输流程
- **队列问题修复**: `QUEUE_ISSUE_FIX.md` - 队列常见问题

---

## ✅ 重构检查清单

- [x] 队列代码移动到`log_processor`目录
- [x] 所有配置集中到`config.py`
- [x] 支持环境变量覆盖配置
- [x] main.py导入路径已更新
- [x] Worker导入路径已更新
- [x] 一键切换队列/直接模式
- [x] 创建迁移文档

---

**重构完成！**

现在所有队列相关的代码都整合在`log_processor`目录中，所有配置参数都集中在`config.py`，便于统一管理和维护。

**下一步**: 删除旧文件 `backend/task_queue.py` 和 `backend/worker.py`，然后按照迁移步骤重启服务。
