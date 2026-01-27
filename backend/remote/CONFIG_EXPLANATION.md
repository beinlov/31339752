# C2端配置说明 - 推送 vs 拉取模式

## 🔄 架构演变

### 旧架构：推送模式（remote_uploader.py）

```
┌─────────────────┐                    ┌─────────────────┐
│   C2端（客户端）  │   主动推送           │  平台（服务器）   │
│                 │ ──────────────>    │                 │
│ - 读取日志       │ POST /api/upload   │ - 接收数据       │
│ - 处理数据       │                    │ - 存储到数据库   │
│ - 主动上传       │                    │                 │
└─────────────────┘                    └─────────────────┘
```

**配置需求**：
```json
{
  "server": {
    "api_endpoint": "http://平台IP:8000",  // C2需要知道平台地址
    "api_key": "认证密钥"                   // C2连接平台的密钥
  }
}
```

**优点**：
- ✅ C2主动推送，实时性好
- ✅ 平台端简单，只需被动接收

**缺点**：
- ❌ C2需要知道平台地址（配置复杂）
- ❌ C2需要主动连接（防火墙问题）
- ❌ 无法控制数据流速（可能压垮平台）

---

### 新架构：拉取模式（c2_data_server.py，当前）

```
┌─────────────────┐                    ┌─────────────────┐
│   C2端（服务器）  │   被动响应           │  平台（客户端）   │
│                 │ <──────────────    │                 │
│ - 读取日志       │ GET /api/pull      │ - 主动拉取       │
│ - 缓存数据       │                    │ - 控制速度       │
│ - 等待拉取       │                    │ - 存储到数据库   │
└─────────────────┘                    └─────────────────┘
```

**配置需求**：
```json
{
  "http_server": {
    "host": "0.0.0.0",        // C2监听地址
    "port": 8888,             // C2监听端口
    "api_key": "认证密钥"      // 验证平台的密钥
  }
}
```

**优点**：
- ✅ C2配置简单，不需要知道平台地址
- ✅ 平台控制拉取速度（背压控制）
- ✅ 断点续传，数据不丢失
- ✅ 适合多C2架构

**缺点**：
- ⚠️ C2需要有公网IP或通过端口映射
- ⚠️ 平台需要配置所有C2地址

---

## 📋 配置对比

### 1. 推送模式配置（已废弃）

```json
{
  "server": {
    "_comment": "平台服务器配置（C2需要知道平台地址）",
    "api_endpoint": "http://平台IP:8000/api/upload",
    "api_key": "平台提供的API_KEY"
  },
  
  "processing": {
    "upload_interval": 300,    // C2主动推送间隔
    "batch_size": 500          // 每次推送数量
  }
}
```

**使用场景**：
- C2端运行 `remote_uploader.py`
- C2主动连接平台推送数据
- 平台端只需要接收接口

---

### 2. 拉取模式配置（当前使用）

```json
{
  "http_server": {
    "_comment": "C2端HTTP服务器配置（平台来拉取）",
    "host": "0.0.0.0",         // C2监听地址
    "port": 8888,              // C2监听端口
    "api_key": "验证平台的密钥"
  },
  
  "cache": {
    "max_cached_records": 10000,  // 缓存上限
    "high_watermark": 8000,       // 背压控制
    "low_watermark": 2000
  }
}
```

**使用场景**：
- C2端运行 `c2_data_server.py`
- 平台主动连接C2拉取数据
- C2端实现背压控制

---

## 🎯 为什么删除 `server.*` 配置？

### 1. **架构改变**

| 配置项 | 推送模式 | 拉取模式 |
|-------|---------|---------|
| `server.api_endpoint` | ✅ 必需 | ❌ 不需要（C2不知道平台地址） |
| `server.api_key` | ✅ 必需 | ❌ 不需要（认证方向相反） |
| `http_server.host` | ❌ 不需要 | ✅ 必需（C2监听地址） |
| `http_server.port` | ❌ 不需要 | ✅ 必需（C2监听端口） |
| `http_server.api_key` | ❌ 不需要 | ✅ 必需（验证平台身份） |

### 2. **认证方向不同**

**推送模式**：
```
C2端 ──(携带API Key)──> 平台端
      "我是C2，这是我的密钥"
      平台验证C2的身份
```

**拉取模式**：
```
平台端 ──(携带API Key)──> C2端
       "我是平台，这是我的密钥"
       C2验证平台的身份
```

### 3. **配置职责清晰**

**推送模式**：C2需要配置平台信息
```json
{
  "server": {
    "api_endpoint": "http://平台地址",  // C2需要知道往哪推
    "api_key": "C2的身份证明"
  }
}
```

**拉取模式**：C2只需配置自己的服务
```json
{
  "http_server": {
    "port": 8888,              // C2监听哪个端口
    "api_key": "验证来访者的密钥"
  }
}
```

---

## 🔧 实际配置示例

### 场景1: 纯拉取模式（推荐，当前方案）

**C2端 config.json**：
```json
{
  "botnet": {
    "botnet_type": "test",
    "log_dir": "/home/ubuntu/log",
    "log_file_pattern": "test_{date}.log"
  },
  
  "http_server": {
    "host": "0.0.0.0",
    "port": 8888,
    "api_key": "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
  },
  
  "cache": {
    "max_cached_records": 10000,
    "high_watermark": 8000,
    "low_watermark": 2000
  }
}
```

**平台端 config.py**：
```python
C2_ENDPOINTS = [
    {
        'name': 'C2-test',
        'url': 'http://C2公网IP:8888',      # 平台配置C2地址
        'api_key': 'KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4',
        'enabled': True
    }
]
```

---

### 场景2: 纯推送模式（旧方案，不推荐）

**C2端 config.json**：
```json
{
  "botnet": {
    "botnet_type": "test",
    "log_dir": "/home/ubuntu/log"
  },
  
  "server": {
    "api_endpoint": "http://平台IP:8000/api/upload",  // C2配置平台地址
    "api_key": "C2_API_KEY"
  },
  
  "processing": {
    "upload_interval": 300,
    "batch_size": 500
  }
}
```

**平台端**：
```python
@app.post("/api/upload")
async def upload_data(request):
    # 被动接收C2推送的数据
    api_key = request.headers.get('X-API-Key')
    if api_key != EXPECTED_API_KEY:
        return {'error': 'Unauthorized'}
    # 处理数据...
```

---

### 场景3: 双模式（灵活但复杂）

如果你需要同时支持推送和拉取，参考 `config_with_both_modes.json`。

---

## ✅ 总结

### 删除的配置及原因

| 配置项 | 用途 | 是否需要 | 原因 |
|-------|------|---------|------|
| `server.api_endpoint` | C2推送数据到平台的地址 | ❌ 不需要 | 改为拉取模式，C2不推送 |
| `server.api_key` | C2连接平台的认证 | ❌ 不需要 | 认证方向相反了 |
| `server.local_server_*` | 本地服务器配置 | ❌ 不需要 | 已被 `http_server.*` 取代 |

### 新增的配置及用途

| 配置项 | 用途 | 是否必需 |
|-------|------|---------|
| `http_server.host` | C2监听地址 | ✅ 必需 |
| `http_server.port` | C2监听端口 | ✅ 必需 |
| `http_server.api_key` | 验证平台身份的密钥 | ✅ 必需 |
| `cache.max_cached_records` | 缓存上限 | ✅ 必需（背压控制） |
| `cache.high_watermark` | 高水位线 | ✅ 必需（背压控制） |
| `cache.low_watermark` | 低水位线 | ✅ 必需（背压控制） |

---

## 🤔 常见疑问

### Q1: 如果我还想用推送模式怎么办？

**答**：使用旧的 `remote_uploader.py` 和相应的配置文件。

### Q2: 可以同时支持推送和拉取吗？

**答**：理论上可以，但会增加复杂度。参考 `config_with_both_modes.json`。

### Q3: 拉取模式的API Key和推送模式的一样吗？

**答**：建议分开：
- 推送模式：`C2_PUSH_API_KEY`（C2的身份证明）
- 拉取模式：`C2_PULL_API_KEY`（验证平台的身份）

### Q4: C2没有公网IP怎么办？

**答**：
1. 使用SSH隧道或反向代理
2. 或使用推送模式（C2主动推送到平台）

---

## 📚 相关文档

- `README_BACKPRESSURE.md` - 背压控制详细说明
- `config.json` - 当前使用的配置（拉取模式）
- `config_with_both_modes.json` - 双模式配置示例
