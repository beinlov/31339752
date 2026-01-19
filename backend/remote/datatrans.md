# 数据传输逻辑文档（改进版）

## 概述

本文档描述了C2端到服务器端的数据拉取机制，采用**两阶段确认**和**SQLite持久化**，确保数据传输的可靠性和鲁棒性。

---

## 核心改进

### 🔒 两阶段确认机制

**问题**：原方案中 `confirm=true` 会立即删除C2端数据，如果服务器在保存前崩溃，数据永久丢失。

**改进方案**：

```bash
# 阶段1：拉取数据（不删除）
curl -H "X-API-Key: xxx" "http://c2:8888/api/pull?limit=1000&confirm=false"

# 阶段2：保存成功后确认删除
curl -X POST -H "X-API-Key: xxx" \
  -H "Content-Type: application/json" \
  -d '{"count": 1000}' \
  http://c2:8888/api/confirm
```

**优势**：
- ✅ 服务器崩溃不丢数据
- ✅ C2端数据持久化保存
- ✅ 可重复拉取未确认数据

---

### 💾 SQLite持久化缓存

**问题**：原方案使用JSON文件缓存，缓存满时直接丢弃旧数据。

**改进方案**：

```sql
-- 表结构
CREATE TABLE cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    data TEXT NOT NULL,
    pulled INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    pulled_at TEXT,
    UNIQUE(ip, timestamp)
);

-- 查询未拉取的数据
SELECT * FROM cache WHERE pulled=0 ORDER BY created_at LIMIT 1000;

-- 确认后标记为已拉取
UPDATE cache SET pulled=1, pulled_at=CURRENT_TIMESTAMP WHERE id IN (...);

-- 定期清理已拉取的旧数据（保留7天）
DELETE FROM cache WHERE pulled=1 AND pulled_at < datetime('now', '-7 days');
```

**优势**：
- ✅ C2端重启数据不丢失
- ✅ 防止内存溢出
- ✅ 支持数据去重（UNIQUE约束）
- ✅ 已拉取数据保留7天防止重复

---

### 🔄 断点续传

**问题**：原方案无法记录拉取进度，服务器重启后可能重复拉取。

**改进方案**：

```python
# 服务器端记录最后处理时间戳
last_timestamp = load_from_state_file()  # 例如：2026-01-08T12:00:00

# 拉取时传递since参数
response = requests.get(
    "http://c2:8888/api/pull",
    params={
        "limit": 1000,
        "since": last_timestamp,  # 只拉取此时间后的数据
        "confirm": "false"
    }
)

# 保存成功后更新时间戳
save_to_state_file(max_timestamp_from_records)
```

**优势**：
- ✅ 避免重复拉取
- ✅ 服务器重启无影响
- ✅ 按时间顺序处理

---

### 📊 数据去重

**实现方式**：

```python
# 数据库层去重
CREATE UNIQUE INDEX idx_ip_timestamp ON cache(ip, timestamp);

# 插入时自动去重
try:
    INSERT INTO cache (ip, timestamp, data) VALUES (?, ?, ?);
except sqlite3.IntegrityError:
    pass  # 重复记录，跳过
```

---

## 快速部署

### 1️⃣ C2端（提供HTTP接口）

```bash
# 在C2服务器上执行

cd backend/remote

# 生成API Key
export C2_API_KEY="sk-$(openssl rand -hex 16)"
echo "保存此API Key: $C2_API_KEY"

# 安装依赖
pip3 install aiohttp aiofiles

# 启动HTTP服务
python3 c2_data_server.py

# 会看到：
# SQLite数据库初始化成功: /tmp/c2_data_cache.db
# HTTP服务: http://0.0.0.0:8888
```

**如果C2没有公网IP，使用ngrok**：
```bash
# 另开一个终端
ngrok http 8888

# 会得到公网地址，例如：
# Forwarding  https://abc123.ngrok.io -> http://localhost:8888
```

---

### 2️⃣ 服务器端（拉取数据）

**注意：服务器端拉取逻辑已集成到主程序中，无需单独启动。**

```bash
# 在校园网服务器上执行

cd backend

# 配置C2端点（在config.py中）
# 编辑 config.py 中的 C2_ENDPOINTS 配置

# 或使用环境变量（临时测试）
export C2_ENDPOINT_1="http://C2的IP:8888"  # 或 https://abc123.ngrok.io
export C2_API_KEY_1="步骤1生成的API_KEY"

# 启动日志处理器（包含远程拉取功能）
python3 log_processor/main.py

# 会看到：
# 初始化远程拉取器，配置了 1 个 C2端点
# [C2-1] ✓ 拉取成功: 1234 条
# [C2-1] [ramnit] 处理成功: 1234 条
# [C2-1] ✓ 已确认删除: 1234 条
```

---

### 3️⃣ 验证数据流

```bash
# 在服务器上测试C2接口
curl -H "X-API-Key: 你的API_KEY" http://C2的IP:8888/api/stats

# 应该返回：
{
  "cached_records": 1234,      # 未拉取记录数
  "pulled_records": 5000,      # 已拉取记录数
  "total_generated": 10000,    # 总生成记录数
  "total_pulled": 8766         # 累计拉取数
}

# 健康检查
curl http://C2的IP:8888/health
# 返回：{"status": "ok", "service": "c2-data-server"}
```

---

## API接口说明

### GET /api/pull

拉取数据（阶段1）

**请求参数**：
- `limit`：最大拉取数量（默认1000，最大5000）
- `since`：只拉取此时间之后的数据（ISO格式，可选）
- `confirm`：是否自动确认删除（默认false，**不建议使用true**）

**请求示例**：
```bash
curl -H "X-API-Key: xxx" \
  "http://c2:8888/api/pull?limit=1000&since=2026-01-08T12:00:00&confirm=false"
```

**响应**：
```json
{
  "success": true,
  "count": 1000,
  "data": [
    {
      "ip": "1.2.3.4",
      "timestamp": "2026-01-08T12:30:00",
      "botnet_type": "ramnit",
      "date": "2026-01-08",
      "_cache_id": 12345
    }
  ],
  "stats": {
    "cached_records": 9000,
    "total_generated": 50000,
    "total_pulled": 41000
  }
}
```

---

### POST /api/confirm

确认拉取（阶段2）

**请求体**：
```json
{
  "count": 1000
}
```

**请求示例**：
```bash
curl -X POST -H "X-API-Key: xxx" \
  -H "Content-Type: application/json" \
  -d '{"count": 1000}' \
  http://c2:8888/api/confirm
```

**响应**：
```json
{
  "success": true,
  "message": "已确认 1000 条"
}
```

---

### GET /api/stats

获取统计信息

**请求示例**：
```bash
curl -H "X-API-Key: xxx" http://c2:8888/api/stats
```

**响应**：
```json
{
  "cached_records": 1234,
  "pulled_records": 5000,
  "total_generated": 10000,
  "total_pulled": 8766,
  "cache_full": false
}
```

---

### GET /health

健康检查（无需认证）

**响应**：
```json
{
  "status": "ok",
  "service": "c2-data-server"
}
```

---

## 配置文件说明

### C2端：config.json

```json
{
  "botnet": {
    "botnet_type": "ramnit",
    "log_dir": "/home/ubuntu/logs",
    "log_file_pattern": "ramnit_{datetime}.log"
  },
  "cache": {
    "db_file": "/tmp/c2_data_cache.db",
    "max_cached_records": 10000,
    "retention_days": 7,
    "two_phase_commit": true
  },
  "http_server": {
    "host": "0.0.0.0",
    "port": 8888,
    "api_key": "your-secret-api-key-here"
  }
}
```

**建议**：
- `api_key` 使用环境变量 `C2_API_KEY` 代替
- 生产环境：`openssl rand -hex 32`

---

### 服务器端：config.py

```python
C2_ENDPOINTS = [
    {
        'name': 'C2-Ramnit-1',
        'url': 'http://123.45.67.89:8888',
        'api_key': os.environ.get('C2_API_KEY_1', 'your-key'),
        'enabled': True,
        'pull_interval': 60,
        'batch_size': 1000,
        'timeout': 30,
    },
]
```

---

## 生产部署（systemd）

### C2端服务

```bash
sudo tee /etc/systemd/system/c2-data-server.service << 'EOF'
[Unit]
Description=C2 Data Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/backend/remote
Environment="C2_API_KEY=your-secret-key-here"
Environment="C2_HTTP_PORT=8888"
ExecStart=/usr/bin/python3 c2_data_server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable c2-data-server
sudo systemctl start c2-data-server
```

---

### 服务器端服务

```bash
sudo tee /etc/systemd/system/botnet-log-processor.service << 'EOF'
[Unit]
Description=Botnet Log Processor with Remote Pulling
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/backend
Environment="C2_ENDPOINT_1=http://c2-ip:8888"
Environment="C2_API_KEY_1=your-secret-key"
ExecStart=/usr/bin/python3 log_processor/main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable botnet-log-processor
sudo systemctl start botnet-log-processor
```

---

## 常见问题

### Q1: C2端无公网IP怎么办？

**使用内网穿透**：

**选项1：ngrok（最简单）**
```bash
ngrok http 8888
# 免费版每次重启会换域名
```

**选项2：frp（自建，域名固定）**
```bash
# 需要一台有公网IP的中转服务器
# 配置frpc.ini
[c2-http]
type = tcp
local_ip = 127.0.0.1
local_port = 8888
remote_port = 6000
```

**选项3：Cloudflare Tunnel（免费，域名固定）**
```bash
cloudflared tunnel --url http://localhost:8888
```

---

### Q2: 如何保证安全？

1. **使用HTTPS**（ngrok自动提供）
2. **强API Key**：`openssl rand -hex 32`
3. **防火墙**：只允许服务器IP访问
4. **定期轮换**：每月更换API Key

---

### Q3: 数据会丢失吗？

**采用两阶段确认机制，最大程度保证数据不丢失**：
- ✅ C2端使用SQLite持久化缓存
- ✅ 服务器先拉取数据（不删除），保存成功后再确认删除
- ✅ 支持断点续传，记录最后处理时间戳
- ✅ 服务器拉取失败会自动重试，C2端数据保持不变
- ✅ 即使C2端重启，SQLite中的数据也不会丢失

---

### Q4: 性能如何？

| 指标 | 数值 |
|------|------|
| 拉取延迟 | 60秒（可调） |
| 单次拉取量 | 1000条（可调） |
| C2端内存 | <50MB（SQLite持久化） |
| 网络带宽 | <1Mbps（普通场景） |
| 并发支持 | 支持多C2并行拉取 |

---

### Q5: 如何监控？

```bash
# 查看C2端日志
sudo journalctl -u c2-data-server -f

# 查看服务器端日志
sudo journalctl -u botnet-log-processor -f

# 查看C2端缓存大小
curl -H "X-API-Key: xxx" http://c2-ip:8888/api/stats

# 检查数据库大小
ls -lh /tmp/c2_data_cache.db
```

---

## 故障排查

### 问题：服务器拉取失败

```bash
# 1. 测试C2端是否可访问
curl http://c2-ip:8888/health
# 应该返回：{"status": "ok"}

# 2. 测试认证
curl -H "X-API-Key: 错误的key" http://c2-ip:8888/api/stats
# 应该返回401

curl -H "X-API-Key: 正确的key" http://c2-ip:8888/api/stats
# 应该返回200

# 3. 检查防火墙
telnet c2-ip 8888
```

---

### 问题：C2端数据不增长

```bash
# 检查日志文件
ls -lh /path/to/logs/

# 检查后台读取任务日志
sudo journalctl -u c2-data-server | grep "读取日志"

# 检查SQLite数据库
sqlite3 /tmp/c2_data_cache.db "SELECT COUNT(*) FROM cache WHERE pulled=0;"

# 重启服务
sudo systemctl restart c2-data-server
```

---

### 问题：数据库文件过大

```bash
# 检查数据库大小
ls -lh /tmp/c2_data_cache.db

# 手动清理已拉取的旧数据
sqlite3 /tmp/c2_data_cache.db "DELETE FROM cache WHERE pulled=1 AND pulled_at < datetime('now', '-1 days');"

# 优化数据库
sqlite3 /tmp/c2_data_cache.db "VACUUM;"
```

---

## 与原代码对比

### 需要停用的脚本

❌ `remote_uploader.py`（原推送模式，如果存在）

### 需要启动的脚本

✅ `c2_data_server.py`（C2端HTTP服务）  
✅ `log_processor/main.py`（服务器端，包含拉取功能）

### 可复用的代码

✅ `LogReader`、`IPProcessor`等日志处理逻辑全部复用

---

## 架构对比

| 维度 | 原架构（推送） | 新架构（拉取+两阶段确认） |
|------|--------------|----------------------|
| 服务器网络要求 | ❌ 需要公网IP | ✅ 无需公网IP |
| C2端网络要求 | ✅ 无需公网IP | ⚠️ 需要公网访问 |
| 数据可靠性 | ⚠️ 可能丢失 | ✅ 两阶段确认 |
| 持久化 | ❌ JSON文件 | ✅ SQLite数据库 |
| 断点续传 | ❌ 不支持 | ✅ 支持 |
| C2端重启影响 | ❌ 数据丢失 | ✅ 数据保留 |
| 数据去重 | ⚠️ 依赖应用层 | ✅ 数据库层去重 |

---

## 总结

**改进后的优势**：
1. ✅ 两阶段确认，数据不丢失
2. ✅ SQLite持久化，重启无影响
3. ✅ 断点续传，避免重复
4. ✅ 数据库层去重，性能更好
5. ✅ 清晰的API设计，易于维护

**部署完成！数据应该在60秒内开始流动。**
