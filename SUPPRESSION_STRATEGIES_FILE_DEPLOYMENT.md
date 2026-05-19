# 抑制阻断策略部署指南（文件推送方式）

## ? 概述

本文档说明如何部署IP黑名单、域名黑名单、丢包策略的文件推送版本。

### 核心变化

**之前**: 远程设备主动拉取平台数据（需要暴露平台IP）
```
远程设备 ──HTTP请求──> 平台大屏
```

**现在**: 平台主动推送配置到远程设备（平台IP不暴露）
```
平台大屏 ──SSH推送文件──> 远程设备 ──文件监控──> 自动应用
```

---

## ? 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│              平台大屏服务器                                   │
│  - 管理员添加/修改黑名单                                      │
│  - 点击"推送"按钮                                            │
│  - 通过SSH写入配置文件到远程设备                              │
└────────────────────┬────────────────────────────────────────┘
                    │ SSH/SFTP 推送配置文件
                    ▼
┌─────────────────────────────────────────────────────────────┐
│            远程设备（网关/DNS服务器）                         │
│  - 配置目录: /opt/suppression_config/                       │
│  - 文件监控脚本持续运行                                       │
│  - 检测到文件变化 → 自动应用到iptables/dnsmasq              │
└─────────────────────────────────────────────────────────────┘
```

---

## ? 部署准备

### 1. 平台大屏端

**配置SSH连接信息** - 编辑 `/home/spider/31339752/backend/config.py`:

```python
RELAY_CONFIG = {
    'host': '远程设备IP',           # 网关或DNS服务器的IP
    'port': 22,                      # SSH端口
    'username': 'admin',             # SSH用户名
    'password': 'password',          # SSH密码
    'share_path': '/opt/suppression_config',  # 远程配置目录
    'enabled': True
}
```

**安装依赖**:
```bash
pip3 install paramiko
```

### 2. 远程设备端

**系统要求**:
- Ubuntu/Debian Linux (推荐)
- CentOS/RHEL (支持)
- 需要root权限

**安装依赖**:
```bash
# 通用依赖
sudo apt-get install -y python3 python3-pip ipset iptables

# Python依赖
pip3 install watchdog

# DNS服务器还需要安装dnsmasq
sudo apt-get install -y dnsmasq
```

---

## ? 部署步骤

### 方案一：IP黑名单（部署在网关设备）

#### 1. 创建配置目录

```bash
# SSH登录到网关设备
ssh admin@网关IP

# 创建配置目录
sudo mkdir -p /opt/suppression_config
sudo chmod 755 /opt/suppression_config
```

#### 2. 复制脚本文件

**从平台服务器复制**:
```bash
# 在平台服务器执行
cd /home/spider/31339752/backend/suppression_scripts

scp gateway_black_white_file.py admin@网关IP:/opt/
```

#### 3. 启动文件监控服务

**方式A: 前台运行（测试用）**:
```bash
# 在网关设备上
cd /opt
sudo python3 gateway_black_white_file.py --config-path /opt/suppression_config
```

**期望输出**:
```
正在初始化IP黑名单管控环境...
IP黑名单集合 blacklist_set 已挂载到 iptables
============================================================
IP黑名单自动同步脚本已启动（文件监控模式）
配置目录: /opt/suppression_config
配置文件: /opt/suppression_config/ip_blacklist.txt
ipset集合: blacklist_set
============================================================
```

**方式B: systemd服务（生产环境推荐）**:

创建服务文件 `/etc/systemd/system/ip-blacklist.service`:
```ini
[Unit]
Description=IP Blacklist File Monitor Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt
ExecStart=/usr/bin/python3 /opt/gateway_black_white_file.py --config-path /opt/suppression_config
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ip-blacklist
sudo systemctl start ip-blacklist
sudo systemctl status ip-blacklist
```

#### 4. 从平台推送配置

**方法1: 在平台大屏界面操作**
1. 登录平台大屏
2. 进入 **抑制阻断策略** → **IP黑名单**
3. 添加需要屏蔽的IP地址
4. 点击 **? 推送到网关设备** 按钮

**方法2: 使用API**
```bash
curl -X POST http://平台IP:8000/api/suppression/config-push/ip-blacklist
```

#### 5. 验证

**查看网关设备日志**:
```bash
# 查看服务日志
sudo journalctl -u ip-blacklist -f

# 期望看到:
[10:30:00] 检测到配置文件更新: /opt/suppression_config/ip_blacklist.txt
[10:30:00] IP黑名单已更新，当前包含 5 个IP
```

**检查iptables规则**:
```bash
sudo ipset list blacklist_set
# 应该看到推送的IP列表

sudo iptables -L FORWARD -n
# 应该看到包含blacklist_set的规则
```

---

### 方案二：域名黑名单（部署在DNS服务器）

#### 1. 创建配置目录

```bash
ssh admin@DNS服务器IP
sudo mkdir -p /opt/suppression_config
sudo mkdir -p /etc/dnsmasq.d
sudo chmod 755 /opt/suppression_config
```

#### 2. 复制脚本文件

```bash
# 从平台服务器
cd /home/spider/31339752/backend/suppression_scripts
scp dns_black_white_file.py admin@DNS服务器IP:/opt/
```

#### 3. 配置dnsmasq

确保dnsmasq会加载 `/etc/dnsmasq.d/` 目录的配置:
```bash
# 检查/etc/dnsmasq.conf中是否有以下行
grep "conf-dir=/etc/dnsmasq.d" /etc/dnsmasq.conf

# 如果没有，添加
echo "conf-dir=/etc/dnsmasq.d" | sudo tee -a /etc/dnsmasq.conf
```

#### 4. 启动文件监控服务

创建服务文件 `/etc/systemd/system/dns-blacklist.service`:
```ini
[Unit]
Description=DNS Blacklist File Monitor Service
After=network.target dnsmasq.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt
ExecStart=/usr/bin/python3 /opt/dns_black_white_file.py --config-path /opt/suppression_config
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dns-blacklist
sudo systemctl start dns-blacklist
sudo systemctl status dns-blacklist
```

#### 5. 从平台推送配置

在平台大屏:
1. 进入 **抑制阻断策略** → **域名黑名单**
2. 添加需要屏蔽的域名
3. 点击 **? 推送到DNS服务器** 按钮

#### 6. 验证

**查看日志**:
```bash
sudo journalctl -u dns-blacklist -f

# 期望看到:
[10:30:00] 检测到配置文件更新: /opt/suppression_config/domain_blacklist.txt
[10:30:00] 检测到更新，正在重启 dnsmasq...
[10:30:01] 域名黑名单已更新，当前包含 10 个域名
```

**检查dnsmasq配置**:
```bash
cat /etc/dnsmasq.d/dns_blacklist.conf

# 应该看到类似:
# address=/malware.com/0.0.0.0
# address=/botnet.net/0.0.0.0
```

**测试DNS解析**:
```bash
nslookup malware.com localhost
# 应该返回 0.0.0.0
```

---

### 方案三：丢包策略（部署在网关设备）

#### 1. 创建配置目录

```bash
ssh admin@网关IP
sudo mkdir -p /opt/suppression_config
```

#### 2. 复制脚本文件

```bash
# 从平台服务器
cd /home/spider/31339752/backend/suppression_scripts
scp gateway_packet_loss_file.py admin@网关IP:/opt/
```

#### 3. 启动文件监控服务

创建服务文件 `/etc/systemd/system/packet-loss.service`:
```ini
[Unit]
Description=Packet Loss Policy File Monitor Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt
ExecStart=/usr/bin/python3 /opt/gateway_packet_loss_file.py --config-path /opt/suppression_config
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动:
```bash
sudo systemctl daemon-reload
sudo systemctl enable packet-loss
sudo systemctl start packet-loss
sudo systemctl status packet-loss
```

#### 4. 从平台推送配置

在平台大屏:
1. 进入 **抑制阻断策略** → **丢包策略**
2. 添加需要设置丢包的IP和丢包率
3. 点击 **? 推送到网关设备** 按钮

#### 5. 验证

**查看日志**:
```bash
sudo journalctl -u packet-loss -f

# 期望看到:
[10:30:00] 检测到配置文件更新: /opt/suppression_config/packet_loss.json
[10:30:00] 激活规则: 192.168.1.100 (丢包率: 30.0%)
[10:30:00] 丢包策略已更新，当前包含 3 条规则
```

**检查iptables规则**:
```bash
sudo iptables -L INTERMITTENT_DROP -n
# 应该看到带有statistic --probability的规则
```

---

## ? 配置文件格式

### IP黑名单 (`ip_blacklist.txt`)
```
# IP Blacklist - Auto-generated by platform
# Total IPs: 3
192.168.1.100
10.0.0.50
172.16.0.10
```

### 域名黑名单 (`domain_blacklist.txt`)
```
# Domain Blacklist - Auto-generated by platform
# Total Domains: 2
malware.com
botnet.net
```

### 丢包策略 (`packet_loss.json`)
```json
{
  "192.168.1.100": 0.3,
  "10.0.0.50": 0.5,
  "172.16.0.10": 0.2
}
```

---

## ? API接口说明

### 手动推送单个策略

**IP黑名单**:
```http
POST /api/suppression/config-push/ip-blacklist

Response:
{
  "status": "success",
  "message": "IP黑名单已推送到远程设备，共5条",
  "count": 5
}
```

**域名黑名单**:
```http
POST /api/suppression/config-push/domain-blacklist

Response:
{
  "status": "success",
  "message": "域名黑名单已推送到远程设备，共10条",
  "count": 10
}
```

**丢包策略**:
```http
POST /api/suppression/config-push/packet-loss

Response:
{
  "status": "success",
  "message": "丢包策略已推送到远程设备，共3条",
  "count": 3
}
```

### 一键推送所有策略

```http
POST /api/suppression/config-push/all

Response:
{
  "status": "success",
  "message": "配置推送完成",
  "details": {
    "ip_blacklist": {"success": true, "count": 5},
    "domain_blacklist": {"success": true, "count": 10},
    "packet_loss": {"success": true, "count": 3}
  }
}
```

### 健康检查

```http
GET /api/suppression/config-push/health

Response:
{
  "status": "healthy",
  "message": "配置推送服务正常",
  "target": "192.168.1.100:22",
  "config_path": "/opt/suppression_config"
}
```

---

## ? 故障排查

### 问题1: 平台无法推送配置

**症状**: 点击推送按钮后报错 "推送失败"

**排查步骤**:
```bash
# 1. 测试SSH连接
ssh admin@远程设备IP

# 2. 检查平台日志
tail -f /home/spider/31339752/logs/backend.log | grep "推送"

# 3. 测试健康检查API
curl http://localhost:8000/api/suppression/config-push/health
```

**解决方案**:
- 确认远程设备SSH服务正常
- 检查防火墙是否开放22端口
- 验证config.py中的SSH凭据正确

---

### 问题2: 配置文件未被应用

**症状**: 配置推送成功，但iptables/dnsmasq未生效

**排查步骤**:
```bash
# 1. 检查配置文件是否存在
ls -la /opt/suppression_config/

# 2. 查看服务日志
sudo journalctl -u ip-blacklist -f
sudo journalctl -u dns-blacklist -f
sudo journalctl -u packet-loss -f

# 3. 检查服务是否运行
sudo systemctl status ip-blacklist
sudo systemctl status dns-blacklist
sudo systemctl status packet-loss
```

**解决方案**:
- 重启对应的服务
- 检查脚本是否有权限读取配置文件
- 查看服务日志中的错误信息

---

### 问题3: watchdog未检测到文件变化

**症状**: 手动修改配置文件不触发更新

**排查步骤**:
```bash
# 1. 检查watchdog是否安装
python3 -c "from watchdog.observers import Observer; print('OK')"

# 2. 手动测试脚本
sudo python3 /opt/gateway_black_white_file.py --config-path /opt/suppression_config

# 3. 手动创建测试文件
echo "192.168.1.1" > /opt/suppression_config/ip_blacklist.txt
```

**解决方案**:
- 安装watchdog: `pip3 install watchdog`
- 确认配置目录权限正确
- 检查脚本的文件监听逻辑

---

## ? 监控和维护

### 日志位置

**平台大屏**:
```
/home/spider/31339752/logs/backend.log
```

**远程设备**:
```bash
# 查看服务日志
sudo journalctl -u ip-blacklist -f
sudo journalctl -u dns-blacklist -f
sudo journalctl -u packet-loss -f
```

### 定期检查

建议设置cron任务定期检查服务状态:
```bash
# 编辑crontab
crontab -e

# 添加每小时检查
0 * * * * systemctl is-active --quiet ip-blacklist || systemctl start ip-blacklist
```

---

## ? 安全建议

### 1. 使用SSH密钥认证

```bash
# 在平台服务器生成密钥
ssh-keygen -t rsa -b 4096 -f ~/.ssh/relay_key

# 复制公钥到远程设备
ssh-copy-id -i ~/.ssh/relay_key.pub admin@远程设备IP
```

修改 `config.py`:
```python
RELAY_CONFIG = {
    'host': '远程设备IP',
    'username': 'admin',
    'key_filename': '/root/.ssh/relay_key',
    'password': None
}
```

### 2. 限制SSH访问

```bash
# 在远程设备上
sudo ufw allow from 平台IP to any port 22
sudo ufw enable
```

### 3. 配置文件权限

```bash
sudo chmod 700 /opt/suppression_config
sudo chmod 600 /opt/suppression_config/*.txt
sudo chmod 600 /opt/suppression_config/*.json
```

---

## ? 部署检查清单

### 平台大屏端
- [ ] 修改 `backend/config.py` 中的 `RELAY_CONFIG`
- [ ] 安装 `paramiko`: `pip3 install paramiko`
- [ ] 测试SSH连接到远程设备
- [ ] 启动平台服务
- [ ] 测试健康检查API

### 远程设备端（IP黑名单）
- [ ] 安装 `ipset`, `iptables`, `watchdog`
- [ ] 创建配置目录 `/opt/suppression_config`
- [ ] 复制 `gateway_black_white_file.py` 脚本
- [ ] 创建并启动 systemd 服务
- [ ] 验证 ipset 集合已创建

### 远程设备端（域名黑名单）
- [ ] 安装 `dnsmasq`, `watchdog`
- [ ] 配置 dnsmasq 加载 `/etc/dnsmasq.d/`
- [ ] 复制 `dns_black_white_file.py` 脚本
- [ ] 创建并启动 systemd 服务
- [ ] 测试 DNS 解析

### 远程设备端（丢包策略）
- [ ] 安装 `iptables`, `watchdog`
- [ ] 复制 `gateway_packet_loss_file.py` 脚本
- [ ] 创建并启动 systemd 服务
- [ ] 验证 iptables 规则已创建

### 功能测试
- [ ] 在平台添加IP黑名单并推送
- [ ] 在平台添加域名黑名单并推送
- [ ] 在平台添加丢包策略并推送
- [ ] 验证远程设备日志显示正常
- [ ] 验证规则已生效

---

## ? 总结

**关键要点**:
1. 平台IP不暴露，所有配置通过SSH主动推送
2. 远程设备使用文件监控，配置文件更新自动应用
3. 支持三种抑制策略：IP黑名单、域名黑名单、丢包策略
4. 所有脚本支持systemd服务管理，开机自启

**与旧版本对比**:
- ? 不需要暴露平台IP
- ? 配置推送更安全
- ? 实时生效，无延迟
- ? 统一的部署流程

祝部署顺利！?
