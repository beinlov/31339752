# 快速启动指南

**版本**: v3.0（内置Worker模式）  
**更新日期**: 2026-01-15

---

## 🚀 一键启动

```bash
# 进入目录
cd d:\workspace\botnet\backend\log_processor

# 启动服务（仅此一条命令！）
python main.py
```

**就这么简单！** 🎉

---

## 📋 启动前检查

### 1. 确认Redis运行

```bash
redis-cli ping
# 期望输出: PONG
```

如果未运行:
```bash
redis-server
```

---

### 2. 确认MySQL运行

```bash
mysql -u root -p -e "SELECT 1"
# 能正常连接即可
```

---

### 3. 确认配置正确

检查 `backend/config.py`:

```python
# 队列模式（必须启用）
QUEUE_MODE_ENABLED = True

# 内置Worker配置（必须启用）
INTERNAL_WORKER_CONFIG = {
    'worker_count': 1,     # Worker数量
    'enabled': True,       # 必须为True
}

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '你的密码',
    'database': 'botnet'
}
```

---

## ✅ 验证运行

### 1. 查看启动日志

启动后应该看到:

```
[队列模式] 已启用 - 数据将通过Redis队列异步处理
[内置Worker] 已启用 - 将启动 1 个Worker协程
正在启动 1 个内置Worker协程...
[OK] 内置Worker-1 已启动
[OK] 所有内置Worker已启动 (共 1 个)
[内置Worker-1] 启动
Botnet Log Processor is running. Press Ctrl+C to stop.
```

---

### 2. 检查日志文件

```bash
tail -f logs/log_processor.log
```

**数据处理时应该看到**:

```
远程拉取: 总计 1000, 已保存 1000
[内置Worker-1] 开始处理任务: test_1737008123.456, 1000 条IP
[内置Worker-1] 任务完成 | 处理 1000, 错误 0, 写入 950 | 耗时 5.23秒
```

---

### 3. 检查数据库

```bash
python backend/scripts/check_test_data.py
```

**期望输出**:

```
✅ 表存在: botnet_communications_test
✅ 最近5分钟有新数据写入
📊 总数据量: 1234 条
```

---

## ⚙️ 常用配置

### 低负载（默认）

```python
INTERNAL_WORKER_CONFIG = {
    'worker_count': 1,              # 1个Worker
}
```

适用于: 单核CPU、数据量<1万/天

---

### 中等负载

```python
INTERNAL_WORKER_CONFIG = {
    'worker_count': 2,              # 2个Worker
    'enricher_concurrent': 30,      # 更高并发
}
```

适用于: 双核CPU、数据量1-10万/天

---

### 高负载

```python
INTERNAL_WORKER_CONFIG = {
    'worker_count': 4,              # 4个Worker
    'enricher_concurrent': 50,      # 高并发
    'db_batch_size': 500,           # 大批量
}
```

适用于: 四核+CPU、数据量>10万/天

---

## 🛑 停止服务

### 优雅停止

```bash
# 在运行终端按 Ctrl+C
# 程序会自动:
# 1. 停止所有内置Worker
# 2. 停止远程拉取任务
# 3. 刷新缓冲区数据
# 4. 优雅退出
```

### 强制停止

```bash
# Windows
taskkill /F /IM python.exe

# Linux/Mac
pkill -9 python
```

---

## 🐛 常见问题

### Q1: 启动后Worker未显示

**检查**:
```bash
grep "内置Worker" logs/log_processor.log
```

**可能原因**:
1. `QUEUE_MODE_ENABLED = False` - 需要设为True
2. `INTERNAL_WORKER_CONFIG['enabled'] = False` - 需要设为True
3. Redis未运行 - 启动Redis

---

### Q2: 数据未写入数据库

**检查**:
```bash
python backend/scripts/check_queue_status.py
```

**可能原因**:
1. Worker未启动 - 检查日志
2. 数据库连接失败 - 检查DB_CONFIG
3. 队列名称不匹配 - 运行诊断脚本

---

### Q3: Redis连接失败

**错误信息**:
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**解决**:
```bash
# 启动Redis
redis-server

# 或检查Redis地址配置
grep "QUEUE_REDIS_CONFIG" backend/config.py
```

---

### Q4: 想使用旧的独立Worker

**临时禁用内置Worker**:

```python
# config.py
INTERNAL_WORKER_CONFIG = {
    'enabled': False,
}
```

然后手动启动:
```bash
python backend/log_processor/worker.py
```

---

## 📊 性能监控

### 查看实时统计

日志中每60秒输出一次:

```
=== 统计信息 ===
总行数: 1000
处理行数: 950
错误数: 5
运行时间: 0:05:30
[test] 写入: 950, 重复: 45, 缓冲: 0
IP查询: 1000, L1命中率: 85.50%, L2命中率: 12.30%, 总命中率: 97.80%
远程拉取: 总计 5000, 已保存 5000, 错误 0
内置Worker: 1 个协程运行中
```

---

### 查看队列状态

```bash
python backend/scripts/check_queue_status.py
```

---

### 查看数据库状态

```bash
python backend/scripts/check_test_data.py
```

---

## 🎯 启动脚本（可选）

创建 `start.bat` (Windows):

```batch
@echo off
cd /d d:\workspace\botnet\backend\log_processor
echo 正在启动Botnet数据处理系统...
python main.py
pause
```

创建 `start.sh` (Linux/Mac):

```bash
#!/bin/bash
cd "$(dirname "$0")/backend/log_processor"
echo "正在启动Botnet数据处理系统..."
python main.py
```

使用:
```bash
# Windows
双击 start.bat

# Linux/Mac
chmod +x start.sh
./start.sh
```

---

## 📚 相关文档

- **内置Worker迁移指南**: `INTERNAL_WORKER_MIGRATION.md`
- **完整配置指南**: `DATA_TRANSMISSION_COMPLETE_GUIDE.md`
- **故障排查**: `WORKER_STUCK_FIX.md`

---

## ✨ 新架构优势

| 优势 | 说明 |
|------|------|
| ✅ **一键启动** | 只需 `python main.py` |
| ✅ **自动化** | Worker自动启动和停止 |
| ✅ **简化部署** | 无需管理多个进程 |
| ✅ **资源共享** | Worker共享IP缓存 |
| ✅ **配置集中** | 所有参数在config.py |
| ✅ **易于扩展** | 配置Worker数量即可 |

---

**🎉 享受全新的一键启动体验！**

---

**版本**: v3.0  
**架构**: 内置Worker模式  
**文档更新**: 2026-01-15
