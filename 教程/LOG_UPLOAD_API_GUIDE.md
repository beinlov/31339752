# 日志上传接口使用指南

## 📋 概述

本系统提供了安全的API接口，用于接收远端蜜罐服务器上传的日志数据。日志上传后会自动被日志处理器处理并写入数据库。

## 🔧 架构流程

```
┌─────────────┐         HTTP POST          ┌──────────────┐
│  远端蜜罐    │  ──────────────────────►  │  本地API     │
│  (蜜罐服务器) │   (带API密钥认证)          │  (FastAPI)   │
└─────────────┘                            └──────────────┘
                                                   │
                                                   ▼
                                           保存到日志文件
                                           backend/logs/{type}/
                                                   │
                                                   ▼
                                           ┌──────────────┐
                                           │ 日志处理器    │
                                           │ (自动监控)   │
                                           └──────────────┘
                                                   │
                                                   ▼
                                           ┌──────────────┐
                                           │  数据库       │
                                           │  (MySQL)     │
                                           └──────────────┘
```

---

## 🚀 快速开始

### 步骤1: 配置安全参数

编辑 `backend/config.py`：

```python
# API密钥（强烈建议修改）
API_KEY = "your-secret-api-key-change-this-in-production"

# IP白名单（生产环境必须配置）
ALLOWED_UPLOAD_IPS = [
    "192.168.1.100",  # 远端服务器1的IP
    "10.0.0.50",      # 远端服务器2的IP
]

# 单次上传限制
MAX_LOGS_PER_UPLOAD = 10000
```

**生成强密钥的方法**：
```bash
# Linux/Mac
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### 步骤2: 启动服务

```bash
# 启动后端API（端口8000）
cd backend
python main.py

# 启动日志处理器
cd backend/log_processor
python main.py

# 或使用一键启动脚本
cd backend
start_all.bat   # Windows
./start_all.sh  # Linux/Mac
```

### 步骤3: 本地测试

```bash
# 运行测试脚本
python test_upload.py
```

**预期输出**：
```
============================================================
  僵尸网络日志上传接口测试工具
============================================================

📊 测试1: 查询上传接口状态
============================================================
状态码: 200
API状态: running
...
✅ 状态查询成功！

📤 测试: 上传 Mozi 僵尸网络日志
============================================================
✅ 上传成功！
  - 接收数量: 3
  - 保存位置: backend/logs/mozi/2025-10-30.txt
```

### 步骤4: 部署远端上传脚本

**在远端服务器上**：

1. 复制 `remote_uploader.py` 到远端服务器
2. 编辑配置：
   ```python
   # 修改本地服务器地址
   LOCAL_SERVER_HOST = "你的本地服务器公网IP"
   
   # 修改API密钥（与config.py一致）
   API_KEY = "your-secret-api-key-change-this-in-production"
   
   # 修改僵尸网络类型
   BOTNET_TYPE = "mozi"  # 根据实际蜜罐类型
   
   # 修改日志文件路径
   LOG_FILE_PATH = "/var/log/honeypot/botnet.log"
   ```

3. 测试连接：
   ```bash
   python remote_uploader.py test
   ```

4. 启动上传器：
   ```bash
   # 前台运行（测试用）
   python remote_uploader.py
   
   # 后台运行（生产环境）
   nohup python remote_uploader.py > /tmp/uploader.log 2>&1 &
   
   # 或使用systemd服务（推荐）
   ```

---

## 📡 API接口说明

### 1. 上传日志接口

**端点**: `POST /api/upload-logs`

**认证**: 需要API密钥（Header: `X-API-Key`）

**请求格式**:
```json
{
  "botnet_type": "mozi",
  "logs": [
    "2025-10-30 12:00:00,1.2.3.4,infection,bot_v1.0",
    "2025-10-30 12:01:00,1.2.3.5,beacon"
  ],
  "source_ip": "192.168.1.100"
}
```

**字段说明**:
- `botnet_type` (必需): 僵尸网络类型
  - 允许值: `asruex`, `mozi`, `andromeda`, `moobot`, `ramnit`, `leethozer`
- `logs` (必需): 日志行数组
  - 格式: `timestamp,ip,event_type,extras...`
  - 最大行数: 10000（可配置）
- `source_ip` (可选): 远端IP标识

**响应格式**:
```json
{
  "status": "success",
  "message": "成功接收并保存 2 条日志",
  "received_count": 2,
  "saved_to": "backend/logs/mozi/2025-10-30.txt",
  "timestamp": "2025-10-30 15:30:00"
}
```

**错误响应**:

| 状态码 | 说明 | 解决方法 |
|--------|------|----------|
| 401 | API密钥无效 | 检查 `X-API-Key` 是否正确 |
| 403 | IP未授权 | 将IP添加到 `ALLOWED_UPLOAD_IPS` |
| 422 | 参数验证失败 | 检查请求格式和参数 |
| 500 | 服务器错误 | 查看后端日志 |

**示例代码**:

```bash
# curl命令
curl -X POST "http://localhost:8000/api/upload-logs" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "botnet_type": "mozi",
    "logs": [
      "2025-10-30 15:00:00,8.8.8.8,infection,test"
    ]
  }'
```

```python
# Python代码
import requests

headers = {
    "Content-Type": "application/json",
    "X-API-Key": "your-api-key"
}

data = {
    "botnet_type": "mozi",
    "logs": [
        "2025-10-30 15:00:00,8.8.8.8,infection,test"
    ]
}

response = requests.post(
    "http://localhost:8000/api/upload-logs",
    json=data,
    headers=headers
)

print(response.json())
```

### 2. 查询状态接口

**端点**: `GET /api/upload-status`

**认证**: 无需认证（只读接口）

**响应格式**:
```json
{
  "api_status": "running",
  "timestamp": "2025-10-30 15:30:00",
  "security": {
    "api_key_required": true,
    "ip_whitelist_enabled": true,
    "max_logs_per_upload": 10000
  },
  "botnet_types": [
    {
      "type": "mozi",
      "log_files": 5,
      "total_lines": 12345,
      "latest_file": "2025-10-30.txt",
      "last_modified": "2025-10-30 15:29:00"
    }
  ]
}
```

**示例**:
```bash
curl http://localhost:8000/api/upload-status
```

---

## 🔒 安全性配置

### 1. API密钥认证

所有上传请求必须在HTTP Header中包含 `X-API-Key`：

```
X-API-Key: your-secret-api-key-change-this-in-production
```

**配置位置**: `backend/config.py` 中的 `API_KEY`

**建议**:
- ✅ 使用至少32字符的随机字符串
- ✅ 定期更换密钥
- ✅ 不要在代码中硬编码（使用环境变量）
- ❌ 不要使用简单密码

### 2. IP白名单

限制只有特定IP才能上传日志。

**配置位置**: `backend/config.py` 中的 `ALLOWED_UPLOAD_IPS`

```python
# 空列表 = 允许所有IP（仅开发环境）
ALLOWED_UPLOAD_IPS = []

# 生产环境必须配置具体IP
ALLOWED_UPLOAD_IPS = [
    "192.168.1.100",
    "10.0.0.50"
]
```

### 3. 速率限制（可选）

如需要更严格的速率限制，可以添加：

```python
# 在 backend/main.py 中添加
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/upload-logs")
@limiter.limit("10/minute")  # 每分钟最多10次
async def upload_logs(...):
    ...
```

---

## 📊 监控和调试

### 查看实时上传情况

```bash
# 监控后端日志
tail -f backend/uvicorn.log | grep "upload"

# 监控日志处理器
tail -f backend/log_processor.log

# 查看日志文件
ls -lh backend/logs/*/2025-10-30.txt
```

### 统计上传数据

```bash
# 今天上传的总行数
wc -l backend/logs/*/$(date +%Y-%m-%d).txt

# 各僵尸网络的上传量
for dir in backend/logs/*/; do
    echo "$(basename $dir): $(wc -l $dir/*.txt 2>/dev/null | tail -1)"
done
```

### 验证数据已入库

```sql
-- 查看最近上传的数据
SELECT * FROM botnet_nodes_mozi 
WHERE created_at > NOW() - INTERVAL 10 MINUTE
ORDER BY created_at DESC 
LIMIT 10;

-- 统计今天的上传量
SELECT 
    DATE(created_at) as date,
    COUNT(*) as count
FROM botnet_nodes_mozi
WHERE DATE(created_at) = CURDATE()
GROUP BY DATE(created_at);
```

---

## 🔧 故障排查

### 问题1: 连接被拒绝

**症状**: `Connection refused` 或 `Failed to connect`

**检查**:
```bash
# 1. 后端是否运行？
netstat -an | grep 8000
# 或
lsof -i :8000

# 2. 防火墙是否开放端口？
# Linux
sudo ufw status
sudo ufw allow 8000

# Windows
netsh advfirewall firewall add rule name="API Port 8000" dir=in action=allow protocol=TCP localport=8000
```

### 问题2: 401 认证失败

**症状**: `无效的API密钥`

**检查**:
1. 确认 `test_upload.py` 中的 `API_KEY` 与 `backend/config.py` 一致
2. 确认Header名称为 `X-API-Key`（注意大小写）
3. 重启后端服务使配置生效

### 问题3: 403 IP未授权

**症状**: `IP未授权`

**解决**:
```python
# 方案1: 临时禁用白名单（仅开发环境）
ALLOWED_UPLOAD_IPS = []

# 方案2: 添加IP到白名单
ALLOWED_UPLOAD_IPS = [
    "你的远端IP"
]
```

**查看你的IP**:
```bash
# 远端服务器查看公网IP
curl ifconfig.me
curl ipinfo.io/ip
```

### 问题4: 日志未被处理

**症状**: 日志文件已保存，但数据库无数据

**检查**:
```bash
# 1. 日志处理器是否运行？
ps aux | grep "log_processor/main.py"

# 2. 查看处理器日志
tail -f backend/log_processor.log

# 3. 检查日志格式
head backend/logs/mozi/2025-10-30.txt
# 应该是: timestamp,ip,event_type,extras...
```

### 问题5: 数据重复

**症状**: 同一条日志被插入多次

**检查**:
```sql
-- 检查是否有重复
SELECT ip, created_at, COUNT(*) as count
FROM botnet_nodes_mozi
GROUP BY ip, created_at
HAVING count > 1;
```

**解决**: 确保去重机制已部署
```bash
cd backend/log_processor
./setup_deduplication.sh  # Linux/Mac
setup_deduplication.bat   # Windows
```

---

## 📚 文件清单

| 文件 | 位置 | 用途 |
|------|------|------|
| `backend/main.py` | 后端 | 包含上传接口实现 |
| `backend/config.py` | 后端 | 安全配置（API密钥、白名单） |
| `test_upload.py` | 根目录 | 本地测试脚本 |
| `remote_uploader.py` | 根目录 | 远端上传脚本 |
| `LOG_UPLOAD_API_GUIDE.md` | 根目录 | 本文档 |

---

## 🎯 最佳实践

### 开发环境

1. ✅ 使用测试API密钥
2. ✅ 禁用IP白名单（`ALLOWED_UPLOAD_IPS = []`）
3. ✅ 使用 `test_upload.py` 进行本地测试
4. ✅ 关注日志输出

### 生产环境

1. ✅ 使用强密钥（32+字符）
2. ✅ 启用IP白名单（只允许已知IP）
3. ✅ 使用HTTPS（配置反向代理）
4. ✅ 启用速率限制
5. ✅ 监控上传日志和错误
6. ✅ 定期备份数据库
7. ✅ 定期更换API密钥

### 远端部署

1. ✅ 使用 systemd 或 supervisor 管理进程
2. ✅ 配置日志轮转
3. ✅ 监控上传器状态
4. ✅ 配置失败告警

**systemd服务示例**:
```ini
# /etc/systemd/system/log-uploader.service
[Unit]
Description=Botnet Log Uploader
After=network.target

[Service]
Type=simple
User=honeypot
WorkingDirectory=/opt/honeypot
ExecStart=/usr/bin/python3 /opt/honeypot/remote_uploader.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable log-uploader
sudo systemctl start log-uploader
sudo systemctl status log-uploader
```

---

## ✅ 部署检查清单

### 本地服务器

- [ ] 后端API已启动（端口8000）
- [ ] 日志处理器已启动
- [ ] API密钥已配置（强密码）
- [ ] IP白名单已配置（如需要）
- [ ] 防火墙已开放端口8000
- [ ] 运行 `test_upload.py` 测试成功
- [ ] `/api/upload-status` 可访问
- [ ] 去重机制已部署

### 远端服务器

- [ ] `remote_uploader.py` 已部署
- [ ] 配置已正确填写（IP、API密钥、路径）
- [ ] 运行 `python remote_uploader.py test` 测试成功
- [ ] 进程管理已配置（systemd/supervisor）
- [ ] 日志监控已配置
- [ ] 失败告警已配置

---

## 🆘 技术支持

### 相关文档
- **日志处理器**: `backend/log_processor/README.md`
- **去重机制**: `backend/log_processor/DEDUPLICATION.md`
- **快速开始**: `backend/log_processor/QUICKSTART.md`
- **系统启动**: `backend/STARTUP_GUIDE.md`

### 常见资源
- API文档: `http://localhost:8000/docs`（FastAPI自动生成）
- 状态查询: `http://localhost:8000/api/upload-status`

---

**祝部署顺利！** 🎉



