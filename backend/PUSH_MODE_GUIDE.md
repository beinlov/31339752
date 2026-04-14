# 数据推送模式使用指南

## 概述

由于传输链路上配置了反溯源，C2端会先将数据传输至中转服务器（C2与中转服务器通过OpenVPN通路通信），然后中转服务器再将数据传输至本服务器。由于中转服务器配置了动态IP资源池，其IP会周期性变化，因此本服务器采用**被动接收推送**的方式来获取数据。

## 架构说明

### Pull模式（传统模式）
```
本服务器 ----[主动拉取]----> C2端
```

### Push模式（新模式）
```
C2端 ----[OpenVPN]----> 中转服务器 ----[推送]----> 本服务器
```

### 安全特性

1. **HMAC签名验证**：防止数据篡改和伪造请求
2. **时间戳验证**：防止重放攻击（默认5分钟容忍度）
3. **Nonce缓存**：防止相同请求重复处理
4. **API密钥认证**：双重认证保障
5. **IP白名单**（可选）：由于动态IP，默认禁用

## 配置步骤

### 1. 修改配置文件

编辑 `backend/config.py`，设置数据传输模式：

```python
# 方式1：直接修改配置文件
DATA_TRANSFER_MODE = 'push'  # 改为 'push'

# 方式2：使用环境变量（推荐）
# export DATA_TRANSFER_MODE=push
```

### 2. 配置推送模式参数

在 `config.py` 中的 `PUSH_MODE_CONFIG` 部分：

```python
PUSH_MODE_CONFIG = {
    'enabled': True,  # 自动根据 DATA_TRANSFER_MODE 设置
    
    # HMAC签名配置
    'use_signature': True,
    'signature_secret': '生产环境必须修改为强密钥',  # ⚠️ 重要：修改此密钥
    'signature_algorithm': 'sha256',
    
    # 时间戳防重放
    'timestamp_tolerance': 300,  # 5分钟容忍度
    
    # Nonce缓存
    'enable_nonce_cache': True,
    'nonce_cache_size': 10000,
    'nonce_cache_ttl': 600,
    
    # API密钥
    'api_key': 'KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4',  # ⚠️ 生产环境修改
    
    # IP白名单（动态IP场景下留空）
    'allowed_ips': [],
    
    # 数据限制
    'max_batch_size': 5000,
    'max_request_size_mb': 50,
    
    # 推送确认
    'require_confirmation': True,
    'return_detailed_stats': True,
}
```

### 3. 重启服务

```bash
# 停止现有服务
pkill -f "python.*main.py"

# 启动服务（推送模式）
cd /home/spider/31339752/backend
export DATA_TRANSFER_MODE=push
python main.py
```

查看日志确认推送模式已启用：
```
数据传输模式: push
✅ 推送模式已启用 - 本服务器将被动接收中转服务器推送的数据
✅ 数据推送接收模式已启用 (DATA_TRANSFER_MODE=push)
```

## API接口说明

### 1. 数据推送接口

**端点**: `POST /api/data-push`

**请求头**:
```http
Content-Type: application/json
X-API-Key: <API密钥>
X-Signature: <HMAC签名>
```

**请求体**:
```json
{
    "botnet_type": "ramnit",
    "data": [
        {
            "ip": "1.2.3.4",
            "timestamp": "2025-01-01T12:00:00Z",
            "event_type": "infection",
            "source": "relay_server",
            "botnet_type": "ramnit"
        }
    ],
    "timestamp": "2025-01-01T12:00:05Z",
    "nonce": "random-unique-string-12345",
    "relay_server_id": "relay-001"
}
```

**响应**:
```json
{
    "success": true,
    "message": "成功处理100条数据",
    "received_count": 100,
    "processed_count": 100,
    "duplicate_count": 0,
    "error_count": 0,
    "timestamp": "2025-01-01T12:00:06Z",
    "processing_time_ms": 234.5
}
```

### 2. 推送状态接口

**端点**: `GET /api/push-status`

**响应**:
```json
{
    "mode": "push",
    "enabled": true,
    "config": {
        "use_signature": true,
        "timestamp_tolerance": 300,
        "enable_nonce_cache": true,
        "max_batch_size": 5000,
        "ip_whitelist_enabled": false
    },
    "nonce_cache": {
        "size": 123,
        "max_size": 10000,
        "ttl": 600
    },
    "timestamp": "2025-01-01T12:00:00Z"
}
```

### 3. 健康检查接口

**端点**: `GET /api/push-health`

**响应**:
```json
{
    "status": "ok",
    "service": "data-push-receiver",
    "mode": "push",
    "timestamp": "2025-01-01T12:00:00Z"
}
```

## HMAC签名生成

### Python示例

```python
import hmac
import hashlib
import json
from datetime import datetime

def generate_signature(request_body: dict, secret: str, nonce: str = None) -> tuple:
    """
    生成HMAC签名
    
    Returns:
        (signature, timestamp, nonce)
    """
    timestamp = datetime.now().isoformat()
    
    # 序列化请求体
    body_str = json.dumps(request_body, ensure_ascii=False)
    
    # 构造签名消息
    message_parts = [timestamp]
    if nonce:
        message_parts.append(nonce)
    message_parts.append(body_str)
    message = ''.join(message_parts)
    
    # 计算HMAC-SHA256
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature, timestamp, nonce

# 使用示例
secret = "CHANGE_ME_IN_PRODUCTION_use_strong_random_key_here"
nonce = "unique-nonce-12345"

request_data = {
    "botnet_type": "ramnit",
    "data": [...],
    "timestamp": "2025-01-01T12:00:00Z",
    "nonce": nonce
}

signature, timestamp, _ = generate_signature(request_data, secret, nonce)
print(f"Signature: {signature}")
```

### Shell/cURL示例

```bash
#!/bin/bash

SECRET="CHANGE_ME_IN_PRODUCTION_use_strong_random_key_here"
API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
NONCE="test-nonce-$(date +%s)"

# 构造请求体
REQUEST_BODY=$(cat <<EOF
{
    "botnet_type": "ramnit",
    "data": [{"ip": "1.2.3.4", "timestamp": "$TIMESTAMP"}],
    "timestamp": "$TIMESTAMP",
    "nonce": "$NONCE"
}
EOF
)

# 计算签名：timestamp + nonce + request_body
MESSAGE="${TIMESTAMP}${NONCE}${REQUEST_BODY}"
SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$SECRET" | cut -d' ' -f2)

# 发送请求
curl -X POST http://localhost:8000/api/data-push \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -H "X-Signature: $SIGNATURE" \
  -d "$REQUEST_BODY"
```

## 中转服务器实现建议

### 基本流程

1. **从C2端拉取数据**（通过OpenVPN）
2. **构造推送请求**
3. **生成HMAC签名**
4. **推送到本服务器**
5. **处理响应和重试**

### 重试机制

推送失败时应实现指数退避重试：

```python
import time
import requests

def push_with_retry(url, data, headers, max_retries=3):
    """推送数据并自动重试"""
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"推送失败 (尝试 {attempt+1}/{max_retries}): {response.status_code}")
        except Exception as e:
            print(f"推送异常 (尝试 {attempt+1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # 指数退避: 1s, 2s, 4s
            time.sleep(wait_time)
    
    return None
```

### 完整中转服务器示例

```python
#!/usr/bin/env python3
"""
中转服务器推送脚本示例
从C2端拉取数据并推送到本服务器
"""

import requests
import hmac
import hashlib
import json
from datetime import datetime
import time

# 配置
C2_URL = "http://c2-server:8888/api/pull"
C2_API_KEY = "c2-api-key"
PLATFORM_URL = "http://platform-server:8000/api/data-push"
PLATFORM_API_KEY = "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
SIGNATURE_SECRET = "CHANGE_ME_IN_PRODUCTION_use_strong_random_key_here"

def pull_from_c2():
    """从C2端拉取数据"""
    response = requests.get(
        f"{C2_URL}?limit=1000",
        headers={"X-API-Key": C2_API_KEY},
        timeout=30
    )
    response.raise_for_status()
    return response.json()

def generate_signature(request_body_str, timestamp, nonce):
    """生成HMAC签名"""
    message = timestamp + nonce + request_body_str
    signature = hmac.new(
        SIGNATURE_SECRET.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def push_to_platform(data):
    """推送数据到本服务器"""
    timestamp = datetime.now().isoformat()
    nonce = f"relay-{int(time.time())}"
    
    # 构造推送数据
    push_data = {
        "botnet_type": data["botnet_type"],
        "data": data["data"],
        "timestamp": timestamp,
        "nonce": nonce,
        "relay_server_id": "relay-001"
    }
    
    # 序列化请求体
    request_body = json.dumps(push_data, ensure_ascii=False)
    
    # 生成签名
    signature = generate_signature(request_body, timestamp, nonce)
    
    # 发送请求
    response = requests.post(
        PLATFORM_URL,
        data=request_body,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": PLATFORM_API_KEY,
            "X-Signature": signature
        },
        timeout=30
    )
    response.raise_for_status()
    return response.json()

def main():
    """主循环"""
    while True:
        try:
            # 1. 从C2拉取
            c2_data = pull_from_c2()
            if c2_data.get("count", 0) > 0:
                # 2. 推送到平台
                result = push_to_platform(c2_data)
                print(f"推送成功: {result}")
            else:
                print("无新数据")
            
            # 3. 等待下一次
            time.sleep(10)
            
        except Exception as e:
            print(f"错误: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
```

## 测试

### 使用测试脚本

```bash
cd /home/spider/31339752/backend

# 基础测试
python test_push_mode.py

# 自定义测试
python test_push_mode.py \
  --botnet-type ramnit \
  --count 100 \
  --base-url http://localhost:8000

# 测试认证失败（不使用签名）
python test_push_mode.py --no-signature
```

### 手动测试

```bash
# 1. 健康检查
curl http://localhost:8000/api/push-health

# 2. 状态查询
curl http://localhost:8000/api/push-status

# 3. 推送数据（需要生成签名）
# 见上文 Shell/cURL 示例
```

## 监控与日志

### 查看推送日志

```bash
# 查看main.py日志
tail -f /home/spider/31339752/backend/logs/main_app.log | grep PUSH

# 查看日志处理器日志
tail -f /home/spider/31339752/backend/logs/log_processor.log
```

### 推送模式标识

日志中会看到以下标识：
- `✅ 推送模式已启用` - 推送模式已启动
- `[PUSH] 收到推送请求` - 接收到推送数据
- `[PUSH] 推送处理成功` - 数据处理成功
- `[PUSH] HMAC签名验证失败` - 签名验证失败

## 切换回Pull模式

如需切换回传统的Pull模式：

```python
# 方式1：修改 config.py
DATA_TRANSFER_MODE = 'pull'

# 方式2：环境变量
export DATA_TRANSFER_MODE=pull
```

然后重启服务即可。

## 常见问题

### 1. 推送失败：签名验证失败

**原因**：签名密钥不一致或签名算法错误

**解决**：
- 确认中转服务器和本服务器的 `SIGNATURE_SECRET` 一致
- 确认签名算法为 `sha256`
- 确认签名消息构造顺序：`timestamp + nonce + request_body`

### 2. 推送失败：时间戳超出范围

**原因**：中转服务器与本服务器时间不同步

**解决**：
```bash
# 同步系统时间
sudo ntpdate -u ntp.aliyun.com
```

### 3. 推送失败：重放攻击检测

**原因**：使用了相同的nonce

**解决**：确保每次请求使用唯一的nonce

### 4. 推送路由未注册

**原因**：未启用推送模式

**解决**：
1. 检查 `DATA_TRANSFER_MODE` 是否为 `push`
2. 检查日志是否有 `✅ 数据推送接收模式已启用`
3. 访问 `/docs` 查看是否有推送相关API

## 性能优化建议

1. **批量推送**：中转服务器应批量推送数据（建议1000-5000条/批）
2. **并发限制**：避免同时推送过多请求
3. **错误重试**：实现指数退避重试机制
4. **监控告警**：监控推送成功率和延迟

## 安全建议

1. **生产环境必须修改密钥**：`SIGNATURE_SECRET` 和 `API_KEY`
2. **使用HTTPS**：生产环境必须启用HTTPS
3. **定期轮换密钥**：建议每季度更换一次密钥
4. **监控异常**：监控认证失败、重放攻击等异常行为
