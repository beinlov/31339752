# 拉取模式快速启动指南

## 场景
- ✅ C2端在公网或有公网访问方式（公网IP / ngrok / frp）
- ❌ 服务器在校园网内，无公网IP

---

## 快速启动（5分钟）

### 1️⃣ C2端（提供HTTP接口）

```bash
# 在C2服务器上执行

cd backend/remote

# 生成API Key
export C2_API_KEY="sk-$(openssl rand -hex 16)"
echo "保存此API Key: $C2_API_KEY"

# 启动HTTP服务
pip3 install aiohttp aiofiles
python3 c2_data_server.py

# 会看到：
# HTTP服务: http://0.0.0.0:8888
```

**如果C2没有公网IP，使用ngrok**：
```bash
# 另开一个终端
ngrok http 8888

# 会得到公网地址，例如：
# Forwarding  https://abc123.ngrok.io -> http://localhost:8888
```

### 2️⃣ 服务器端（拉取数据）

```bash
# 在校园网服务器上执行

cd backend/remote

# 配置C2端点（使用步骤1的API Key）
export C2_ENDPOINT_1="http://C2的IP:8888"  # 或 https://abc123.ngrok.io
export C2_API_KEY_1="步骤1生成的API_KEY"
export PULL_INTERVAL=60  # 拉取间隔60秒

# 安装依赖
pip3 install aiohttp

# 启动拉取服务
python3 server_data_puller.py

# 会看到：
# [C2-1] ✓ 拉取成功: 1234 条
# ✓ 保存成功: 1234 条
```

### 3️⃣ 验证数据流

```bash
# 在服务器上测试C2接口
curl -H "X-API-Key: 你的API_KEY" http://C2的IP:8888/api/stats

# 应该返回：
{
  "success": true,
  "stats": {
    "cached_records": 1234,
    "total_generated": 5678,
    "total_pulled": 4444
  }
}
```

---

## 生产部署（使用systemd）

### C2端服务

```bash
# 创建服务文件
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

### 服务器端拉取服务

```bash
sudo tee /etc/systemd/system/server-data-puller.service << 'EOF'
[Unit]
Description=Server Data Puller
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/backend/remote
Environment="C2_ENDPOINT_1=http://c2-ip:8888"
Environment="C2_API_KEY_1=your-secret-key"
Environment="PULL_INTERVAL=60"
ExecStart=/usr/bin/python3 server_data_puller.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable server-data-puller
sudo systemctl start server-data-puller
```

---

## 常见问题

### Q1: C2端无公网IP怎么办？

**使用内网穿透**：

选项1：ngrok（最简单）
```bash
ngrok http 8888
# 免费版每次重启会换域名
```

选项2：frp（自建，域名固定）
```bash
# 需要一台有公网IP的中转服务器
# 配置frpc.ini
[c2-http]
type = tcp
local_ip = 127.0.0.1
local_port = 8888
remote_port = 6000
```

选项3：Cloudflare Tunnel（免费，域名固定）
```bash
cloudflared tunnel --url http://localhost:8888
```

### Q2: 如何保证安全？

1. **使用HTTPS**（ngrok自动提供）
2. **强API Key**：`openssl rand -hex 32`
3. **防火墙**：只允许服务器IP访问
4. **定期轮换**：每月更换API Key

### Q3: 数据会丢失吗？

**不会**：
- C2端缓存数据到磁盘（`/tmp/c2_data_cache.json`）
- 服务器拉取失败会自动重试
- C2端只在确认拉取后才删除数据

### Q4: 性能如何？

| 指标 | 数值 |
|------|------|
| 拉取延迟 | 60秒（可调） |
| 单次拉取量 | 1000条（可调） |
| C2端内存 | <100MB（1万条缓存） |
| 网络带宽 | <1Mbps（普通场景） |

### Q5: 如何监控？

```bash
# 查看C2端日志
sudo journalctl -u c2-data-server -f

# 查看服务器端日志
sudo journalctl -u server-data-puller -f

# 查看C2端缓存大小
curl -H "X-API-Key: xxx" http://c2-ip:8888/api/stats
```

---

## 与原代码对比

### 需要停用的脚本

❌ `remote_uploader.py`（原推送模式）

### 需要启动的脚本

✅ `c2_data_server.py`（C2端HTTP服务）  
✅ `server_data_puller.py`（服务器端拉取）

### 可复用的代码

✅ `LogReader`、`IPProcessor`等日志处理逻辑全部复用

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

### 问题：C2端数据不增长

```bash
# 检查日志文件
ls -lh /path/to/logs/

# 检查后台读取任务日志
sudo journalctl -u c2-data-server | grep "读取日志"

# 重启服务
sudo systemctl restart c2-data-server
```

---

## 迁移步骤（从推送模式迁移）

```bash
# 1. 停止原推送脚本
pkill -f remote_uploader.py

# 2. 部署C2端HTTP服务
# （按上述步骤1）

# 3. 部署服务器端拉取服务
# （按上述步骤2）

# 4. 验证数据流
# （按上述步骤3）

# 5. 删除原脚本的定时任务（如有）
crontab -e
# 删除 remote_uploader.py 相关的定时任务
```

---

**部署完成！数据应该在60秒内开始流动。**
