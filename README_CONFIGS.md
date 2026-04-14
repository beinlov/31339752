# 配置文件总览

## 📁 配置文件位置

### C2端服务器（pull_mode/）
```
pull_mode/
├── config.production.json        # 主配置文件 ✅ 已配置
└── .env.example                  # 环境变量示例 ⭐ 新增
```

### 中转服务器（relay/）
```
relay/
├── relay_config.json             # 主配置文件 ⚠️ 需要填写
└── .env.example                  # 环境变量示例 ⭐ 新增
```

### 平台服务器（backend/）
```
backend/
├── config.py                     # 主配置文件 ⚠️ 需要修改
└── .env.push.example             # 推送模式环境变量 ⭐ 新增
```

---

## 📚 配置文档

### 必读文档（按顺序）

1. **[TODO_CONFIG_CHECKLIST.md](TODO_CONFIG_CHECKLIST.md)** ⭐ **从这里开始！**
   - 必须填写的配置项清单
   - 快速配置脚本
   - 配置验证方法

2. **[CONFIG_SYNC_GUIDE.md](CONFIG_SYNC_GUIDE.md)** 📖 详细指南
   - 三服务器配置对齐表
   - 密钥配置说明
   - 常见配置错误
   - 一键配置脚本

3. **[relay/QUICK_START.md](relay/QUICK_START.md)** 🚀 快速开始
   - 5分钟快速部署
   - 验证步骤
   - 常用命令

4. **[relay/README_DEPLOYMENT.md](relay/README_DEPLOYMENT.md)** 📚 完整部署
   - 详细部署步骤
   - 故障排查
   - 性能优化

---

## 🔑 密钥配置一览

### 已对齐的API密钥
```
值: KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4

位置：
✅ pull_mode/config.production.json -> http_server.api_key
✅ relay/relay_config.json -> puller.c2_servers[0].api_key
✅ relay/relay_config.json -> pusher.platform_api_key
✅ backend/config.py -> PUSH_MODE_CONFIG['api_key']
```

### 需要生成的签名密钥
```
生成命令: openssl rand -hex 32

位置：
❌ relay/relay_config.json -> pusher.signature_secret
❌ backend/config.py -> PUSH_MODE_CONFIG['signature_secret']

⚠️ 重要：两者必须完全一致！
```

---

## ✅ 配置填写顺序

### 步骤1：生成签名密钥
```bash
openssl rand -hex 32
# 复制输出的密钥
```

### 步骤2：填写中转服务器配置
```bash
cd /home/spider/31339752/relay
vim relay_config.json

# 修改三个 [TODO] 项：
# 1. "platform_url": "http://YOUR_PLATFORM_IP:8000"
# 2. "signature_secret": "粘贴生成的密钥"
# 3. "instance_id": "i-你的AWS实例ID"
```

### 步骤3：配置平台服务器
```bash
cd /home/spider/31339752/backend

# 使用环境变量（推荐）
cat > .env.push << EOF
export DATA_TRANSFER_MODE="push"
export PUSH_SIGNATURE_SECRET="与中转服务器相同的密钥"
export PUSH_API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
EOF
```

### 步骤4：配置AWS凭证（中转服务器）
```bash
# 在中转服务器上
aws configure
# 或设置环境变量
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
```

---

## 🚀 快速配置（推荐）

### 使用快速配置脚本
```bash
cd /home/spider/31339752

# 参见 TODO_CONFIG_CHECKLIST.md 中的快速配置脚本
# 自动完成所有配置填写
```

---

## 📋 配置验证

### 中转服务器
```bash
cd relay
python3 -c "
from config_loader import load_config, validate_config
config = load_config('relay_config.json')
validate_config(config)
"
```

### 平台服务器
```bash
cd backend
source .env.push
python3 -c "
import config
print('模式:', config.DATA_TRANSFER_MODE)
print('推送:', config.PUSH_MODE_CONFIG['enabled'])
"
```

---

## 📞 需要帮助？

1. **配置问题** → 查看 [CONFIG_SYNC_GUIDE.md](CONFIG_SYNC_GUIDE.md)
2. **部署问题** → 查看 [relay/README_DEPLOYMENT.md](relay/README_DEPLOYMENT.md)
3. **快速开始** → 查看 [relay/QUICK_START.md](relay/QUICK_START.md)
4. **架构说明** → 查看 [relay/ARCHITECTURE.md](relay/ARCHITECTURE.md)
5. **C2兼容性** → 查看 [relay/C2_COMPATIBILITY.md](relay/C2_COMPATIBILITY.md)

---

## 🎯 快速参考

| 需要填写 | 位置 | 说明 |
|---------|------|------|
| ❌ 平台地址 | relay/relay_config.json | pusher.platform_url |
| ❌ 签名密钥 | relay + backend | 两者必须一致 |
| ❌ AWS实例ID | relay/relay_config.json | ip_change.instance_id |
| ⚠️ 传输模式 | backend/config.py | 改为 'push' |
| ⚠️ AWS凭证 | 中转服务器环境变量 | AWS_ACCESS_KEY_ID 等 |

---

**从 [TODO_CONFIG_CHECKLIST.md](TODO_CONFIG_CHECKLIST.md) 开始配置！**
