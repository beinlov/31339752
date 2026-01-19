# 僵尸网络抑制阻断攻击脚本

## ? 目录结构

```
suppression_scripts/
├── __init__.py                  # 包初始化文件
├── task_executor.py             # 任务执行器（核心管理模块）
├── port.py                      # 端口资源消耗攻击脚本
├── stack.py                     # SYN洪水攻击脚本（TCP/IP栈攻击）
├── tcp_rst.py                   # TCP RST攻击脚本
├── dns_black_white.py           # DNS黑白名单脚本
├── gateway_packet_loss.py       # 网关丢包策略脚本
└── README.md                    # 本文档
```

## ? 功能说明

### 1. **task_executor.py** - 任务执行器
核心管理模块，负责：
- 启动和停止攻击任务进程
- 管理任务生命周期
- 监控任务状态
- 提供回调机制更新任务状态到数据库

**主要类：**
- `TaskExecutor`: 基类
- `PortConsumeExecutor`: 端口资源消耗任务执行器
- `SynFloodExecutor`: SYN洪水攻击任务执行器

**主要函数：**
- `stop_task(task_id)`: 停止指定任务
- `get_running_tasks()`: 获取所有运行中的任务
- `cleanup_finished_tasks()`: 清理已完成的任务

### 2. **port.py** - 端口资源消耗攻击
通过大量TCP连接占用目标的端口资源。

**命令行参数：**
```bash
python port.py <target_ip> <target_port> <threads>
```

**示例：**
```bash
python port.py 192.168.1.100 80 100
```

### 3. **stack.py** - SYN洪水攻击
发送大量SYN包消耗目标的TCP/IP栈资源。

**命令行参数：**
```bash
python stack.py <target_ip> <target_port> <threads> <duration> <rate>
```

**示例：**
```bash
python stack.py 192.168.1.100 80 50 60 1000
```

### 4. **tcp_rst.py** - TCP RST攻击
通过发送RST包强制断开已建立的TCP连接。

### 5. **dns_black_white.py** - DNS黑白名单
管理DNS查询的黑白名单策略。

### 6. **gateway_packet_loss.py** - 网关丢包策略
实现间歇性丢包策略，影响目标网络通信质量。

## ? 集成方式

这些脚本已被集成到FastAPI后端中，通过`router/suppression.py`提供RESTful API接口。

### API调用流程

1. **前端发起请求** → 
2. **FastAPI接收** (`suppression.py`) → 
3. **任务执行器启动** (`task_executor.py`) → 
4. **攻击脚本运行** (`port.py`, `stack.py`, etc.) → 
5. **状态回调更新数据库**

### 任务管理

- 每个任务都有唯一的`task_id`
- 任务在独立的子进程中运行
- 支持实时停止任务
- 任务日志自动记录到内存和数据库

## ? 数据库表

### port_consume_task - 端口资源消耗任务
```sql
- task_id: 任务ID
- target_ip: 目标IP
- target_port: 目标端口
- threads: 线程数
- status: 状态 (running/stopped/error)
- start_time: 启动时间
- stop_time: 停止时间
```

### syn_flood_task - SYN洪水攻击任务
```sql
- task_id: 任务ID
- target_ip: 目标IP
- target_port: 目标端口
- threads: 线程数
- duration: 持续时间（秒）
- rate: 速率（包/秒）
- status: 状态
- start_time: 启动时间
- stop_time: 停止时间
```

## ? 使用示例

### Python代码中使用

```python
from suppression_scripts.task_executor import PortConsumeExecutor

# 创建执行器
executor = PortConsumeExecutor(task_id="test-001")

# 启动任务
executor.start(
    ip="192.168.1.100",
    port=80,
    threads=100,
    callback=my_callback_function
)

# 停止任务
executor.stop()
```

### 通过API使用

```bash
# 启动端口资源消耗攻击
curl -X POST http://localhost:8000/api/suppression/port-consume/start \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.100",
    "port": 80,
    "threads": 100
  }'

# 停止任务
curl -X POST http://localhost:8000/api/suppression/task/{task_id}/stop
```

## ?? 注意事项

1. **权限要求**：某些攻击脚本可能需要管理员/root权限
2. **网络环境**：确保网络配置允许发送原始数据包
3. **资源消耗**：高线程数会消耗大量系统资源
4. **合法性**：仅用于授权的安全测试环境
5. **防火墙**：可能被防火墙或IDS检测和阻止

## ? 安全建议

- 只在隔离的测试环境中使用
- 获得明确的书面授权
- 记录所有操作日志
- 定期清理已完成的任务
- 监控系统资源使用情况

## ? 日志记录

所有任务的执行日志都会：
1. 实时输出到控制台
2. 保存到内存中（最多100条/任务）
3. 通过回调函数更新到数据库
4. 可通过API查询：`GET /api/suppression/logs`

## ?? 故障排查

### 任务启动失败
- 检查Python路径是否正确
- 确认攻击脚本文件存在
- 查看日志获取详细错误信息

### 任务无法停止
- 使用系统进程管理器手动终止
- 检查进程是否有权限被终止
- 重启后端服务

### 数据库状态不同步
- 检查回调函数是否正常执行
- 手动更新数据库表状态
- 清理僵尸进程

## ? 相关文档

- `backend/router/suppression.py` - API路由实现
- `backend/scripts/init_suppression_tables.py` - 数据库初始化
- `抑制阻断集成说明.md` - 完整集成文档
