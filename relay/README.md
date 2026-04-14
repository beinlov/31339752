# 中转服务器 (Relay Server)

僵尸网络数据中转服务 - 从C2端拉取数据并推送到平台服务器，支持动态IP切换

---

## 📋 项目概述

中转服务器作为C2端和平台服务器之间的桥梁，负责：
- 📥 从C2端（通过OpenVPN）定时拉取数据
- 💾 本地SQLite缓存（防止数据丢失）
- 📤 向平台服务器定时推送数据
- 🔄 AWS EIP动态切换（隐藏真实IP）
- 🔐 HMAC签名认证（确保数据安全）

---

## 🏗️ 系统架构

```
┌─────────────┐       ┌──────────────┐       ┌───────────────┐
│ C2服务器     │       │ 中转服务器    │       │ 平台服务器     │
│ (动态IP)    │◄─────►│ (本服务)     │──────►│ (固定IP)      │
│             │ VPN   │              │ HTTPS │               │
└─────────────┘       └──────────────┘       └───────────────┘
                            │
                            │
                      ┌─────┴─────┐
                      │ AWS EIP   │
                      │ 动态切换   │
                      └───────────┘
```

---

## 📁 文件结构

```
relay/
├── relay_service.py           # 主服务协调器
├── data_puller.py             # 从C2拉取数据
├── data_pusher.py             # 向平台推送数据
├── data_storage.py            # SQLite本地缓存
├── changeip.py                # 动态IP切换核心（复用现有代码）
├── ip_changer_adapter.py      # IP切换适配器（封装changeip.py）
├── config_loader.py           # 配置加载器
├── health_monitor.py          # 健康监控脚本
├── relay_config_example.json  # 配置模板
├── relay_config.json          # 实际配置（需创建）
├── start_relay.sh             # 启动脚本
├── relay-server.service       # Systemd服务文件
├── README.md                  # 本文件
└── README_DEPLOYMENT.md       # 详细部署文档
```

---

## ✨ 核心特性

### 1. 数据中转
- ✅ 多C2端点支持
- ✅ 两阶段提交确认
- ✅ 本地缓存（7天）
- ✅ 失败自动重试
- ✅ 批量拉取/推送

### 2. 动态IP切换
- ✅ AWS EIP池管理
- ✅ 定时自动切换
- ✅ OpenVPN自动重连
- ✅ 切换时暂停传输
- ✅ 路由自动配置

### 3. 安全认证
- ✅ HMAC-SHA256签名
- ✅ API密钥认证
- ✅ 时间戳验证
- ✅ Nonce防重放

### 4. 运维监控
- ✅ 健康状态检查
- ✅ 统计信息输出
- ✅ 日志记录
- ✅ Systemd集成

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# Python依赖
pip3 install requests boto3

# 系统依赖
sudo apt install -y openvpn awscli
```

### 2. 配置AWS凭证

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-2"
```

### 3. 配置OpenVPN

```bash
sudo cp your-vpn-config.ovpn /etc/openvpn/client.conf
sudo openvpn --config /etc/openvpn/client.conf --daemon
```

### 4. 配置中转服务

```bash
# 复制配置模板
cp relay_config_example.json relay_config.json

# 编辑配置
vim relay_config.json
```

**关键配置**：
```json
{
  "puller": {
    "c2_servers": [
      {
        "url": "http://10.8.0.1:8888",
        "api_key": "你的C2端API密钥"
      }
    ]
  },
  "pusher": {
    "platform_url": "http://你的平台:8000",
    "platform_api_key": "平台API密钥",
    "signature_secret": "HMAC签名密钥"
  },
  "ip_change": {
    "enabled": true,
    "instance_id": "你的AWS实例ID"
  }
}
```

### 5. 运行服务

```bash
# 测试运行
chmod +x start_relay.sh
./start_relay.sh

# 或作为systemd服务
sudo cp relay-server.service /etc/systemd/system/
sudo systemctl enable relay-server
sudo systemctl start relay-server
```

### 6. 验证运行

```bash
# 查看状态
sudo systemctl status relay-server

# 查看日志
tail -f relay_service.log

# 健康检查
python3 health_monitor.py
```

---

## 📊 监控管理

### 查看服务状态

```bash
# Systemd状态
sudo systemctl status relay-server

# 实时日志
sudo journalctl -u relay-server -f

# 统计信息
tail -f relay_service.log | grep "服务统计"
```

### 健康检查

```bash
# 一次性检查
python3 health_monitor.py

# 循环监控（每5分钟）
python3 health_monitor.py --loop --interval 300
```

### 数据库查询

```bash
# 查看数据统计
sqlite3 relay_cache.db "
SELECT status, COUNT(*) as count 
FROM data_records 
GROUP BY status;
"

# 查看最近数据
sqlite3 relay_cache.db "
SELECT * FROM data_records 
ORDER BY created_at DESC 
LIMIT 10;
"
```

---

## ⚙️ 配置说明

### 环境变量（优先级高于配置文件）

```bash
# C2端配置
export C2_URL="http://10.8.0.1:8888"
export C2_API_KEY="your-c2-api-key"

# 平台配置
export PLATFORM_URL="http://your-platform:8000"
export PLATFORM_API_KEY="your-platform-key"
export SIGNATURE_SECRET="your-signature-secret"

# AWS配置
export AWS_INSTANCE_ID="i-xxxxx"
export IP_CHANGE_ENABLED="true"
export IP_CHANGE_INTERVAL="600"

# 间隔配置
export PULL_INTERVAL="10"
export PUSH_INTERVAL="5"
```

### 配置文件参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `intervals.pull` | 拉取间隔（秒） | 10 |
| `intervals.push` | 推送间隔（秒） | 5 |
| `intervals.cleanup` | 清理间隔（秒） | 3600 |
| `ip_change.change_interval` | IP切换间隔（秒） | 600 |
| `ip_change.max_eips` | 最大EIP数量 | 5 |
| `puller.batch_size` | 拉取批量大小 | 1000 |
| `pusher.batch_size` | 推送批量大小 | 1000 |
| `storage.retention_days` | 数据保留天数 | 7 |

---

## 🔧 常见问题

### Q1: C2服务器连接失败？

检查OpenVPN连接：
```bash
pgrep -f openvpn
ip addr show tun0
ping 10.8.0.1
```

### Q2: 平台推送失败（签名错误）？

确保签名密钥一致：
- 中转服务器：`relay_config.json`中的`signature_secret`
- 平台服务器：`config.py`中的`PUSH_MODE_CONFIG['signature_secret']`

### Q3: IP切换失败？

检查AWS凭证和权限：
```bash
aws configure list
aws ec2 describe-addresses --region us-east-2
```

### Q4: 数据积压（pending过多）？

检查推送状态：
```bash
python3 health_monitor.py
tail -f relay_service.log | grep "推送"
```

### Q5: 磁盘空间不足？

清理过期数据：
```bash
sqlite3 relay_cache.db "
DELETE FROM data_records 
WHERE created_at < datetime('now', '-3 days') 
AND status = 'pushed';
"
sqlite3 relay_cache.db "VACUUM;"
```

---

## 📚 详细文档

**[📖 完整部署文档 (README_DEPLOYMENT.md)](README_DEPLOYMENT.md)**

包含：
- 详细部署步骤
- 配置说明
- 故障排查
- 性能优化
- 安全建议

---

## 🔐 安全注意事项

1. **修改默认密钥**
   ```bash
   # 生成强随机密钥
   openssl rand -hex 32
   ```

2. **限制网络访问**
   ```bash
   # 仅允许必要的出站连接
   sudo ufw allow out to 10.8.0.0/24  # OpenVPN
   sudo ufw allow out to 平台IP port 8000
   ```

3. **定期审计日志**
   ```bash
   grep "❌\|ERROR" relay_service.log
   ```

4. **备份配置和数据**
   ```bash
   tar -czf relay_backup_$(date +%Y%m%d).tar.gz \
       relay_config.json relay_cache.db
   ```

---

## 📈 性能优化建议

### 根据数据量调整间隔

| 数据量 | pull间隔 | push间隔 |
|--------|----------|----------|
| < 1000条/小时 | 30秒 | 60秒 |
| 1000-10000条/小时 | 10秒 | 5秒 |
| > 10000条/小时 | 5秒 | 2秒 |

### 批量大小建议

```json
{
  "puller": {"batch_size": 5000},  // 大数据量
  "pusher": {"batch_size": 5000}
}
```

---

## 📝 更新日志

### v1.0.0 (2025-01-XX)
- ✅ 初始版本发布
- ✅ 支持数据拉取/推送
- ✅ 支持动态IP切换
- ✅ 支持健康监控
- ✅ 支持Systemd服务

---

## 📞 技术支持

遇到问题？请提供：
1. 系统版本：`uname -a`
2. Python版本：`python3 --version`
3. 服务日志：`sudo journalctl -u relay-server -n 200`
4. 健康检查：`python3 health_monitor.py`

---

## 📜 许可证

本项目基于MIT许可证开源

---

**🚀 现在就开始部署吧！**

阅读 [📖 详细部署文档](README_DEPLOYMENT.md) 了解更多信息。
