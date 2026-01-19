# 拉取模式部署指南

**场景**: 服务器在校园网内，无公网IP，无法接收C2端的主动推送。

**解决方案**: 反转数据流方向，由服务器主动从C2端拉取数据。

---

## 架构对比

### 原架构（推送模式）
```
C2端（有公网IP）  ----HTTP POST---->  服务器（有公网IP）
   读日志                                接收数据
   处理IP                                存数据库
   主动上传
```

### 新架构（拉取模式）
```
C2端（有公网IP）  <----HTTP GET-----  服务器（校园网内，无公网IP）
   读日志                                定期拉取
   缓存数据                              存数据库
   提供HTTP接口
```

---

## 部署步骤

### 1. C2端部署（提供HTTP服务）

#### 1.1 确保C2端有公网访问方式

选项A：C2端有公网IP
```bash
# 直接使用公网IP
C2_ENDPOINT=http://123.45.67.89:8888
```

选项B：C2端无公网IP，使用ngrok/frp等内网穿透
```bash
# 使用ngrok
ngrok http 8888

# 会得到一个公网地址，例如：
# https://abc123.ngrok.io
```

选项C：C2端无公网IP，使用域名 + DDNS
```bash
# 配置DDNS，例如使用花生壳
# 得到域名：c2-server.example.com
```

#### 1.2 启动C2端HTTP服务

```bash
cd backend/remote

# 设置环境变量
export C2_API_KEY="your-very-secret-api-key-$(date +%s)"
export C2_HTTP_HOST="0.0.0.0"  # 监听所有接口
export C2_HTTP_PORT="8888"

# 安装依赖
pip3 install aiohttp aiofiles

# 启动服务
python3 c2_data_server.py
```

#### 1.3 使用systemd守护进程（推荐）

创建 `/etc/systemd/system/c2-data-server.service`:

```ini
[Unit]
Description=C2 Data Server (HTTP Pull Mode)
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/backend/remote
Environment="C2_API_KEY=your-very-secret-api-key"
Environment="C2_HTTP_HOST=0.0.0.0"
Environment="C2_HTTP_PORT=8888"
ExecStart=/usr/bin/python3 c2_data_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable c2-data-server
sudo systemctl start c2-data-server
sudo systemctl status c2-data-server
```

#### 1.4 测试C2端接口

```bash
# 健康检查（无需认证）
curl http://localhost:8888/health

# 获取统计信息
curl -H "X-API-Key: your-api-key" http://localhost:8888/api/stats

# 拉取数据（不确认）
curl -H "X-API-Key: your-api-key" "http://localhost:8888/api/pull?limit=10&confirm=false"

# 拉取数据（确认删除）
curl -H "X-API-Key: your-api-key" "http://localhost:8888/api/pull?limit=10&confirm=true"
```

---

### 2. 服务器端部署（拉取数据）

#### 2.1 配置C2端点列表

编辑 `server_data_puller.py` 或使用环境变量：

```bash
# 方式1：环境变量
export C2_ENDPOINT_1="http://c2-server-1.example.com:8888"
export C2_API_KEY_1="your-very-secret-api-key"

export C2_ENDPOINT_2="http://c2-server-2.example.com:8888"
export C2_API_KEY_2="another-api-key"

# 方式2：配置文件（推荐）
# 创建 puller_config.json
```

`puller_config.json`:
```json
{
  "c2_endpoints": [
    {
      "name": "C2-Ramnit-1",
      "url": "http://123.45.67.89:8888",
      "api_key": "secret-key-1"
    },
    {
      "name": "C2-Zeus-1",
      "url": "https://abc123.ngrok.io",
      "api_key": "secret-key-2"
    }
  ],
  "pull_interval": 60,
  "pull_batch_size": 1000
}
```

#### 2.2 启动拉取服务

```bash
cd backend/remote

# 安装依赖
pip3 install aiohttp

# 测试运行
python3 server_data_puller.py

# 或使用systemd守护进程
```

创建 `/etc/systemd/system/server-data-puller.service`:

```ini
[Unit]
Description=Server Data Puller (Pull from C2)
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/backend/remote
Environment="C2_ENDPOINT_1=http://c2-server.example.com:8888"
Environment="C2_API_KEY_1=your-secret-key"
Environment="PULL_INTERVAL=60"
ExecStart=/usr/bin/python3 server_data_puller.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 安全建议

### 1. API Key管理

❌ **不要**：
```python
API_KEY = "hardcoded-key-123"  # 永远不要硬编码
```

✅ **推荐**：
```bash
# 使用环境变量
export C2_API_KEY=$(openssl rand -hex 32)

# 或使用密钥管理工具
# - AWS Secrets Manager
# - HashiCorp Vault
# - 配置文件 + chmod 600
```

### 2. HTTPS加密

如果C2端暴露在公网，**强烈建议使用HTTPS**：

选项A：使用Nginx反向代理 + Let's Encrypt
```nginx
server {
    listen 443 ssl;
    server_name c2-server.example.com;
    
    ssl_certificate /etc/letsencrypt/live/c2-server.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/c2-server.example.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8888;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

选项B：使用ngrok（自动HTTPS）
```bash
ngrok http 8888
# 会得到 https://abc123.ngrok.io
```

### 3. 防火墙规则

C2端：
```bash
# 只允许服务器IP访问8888端口
sudo ufw allow from 服务器IP to any port 8888
sudo ufw deny 8888
```

服务器端：
```bash
# 允许出站到C2端
# （通常校园网不限制出站，无需配置）
```

### 4. 访问日志

监控异常访问：
```bash
# C2端
tail -f /tmp/c2_data_server.log | grep "401\|403\|500"

# 服务器端
tail -f /tmp/server_puller.log | grep "ERROR"
```

---

## 性能优化

### 1. 调整拉取间隔

根据数据量调整：
```python
# 数据量大（每小时>1万条）
PULL_INTERVAL = 30  # 30秒拉取一次

# 数据量小（每小时<1000条）
PULL_INTERVAL = 300  # 5分钟拉取一次
```

### 2. 批量大小

```python
# 高频小批量
PULL_BATCH_SIZE = 500

# 低频大批量
PULL_BATCH_SIZE = 5000
```

### 3. C2端缓存大小

```python
# C2端缓存限制
MAX_CACHED_RECORDS = 10000  # 防止内存溢出

# 如果服务器长时间离线，C2端会丢弃最旧的数据
# 解决方案：增加缓存或使用持久化队列（SQLite）
```

---

## 监控与告警

### 1. 健康检查

服务器端定期检查C2端健康：
```bash
# crontab
*/5 * * * * curl -s http://c2-server:8888/health || echo "C2 down" | mail -s "Alert" admin@example.com
```

### 2. 数据延迟监控

```python
# 在服务器端检查数据时间戳
latest_timestamp = max(record['timestamp'] for record in records)
delay = datetime.now() - datetime.fromisoformat(latest_timestamp)

if delay > timedelta(hours=1):
    logger.warning(f"数据延迟: {delay}")
```

### 3. Prometheus监控（可选）

```python
# 在C2端暴露metrics接口
@app.get('/metrics')
async def metrics():
    return f"""
# HELP c2_cached_records Number of cached records
# TYPE c2_cached_records gauge
c2_cached_records {len(data_cache.records)}

# HELP c2_total_generated Total generated records
# TYPE c2_total_generated counter
c2_total_generated {data_cache.total_generated}
"""
```

---

## 故障排查

### 问题1：服务器拉取失败

```bash
# 检查C2端是否可访问
curl -v http://c2-server:8888/health

# 检查认证
curl -H "X-API-Key: wrong-key" http://c2-server:8888/api/stats
# 应该返回401

# 检查防火墙
telnet c2-server 8888
```

### 问题2：C2端数据不更新

```bash
# 检查日志文件是否有新数据
ls -lh /path/to/logs/

# 检查后台读取任务
# 在C2端日志中查找 "读取日志文件"
tail -f /tmp/c2_data_server.log | grep "读取日志"

# 手动触发读取
# 重启C2服务
sudo systemctl restart c2-data-server
```

### 问题3：内存占用过高

```bash
# C2端缓存过大
# 检查缓存大小
curl -H "X-API-Key: xxx" http://c2-server:8888/api/stats
# 查看 cached_records

# 解决方案1：降低MAX_CACHED_RECORDS
# 解决方案2：增加拉取频率
# 解决方案3：使用SQLite持久化
```

---

## 与原代码的差异

### 文件对比

| 原模式（推送） | 新模式（拉取） | 说明 |
|---------------|---------------|------|
| `remote_uploader.py` | `c2_data_server.py` | C2端：从主动上传改为提供HTTP接口 |
| 服务器端接收脚本 | `server_data_puller.py` | 服务器端：从被动接收改为主动拉取 |
| 需要公网IP | 不需要公网IP | 服务器可在内网运行 |

### 代码复用

✅ **可复用的代码**：
- `LogReader`：日志读取逻辑
- `IPProcessor`：IP提取和规范化
- 数据库保存逻辑

❌ **需要替换的代码**：
- `RemoteUploader`：不再需要（替换为HTTP接口）
- `AsyncLogProcessor`：主循环改为后台任务
- 配置中的`api_endpoint`：改为C2端的HTTP端口

---

## 混合模式（可选）

如果有些C2在公网，有些在内网，可以**同时运行两种模式**：

```bash
# 公网C2：推送模式
python3 remote_uploader.py  # 原有脚本

# 内网C2：拉取模式  
python3 c2_data_server.py  # 提供HTTP接口

# 服务器端：
# - 接收公网C2的推送
# - 主动拉取内网C2的数据
python3 server_data_puller.py  # 拉取内网C2
```

---

## 后续优化方向

1. **数据去重**：服务器端需要检查是否重复拉取
2. **断点续传**：记录上次拉取的时间戳，避免重复
3. **压缩传输**：大批量数据使用gzip压缩
4. **多线程拉取**：支持更多C2端点
5. **智能调度**：根据C2端负载动态调整拉取频率

---

## 总结

| 指标 | 推送模式 | 拉取模式 |
|------|----------|----------|
| 服务器网络要求 | ❌ 需要公网IP | ✅ 无需公网IP |
| C2端网络要求 | ✅ 无需公网IP | ⚠️ 需要公网访问 |
| 实时性 | ✅ 高（秒级） | ⚠️ 中（分钟级） |
| 服务器负载 | ✅ 低（被动） | ⚠️ 中（主动轮询） |
| 数据可靠性 | ⚠️ C2端负责重传 | ✅ 服务器主动重试 |
| 部署复杂度 | ✅ 简单 | ⚠️ 中等 |

**结论**：对于校园网环境（服务器无公网IP），**拉取模式是最优选择**。
