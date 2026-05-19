# 任务管理功能更新说明

## ? 更新内容

为 **TCP RST攻击** 和 **计算资源消耗** 添加了类似于端口资源消耗的任务管理功能。

---

## ? 新增数据库表

### 1. TCP RST攻击任务表 (`tcp_rst_task`)

```sql
CREATE TABLE tcp_rst_task (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(100) UNIQUE NOT NULL,          -- 任务ID (tcp-rst_IP_PORT_timestamp)
    attack_id VARCHAR(100) UNIQUE NOT NULL,        -- 攻击ID (tcp-syn-timestamp)
    target_ip VARCHAR(45) NOT NULL,                -- 目标IP
    target_port INT NOT NULL,                      -- 目标端口
    capture_interface VARCHAR(50),                 -- 捕获接口
    inject_interface VARCHAR(50),                  -- 注入接口
    status VARCHAR(20) DEFAULT 'running',          -- 状态: running/stopped
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP, -- 启动时间
    stop_time DATETIME,                            -- 停止时间
    INDEX idx_task_id (task_id),
    INDEX idx_attack_id (attack_id),
    INDEX idx_status (status)
);
```

**字段说明**:
- `task_id`: 用于在任务列表中标识任务
- `attack_id`: 用于与中继节点通信时标识攻击
- `capture_interface`/`inject_interface`: 网络接口配置

---

### 2. 计算资源消耗任务表 (`compute_consume_task`)

```sql
CREATE TABLE compute_consume_task (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(100) UNIQUE NOT NULL,          -- 任务ID (compute-consume_domain_timestamp)
    target_url VARCHAR(500) NOT NULL,              -- 目标URL
    rate INT DEFAULT 50,                           -- 每秒启动序列数
    concurrency INT DEFAULT 100,                   -- 并发连接数
    duration INT DEFAULT 60,                       -- 持续时间(秒)
    status VARCHAR(20) DEFAULT 'running',          -- 状态: running/stopped
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP, -- 启动时间
    stop_time DATETIME,                            -- 停止时间
    INDEX idx_task_id (task_id),
    INDEX idx_status (status)
);
```

**字段说明**:
- `target_url`: 攻击目标的完整URL
- `rate`/`concurrency`/`duration`: 攻击参数

---

## ? 修改的API接口

### 1. TCP RST攻击启动 (`/api/suppression/relay-file/attack/start`)

**修改前**:
```json
// 只写入命令文件到中继节点
{
  "status": "success",
  "attack_id": "tcp-syn-1747022800"
}
```

**修改后**:
```json
// 同时保存到数据库 + 写入命令文件
{
  "status": "success",
  "attack_id": "tcp-syn-1747022800",
  "task_id": "tcp-rst_192.168.1.10_80_1747022800"
}
```

**数据库操作**:
```sql
INSERT INTO tcp_rst_task 
(task_id, attack_id, target_ip, target_port, capture_interface, inject_interface, status, start_time)
VALUES ('tcp-rst_...', 'tcp-syn-...', '192.168.1.10', 80, 'eth0', 'eth1', 'running', NOW())
```

---

### 2. TCP RST攻击停止 (`/api/suppression/relay-file/attack/stop`)

**新增功能**:
- 停止时更新数据库状态为 `stopped`
- 记录停止时间

**数据库操作**:
```sql
UPDATE tcp_rst_task
SET status = 'stopped', stop_time = NOW()
WHERE attack_id = 'tcp-syn-1747022800' AND status = 'running'
```

---

### 3. 计算资源消耗启动 (`/api/suppression/compute-consume/start`)

**修改前**:
```sql
-- 错误的SQL语法(SQLite格式) + 错误的表
INSERT INTO suppression_tasks (task_id, task_type, target, parameters, status, start_time)
VALUES (?, ?, ?, ?, ?, ?)
```

**修改后**:
```sql
-- 正确的MySQL语法 + 正确的表
INSERT INTO compute_consume_task 
(task_id, target_url, rate, concurrency, duration, status, start_time)
VALUES (%s, %s, %s, %s, %s, 'running', NOW())
```

---

### 4. 任务列表查询 (`/api/suppression/tasks`)

**新增查询**:

```sql
-- 查询TCP RST攻击任务
SELECT task_id, attack_id, target_ip as ip, target_port as port, 
       capture_interface, inject_interface,
       status, DATE_FORMAT(start_time, '%Y-%m-%d %H:%i:%s') as start_time,
       DATE_FORMAT(stop_time, '%Y-%m-%d %H:%i:%s') as stop_time,
       'tcp-syn-flood' as task_type
FROM tcp_rst_task
ORDER BY start_time DESC
LIMIT 100

-- 查询计算资源消耗任务
SELECT task_id, target_url as url, rate, concurrency, duration,
       status, DATE_FORMAT(start_time, '%Y-%m-%d %H:%i:%s') as start_time,
       DATE_FORMAT(stop_time, '%Y-%m-%d %H:%i:%s') as stop_time,
       'compute-consume' as task_type
FROM compute_consume_task
ORDER BY start_time DESC
LIMIT 100
```

**返回数据格式**:
```json
{
  "status": "success",
  "data": [
    {
      "task_id": "tcp-rst_192.168.1.10_80_1747022800",
      "attack_id": "tcp-syn-1747022800",
      "ip": "192.168.1.10",
      "port": 80,
      "capture_interface": "eth0",
      "inject_interface": "eth1",
      "status": "running",
      "start_time": "2024-01-10 14:30:00",
      "stop_time": null,
      "task_type": "tcp-syn-flood"
    },
    {
      "task_id": "compute-consume_example.com_1747022900",
      "url": "https://example.com",
      "rate": 50,
      "concurrency": 100,
      "duration": 60,
      "status": "stopped",
      "start_time": "2024-01-10 14:32:00",
      "stop_time": "2024-01-10 14:33:00",
      "task_type": "compute-consume"
    }
  ]
}
```

---

### 5. 停止任务 (`/api/suppression/task/{task_id}/stop`)

**新增支持**:
- 现在可以停止TCP RST攻击任务
- 现在可以停止计算资源消耗任务

**处理逻辑**:
```python
# 1. 尝试更新端口资源消耗任务
UPDATE port_consume_task ...

# 2. 尝试更新SYN洪水攻击任务
UPDATE syn_flood_task ...

# 3. 尝试更新TCP RST攻击任务 (新增)
UPDATE tcp_rst_task ...

# 4. 尝试更新计算资源消耗任务 (新增)
UPDATE compute_consume_task ...
```

---

### 6. 任务状态更新回调 (`update_task_status_callback`)

**新增处理**:
```python
elif task_id.startswith('tcp-rst'):
    if status in ["已完成", "已停止", "错误"]:
        UPDATE tcp_rst_task SET status = 'stopped', stop_time = NOW()

elif task_id.startswith('compute-consume'):
    if status in ["已完成", "已停止", "错误"]:
        UPDATE compute_consume_task SET status = 'stopped', stop_time = NOW()
```

---

## ? 前端展示

前端 `SuppressionStrategy.js` 中已经有任务列表展示逻辑，现在会自动显示：

### TCP RST攻击任务列表

```
运行中的任务
┌──────────────────────────────────────────────────────────────┐
│ 任务ID       │ 目标        │ 状态   │ 启动时间        │ 操作 │
├──────────────────────────────────────────────────────────────┤
│ tcp-rst_...  │ 192.168.1.10:80 │ 运行中 │ 2024-01-10 14:30│ [停止]│
│ tcp-rst_...  │ 192.168.1.20:443│ 已停止 │ 2024-01-10 14:28│  -    │
└──────────────────────────────────────────────────────────────┘
```

### 计算资源消耗任务列表

```
运行中的任务
┌────────────────────────────────────────────────────────────────────┐
│ 任务ID            │ 目标URL          │ 状态   │ 启动时间        │ 操作 │
├────────────────────────────────────────────────────────────────────┤
│ compute-consume_..│ https://example..│ 运行中 │ 2024-01-10 14:32│ [停止]│
│ compute-consume_..│ https://test.com │ 已停止 │ 2024-01-10 14:30│  -    │
└────────────────────────────────────────────────────────────────────┘
```

---

## ? 功能对比

| 策略 | 启动前 | 启动后 |
|------|--------|--------|
| **端口资源消耗** | ? 保存到数据库<br>? 任务列表显示<br>? 可停止 | 无变化 |
| **SYN洪水攻击** | ? 保存到数据库<br>? 任务列表显示<br>? 可停止 | 无变化 |
| **TCP RST攻击** | ? 不保存到数据库<br>? 任务列表不显示<br>?? 只能通过attack_id停止 | ? 保存到数据库<br>? 任务列表显示<br>? 可通过task_id或attack_id停止 |
| **计算资源消耗** | ?? 保存到错误的表<br>?? 使用SQLite语法<br>?? 任务列表不显示 | ? 保存到正确的表<br>? 使用MySQL语法<br>? 任务列表显示 |

---

## ? 使用示例

### 1. 启动TCP RST攻击

```bash
curl -X POST http://localhost:8000/api/suppression/relay-file/attack/start \
  -H "Content-Type: application/json" \
  -d '{
    "target_ip": "192.168.1.10",
    "target_port": 80,
    "capture_interface": "eth0",
    "inject_interface": "eth1"
  }'

# 响应
{
  "status": "success",
  "message": "攻击命令已下发",
  "attack_id": "tcp-syn-1747022800",
  "task_id": "tcp-rst_192.168.1.10_80_1747022800"
}
```

### 2. 查看任务列表

```bash
curl http://localhost:8000/api/suppression/tasks

# 响应包含TCP RST和计算资源消耗任务
{
  "status": "success",
  "data": [
    {
      "task_id": "tcp-rst_192.168.1.10_80_1747022800",
      "attack_id": "tcp-syn-1747022800",
      "ip": "192.168.1.10",
      "port": 80,
      "status": "running",
      "task_type": "tcp-syn-flood"
    },
    {
      "task_id": "compute-consume_example.com_1747022900",
      "url": "https://example.com",
      "status": "running",
      "task_type": "compute-consume"
    }
  ]
}
```

### 3. 停止任务

```bash
# 方式1: 通过task_id停止
curl -X POST http://localhost:8000/api/suppression/task/tcp-rst_192.168.1.10_80_1747022800/stop

# 方式2: 通过attack_id停止（仅TCP RST）
curl -X POST http://localhost:8000/api/suppression/relay-file/attack/stop?attack_id=tcp-syn-1747022800
```

---

## ? 总结

### 关键改进

1. **统一的任务管理**: 所有策略现在都有一致的任务管理方式
2. **数据库持久化**: TCP RST和计算资源消耗任务现在会保存到数据库
3. **界面一致性**: 所有任务都在"运行中的任务"列表中显示
4. **状态追踪**: 可以查看任务的运行状态（运行中/已停止）和时间信息
5. **修复Bug**: 修正了计算资源消耗使用错误SQL语法的问题

### 数据库表总结

| 表名 | 对应策略 | 状态 |
|------|---------|------|
| `port_consume_task` | 端口资源消耗 | ? 已存在 |
| `syn_flood_task` | SYN洪水攻击 | ? 已存在 |
| `tcp_rst_task` | TCP RST攻击 | ? 新增 |
| `compute_consume_task` | 计算资源消耗 | ? 新增 |

---

## ? 注意事项

1. **首次启动**: 数据库表会自动创建，无需手动建表
2. **旧数据**: 之前的TCP RST和计算资源消耗任务不会在列表中显示（因为没保存到数据库）
3. **task_id格式**: 
   - TCP RST: `tcp-rst_{IP}_{PORT}_{timestamp}`
   - 计算资源消耗: `compute-consume_{domain}_{timestamp}`
4. **停止方式**: TCP RST可以通过task_id或attack_id两种方式停止

祝使用愉快！?
