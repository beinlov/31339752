# 快速开始指南

5分钟部署中继节点

---

## ⚡ 超快部署（3步）

### 步骤1: 安装依赖

```bash
cd relay_node
pip3 install -r requirements.txt
```

### 步骤2: 配置

```bash
# 编辑配置文件
vim relay_node_config.json

# 必须修改的配置：
# 1. puller.c2_servers[0].url -> C2服务器地址
# 2. puller.c2_servers[0].api_key -> C2 API密钥
# 3. server.api_key -> 中继节点API密钥（供平台访问）
```

### 步骤3: 启动

```bash
chmod +x start_relay_node.sh
./start_relay_node.sh
```

✅ **完成！** 服务已运行在 http://0.0.0.0:8888

---

## 🧪 验证部署

```bash
# 健康检查
curl -H "X-API-Key: your_api_key" http://localhost:8888/health

# 应该看到：
# {
#   "status": "healthy",
#   "storage": {...},
#   "c2_servers": {"c2-1": true}
# }
```

---

## ⚙️ 配置平台

修改平台的配置文件：

```python
# backend/config.py

C2_ENDPOINTS = [
    {
        'id': 'relay-node-1',
        'url': 'http://中继节点IP:8888',
        'api_key': 'your_relay_node_api_key',
        'botnet_type': 'utg_q_008',
        'enabled': True
    }
]
```

重启平台：

```bash
cd /path/to/backend
pkill -f "python3 main.py"
python3 main.py
```

---

## 📊 监控

```bash
# 查看日志
tail -f relay_node.log

# 查看统计
curl -H "X-API-Key: xxx" http://localhost:8888/api/stats

# 查看数据库
sqlite3 relay_node_cache.db "SELECT status, COUNT(*) FROM data_records GROUP BY status;"
```

---

## 🔧 常见配置

### 修改端口

```json
{
  "server": {
    "port": 9999
  }
}
```

### 修改拉取间隔

```json
{
  "intervals": {
    "pull": 5
  }
}
```

### 添加多个C2

```json
{
  "puller": {
    "c2_servers": [
      {
        "id": "c2-1",
        "url": "http://C2_IP1:8888",
        "api_key": "xxx"
      },
      {
        "id": "c2-2",
        "url": "http://C2_IP2:8888",
        "api_key": "yyy"
      }
    ]
  }
}
```

---

## 🚀 生产部署建议

### 1. 使用systemd服务

创建 `/etc/systemd/system/relay-node.service`：

```ini
[Unit]
Description=Relay Node Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/relay_node
ExecStart=/usr/bin/python3 /path/to/relay_node/relay_data_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable relay-node
sudo systemctl start relay-node
sudo systemctl status relay-node
```

### 2. 启用HTTPS

```bash
# 生成证书
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# 修改配置
vim relay_node_config.json
# 设置 "use_https": true

# 重启服务
```

详见 [HTTPS_UPGRADE_GUIDE.md](HTTPS_UPGRADE_GUIDE.md)

### 3. 配置防火墙

```bash
sudo ufw allow 8888/tcp
sudo ufw enable
```

---

## 🐛 故障排查

### 问题：C2连接失败

```bash
# 检查网络
ping C2_IP
curl http://C2_IP:8888/health

# 检查配置
cat relay_node_config.json | grep url
```

### 问题：平台拉不到数据

```bash
# 检查中继节点
curl -H "X-API-Key: xxx" http://中继节点IP:8888/api/stats

# 检查平台配置
# backend/config.py 中的 C2_ENDPOINTS
```

### 问题：数据积压

```bash
# 查看pending数量
sqlite3 relay_node_cache.db "SELECT COUNT(*) FROM data_records WHERE status='pending';"

# 检查平台是否在拉取
tail -f relay_node.log | grep "平台拉取"
```

---

## 📞 获取帮助

1. 查看完整文档：[README.md](README.md)
2. HTTPS升级：[HTTPS_UPGRADE_GUIDE.md](HTTPS_UPGRADE_GUIDE.md)
3. 检查日志：`tail -f relay_node.log`

---

**🎉 开始使用吧！**
