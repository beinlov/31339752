# 三服务器配置对齐指南

## 📋 配置同步清单

### 🔑 密钥配置对齐表

| 配置项 | C2端 | 中转服务器 | 平台服务器 | 值 |
|-------|------|-----------|-----------|-----|
| **C2 API密钥** | `http_server.api_key` | `puller.c2_servers[].api_key` | N/A | `KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4` |
| **平台 API密钥** | N/A | `pusher.platform_api_key` | `PUSH_MODE_CONFIG['api_key']` | `KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4` |
| **HMAC签名密钥** | N/A | `pusher.signature_secret` | `PUSH_MODE_CONFIG['signature_secret']` | `[TODO:生成强密钥]` |

---

## 📝 需要填写的配置项（标记为TODO）

### 1️⃣ C2端 (pull_mode/config.production.json)

```json
{
  "botnet": {
    "botnet_type": "utg_q_008"  // ✅ 已配置，确认是否需要修改
  },
  
  "log_sources": {
    "online": {
      "path": "/home/irc_server/logs/user_activity.log"  // ✅ 已配置
    },
    "cleanup": {
      "path": "/home/irc_server/logs/reports.db"  // ✅ 已配置
    }
  },
  
  "http_server": {
    "host": "0.0.0.0",  // ✅ 已配置
    "port": 8888,       // ✅ 已配置
    "api_key": "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"  // ✅ 已对齐
  }
}
```

**需要检查**：
- [ ] `botnet_type` 是否正确
- [ ] 日志文件路径是否存在
- [ ] API密钥是否需要修改为更安全的值

---

### 2️⃣ 中转服务器 (relay/relay_config.json)

```json
{
  "puller": {
    "c2_servers": [{
      "url": "http://10.8.0.1:8888",  // [TODO] 确认C2端OpenVPN内网IP
      "api_key": "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"  // ✅ 已对齐
    }]
  },
  
  "pusher": {
    "platform_url": "http://YOUR_PLATFORM_IP_OR_DOMAIN:8000",  // ❌ [TODO] 填写平台服务器地址
    "platform_api_key": "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4",  // ✅ 已对齐
    "signature_secret": "CHANGE_ME_IN_PRODUCTION_use_strong_random_key_here"  // ⚠️ [TODO] 生成强密钥
  },
  
  "ip_change": {
    "aws_region": "us-east-2",  // [TODO] 确认AWS区域
    "instance_id": "i-YOUR_INSTANCE_ID_HERE"  // ❌ [TODO] 填写AWS实例ID
  }
}
```

**需要填写**：
- [ ] `platform_url` - 平台服务器的公网IP或域名
- [ ] `instance_id` - AWS实例ID
- [ ] `signature_secret` - 生成强随机密钥（见下方命令）
- [ ] 确认 `url` - C2端的OpenVPN内网IP

---

### 3️⃣ 平台服务器 (backend/config.py)

```python
# 第391行：确认数据传输模式
DATA_TRANSFER_MODE = os.environ.get('DATA_TRANSFER_MODE', 'push')  # 改为 'push'

# 第400行：HMAC签名密钥
'signature_secret': os.environ.get('PUSH_SIGNATURE_SECRET', 
    'CHANGE_ME_IN_PRODUCTION_use_strong_random_key_here'),  # ⚠️ [TODO] 生成强密钥

# 第410行：API密钥（已对齐）
'api_key': os.environ.get('PUSH_API_KEY', 
    'KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4'),  # ✅ 已对齐
```

**需要修改**：
- [ ] 设置 `DATA_TRANSFER_MODE='push'` （环境变量或修改默认值）
- [ ] 生成并设置 `PUSH_SIGNATURE_SECRET`（环境变量推荐）

---

## 🔐 生成强随机密钥

### 方法1：使用OpenSSL（推荐）
```bash
openssl rand -hex 32
# 输出示例：a8f5f167f44f4964e6c998dee827110c682e00fa7bc91ec7eaa6e0dce7564e93
```

### 方法2：使用Python
```python
import secrets
print(secrets.token_hex(32))
```

### 方法3：在线生成
访问：https://www.random.org/strings/ （64个字符，a-f和0-9）

---

## 📊 配置文件对比表

### API密钥配置

| 服务器 | 配置文件 | 配置路径 | 当前值 | 状态 |
|--------|---------|---------|--------|------|
| **C2端** | `pull_mode/config.production.json` | `http_server.api_key` | `KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4` | ✅ 已对齐 |
| **中转** | `relay/relay_config.json` | `puller.c2_servers[0].api_key` | `KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4` | ✅ 已对齐 |
| **中转** | `relay/relay_config.json` | `pusher.platform_api_key` | `KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4` | ✅ 已对齐 |
| **平台** | `backend/config.py` | `PUSH_MODE_CONFIG['api_key']` | `KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4` | ✅ 已对齐 |

### 签名密钥配置

| 服务器 | 配置文件 | 配置路径 | 当前值 | 状态 |
|--------|---------|---------|--------|------|
| **中转** | `relay/relay_config.json` | `pusher.signature_secret` | `CHANGE_ME_IN_PRODUCTION_...` | ⚠️ 需要生成 |
| **平台** | `backend/config.py` | `PUSH_MODE_CONFIG['signature_secret']` | `CHANGE_ME_IN_PRODUCTION_...` | ⚠️ 需要生成 |

---

## 🚀 快速配置步骤

### 步骤1：生成签名密钥
```bash
# 生成密钥
export NEW_SIGNATURE_SECRET=$(openssl rand -hex 32)
echo "新生成的签名密钥: $NEW_SIGNATURE_SECRET"
```

### 步骤2：获取AWS实例ID
```bash
# 在中转服务器上运行
export AWS_REGION="us-east-2"
aws ec2 describe-instances --region $AWS_REGION --query 'Reservations[*].Instances[*].[InstanceId,PublicIpAddress,State.Name]' --output table

# 记录你的实例ID（格式：i-xxxxxxxxxxxxxxx）
```

### 步骤3：获取平台服务器地址
```bash
# [TODO] 填写你的平台服务器公网IP或域名
PLATFORM_URL="http://YOUR_IP_OR_DOMAIN:8000"
```

### 步骤4：更新中转服务器配置
```bash
cd /home/spider/31339752/relay

# 编辑配置文件
vim relay_config.json

# 修改以下项：
# 1. platform_url: "http://YOUR_PLATFORM_IP_OR_DOMAIN:8000"
# 2. signature_secret: "你生成的密钥"
# 3. instance_id: "i-你的实例ID"
```

### 步骤5：更新平台服务器配置
```bash
cd /home/spider/31339752/backend

# 方式1：使用环境变量（推荐）
export DATA_TRANSFER_MODE="push"
export PUSH_SIGNATURE_SECRET="你生成的密钥"
export PUSH_API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"

# 方式2：直接修改config.py
vim config.py
# 修改第391行：DATA_TRANSFER_MODE = 'push'
# 修改第400行：'signature_secret': '你生成的密钥',
```

---

## ✅ 配置验证清单

### C2端验证
```bash
cd /home/spider/31339752/pull_mode

# 1. 检查配置文件
cat config.production.json | grep -E "botnet_type|api_key|port"

# 2. 启动C2服务器
./start_c2_server.sh

# 3. 测试API
curl -H "X-API-Key: KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4" http://localhost:8888/health
```

### 中转服务器验证
```bash
cd /home/spider/31339752/relay

# 1. 检查配置文件
cat relay_config.json | grep -E "url|api_key|platform_url|signature_secret|instance_id"

# 2. 验证连通性
# C2端连通性（需要先建立OpenVPN）
curl -H "X-API-Key: KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4" http://10.8.0.1:8888/health

# 平台端连通性
curl http://YOUR_PLATFORM_IP:8000/api/push-health

# 3. 启动中转服务
./start_relay.sh
```

### 平台服务器验证
```bash
cd /home/spider/31339752/backend

# 1. 检查推送模式配置
python3 -c "
import config
print('传输模式:', config.DATA_TRANSFER_MODE)
print('推送启用:', config.PUSH_MODE_CONFIG['enabled'])
print('API密钥:', config.PUSH_MODE_CONFIG['api_key'][:20] + '...')
print('签名密钥:', config.PUSH_MODE_CONFIG['signature_secret'][:20] + '...')
"

# 2. 启动平台服务
export DATA_TRANSFER_MODE="push"
python3 main.py

# 3. 测试推送接口
curl http://localhost:8000/api/push-health
```

---

## 🔍 常见配置错误

### 错误1：C2端API密钥不匹配
**现象**：中转服务器显示 "❌ C2拉取HTTP错误: 401"

**解决**：
```bash
# 检查C2端配置
grep api_key pull_mode/config.production.json

# 检查中转端配置
grep api_key relay/relay_config.json

# 确保两者一致
```

### 错误2：平台端API密钥不匹配
**现象**：中转服务器显示 "❌ 平台推送失败: 401"

**解决**：
```bash
# 检查中转端配置
grep platform_api_key relay/relay_config.json

# 检查平台端配置
grep "PUSH_API_KEY" backend/config.py

# 确保两者一致
```

### 错误3：签名密钥不匹配
**现象**：中转服务器显示 "❌ 签名验证失败"

**解决**：
```bash
# 检查中转端配置
grep signature_secret relay/relay_config.json

# 检查平台端配置
grep "PUSH_SIGNATURE_SECRET" backend/config.py

# 确保两者完全一致（包括大小写）
```

### 错误4：AWS实例ID错误
**现象**：IP切换失败 "InvalidInstanceID.NotFound"

**解决**：
```bash
# 获取正确的实例ID
aws ec2 describe-instances --region us-east-2 \
    --query 'Reservations[*].Instances[*].[InstanceId]' \
    --output text
```

---

## 📚 环境变量配置（推荐）

### C2端环境变量
```bash
export C2_API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
export C2_HTTP_PORT="8888"
```

### 中转服务器环境变量
```bash
export C2_URL="http://10.8.0.1:8888"
export C2_API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
export PLATFORM_URL="http://YOUR_PLATFORM_IP:8000"
export PLATFORM_API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
export SIGNATURE_SECRET="你生成的密钥"
export AWS_REGION="us-east-2"
export AWS_INSTANCE_ID="i-你的实例ID"
export AWS_ACCESS_KEY_ID="你的AWS访问密钥"
export AWS_SECRET_ACCESS_KEY="你的AWS秘密密钥"
```

### 平台服务器环境变量
```bash
export DATA_TRANSFER_MODE="push"
export PUSH_API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
export PUSH_SIGNATURE_SECRET="你生成的密钥"
```

---

## 🎯 配置完成检查表

- [ ] **C2端**
  - [ ] `botnet_type` 已确认
  - [ ] 日志路径已确认存在
  - [ ] `api_key` = `KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4`
  - [ ] 服务启动成功，端口8888可访问

- [ ] **中转服务器**
  - [ ] OpenVPN已连接，可以ping通C2端
  - [ ] `puller.c2_servers[0].url` = `http://10.8.0.1:8888`
  - [ ] `puller.c2_servers[0].api_key` = `KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4`
  - [ ] `pusher.platform_url` 已填写正确的平台地址
  - [ ] `pusher.platform_api_key` = `KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4`
  - [ ] `pusher.signature_secret` 已生成并填写
  - [ ] `ip_change.instance_id` 已填写正确的AWS实例ID
  - [ ] AWS凭证已配置

- [ ] **平台服务器**
  - [ ] `DATA_TRANSFER_MODE` = `push`
  - [ ] `PUSH_MODE_CONFIG['api_key']` = `KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4`
  - [ ] `PUSH_MODE_CONFIG['signature_secret']` 与中转服务器一致
  - [ ] 服务启动成功，端口8000可访问
  - [ ] `/api/push-health` 接口正常

- [ ] **密钥对齐**
  - [ ] C2 API密钥在C2端和中转端一致
  - [ ] 平台 API密钥在中转端和平台端一致
  - [ ] HMAC签名密钥在中转端和平台端一致

---

## 🚀 一键配置脚本（待填写参数）

```bash
#!/bin/bash
# 三服务器配置同步脚本

# ========== 需要填写的参数 ==========
PLATFORM_IP_OR_DOMAIN="YOUR_PLATFORM_IP_OR_DOMAIN"  # [TODO] 填写平台服务器地址
AWS_INSTANCE_ID="i-YOUR_INSTANCE_ID_HERE"           # [TODO] 填写AWS实例ID
AWS_REGION="us-east-2"                              # [TODO] 确认AWS区域

# 生成签名密钥
SIGNATURE_SECRET=$(openssl rand -hex 32)

# 统一的API密钥
C2_API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
PLATFORM_API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"

echo "========================================

"
echo "配置参数："
echo "平台地址: $PLATFORM_IP_OR_DOMAIN"
echo "AWS实例ID: $AWS_INSTANCE_ID"
echo "签名密钥: $SIGNATURE_SECRET"
echo "========================================"

# 导出环境变量
export C2_API_KEY="$C2_API_KEY"
export PLATFORM_URL="http://$PLATFORM_IP_OR_DOMAIN:8000"
export PLATFORM_API_KEY="$PLATFORM_API_KEY"
export SIGNATURE_SECRET="$SIGNATURE_SECRET"
export AWS_INSTANCE_ID="$AWS_INSTANCE_ID"
export AWS_REGION="$AWS_REGION"
export DATA_TRANSFER_MODE="push"
export PUSH_API_KEY="$PLATFORM_API_KEY"
export PUSH_SIGNATURE_SECRET="$SIGNATURE_SECRET"

echo "环境变量已设置！"
echo "请将以上环境变量添加到 ~/.bashrc 或 ~/.profile 中"
```

---

**配置完成后，按照 README_DEPLOYMENT.md 中的步骤启动三个服务器即可！**
