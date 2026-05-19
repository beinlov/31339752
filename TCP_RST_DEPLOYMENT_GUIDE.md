# TCP RST攻击系统 - 完整部署文档

## ? 系统概述

本系统实现了通过中继节点对C2-Bot通信进行TCP RST攻击的功能，采用**文件通信方式**确保平台大屏IP不暴露。

### 架构图
```
┌─────────────────────────────────────────────────────────────┐
│              平台大屏服务器 (你当前的服务器)                  │
│  - IP: 不暴露给外部                                          │
│  - 通过SSH主动连接中继位置                                    │
│  - 写命令文件 → 读状态文件                                    │
└────────────────────┬────────────────────────────────────────┘
                    │ SSH/SFTP (单向主动连接)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              中继位置服务器 (需要部署脚本)                     │
│  - IP: 可以被平台访问                                        │
│  - 位置: 能够监听C2和Bot的通信链路                           │
│  - 运行: relay_node_file_monitor.py + tcp_rst.py           │
└────────────────────┬────────────────────────────────────────┘
                    │ 监听流量并注入RST包
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                 C2 ?────? Bot 通信                          │
│          (攻击目标: 断开此连接)                              │
└─────────────────────────────────────────────────────────────┘
```

---

## ? 部署前准备

### 需要的信息

#### 1. 中继位置服务器信息
- [ ] **IP地址**: 例如 `10.0.50.123`
- [ ] **SSH端口**: 通常是 `22`
- [ ] **SSH用户名**: 例如 `admin` 或 `root`
- [ ] **SSH密码**: 或SSH私钥路径
- [ ] **网络接口名称**: 通过 `ip addr` 或 `ifconfig` 查看，例如 `eth0`、`ens33`

#### 2. 攻击目标信息（部署完成后使用）
- [ ] **目标IP**: Bot节点的IP地址
- [ ] **目标端口**: Bot通信端口（通常是C2的端口）

---

## ? 第一部分：平台大屏端配置（当前服务器）

### 步骤1: 修改配置文件

编辑 `/home/spider/31339752/backend/config.py`，找到第570行左右的 `RELAY_CONFIG`：

```python
# 中继节点SSH/SFTP配置
RELAY_CONFIG = {
    # =====================================================
    # ?? 重要：请修改以下配置为实际的中继位置信息
    # =====================================================
    
    # 中继节点SSH连接信息
    'host': os.environ.get('RELAY_HOST', '10.0.50.123'),      # ← 修改为中继位置的IP地址
    'port': int(os.environ.get('RELAY_PORT', '22')),          # ← SSH端口
    'username': os.environ.get('RELAY_USERNAME', 'admin'),    # ← SSH用户名
    'password': os.environ.get('RELAY_PASSWORD', 'MyPass123'),# ← SSH密码
    
    # 共享目录路径（中继节点上的绝对路径）
    'share_path': os.environ.get('RELAY_SHARE_PATH', '/opt/relay_share'),
    
    # 轮询间隔（秒）- 平台读取状态文件的频率
    'poll_interval': int(os.environ.get('RELAY_POLL_INTERVAL', '2')),
    
    # 连接超时（秒）
    'connection_timeout': int(os.environ.get('RELAY_TIMEOUT', '10')),
    
    # 是否启用中继文件通信模式
    'enabled': os.environ.get('RELAY_ENABLED', 'true').lower() == 'true',
}
```

**配置说明**:
- `host`: 中继位置的IP地址
- `port`: SSH端口，默认22
- `username`: SSH登录用户名
- `password`: SSH登录密码（建议使用SSH密钥，见安全建议）
- `share_path`: 中继位置的共享目录，**必须与中继位置部署时一致**

### 步骤2: 安装平台依赖（如未安装）

```bash
cd /home/spider/31339752/backend

# 安装SSH客户端库
pip3 install paramiko

# 验证
python3 -c "import paramiko; print('? paramiko已安装')"
```

### 步骤3: 测试SSH连接

在部署前，先测试能否SSH到中继位置：

```bash
# 替换为实际的中继位置信息
ssh admin@10.0.50.123

# 如果成功登录，说明网络连通
# 输入 exit 退出
```

### 步骤4: 启动平台服务

```bash
cd /home/spider/31339752/backend

# 方式1: 直接启动（前台）
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# 方式2: 后台启动
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &

# 方式3: 使用现有启动脚本（如果有）
# Linux系统请使用对应的.sh脚本，不要使用.bat文件
```

**验证平台启动成功**：
```bash
# 查看日志，应该看到：
tail -f ../logs/backend.log

# 期望输出：
# ? 中继文件管理器已初始化
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## ? 第二部分：中继位置服务器部署

### 步骤1: 准备中继位置服务器

SSH登录到中继位置：

```bash
ssh admin@10.0.50.123
```

### 步骤2: 创建目录结构

```bash
# 创建脚本目录
sudo mkdir -p /opt/relay_scripts

# 创建共享目录
sudo mkdir -p /opt/relay_share/commands
sudo mkdir -p /opt/relay_share/status
sudo mkdir -p /opt/relay_share/processed

# 设置权限（假设当前用户是admin）
sudo chown -R $USER:$USER /opt/relay_scripts
sudo chown -R $USER:$USER /opt/relay_share

# 验证目录结构
tree /opt/ -L 2
# 或
ls -R /opt/relay_*
```

**目录说明**：
```
/opt/relay_scripts/       ← 存放Python脚本
/opt/relay_share/
  ├── commands/           ← 平台写入命令文件
  ├── status/             ← 中继节点写入状态文件
  └── processed/          ← 已处理的命令文件归档
```

### 步骤3: 复制脚本文件

**在平台服务器上执行**（不是中继位置）：

```bash
# 进入脚本目录
cd /home/spider/31339752/backend/suppression_scripts

# 复制文件到中继位置
scp relay_node_file_monitor.py admin@10.0.50.123:/opt/relay_scripts/
scp tcp_rst.py admin@10.0.50.123:/opt/relay_scripts/

# 验证复制成功
ssh admin@10.0.50.123 "ls -lh /opt/relay_scripts/"
```

**期望输出**：
```
-rw-r--r-- 1 admin admin  15K May 11 10:00 relay_node_file_monitor.py
-rw-r--r-- 1 admin admin 3.5K May 11 10:00 tcp_rst.py
```

### 步骤4: 安装依赖（在中继位置）

回到中继位置的SSH会话：

```bash
# 更新包管理器
sudo apt-get update  # Ubuntu/Debian
# 或
# sudo yum update      # CentOS/RHEL

# 安装Python3和pip（如果没有）
sudo apt-get install -y python3 python3-pip

# 安装网络抓包库
sudo apt-get install -y libpcap-dev python3-dev

# 安装Python依赖
pip3 install watchdog scapy

# 验证安装
python3 -c "from watchdog.observers import Observer; print('? watchdog OK')"
python3 -c "from scapy.all import sniff; print('? scapy OK')"
```

### 步骤5: 配置网络权限（重要）

```bash
# 给Python3网络抓包权限
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3)

# 验证权限
getcap $(which python3)
# 应该输出: /usr/bin/python3 = cap_net_admin,cap_net_raw+eip
```

**如果不执行此步骤，将无法捕获网络流量！**

### 步骤6: 确定网络接口名称

```bash
# 查看网络接口
ip addr show

# 或
ifconfig -a
```

**输出示例**：
```
1: lo: <LOOPBACK,UP,LOWER_UP>
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP>    ← 这个是你要的接口名
3: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP>   ← 或者这个
```

**记住接口名称**，例如 `eth0` 或 `ens33`，后面会用到。

### 步骤7: 启动中继节点服务

#### 方式A: 前台运行（推荐先用这个测试）

```bash
cd /opt/relay_scripts

# 启动服务（替换eth0为实际接口名）
python3 relay_node_file_monitor.py \
  --share-path /opt/relay_share \
  --interface eth0
```

**成功输出示例**：
```
============================================================
中继节点文件监控服务启动
共享目录: /opt/relay_share
命令目录: /opt/relay_share/commands
状态目录: /opt/relay_share/status
网络接口: eth0
============================================================
2026-05-11 10:25:00 - INFO - 开始监听接口: eth0
2026-05-11 10:25:00 - INFO - 流量监听已启动
2026-05-11 10:25:00 - INFO - 开始监控命令目录: /opt/relay_share/commands
```

**测试成功后按 Ctrl+C 停止，然后使用后台方式启动**

#### 方式B: 后台运行（生产环境）

```bash
cd /opt/relay_scripts

nohup python3 relay_node_file_monitor.py \
  --share-path /opt/relay_share \
  --interface eth0 \
  > service.log 2>&1 &

# 记录进程ID
echo $! > relay_node.pid

# 查看进程
ps aux | grep relay_node_file_monitor

# 查看日志
tail -f relay_node.log
```

#### 方式C: 使用systemd服务（推荐，开机自启）

**创建服务文件**：

```bash
sudo nano /etc/systemd/system/relay-node.service
```

**粘贴以下内容**（根据实际情况修改用户名和接口）：

```ini
[Unit]
Description=TCP RST Relay Node File Monitor Service
After=network.target

[Service]
Type=simple
User=admin
Group=admin
WorkingDirectory=/opt/relay_scripts
ExecStart=/usr/bin/python3 /opt/relay_scripts/relay_node_file_monitor.py \
  --share-path /opt/relay_share \
  --interface eth0
Restart=always
RestartSec=10
StandardOutput=append:/opt/relay_scripts/service.log
StandardError=append:/opt/relay_scripts/service.log

# 安全设置
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**保存并启动服务**：

```bash
# 重新加载systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start relay-node

# 查看状态
sudo systemctl status relay-node

# 设置开机自启
sudo systemctl enable relay-node

# 查看日志
sudo journalctl -u relay-node -f
```

**服务管理命令**：
```bash
sudo systemctl start relay-node    # 启动
sudo systemctl stop relay-node     # 停止
sudo systemctl restart relay-node  # 重启
sudo systemctl status relay-node   # 查看状态
```

---

## ? 第三部分：验证部署

### 验证1: 检查中继节点服务状态

在中继位置执行：

```bash
# 检查进程
ps aux | grep relay_node_file_monitor

# 检查日志
tail -20 /opt/relay_scripts/relay_node.log

# 检查目录
ls -la /opt/relay_share/commands/
ls -la /opt/relay_share/status/
```

### 验证2: 测试平台到中继的连接

在平台服务器执行：

```bash
# 测试健康检查API
curl http://localhost:8000/api/suppression/relay-file/health

# 期望返回：
{
  "status": "healthy",
  "message": "中继连接正常",
  "share_path": "/opt/relay_share",
  "files_count": 0
}
```

### 验证3: 端到端测试

#### 3.1 在平台大屏前端界面操作

1. 访问平台大屏: `http://平台IP:9000`
2. 登录系统
3. 进入 **抑制阻断策略** → **TCP SYN洪水** 选项卡
4. 填写测试参数：
   - 目标IP: `192.168.1.100`（任意可达IP）
   - 目标端口: `80`
   - 捕获接口: `eth0`（或留空）
   - 注入接口: `eth0`（或留空）
5. 点击 **启动TCP RST攻击**

#### 3.2 观察中继位置日志

```bash
# 查看日志
tail -f /opt/relay_scripts/relay_node.log

# 应该看到：
2026-05-11 10:30:00 - INFO - 检测到新命令文件: tcp-syn-1715407800.json
2026-05-11 10:30:00 - INFO - 读取命令: {"type":"start_attack", ...}
2026-05-11 10:30:01 - INFO - 攻击任务启动成功: tcp-syn-1715407800, PID=12345
```

#### 3.3 检查文件生成

```bash
# 检查processed目录（命令文件应该被移动到这里）
ls -la /opt/relay_share/processed/

# 检查status目录（应该生成状态文件）
ls -la /opt/relay_share/status/

# 查看状态文件内容
cat /opt/relay_share/status/tcp-syn-*_attack.json
```

#### 3.4 在前端查看状态

回到平台大屏界面，应该能看到：
- 攻击ID
- 攻击状态: **运行中**
- 进程ID
- 目标IP和端口

如果有C2-Bot通信流量经过中继位置，还会显示连接状态列表。

---

## ? 第四部分：正式使用

### 使用场景：阻断Bot与C2的通信

假设你已知：
- **Bot IP**: `192.168.1.50`
- **C2 IP**: `185.220.101.5`
- **通信端口**: `443`

#### 步骤1: 确认中继位置能监听到流量

在中继位置执行：

```bash
# 使用tcpdump监听目标流量
sudo tcpdump -i eth0 host 192.168.1.50 and port 443

# 如果能看到数据包，说明位置正确
# Ctrl+C 停止
```

#### 步骤2: 在平台大屏发起攻击

1. 填写参数：
   - **目标IP**: `192.168.1.50`（Bot的IP）
   - **目标端口**: `443`（通信端口）
   - **捕获接口**: `eth0`
   - **注入接口**: `eth0`

2. 点击 **启动TCP RST攻击**

#### 步骤3: 观察效果

**在平台大屏**：
- 查看连接状态列表
- 观察连接是否从 `active` 变为 `closed` 或 `timeout`

**在中继位置日志**：
```bash
tail -f /opt/relay_scripts/relay_node.log

# 期望看到：
2026-05-11 10:35:00 - INFO - 新连接: 192.168.1.50:54321-185.220.101.5:443 [SYN]
2026-05-11 10:35:01 - INFO - 连接活跃: 192.168.1.50:54321-185.220.101.5:443 [ACK]
2026-05-11 10:35:02 - INFO - RST包已注入: 192.168.1.50:54321-185.220.101.5:443
2026-05-11 10:35:02 - INFO - 连接关闭: 192.168.1.50:54321-185.220.101.5:443 [RST]
```

#### 步骤4: 停止攻击

在平台大屏点击 **停止当前攻击** 按钮。

---

## ? 故障排查

### 问题1: 平台无法连接中继位置

**症状**：
- 健康检查API返回错误
- 日志显示 `SSH连接失败`

**排查步骤**：
```bash
# 1. 测试SSH连接
ssh admin@10.0.50.123

# 2. 检查防火墙
sudo ufw status

# 3. 检查SSH服务
sudo systemctl status ssh

# 4. 检查平台配置
cat /home/spider/31339752/backend/config.py | grep RELAY_CONFIG -A 15
```

**解决方案**：
- 确保SSH端口开放
- 验证用户名密码正确
- 检查网络连通性

---

### 问题2: 命令文件未被处理

**症状**：
- 命令文件一直留在 `commands/` 目录
- 未移动到 `processed/` 目录

**排查步骤**：
```bash
# 1. 检查服务是否运行
ps aux | grep relay_node_file_monitor

# 2. 查看日志
tail -50 /opt/relay_scripts/relay_node.log

# 3. 检查目录权限
ls -la /opt/relay_share/

# 4. 手动测试watchdog
python3 -c "from watchdog.observers import Observer; print('OK')"
```

**解决方案**：
- 重启中继节点服务
- 检查目录权限
- 验证watchdog已安装

---

### 问题3: 无法捕获网络流量

**症状**：
- 日志无连接信息
- 状态文件中 `connections` 为空

**排查步骤**：
```bash
# 1. 检查网络权限
getcap $(which python3)

# 2. 测试接口名称
ip addr show eth0

# 3. 手动测试Scapy
sudo python3 -c "from scapy.all import sniff; sniff(iface='eth0', count=1)"

# 4. 检查是否有流量
sudo tcpdump -i eth0 -c 10
```

**解决方案**：
- 设置网络权限: `sudo setcap cap_net_raw,cap_net_admin=eip $(which python3)`
- 确认接口名称正确
- 确认中继位置能够看到目标流量

---

### 问题4: 前端不显示连接状态

**症状**：
- 攻击已启动，但前端无连接列表

**排查步骤**：
```bash
# 1. 检查状态文件是否生成
ls -la /opt/relay_share/status/

# 2. 查看状态文件内容
cat /opt/relay_share/status/tcp-syn-*_status.json

# 3. 测试平台API
curl http://localhost:8000/api/suppression/relay-file/attack/tcp-syn-XXX/status

# 4. 浏览器控制台检查
# F12 → Console → 查看错误信息
```

**解决方案**：
- 确认有实际流量经过中继位置
- 检查轮询是否正常
- 查看浏览器控制台错误

---

## ? 安全建议

### 1. 使用SSH密钥认证（强烈推荐）

**生成密钥**：
```bash
# 在平台服务器上
ssh-keygen -t rsa -b 4096 -f ~/.ssh/relay_key
```

**复制公钥到中继位置**：
```bash
ssh-copy-id -i ~/.ssh/relay_key.pub admin@10.0.50.123
```

**修改平台配置**：
```python
RELAY_CONFIG = {
    'host': '10.0.50.123',
    'username': 'admin',
    'key_filename': '/root/.ssh/relay_key',  # 使用密钥
    'password': None,  # 不使用密码
    # ...
}
```

### 2. 限制SSH访问

在中继位置：
```bash
# 只允许平台IP访问SSH
sudo ufw allow from 平台大屏IP to any port 22
sudo ufw enable
```

### 3. 文件权限加固

```bash
# 在中继位置
chmod 700 /opt/relay_share/commands
chmod 755 /opt/relay_share/status
chmod 600 /opt/relay_share/commands/*.json
```

---

## ? 监控和维护

### 日志位置

**平台大屏**：
```
/home/spider/31339752/logs/backend.log
```

**中继位置**：
```
/opt/relay_scripts/relay_node.log
/opt/relay_scripts/service.log
```

### 定期清理

在中继位置设置定时清理：

```bash
# 创建清理脚本
sudo nano /opt/relay_scripts/cleanup.sh
```

```bash
#!/bin/bash
# 清理7天前的processed和status文件
find /opt/relay_share/processed/ -name "*.json" -mtime +7 -delete
find /opt/relay_share/status/ -name "*.json" -mtime +7 -delete

# 清理旧日志
find /opt/relay_scripts/ -name "*.log" -size +100M -exec truncate -s 0 {} \;

echo "$(date): 清理完成" >> /opt/relay_scripts/cleanup.log
```

```bash
# 添加执行权限
chmod +x /opt/relay_scripts/cleanup.sh

# 添加到crontab（每天凌晨3点执行）
crontab -e
# 添加行: 0 3 * * * /opt/relay_scripts/cleanup.sh
```

---

## ? 快速参考卡

### 平台大屏配置
```
文件: /home/spider/31339752/backend/config.py
位置: 第570行 RELAY_CONFIG
需要修改: host, username, password, share_path
```

### 中继位置文件
```
脚本位置: /opt/relay_scripts/
  - relay_node_file_monitor.py (主服务)
  - tcp_rst.py (攻击脚本)

共享目录: /opt/relay_share/
  - commands/  (平台写入)
  - status/    (中继写入)
  - processed/ (已处理归档)
```

### 启动命令
```bash
# 平台大屏
cd /home/spider/31339752/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# 中继位置
sudo systemctl start relay-node
# 或
python3 /opt/relay_scripts/relay_node_file_monitor.py --share-path /opt/relay_share --interface eth0
```

### 常用检查命令
```bash
# 检查服务状态
ps aux | grep relay_node
sudo systemctl status relay-node

# 查看日志
tail -f /opt/relay_scripts/relay_node.log

# 测试连接
ssh admin@中继IP
curl http://localhost:8000/api/suppression/relay-file/health
```

---

## ? 部署检查清单

### 平台大屏端
- [ ] 修改 `config.py` 中的 `RELAY_CONFIG`
- [ ] 安装 `paramiko`: `pip3 install paramiko`
- [ ] 测试SSH连接: `ssh 用户名@中继IP`
- [ ] 启动平台服务
- [ ] 验证健康检查API返回正常

### 中继位置端
- [ ] 创建目录: `/opt/relay_scripts` 和 `/opt/relay_share`
- [ ] 复制脚本文件: `relay_node_file_monitor.py` 和 `tcp_rst.py`
- [ ] 安装依赖: `pip3 install watchdog scapy`
- [ ] 设置网络权限: `sudo setcap ...`
- [ ] 确认网络接口名称: `ip addr`
- [ ] 启动中继服务
- [ ] 检查日志输出正常

### 功能测试
- [ ] 发起测试攻击
- [ ] 检查命令文件被移动到 `processed/`
- [ ] 检查状态文件生成
- [ ] 前端显示攻击状态
- [ ] 能够停止攻击

---

## ? 技术支持

如遇到问题，请准备以下信息：

1. **平台大屏**:
   - `config.py` 的 RELAY_CONFIG 部分
   - `logs/backend.log` 最后100行
   - 健康检查API响应

2. **中继位置**:
   - 系统信息: `uname -a`
   - Python版本: `python3 --version`
   - 网络接口: `ip addr show`
   - 日志文件: `relay_node.log` 最后100行

3. **错误截图**:
   - 前端错误信息
   - 浏览器控制台错误

---

## ? 总结

部署完成后，你将拥有：
- ? 一个安全的文件通信系统（平台IP不暴露）
- ? 实时的连接状态监控
- ? 可控的TCP RST攻击能力
- ? 完整的日志和监控

**关键要点**：
1. `tcp_rst.py` 是核心攻击脚本，必不可少
2. 中继位置必须能监听到C2-Bot通信
3. 配置文件中的 `share_path` 必须一致
4. 网络权限设置必须正确

祝部署顺利！?
