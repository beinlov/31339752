# Worker卡住问题修复指南

**问题报告日期**: 2026-01-15  
**状态**: ✅ 已修复

---

## 🐛 问题描述

### 症状1: Worker卡住不处理数据

Worker启动后显示"等待任务"，但即使队列中有任务也不处理，直到按Ctrl+C才开始处理。

### 症状2: Ctrl+C时Redis超时错误

```
redis.exceptions.TimeoutError: Timeout reading from socket
```

---

## 🔍 根本原因

### 原因1: 队列名称不匹配 ⭐ 主要问题

**旧代码配置**:
- `backend/task_queue.py` 使用: `QUEUE_NAME = 'botnet:ip_upload_queue'`
- `backend/worker.py` 从 `botnet:ip_upload_queue` 读取

**新代码配置**:
- `backend/config.py` 默认使用: `task_queue: 'botnet:task_queue'`
- 主程序推送到 `botnet:task_queue`

**结果**: 
- ❌ 主程序推送到 `botnet:task_queue`
- ❌ Worker从 `botnet:ip_upload_queue` 读取
- ❌ 两个队列不是同一个，导致Worker永远等不到任务

### 原因2: 信号处理不当

Ctrl+C中断时，Redis的`blpop`操作未被正确取消，导致超时错误。

---

## ✅ 修复方案

### 修复1: 统一队列名称

修改 `backend/config.py`:

```python
# 队列名称配置
# 注意：为保持兼容性，默认使用 botnet:ip_upload_queue（与旧版本一致）
QUEUE_NAMES = {
    'ip_upload': 'botnet:ip_upload_queue',   # IP上传队列
    'task_queue': 'botnet:ip_upload_queue',  # ⭐ 改为与旧版本一致
}
```

**效果**: 所有组件现在使用相同的队列名称。

---

### 修复2: 改进Worker信号处理

更新 `backend/worker.py` 和 `backend/log_processor/worker.py`:

```python
# 添加Redis超时处理
except redis.TimeoutError as e:
    # Redis超时（通常是Ctrl+C中断时发生）
    if not self.running:
        logger.info("[Worker] Redis超时，准备退出")
        break
    logger.warning(f"[Worker] Redis超时: {e}")
    await asyncio.sleep(1)

# 改进KeyboardInterrupt处理
except KeyboardInterrupt:
    logger.info("[Worker] 收到停止信号...")
    self.running = False  # ⭐ 设置标志位
    break
```

**效果**: Ctrl+C时优雅退出，不再报超时错误。

---

### 修复3: 添加队列诊断日志

Worker启动时显示队列信息:

```python
logger.info(f"[Worker] 队列名称: {task_queue.queue_name}")
logger.info(f"[Worker] 检查队列长度: {task_queue.get_queue_length()}")
```

**效果**: 启动时就能看到使用的队列名称，便于诊断。

---

### 修复4: 创建诊断工具

新增 `backend/scripts/check_queue_status.py`:

```bash
python backend/scripts/check_queue_status.py
```

**功能**:
- ✅ 检查配置的队列名称
- ✅ 检测旧配置是否存在
- ✅ 测试Redis连接
- ✅ 显示所有队列的任务数量
- ✅ 检查是否有Worker在运行
- ✅ 给出诊断建议

---

## 🚀 升级步骤

### 步骤1: 停止所有服务

```bash
# Windows
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *main.py*"
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *worker.py*"

# Linux/Mac
pkill -f "python.*main.py"
pkill -f "python.*worker.py"
```

---

### 步骤2: 清理Redis队列（可选）

如果队列中有积压的任务在错误的队列中:

```bash
redis-cli DEL botnet:task_queue        # 清空新队列
redis-cli DEL botnet:ip_upload_queue   # 清空旧队列
```

⚠️ **警告**: 这会删除所有未处理的任务！

---

### 步骤3: 确认配置

检查 `backend/config.py`:

```python
# 确保队列名称一致
QUEUE_NAMES = {
    'ip_upload': 'botnet:ip_upload_queue',
    'task_queue': 'botnet:ip_upload_queue',  # ⭐ 必须一致
}
```

---

### 步骤4: 运行诊断工具

```bash
cd backend
python scripts/check_queue_status.py
```

**期望输出**:

```
【1. 配置检查】
✅ 队列模式: 启用
✅ Redis地址: localhost:6379
✅ 配置的队列名称:
   - ip_upload: botnet:ip_upload_queue
   - task_queue: botnet:ip_upload_queue

【2. 旧配置检查】
✅ 未检测到旧的task_queue.py（正常）

【3. Redis连接测试】
✅ Redis连接成功

【4. 队列状态检查】
⚪ botnet:ip_upload_queue: 空
⚪ botnet:task_queue: 空
```

---

### 步骤5: 启动服务

```bash
# 启动主程序
cd backend/log_processor
python main.py &

# 启动Worker
python worker.py &
```

**检查Worker日志**:

```bash
tail -f logs/worker.log
```

**期望看到**:

```
[Worker-1] 检查Redis连接...
[Worker-1] Redis连接成功: localhost:6379
[Worker-1] 启动成功，等待任务...
[Worker-1] 队列名称: botnet:ip_upload_queue
[Worker-1] 检查队列长度: 0
```

---

### 步骤6: 验证数据处理

等待主程序拉取数据后:

```bash
# 查看队列状态
python backend/scripts/check_queue_status.py

# 查看Worker日志
tail -f logs/worker.log

# 查看数据库
python backend/scripts/check_test_data.py
```

**期望看到**:

```
[Worker-1] 开始处理任务: test_1737006789.123, 1000 条IP
[Worker-1] 任务完成: test_1737006789.123 | 处理 1000, 错误 0, 写入 950, 重复 50 | 耗时 5.23秒
```

---

## 📋 快速诊断检查清单

### 检查1: 队列名称是否一致？

```bash
# 检查配置
grep "QUEUE_NAMES" backend/config.py

# 运行诊断工具
python backend/scripts/check_queue_status.py
```

**期望**: `ip_upload` 和 `task_queue` 使用相同的队列名。

---

### 检查2: Redis是否运行？

```bash
redis-cli ping
# 期望输出: PONG
```

---

### 检查3: 队列中是否有任务？

```bash
redis-cli LLEN botnet:ip_upload_queue
# 期望输出: 数字（可能为0或正数）
```

---

### 检查4: Worker是否在运行？

```bash
# Windows
tasklist | findstr python

# Linux/Mac
ps aux | grep worker.py
```

**期望**: 看到worker.py进程。

---

### 检查5: Worker是否在消费队列？

```bash
redis-cli CLIENT LIST | findstr blpop
```

**期望**: 看到至少一个客户端在执行`blpop`命令。

---

## 🐛 常见问题

### 问题1: Worker日志显示队列长度为0，但Redis显示有任务

**原因**: Worker连接到错误的Redis或队列名称不匹配。

**解决**:
```bash
# 检查Worker连接的队列
tail -f logs/worker.log | grep "队列名称"

# 检查所有队列
redis-cli --scan --pattern "botnet:*"
```

---

### 问题2: 按Ctrl+C后Worker不响应

**原因**: Redis的`blpop`阻塞操作未被中断。

**解决**:
```bash
# 强制结束进程
# Windows
taskkill /F /PID <进程ID>

# Linux/Mac
kill -9 <进程ID>
```

---

### 问题3: Worker处理速度很慢

**原因**: IP富化并发数太低或数据库批量大小太小。

**解决**: 修改 `backend/config.py`:

```python
WORKER_CONFIG = {
    'enricher_concurrent': 50,  # 增加IP查询并发（默认20）
    'db_batch_size': 500,       # 增加批量写入大小（默认100）
}
```

---

### 问题4: 数据仍然不写入数据库

**可能原因**:
1. ❌ Worker未启动
2. ❌ 队列模式未启用
3. ❌ 队列名称不匹配
4. ❌ 数据库连接失败

**排查步骤**:
```bash
# 1. 运行完整诊断
python backend/scripts/check_queue_status.py

# 2. 检查队列模式
grep "QUEUE_MODE_ENABLED" backend/config.py

# 3. 检查Worker日志
tail -f logs/worker.log

# 4. 检查数据库连接
python backend/scripts/check_test_data.py
```

---

## 📊 修复前后对比

### 修复前

| 问题 | 症状 |
|------|------|
| 队列名称 | `botnet:task_queue` vs `botnet:ip_upload_queue` |
| Worker状态 | 卡住，不处理数据 |
| Ctrl+C | Redis超时错误 |
| 诊断 | 无法诊断队列状态 |

### 修复后

| 改进 | 效果 |
|------|------|
| 队列名称 | ✅ 统一为 `botnet:ip_upload_queue` |
| Worker状态 | ✅ 正常接收和处理任务 |
| Ctrl+C | ✅ 优雅退出，无错误 |
| 诊断 | ✅ 提供完整的诊断工具 |

---

## 🎯 预防措施

### 1. 统一配置管理

所有配置集中在 `backend/config.py`，避免多处硬编码。

### 2. 删除旧文件

```bash
cd backend
rm task_queue.py    # 或重命名为 task_queue.py.old
rm worker.py        # 或重命名为 worker.py.old
```

使用新的模块化版本:
- `backend/log_processor/task_queue.py`
- `backend/log_processor/worker.py`

### 3. 启动时运行诊断

```bash
# 启动前检查
python backend/scripts/check_queue_status.py

# 确认一切正常后再启动服务
```

### 4. 监控队列长度

```bash
# 定期检查队列积压
watch -n 5 'redis-cli LLEN botnet:ip_upload_queue'
```

如果队列长度持续增长，说明Worker处理不过来，需要：
- 增加Worker数量
- 提高Worker并发配置
- 或切换到直接处理模式

---

## 📚 相关文档

- **队列模式重构指南**: `QUEUE_MODE_REFACTORING_GUIDE.md`
- **数据传输完整指南**: `DATA_TRANSMISSION_COMPLETE_GUIDE.md`
- **队列问题修复**: `QUEUE_ISSUE_FIX.md`

---

## ✅ 修复总结

| 修复项 | 状态 | 说明 |
|--------|------|------|
| 队列名称统一 | ✅ 完成 | 所有组件使用 `botnet:ip_upload_queue` |
| 信号处理改进 | ✅ 完成 | Ctrl+C优雅退出 |
| 诊断日志添加 | ✅ 完成 | 显示队列名称和长度 |
| 诊断工具创建 | ✅ 完成 | `check_queue_status.py` |
| 文档更新 | ✅ 完成 | 本文档 |

**问题已修复！Worker现在应该能正常接收和处理任务了。**

---

**修复版本**: v2.1  
**文档更新**: 2026-01-15
