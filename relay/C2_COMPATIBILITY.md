# C2端兼容性说明

## 📋 概述

中转服务器的 `data_puller.py` **完全兼容** pull_mode 中C2端（`c2_data_server.py`）提供的API接口。

---

## ✅ API接口对比

### 1. 拉取接口 (GET /api/pull)

#### C2端提供的接口
```python
# URL: GET http://10.8.0.1:8888/api/pull
# 参数：
- limit: 最大拉取数量（默认1000，最大5000）
- since_seq: 只拉取此序列ID之后的数据（断点续传）
- since_ts: 只拉取此时间之后的数据（备用）
- confirm: 是否自动确认（默认false，推荐两阶段提交）

# 请求头：
- X-API-Key: API密钥

# 返回格式：
{
    "success": true,
    "count": 100,
    "data": [...],          // 主数据字段
    "records": [...],       // 兼容性字段（与data相同）
    "max_seq_id": 12345,   // 当前批次最大序列ID（用于断点续传）
    "stats": {...}         // 缓存统计信息
}
```

#### 中转服务器的实现
```python
# relay/data_puller.py - pull_from_server()

url = f"{server_url}/api/pull"
params = {
    'limit': self.batch_size,              # ✅ 支持limit
    'confirm': 'false',                    # ✅ 使用两阶段提交
    'since_seq': self.last_seq_ids[id]    # ✅ 支持断点续传
}
headers = {
    'X-API-Key': api_key                   # ✅ API密钥认证
}

response = requests.get(url, params=params, headers=headers)
data = response.json()

# 保存max_seq_id用于下次断点续传
if 'max_seq_id' in data:
    self.last_seq_ids[server_id] = data['max_seq_id']  # ✅ 断点续传
```

**兼容性**: ✅ 100% 兼容

---

### 2. 确认接口 (POST /api/confirm)

#### C2端提供的接口
```python
# URL: POST http://10.8.0.1:8888/api/confirm
# 请求头：
- X-API-Key: API密钥
- Content-Type: application/json

# 请求体：
{
    "count": 100  // 确认的记录数
}

# 返回格式：
{
    "success": true,
    "message": "已确认 100 条"
}
```

#### 中转服务器的实现
```python
# relay/data_puller.py - confirm_pull()

url = f"{server_url}/api/confirm"
headers = {
    'X-API-Key': api_key,                  # ✅ API密钥认证
    'Content-Type': 'application/json'     # ✅ JSON格式
}
data = {'count': count}                    # ✅ 确认数量

response = requests.post(url, json=data, headers=headers)
```

**兼容性**: ✅ 100% 兼容

---

### 3. 健康检查 (GET /health)

#### C2端提供的接口
```python
# URL: GET http://10.8.0.1:8888/health
# 返回：
{
    "status": "ok",
    "service": "c2-data-server"
}
```

#### 中转服务器的实现
```python
# relay/data_puller.py - health_check()

url = f"{server_url}/health"
headers = {'X-API-Key': api_key}
response = requests.get(url, headers=headers, timeout=5)
return response.status_code == 200
```

**兼容性**: ✅ 100% 兼容

---

## 🔄 工作流程对比

### C2端的数据流
```
日志文件/数据库
    ↓
后台读取器 (BackgroundReader)
    ↓
SQLite缓存 (DataCache)
    ↓
HTTP接口 (/api/pull)
    ↓
中转服务器拉取
```

### 中转服务器的数据流
```
C2端 (/api/pull)
    ↓
data_puller.pull_from_server()
    ↓
data_storage.save_pulled_data()
    ↓
SQLite缓存 (relay_cache.db)
    ↓
data_pusher.push_data()
    ↓
平台服务器 (/api/data-push)
```

---

## 📊 功能对比表

| 功能 | C2端支持 | 中转服务器支持 | 状态 |
|------|---------|--------------|------|
| **基础拉取** | ✅ | ✅ | ✅ |
| **API密钥认证** | ✅ | ✅ | ✅ |
| **批量拉取** | ✅ (limit参数) | ✅ | ✅ |
| **两阶段提交** | ✅ (confirm=false) | ✅ | ✅ |
| **断点续传** | ✅ (since_seq) | ✅ | ✅ |
| **时间戳过滤** | ✅ (since_ts) | ⚠️ 未使用 | 可选 |
| **健康检查** | ✅ | ✅ | ✅ |
| **统计信息** | ✅ (/api/stats) | ⚠️ 未使用 | 可选 |
| **背压控制** | ✅ | N/A | C2端功能 |

---

## 🆕 断点续传机制（已增强）

### C2端提供的断点续传
```python
# C2端：每条记录有唯一的seq_id
{
    "_seq_id": 12345,
    "ip": "1.2.3.4",
    "timestamp": "2025-01-01T12:00:00Z",
    ...
}

# 拉取时可以指定since_seq
GET /api/pull?since_seq=12345
# 只返回seq_id > 12345的记录
```

### 中转服务器的断点续传
```python
# data_puller.py 已支持
class DataPuller:
    def __init__(self):
        self.last_seq_ids = {}  # 记录每个C2的最大seq_id
    
    def pull_from_server(self, server_config):
        # 使用上次保存的seq_id
        if server_id in self.last_seq_ids:
            params['since_seq'] = self.last_seq_ids[server_id]
        
        # 保存本次的max_seq_id
        if 'max_seq_id' in data:
            self.last_seq_ids[server_id] = data['max_seq_id']
```

**优势**：
- ✅ 避免重复拉取数据
- ✅ 断电重启后可继续
- ✅ 减少网络传输
- ✅ 提高效率

---

## 🔐 认证机制对比

### C2端认证
```python
# c2_data_server.py
def check_auth(request: web.Request) -> bool:
    api_key = request.headers.get('X-API-Key', '')
    return api_key == API_KEY

# 默认密钥（可通过环境变量覆盖）
API_KEY = os.environ.get("C2_API_KEY", "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4")
```

### 中转服务器配置
```json
{
  "puller": {
    "c2_servers": [{
      "url": "http://10.8.0.1:8888",
      "api_key": "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"  // ← 必须与C2端一致
    }]
  }
}
```

**注意**: API密钥必须在C2端和中转服务器配置中保持一致！

---

## 📦 数据格式兼容性

### C2端返回的数据格式
```json
{
  "success": true,
  "count": 2,
  "data": [
    {
      "_seq_id": 1,
      "ip": "223.104.83.215",
      "timestamp": "2025-01-12T10:30:00Z",
      "log_type": "cleanup",
      "botnet_type": "ramnit",
      "event_type": "cleanup",
      "source": "cleanup"
    }
  ]
}
```

### 中转服务器处理
```python
# relay/data_storage.py - save_pulled_data()
for record in records:
    cursor.execute("""
        INSERT INTO data_records (
            botnet_type, ip, timestamp, event_type, 
            source, raw_data, pulled_at, c2_server, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (
        record.get('botnet_type', 'unknown'),  # ✅ 读取botnet_type
        record.get('ip', ''),                   # ✅ 读取ip
        record.get('timestamp', ''),            # ✅ 读取timestamp
        record.get('event_type', ''),           # ✅ 读取event_type
        record.get('source', ''),               # ✅ 读取source
        json.dumps(record),                     # ✅ 保存完整数据
        pulled_at,
        c2_server
    ))
```

**兼容性**: ✅ 完全兼容

---

## 🧪 测试建议

### 1. 连通性测试
```bash
# 在中转服务器上测试C2端连通性
curl -H "X-API-Key: KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4" \
     http://10.8.0.1:8888/health
```

### 2. 拉取测试
```bash
# 手动拉取测试
curl -H "X-API-Key: KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4" \
     "http://10.8.0.1:8888/api/pull?limit=10&confirm=false"
```

### 3. 确认测试
```bash
# 确认测试
curl -X POST \
     -H "X-API-Key: KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4" \
     -H "Content-Type: application/json" \
     -d '{"count": 10}' \
     http://10.8.0.1:8888/api/confirm
```

### 4. 完整流程测试
```bash
# 启动中转服务器
cd /home/spider/31339752/relay
./start_relay.sh

# 观察日志
tail -f relay_service.log | grep "从C2拉取"
```

---

## 🔧 配置示例

### C2端配置 (config.production.json)
```json
{
  "botnet": {
    "botnet_type": "ramnit"
  },
  "http_server": {
    "host": "0.0.0.0",
    "port": 8888,
    "api_key": "your-secret-key-here"
  },
  "cache": {
    "max_cached_records": 10000
  }
}
```

### 中转服务器配置 (relay_config.json)
```json
{
  "puller": {
    "c2_servers": [{
      "id": "c2-server-1",
      "url": "http://10.8.0.1:8888",
      "api_key": "your-secret-key-here",  // ← 与C2端一致
      "enabled": true
    }],
    "batch_size": 1000,
    "timeout": 30,
    "use_two_phase_commit": true
  }
}
```

---

## ✅ 总结

### 完全兼容的特性
- ✅ API接口格式（/api/pull, /api/confirm）
- ✅ 认证机制（X-API-Key）
- ✅ 两阶段提交
- ✅ 断点续传（since_seq）
- ✅ 数据格式
- ✅ 批量拉取
- ✅ 健康检查

### 增强的功能
- ✅ 自动保存断点（last_seq_ids）
- ✅ 多C2端点支持
- ✅ 失败重试机制
- ✅ 本地缓存

### 部署检查清单
- [ ] C2端API密钥与中转服务器配置一致
- [ ] OpenVPN隧道已建立（10.8.0.x网络）
- [ ] C2端服务正在运行（端口8888）
- [ ] 中转服务器可以访问C2端
- [ ] 配置文件中的URL正确（http://10.8.0.1:8888）

---

## 📞 故障排查

### 问题：连接失败
```bash
# 检查OpenVPN
ip addr show tun0
ping 10.8.0.1

# 检查C2端服务
curl http://10.8.0.1:8888/health
```

### 问题：认证失败
```bash
# 确认API密钥一致
grep api_key pull_mode/config.production.json
grep api_key relay/relay_config.json
```

### 问题：无数据返回
```bash
# 检查C2端缓存
curl -H "X-API-Key: your-key" http://10.8.0.1:8888/api/stats
```

---

**结论**: 中转服务器的 `data_puller.py` 与 C2端的 `c2_data_server.py` **完全兼容**，并且已经增强了断点续传功能！
