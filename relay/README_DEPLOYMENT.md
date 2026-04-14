# 中转服务器部署文档

## 目录

- [系统架构](#系统架构)
- [功能特性](#功能特性)
- [系统要求](#系统要求)
- [部署步骤](#部署步骤)
- [配置说明](#配置说明)
- [运行管理](#运行管理)
- [监控运维](#监控运维)
- [故障排查](#故障排查)

---

## 系统架构

```
C2端服务器 (动态IP)
    ↓
OpenVPN隧道 (10.8.0.x)
    ↓
中转服务器 (本服务)
    ├─ 数据拉取模块 → 从C2端拉取数据
    ├─ 本地缓存模块 → SQLite数据库
    ├─ 数据推送模块 → 向平台推送数据
    └─ IP管理模块 → AWS EIP动态切换
         ↓
平台服务器 (固定IP)
```

### 核心模块

1. **relay_service.py** - 主服务协调器
2. **data_puller.py** - C2数据拉取客户端
3. **data_pusher.py** - 平台数据推送客户端
4. **data_storage.py** - 本地SQLite缓存
5. **ip_manager.py** - 动态IP切换管理器
6. **config_loader.py** - 配置加载器
7. **health_monitor.py** - 健康监控脚本

---

## 功能特性

### ✅ 数据中转
- 从C2端定时拉取数据（支持多C2端点）
- 本地SQLite缓存（7天数据保留）
- 向平台定时推送数据
- 两阶段提交确认机制
- 失败重试机制（指数退避）

### ✅ 动态IP切换
- AWS EIP池管理（最多5个IP）
- 定时自动切换IP（默认10分钟）
- OpenVPN自动重连
- IP切换时暂停数据传输
- AWS路由自动配置

### ✅ 安全特性
- HMAC-SHA256签名验证
- API密钥认证
- 时间戳+Nonce防重放攻击

### ✅ 高可靠性
- 本地数据缓存（防止数据丢失）
- 自动故障恢复
- 健康监控
- Systemd服务管理

---

## 系统要求

### 硬件要求
- **CPU**: 2核+
- **内存**: 4GB+
- **磁盘**: 20GB+ （取决于缓存数据量）
- **网络**: 稳定的互联网连接

### 软件要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **Python**: 3.7+
- **OpenVPN**: 2.4+
- **AWS CLI**: 配置好的AWS凭证

### Python依赖
```bash
pip3 install requests boto3
```

### AWS权限要求
IAM用户需要以下权限：
- `ec2:AllocateAddress`
- `ec2:ReleaseAddress`
- `ec2:AssociateAddress`
- `ec2:DisassociateAddress`
- `ec2:DescribeAddresses`
- `ec2:DescribeInstances`
- `ec2:DescribeAccountAttributes`

---

## 部署步骤

### 1. 准备工作

```bash
# 创建工作目录
mkdir -p /opt/relay-server
cd /opt/relay-server

# 上传代码文件到此目录
# 包括: relay文件夹中的所有文件
```

### 2. 安装依赖

```bash
# 安装Python3和pip
sudo apt update
sudo apt install -y python3 python3-pip

# 安装Python依赖
pip3 install requests boto3

# 安装OpenVPN（如果未安装）
sudo apt install -y openvpn

# 安装AWS CLI（用于测试AWS凭证）
sudo apt install -y awscli
```

### 3. 配置AWS凭证

```bash
# 方式1：使用AWS CLI配置
aws configure
# 输入Access Key ID和Secret Access Key

# 方式2：设置环境变量
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_DEFAULT_REGION="us-east-2"

# 验证AWS连接
aws ec2 describe-instances --region us-east-2
```

### 4. 配置OpenVPN

```bash
# 将OpenVPN配置文件放到 /etc/openvpn/client.conf
sudo cp your-vpn-config.ovpn /etc/openvpn/client.conf

# 测试OpenVPN连接
sudo openvpn --config /etc/openvpn/client.conf --daemon

# 检查连接
ip addr show tun0
ping 10.8.0.1  # C2端OpenVPN IP
```

### 5. 配置中转服务

```bash
# 进入relay目录
cd /opt/relay-server/relay

# 复制配置模板
cp relay_config_example.json relay_config.json

# 编辑配置文件
vim relay_config.json
```

**关键配置项**：

```json
{
  "puller": {
    "c2_servers": [
      {
        "id": "c2-server-1",
        "url": "http://10.8.0.1:8888",
        "api_key": "你的C2端API密钥",
        "enabled": true
      }
    ]
  },
  "pusher": {
    "platform_url": "http://你的平台服务器:8000",
    "platform_api_key": "你的平台API密钥",
    "signature_secret": "与平台一致的签名密钥"
  },
  "ip_change": {
    "enabled": true,
    "instance_id": "你的AWS实例ID",
    "change_interval": 600
  }
}
```

### 6. 测试运行

```bash
# 给启动脚本执行权限
chmod +x start_relay.sh

# 测试运行
./start_relay.sh

# 观察日志输出，确认：
# ✓ 配置加载成功
# ✓ C2服务器连接成功
# ✓ 平台服务器连接成功
# ✓ IP管理器启动（如果启用）

# Ctrl+C 停止测试
```

### 7. 配置Systemd服务

```bash
# 编辑服务文件，修改路径
vim relay-server.service

# 将User改为实际用户
# 将WorkingDirectory和ExecStart改为实际路径

# 复制服务文件到systemd目录
sudo cp relay-server.service /etc/systemd/system/

# 重新加载systemd
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable relay-server

# 启动服务
sudo systemctl start relay-server

# 查看状态
sudo systemctl status relay-server
```

### 8. 验证部署

```bash
# 查看服务状态
sudo systemctl status relay-server

# 查看日志
sudo journalctl -u relay-server -f

# 检查数据库
sqlite3 relay_cache.db "SELECT COUNT(*) FROM data_records;"

# 运行健康检查
python3 health_monitor.py
```

---

## 配置说明

### 配置文件 (relay_config.json)

#### 存储配置
```json
{
  "storage": {
    "db_file": "./relay_cache.db",   // SQLite数据库文件路径
    "retention_days": 7                // 数据保留天数
  }
}
```

#### 拉取配置
```json
{
  "puller": {
    "c2_servers": [
      {
        "id": "c2-server-1",           // C2端标识
        "url": "http://10.8.0.1:8888", // C2端URL（OpenVPN内网）
        "api_key": "your-c2-api-key",  // C2端API密钥
        "enabled": true                 // 是否启用
      }
    ],
    "batch_size": 1000,                // 每次拉取数量
    "timeout": 30,                     // 请求超时（秒）
    "use_two_phase_commit": true       // 启用两阶段提交
  }
}
```

#### 推送配置
```json
{
  "pusher": {
    "platform_url": "http://your-platform:8000",  // 平台服务器URL
    "platform_api_key": "your-platform-key",      // 平台API密钥
    "signature_secret": "your-signature-secret",   // HMAC签名密钥
    "relay_id": "relay-001",                       // 中转服务器ID
    "batch_size": 1000,                            // 每次推送数量
    "timeout": 30,                                 // 请求超时（秒）
    "max_retries": 3,                              // 最大重试次数
    "retry_delay": 2                               // 重试延迟基数（秒）
  }
}
```

#### 时间间隔配置
```json
{
  "intervals": {
    "pull": 10,      // 拉取间隔（秒）
    "push": 5,       // 推送间隔（秒）
    "cleanup": 3600, // 清理间隔（秒）
    "retry": 300     // 重试间隔（秒）
  }
}
```

#### IP切换配置
```json
{
  "ip_change": {
    "enabled": true,                          // 是否启用IP切换
    "change_interval": 600,                   // 切换间隔（秒）
    "max_eips": 5,                            // 最大EIP数量
    "aws_region": "us-east-2",                // AWS区域
    "instance_id": "i-0edf3378b3cdc3d49",    // AWS实例ID
    "openvpn_config": "/etc/openvpn/client.conf", // OpenVPN配置文件
    "resume_delay": 30                        // IP切换后恢复延迟（秒）
  }
}
```

### 环境变量（优先级高于配置文件）

```bash
# C2端配置
export C2_URL="http://10.8.0.1:8888"
export C2_API_KEY="your-c2-api-key"

# 平台配置
export PLATFORM_URL="http://your-platform:8000"
export PLATFORM_API_KEY="your-platform-key"
export SIGNATURE_SECRET="your-signature-secret"
export RELAY_ID="relay-001"

# AWS配置
export AWS_REGION="us-east-2"
export AWS_INSTANCE_ID="i-xxxxx"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"

# IP切换配置
export IP_CHANGE_ENABLED="true"
export IP_CHANGE_INTERVAL="600"

# 间隔配置
export PULL_INTERVAL="10"
export PUSH_INTERVAL="5"
```

---

## 运行管理

### 启动服务

```bash
# 使用systemd
sudo systemctl start relay-server

# 或使用启动脚本
./start_relay.sh
```

### 停止服务

```bash
# 使用systemd
sudo systemctl stop relay-server

# 或发送SIGTERM信号
pkill -f relay_service.py
```

### 重启服务

```bash
sudo systemctl restart relay-server
```

### 查看状态

```bash
# 服务状态
sudo systemctl status relay-server

# 实时日志
sudo journalctl -u relay-server -f

# 查看最近100行日志
sudo journalctl -u relay-server -n 100

# 查看今天的日志
sudo journalctl -u relay-server --since today
```

### 查看统计

```bash
# 查看日志文件统计
tail -f relay_service.log | grep "服务统计"

# 查看数据库统计
sqlite3 relay_cache.db <<EOF
SELECT 
    status,
    COUNT(*) as count,
    MIN(created_at) as oldest,
    MAX(created_at) as newest
FROM data_records
GROUP BY status;
EOF
```

---

## 监控运维

### 健康检查

```bash
# 运行一次健康检查
python3 health_monitor.py

# 循环运行（每5分钟检查一次）
python3 health_monitor.py --loop --interval 300
```

### 监控指标

1. **数据传输**
   - 每小时拉取量
   - 每小时推送量
   - 失败率
   - pending数据积压

2. **服务健康**
   - C2服务器连通性
   - 平台服务器连通性
   - OpenVPN连接状态
   - 磁盘空间

3. **IP切换**
   - 切换次数
   - 切换间隔
   - 当前IP

### 日志管理

```bash
# 日志文件位置
# - relay_service.log: 主服务日志
# - /var/log/syslog: OpenVPN日志
# - journalctl: systemd服务日志

# 日志轮转配置 /etc/logrotate.d/relay-server
/opt/relay-server/relay/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 0644 relay relay
}
```

### 数据库维护

```bash
# 查看数据库大小
du -h relay_cache.db

# 清理过期数据（自动，每小时运行一次）
# 手动触发可执行SQL:
sqlite3 relay_cache.db "DELETE FROM data_records WHERE created_at < datetime('now', '-7 days') AND status = 'pushed';"

# 优化数据库
sqlite3 relay_cache.db "VACUUM;"
```

---

## 故障排查

### 问题1：C2服务器连接失败

**症状**：日志显示 "C2连接失败" 或 "OpenVPN可能未连接"

**排查步骤**：
```bash
# 1. 检查OpenVPN状态
sudo systemctl status openvpn@client
pgrep -f openvpn

# 2. 检查tun0接口
ip addr show tun0

# 3. 测试C2端连通性
ping 10.8.0.1
curl http://10.8.0.1:8888/health

# 4. 重启OpenVPN
sudo systemctl restart openvpn@client
```

### 问题2：平台服务器推送失败

**症状**：日志显示 "平台推送失败" 或 "签名验证失败"

**排查步骤**：
```bash
# 1. 检查平台连通性
curl http://your-platform:8000/api/push-health

# 2. 检查签名密钥是否一致
# 对比relay_config.json中的signature_secret
# 与平台config.py中的PUSH_MODE_CONFIG['signature_secret']

# 3. 检查API密钥
# 对比platform_api_key与平台的PUSH_MODE_CONFIG['api_key']

# 4. 查看详细错误
tail -f relay_service.log | grep "推送"
```

### 问题3：IP切换失败

**症状**：日志显示 "IP切换异常" 或 "AWS API不可达"

**排查步骤**：
```bash
# 1. 检查AWS凭证
aws configure list
aws ec2 describe-instances --region us-east-2

# 2. 检查AWS权限
aws ec2 describe-addresses --region us-east-2

# 3. 检查EIP配额
aws ec2 describe-account-attributes \
    --attribute-names max-elastic-ips \
    --region us-east-2

# 4. 查看IP管理器日志
tail -f relay_service.log | grep "IP"
```

### 问题4：数据积压（pending过多）

**症状**：数据库中pending状态的记录持续增长

**排查步骤**：
```bash
# 1. 检查pending数量
sqlite3 relay_cache.db "SELECT COUNT(*) FROM data_records WHERE status = 'pending';"

# 2. 检查平台推送是否正常
python3 health_monitor.py

# 3. 查看推送错误
tail -f relay_service.log | grep "推送失败"

# 4. 手动重试失败数据
sqlite3 relay_cache.db "UPDATE data_records SET status = 'pending', retry_count = 0 WHERE status = 'failed';"
```

### 问题5：磁盘空间不足

**症状**：磁盘使用率过高

**解决方案**：
```bash
# 1. 检查磁盘使用
df -h

# 2. 检查数据库大小
du -h relay_cache.db

# 3. 手动清理过期数据
sqlite3 relay_cache.db "DELETE FROM data_records WHERE created_at < datetime('now', '-3 days') AND status = 'pushed';"

# 4. 优化数据库
sqlite3 relay_cache.db "VACUUM;"

# 5. 清理日志
sudo logrotate -f /etc/logrotate.d/relay-server
```

---

## 性能优化

### 调整拉取/推送间隔

根据数据量调整：
- **小数据量**（< 1000条/小时）: pull=30, push=60
- **中数据量**（1000-10000条/小时）: pull=10, push=5（默认）
- **大数据量**（> 10000条/小时）: pull=5, push=2

### 调整批量大小

```json
{
  "puller": {
    "batch_size": 5000  // 增加批量大小
  },
  "pusher": {
    "batch_size": 5000  // 增加批量大小
  }
}
```

### 数据库优化

```bash
# 定期VACUUM
sqlite3 relay_cache.db "VACUUM;"

# 重建索引
sqlite3 relay_cache.db "REINDEX;"
```

---

## 安全建议

1. **更改默认密钥**
   - 修改`signature_secret`为强随机密钥
   - 修改`platform_api_key`
   - 定期轮换密钥

2. **限制网络访问**
   - 仅允许必要的出站连接
   - 配置防火墙规则

3. **日志审计**
   - 定期检查异常日志
   - 监控失败率

4. **备份重要数据**
   - 定期备份`relay_cache.db`
   - 保存配置文件

---

## 联系支持

如遇到问题，请提供以下信息：
1. 系统版本：`uname -a`
2. Python版本：`python3 --version`
3. 服务日志：`sudo journalctl -u relay-server -n 200`
4. 健康检查结果：`python3 health_monitor.py`
5. 配置文件：`relay_config.json`（隐藏敏感信息）
