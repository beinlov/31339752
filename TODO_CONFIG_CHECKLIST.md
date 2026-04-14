# ✅ 配置填写清单

## 🎯 必须填写的配置项

### 1️⃣ 中转服务器 (relay/relay_config.json)

```json
{
  "pusher": {
    "platform_url": "http://YOUR_PLATFORM_IP_OR_DOMAIN:8000",  // ❌ [必填] 平台服务器地址
    "signature_secret": "CHANGE_ME_..."  // ⚠️ [必填] 生成强密钥
  },
  
  "ip_change": {
    "instance_id": "i-YOUR_INSTANCE_ID_HERE"  // ❌ [必填] AWS实例ID
  }
}
```

**填写方法**：
```bash
cd /home/spider/31339752/relay

# 1. 获取平台服务器IP（或域名）
# [TODO] 你需要知道平台服务器的公网地址
PLATFORM_IP="填写实际IP"

# 2. 生成签名密钥
SIGNATURE_SECRET=$(openssl rand -hex 32)
echo "签名密钥: $SIGNATURE_SECRET"

# 3. 获取AWS实例ID
aws ec2 describe-instances --region us-east-2 \
    --query 'Reservations[*].Instances[*].[InstanceId,PublicIpAddress]' \
    --output table
# 记录你的实例ID（格式：i-xxxxxxxxxxxxxxxxx）

# 4. 编辑配置文件
vim relay_config.json
# 替换以下内容：
#   "YOUR_PLATFORM_IP_OR_DOMAIN" → 实际IP或域名
#   "CHANGE_ME_..." → 生成的签名密钥
#   "i-YOUR_INSTANCE_ID_HERE" → 实际实例ID
```

---

### 2️⃣ 平台服务器 (backend/config.py)

```python
# 第391行
DATA_TRANSFER_MODE = 'push'  // ⚠️ [必改] 改为 'push'

# 第400行
'signature_secret': '...'  // ⚠️ [必填] 与中转服务器一致
```

**填写方法**：
```bash
cd /home/spider/31339752/backend

# 方式1：使用环境变量（推荐）
cat > .env << 'EOF'
export DATA_TRANSFER_MODE="push"
export PUSH_SIGNATURE_SECRET="与中转服务器一致的密钥"
export PUSH_API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
EOF

# 使用
source .env
python3 main.py

# 方式2：直接修改config.py
vim config.py
# 第391行改为：DATA_TRANSFER_MODE = os.environ.get('DATA_TRANSFER_MODE', 'push')
# 第400行改为：'signature_secret': os.environ.get('PUSH_SIGNATURE_SECRET', '与中转服务器一致的密钥'),
```

---

### 3️⃣ AWS凭证配置 (中转服务器)

```bash
# 在中转服务器上配置
export AWS_ACCESS_KEY_ID="your-access-key-id"  // ❌ [必填]
export AWS_SECRET_ACCESS_KEY="your-secret-key"  // ❌ [必填]
export AWS_REGION="us-east-2"  // ✅ [确认] 确认区域
```

**填写方法**：
```bash
# 方式1：AWS CLI配置
aws configure
# 输入Access Key ID
# 输入Secret Access Key
# 输入默认区域：us-east-2

# 方式2：环境变量
cat >> ~/.bashrc << 'EOF'
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-2"
EOF
source ~/.bashrc

# 验证
aws ec2 describe-instances --region us-east-2
```

---

## 📋 可选检查项（已有默认值）

### C2端 (pull_mode/config.production.json)

```json
{
  "botnet": {
    "botnet_type": "utg_q_008"  // ✅ [检查] 确认是否正确
  },
  "log_sources": {
    "online": {
      "path": "/home/irc_server/logs/user_activity.log"  // ✅ [检查] 确认路径存在
    },
    "cleanup": {
      "path": "/home/irc_server/logs/reports.db"  // ✅ [检查] 确认路径存在
    }
  }
}
```

**检查方法**：
```bash
cd /home/spider/31339752/pull_mode

# 1. 检查botnet_type
grep botnet_type config.production.json

# 2. 检查日志文件是否存在
ls -lh /home/irc_server/logs/user_activity.log
ls -lh /home/irc_server/logs/reports.db
```

---

## 🔐 密钥对齐检查

### 统一的API密钥值

| 位置 | 值 | 状态 |
|------|-----|------|
| C2端 | `KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4` | ✅ 已配置 |
| 中转→C2 | `KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4` | ✅ 已对齐 |
| 中转→平台 | `KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4` | ✅ 已对齐 |
| 平台端 | `KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4` | ✅ 已对齐 |

### HMAC签名密钥（需要生成）

| 位置 | 值 | 状态 |
|------|-----|------|
| 中转服务器 | `[待填写]` | ❌ 待生成 |
| 平台服务器 | `[待填写]` | ❌ 待生成 |

**⚠️ 重要：两者必须完全一致！**

**生成命令**：
```bash
openssl rand -hex 32
```

---

## 📝 快速填写脚本

```bash
#!/bin/bash
# 快速配置脚本 - 自动填写配置项

echo "========================================="
echo "三服务器快速配置向导"
echo "========================================="

# 1. 输入平台服务器地址
read -p "请输入平台服务器IP或域名: " PLATFORM_IP
echo "平台地址: http://$PLATFORM_IP:8000"

# 2. 生成签名密钥
echo ""
echo "正在生成签名密钥..."
SIGNATURE_SECRET=$(openssl rand -hex 32)
echo "签名密钥: $SIGNATURE_SECRET"

# 3. 获取AWS实例ID
echo ""
echo "正在获取AWS实例信息..."
echo "请选择你的AWS实例ID："
aws ec2 describe-instances --region us-east-2 \
    --query 'Reservations[*].Instances[*].[InstanceId,PublicIpAddress,State.Name]' \
    --output table

read -p "请输入实例ID (格式: i-xxxxxxxxxxxxxxxxx): " INSTANCE_ID

# 4. 确认信息
echo ""
echo "========================================="
echo "请确认以下配置："
echo "========================================="
echo "平台地址: http://$PLATFORM_IP:8000"
echo "签名密钥: $SIGNATURE_SECRET"
echo "实例ID: $INSTANCE_ID"
echo "API密钥: KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
echo "========================================="
read -p "确认无误？(yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "已取消配置"
    exit 1
fi

# 5. 生成配置文件
echo ""
echo "正在生成配置..."

# 中转服务器环境变量
cat > /home/spider/31339752/relay/.env << EOF
export C2_URL="http://10.8.0.1:8888"
export C2_API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
export PLATFORM_URL="http://$PLATFORM_IP:8000"
export PLATFORM_API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
export SIGNATURE_SECRET="$SIGNATURE_SECRET"
export AWS_INSTANCE_ID="$INSTANCE_ID"
export AWS_REGION="us-east-2"
export IP_CHANGE_ENABLED="true"
EOF

# 平台服务器环境变量
cat > /home/spider/31339752/backend/.env.push << EOF
export DATA_TRANSFER_MODE="push"
export PUSH_API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
export PUSH_SIGNATURE_SECRET="$SIGNATURE_SECRET"
EOF

# 更新中转服务器配置文件
cd /home/spider/31339752/relay
sed -i "s|YOUR_PLATFORM_IP_OR_DOMAIN|$PLATFORM_IP|g" relay_config.json
sed -i "s|CHANGE_ME_IN_PRODUCTION_use_strong_random_key_here|$SIGNATURE_SECRET|g" relay_config.json
sed -i "s|i-YOUR_INSTANCE_ID_HERE|$INSTANCE_ID|g" relay_config.json

echo ""
echo "✅ 配置完成！"
echo ""
echo "生成的文件："
echo "  - /home/spider/31339752/relay/.env"
echo "  - /home/spider/31339752/backend/.env.push"
echo "  - /home/spider/31339752/relay/relay_config.json (已更新)"
echo ""
echo "下一步："
echo "1. 在中转服务器上运行: cd relay && source .env && ./start_relay.sh"
echo "2. 在平台服务器上运行: cd backend && source .env.push && python3 main.py"
echo ""
```

**使用方法**：
```bash
# 保存为脚本
cat > /home/spider/31339752/quick_config.sh << 'EOF'
[粘贴上面的脚本内容]
EOF

# 添加执行权限
chmod +x /home/spider/31339752/quick_config.sh

# 运行
cd /home/spider/31339752
./quick_config.sh
```

---

## ✅ 配置完成后验证

### 1. 中转服务器验证
```bash
cd /home/spider/31339752/relay

# 加载环境变量
source .env

# 验证配置
python3 -c "
from config_loader import load_config
config = load_config('relay_config.json')
print('C2 URL:', config['puller']['c2_servers'][0]['url'])
print('Platform URL:', config['pusher']['platform_url'])
print('Instance ID:', config['ip_change']['instance_id'])
"

# 启动服务
./start_relay.sh
```

### 2. 平台服务器验证
```bash
cd /home/spider/31339752/backend

# 加载环境变量
source .env.push

# 验证配置
python3 -c "
import config
print('传输模式:', config.DATA_TRANSFER_MODE)
print('推送启用:', config.PUSH_MODE_CONFIG['enabled'])
"

# 启动服务
python3 main.py
```

### 3. 连通性测试
```bash
# 在中转服务器上测试
# C2端连通性（需要先启动C2和OpenVPN）
curl -H "X-API-Key: KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4" \
     http://10.8.0.1:8888/health

# 平台端连通性
curl http://$PLATFORM_IP:8000/api/push-health
```

---

## 📚 相关文档

- [CONFIG_SYNC_GUIDE.md](CONFIG_SYNC_GUIDE.md) - 详细的配置同步指南
- [relay/README_DEPLOYMENT.md](relay/README_DEPLOYMENT.md) - 中转服务器部署文档
- [relay/QUICK_START.md](relay/QUICK_START.md) - 快速开始指南

---

## 🎯 总结

**必须填写的配置项（3个）**：
1. ❌ 平台服务器地址 (`relay_config.json` → `pusher.platform_url`)
2. ❌ HMAC签名密钥 (中转和平台必须一致)
3. ❌ AWS实例ID (`relay_config.json` → `ip_change.instance_id`)

**需要配置的环境变量**：
- 中转服务器：AWS访问密钥
- 平台服务器：`DATA_TRANSFER_MODE=push`

**已自动对齐的配置**：
- ✅ C2端API密钥
- ✅ 平台端API密钥
- ✅ 其他默认配置

**使用快速配置脚本可以自动完成所有配置填写！**
