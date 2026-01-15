# 队列模式重构迁移指南

**重构日期**: 2026-01-14  
**重构目标**: 将队列模式相关代码整合到log_processor目录，所有配置集中到config.py

---

## 📋 重构概览

### 重构内容

| 项目 | 旧位置 | 新位置 | 状态 |
|------|--------|--------|------|
| **task_queue.py** | `backend/task_queue.py` | `backend/log_processor/task_queue.py` | ✅ 已迁移 |
| **worker.py** | `backend/worker.py` | `backend/log_processor/worker.py` | ✅ 已迁移 |
| **队列配置** | 硬编码在文件中 | `backend/config.py` | ✅ 已集中 |
| **main.py导入** | `from task_queue import task_queue` | `from log_processor.task_queue import task_queue` | ✅ 已更新 |

### 重构优势

| 优势 | 说明 |
|------|------|
| ✅ **模块化** | 队列相关代码集中在log_processor目录 |
| ✅ **配置集中** | 所有参数在config.py统一管理 |
| ✅ **环境变量** | 支持通过环境变量覆盖配置 |
| ✅ **易于禁用** | 通过QUEUE_MODE_ENABLED一键切换模式 |
| ✅ **向后兼容** | 保持API不变，最小化代码改动 |

---

## 🗂️ 新的目录结构

```
backend/
├── config.py                          ⭐ 所有配置集中在这里
│   ├── QUEUE_MODE_ENABLED            # 队列模式开关
│   ├── QUEUE_REDIS_CONFIG            # Redis连接配置
│   ├── QUEUE_NAMES                   # 队列名称配置
│   └── WORKER_CONFIG                 # Worker进程配置
│
├── log_processor/                     ⭐ 日志处理器模块
│   ├── main.py                       # 主程序（已更新导入）
│   ├── task_queue.py                 # ✨ 队列模块（新位置）
│   ├── worker.py                     # ✨ Worker进程（新位置）
│   ├── enricher.py                   # IP富化器
│   ├── db_writer.py                  # 数据库写入器
│   ├── remote_puller.py              # 远程拉取器
│   └── ... 其他模块
│
├── task_queue.py                      ⚠️  旧文件（需要删除/备份）
└── worker.py                          ⚠️  旧文件（需要删除/备份）
```

---

## ⚙️ 新的配置方式

### 1. config.py中的队列配置

```python
# backend/config.py

# ============================================================
# 队列模式配置（Queue Mode Configuration）
# ============================================================

# 队列模式开关（一键切换）
QUEUE_MODE_ENABLED = True  # True=队列模式, False=直接模式

# Redis队列配置
QUEUE_REDIS_CONFIG = {
    'host': 'localhost',      # Redis服务器地址
    'port': 6379,             # Redis端口
    'db': 0,                  # Redis数据库编号
    'password': None,         # Redis密码（可选）
    'socket_connect_timeout': 5,
    'socket_timeout': 5,
    'retry_on_timeout': True,
    'health_check_interval': 30,
    'decode_responses': True,
}

# 队列名称配置
QUEUE_NAMES = {
    'ip_upload': 'botnet:ip_upload_queue',  # IP上传队列
    'task_queue': 'botnet:task_queue',      # 通用任务队列
}

# Worker配置
WORKER_CONFIG = {
    'worker_count': 1,                # Worker进程数量
    'enricher_concurrent': 20,        # IP富化并发数
    'enricher_cache_size': 10000,     # IP缓存大小
    'enricher_cache_ttl': 86400,      # IP缓存TTL（秒）
    'db_batch_size': 100,             # 数据库批量写入大小
    'max_retries': 3,                 # 失败重试次数
    'retry_delay': 5,                 # 重试延迟（秒）
    'queue_timeout': 1,               # 队列拉取超时（秒）
    'log_level': 'INFO',              # 日志级别
    'log_file': 'logs/worker.log',    # 日志文件路径
}
```

### 2. 通过环境变量覆盖配置

```bash
# 禁用队列模式
export QUEUE_MODE_ENABLED=false

# 修改Redis配置
export QUEUE_REDIS_HOST=192.168.1.100
export QUEUE_REDIS_PORT=6380
export QUEUE_REDIS_PASSWORD=mypassword

# 修改Worker配置
export WORKER_COUNT=4
export WORKER_ENRICHER_CONCURRENT=50
export WORKER_LOG_LEVEL=DEBUG

# 启动程序
python backend/log_processor/main.py
```

---

## 🚀 迁移步骤

### 步骤1: 备份旧文件（可选）

```bash
cd backend

# 备份旧文件
mv task_queue.py task_queue.py.old
mv worker.py worker.py.old

# 或者直接删除
# rm task_queue.py worker.py
```

### 步骤2: 验证新文件存在

```bash
# 检查新文件是否存在
ls -la log_processor/task_queue.py
ls -la log_processor/worker.py

# 检查config.py是否已更新
grep "QUEUE_MODE_ENABLED" config.py
grep "QUEUE_REDIS_CONFIG" config.py
grep "WORKER_CONFIG" config.py
```

### 步骤3: 配置队列模式

编辑 `backend/config.py`:

```python
# 启用队列模式（推荐生产环境）
QUEUE_MODE_ENABLED = True

# 或者禁用队列模式（测试环境）
QUEUE_MODE_ENABLED = False

# 根据需要调整其他配置
QUEUE_REDIS_CONFIG = {
    'host': 'localhost',  # 修改为你的Redis地址
    'port': 6379,
    # ... 其他配置
}

WORKER_CONFIG = {
    'worker_count': 2,  # 修改Worker数量
    # ... 其他配置
}
```

### 步骤4: 重启服务

```bash
# 1. 停止旧的服务
pkill -f "python.*main.py"
pkill -f "python.*worker.py"

# 2. 启动主程序
cd backend/log_processor
python main.py &

# 3. 如果启用了队列模式，启动Worker
cd backend/log_processor
python worker.py &

# 或者启动多个Worker
python worker.py 1 &  # Worker #1
python worker.py 2 &  # Worker #2
python worker.py 3 &  # Worker #3
```

### 步骤5: 验证迁移成功

```bash
# 1. 查看主程序日志
tail -f logs/log_processor.log

# 期望看到（队列模式）:
# [队列模式] 已启用 - 数据将通过Redis队列异步处理
# [队列模式] 所有配置从 config.py 读取

# 或者（直接模式）:
# [直接模式] 队列模式已禁用 - 数据将直接同步处理

# 2. 查看Worker日志（如果启用队列模式）
tail -f logs/worker.log

# 期望看到:
# [Worker-1] 初始化完成
# [Worker-1] 配置: 富化并发=20, 缓存=10000, DB批量=100
# [Worker-1] Redis连接成功
# [Worker-1] 启动成功，等待任务...

# 3. 检查Redis队列
redis-cli LLEN botnet:task_queue
redis-cli INFO clients

# 4. 检查数据处理
python backend/scripts/check_test_data.py
```

---

## 🎯 配置参数速查表

### 队列模式开关

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `QUEUE_MODE_ENABLED` | `config.py` | `true` | 队列模式总开关 |

**环境变量**: `export QUEUE_MODE_ENABLED=false`

---

### Redis连接配置

| 参数 | 位置 | 默认值 | 环境变量 |
|------|------|--------|----------|
| `host` | `QUEUE_REDIS_CONFIG` | `localhost` | `QUEUE_REDIS_HOST` |
| `port` | `QUEUE_REDIS_CONFIG` | `6379` | `QUEUE_REDIS_PORT` |
| `db` | `QUEUE_REDIS_CONFIG` | `0` | `QUEUE_REDIS_DB` |
| `password` | `QUEUE_REDIS_CONFIG` | `None` | `QUEUE_REDIS_PASSWORD` |

**示例配置**:
```python
QUEUE_REDIS_CONFIG = {
    'host': '192.168.1.100',  # 远程Redis
    'port': 6380,             # 自定义端口
    'password': 'mypassword', # 启用认证
}
```

---

### 队列名称配置

| 参数 | 位置 | 默认值 | 环境变量 |
|------|------|--------|----------|
| `ip_upload` | `QUEUE_NAMES` | `botnet:ip_upload_queue` | `QUEUE_NAME_IP_UPLOAD` |
| `task_queue` | `QUEUE_NAMES` | `botnet:task_queue` | `QUEUE_NAME_TASK` |

**用途**:
- `ip_upload`: API上传的IP数据队列
- `task_queue`: 远程拉取的数据队列

---

### Worker进程配置

| 参数 | 位置 | 默认值 | 环境变量 | 说明 |
|------|------|--------|----------|------|
| `worker_count` | `WORKER_CONFIG` | `1` | `WORKER_COUNT` | Worker进程数量 |
| `enricher_concurrent` | `WORKER_CONFIG` | `20` | `WORKER_ENRICHER_CONCURRENT` | IP查询并发数 |
| `enricher_cache_size` | `WORKER_CONFIG` | `10000` | `WORKER_CACHE_SIZE` | IP缓存大小 |
| `enricher_cache_ttl` | `WORKER_CONFIG` | `86400` | `WORKER_CACHE_TTL` | IP缓存TTL（秒） |
| `db_batch_size` | `WORKER_CONFIG` | `100` | `WORKER_DB_BATCH_SIZE` | 批量写入大小 |
| `max_retries` | `WORKER_CONFIG` | `3` | `WORKER_MAX_RETRIES` | 失败重试次数 |
| `retry_delay` | `WORKER_CONFIG` | `5` | `WORKER_RETRY_DELAY` | 重试延迟（秒） |
| `queue_timeout` | `WORKER_CONFIG` | `1` | `WORKER_QUEUE_TIMEOUT` | 队列拉取超时 |
| `log_level` | `WORKER_CONFIG` | `INFO` | `WORKER_LOG_LEVEL` | 日志级别 |
| `log_file` | `WORKER_CONFIG` | `logs/worker.log` | `WORKER_LOG_FILE` | 日志文件 |

**性能调优建议**:
```python
# 高性能配置（多核服务器）
WORKER_CONFIG = {
    'worker_count': 4,              # 4个Worker并发
    'enricher_concurrent': 50,      # 每个Worker 50并发
    'db_batch_size': 500,           # 大批量写入
}

# 低资源配置（单核服务器）
WORKER_CONFIG = {
    'worker_count': 1,              # 单Worker
    'enricher_concurrent': 10,      # 低并发
    'db_batch_size': 50,            # 小批量写入
}
```

---

## 🔄 模式切换指南

### 从队列模式切换到直接模式

```python
# 1. 修改config.py
QUEUE_MODE_ENABLED = False

# 2. 重启主程序
pkill -f "python.*main.py"
python backend/log_processor/main.py &

# 3. 停止Worker（不再需要）
pkill -f "python.*worker.py"
```

**效果**:
- ✅ 数据直接同步处理
- ✅ 无需Redis和Worker
- ⚠️  处理大量数据时可能阻塞

---

### 从直接模式切换到队列模式

```python
# 1. 确保Redis运行
redis-cli ping  # 应返回PONG

# 2. 修改config.py
QUEUE_MODE_ENABLED = True

# 3. 重启主程序
pkill -f "python.*main.py"
python backend/log_processor/main.py &

# 4. 启动Worker（必须！）
python backend/log_processor/worker.py &
```

**效果**:
- ✅ 数据异步处理
- ✅ 支持失败重试
- ✅ 可并发处理

---

## 🐛 故障排查

### 问题1: 主程序启动失败

**症状**:
```
ModuleNotFoundError: No module named 'log_processor.task_queue'
```

**原因**: 新文件未创建

**解决**:
```bash
# 检查文件是否存在
ls -la backend/log_processor/task_queue.py
ls -la backend/log_processor/worker.py

# 如果不存在，从备份恢复或重新创建
```

---

### 问题2: Worker无法连接Redis

**症状**:
```
[Worker-1] Redis连接失败！请确保Redis已启动
```

**原因**: Redis未运行或配置错误

**解决**:
```bash
# 1. 检查Redis是否运行
redis-cli ping

# 2. 检查Redis配置
grep "QUEUE_REDIS_CONFIG" backend/config.py

# 3. 测试连接
redis-cli -h localhost -p 6379 ping
```

---

### 问题3: 队列积压

**症状**:
```
redis-cli LLEN botnet:task_queue
(integer) 50000  # 队列积压5万个任务
```

**原因**: Worker处理速度慢或未启动

**解决**:
```bash
# 1. 检查Worker是否运行
ps aux | grep worker.py

# 2. 启动更多Worker
python backend/log_processor/worker.py 1 &
python backend/log_processor/worker.py 2 &
python backend/log_processor/worker.py 3 &

# 3. 或者临时切换到直接模式
# 修改config.py: QUEUE_MODE_ENABLED = False
# 重启主程序
```

---

### 问题4: 旧worker.py仍在运行

**症状**:
```
ImportError: cannot import name 'task_queue' from 'backend.task_queue'
```

**原因**: 旧版本worker.py仍在使用旧的导入路径

**解决**:
```bash
# 1. 停止所有旧进程
pkill -f "python.*worker.py"
pkill -f "python.*backend/worker.py"

# 2. 删除旧文件
rm backend/task_queue.py
rm backend/worker.py

# 3. 启动新Worker
python backend/log_processor/worker.py &
```

---

## 📝 代码变更总结

### 1. task_queue.py变更

| 变更项 | 旧代码 | 新代码 |
|--------|--------|--------|
| **位置** | `backend/task_queue.py` | `backend/log_processor/task_queue.py` |
| **配置方式** | 硬编码 | 从`config.py`读取 |
| **Redis配置** | `REDIS_HOST = 'localhost'` | `QUEUE_REDIS_CONFIG['host']` |
| **队列名称** | `QUEUE_NAME = 'botnet:ip_upload_queue'` | `QUEUE_NAMES['task_queue']` |
| **模式控制** | 无 | `QUEUE_MODE_ENABLED` |

### 2. worker.py变更

| 变更项 | 旧代码 | 新代码 |
|--------|--------|--------|
| **位置** | `backend/worker.py` | `backend/log_processor/worker.py` |
| **导入** | `from task_queue import task_queue` | `from log_processor.task_queue import task_queue` |
| **配置方式** | 硬编码 | 从`config.py`读取`WORKER_CONFIG` |
| **富化并发** | `max_concurrent=20` | `WORKER_CONFIG['enricher_concurrent']` |
| **批量大小** | `batch_size=100` | `WORKER_CONFIG['db_batch_size']` |
| **日志文件** | 无 | `WORKER_CONFIG['log_file']` |

### 3. main.py变更

| 变更项 | 旧代码 | 新代码 |
|--------|--------|--------|
| **导入** | `from task_queue import task_queue` | `from log_processor.task_queue import task_queue` |
| **模式检测** | `try-except ImportError` | `if QUEUE_MODE_ENABLED` |
| **配置读取** | 无 | 导入`QUEUE_MODE_ENABLED` |

---

## ✅ 迁移检查清单

迁移完成后，请检查以下项目：

- [ ] 旧文件已删除或备份
  ```bash
  ls backend/task_queue.py  # 应不存在或为.old
  ls backend/worker.py      # 应不存在或为.old
  ```

- [ ] 新文件已创建
  ```bash
  ls backend/log_processor/task_queue.py  # 应存在
  ls backend/log_processor/worker.py      # 应存在
  ```

- [ ] config.py已更新
  ```bash
  grep "QUEUE_MODE_ENABLED" backend/config.py
  grep "QUEUE_REDIS_CONFIG" backend/config.py
  grep "WORKER_CONFIG" backend/config.py
  ```

- [ ] 主程序启动正常
  ```bash
  # 日志应显示:
  # [队列模式] 已启用 或 [直接模式] 队列模式已禁用
  ```

- [ ] Worker启动正常（如果启用队列模式）
  ```bash
  # 日志应显示:
  # [Worker-1] 初始化完成
  # [Worker-1] Redis连接成功
  ```

- [ ] 数据正常处理
  ```bash
  python backend/scripts/check_test_data.py
  # 应显示有新数据写入
  ```

- [ ] Redis队列正常
  ```bash
  redis-cli LLEN botnet:task_queue
  # 应返回数字（可能为0或正数）
  ```

---

## 📚 相关文档

- **配置文档**: `backend/config.py` - 所有配置参数说明
- **数据传输指南**: `backend/DATA_TRANSMISSION_COMPLETE_GUIDE.md` - 完整的数据传输流程
- **队列问题修复**: `backend/QUEUE_ISSUE_FIX.md` - 队列常见问题解决

---

**迁移完成标志**:
✅ 所有配置集中在config.py  
✅ 队列代码整合到log_processor目录  
✅ 支持环境变量配置  
✅ 一键切换队列/直接模式  
✅ 向后兼容，最小化改动

**重构版本**: v2.0  
**文档更新**: 2026-01-14
