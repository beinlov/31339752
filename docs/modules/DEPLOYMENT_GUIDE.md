# C2端部署指南

## 一、需要部署的文件清单

### 1. 核心代码文件
```
backend/remote/
├── c2_data_server.py          # C2数据服务器主程序（必需）
├── config.production.json     # 生产环境配置文件（必需）
└── requirements.txt           # Python依赖包列表（推荐）
```

### 2. 文件说明

#### 核心文件
- **c2_data_server.py** - C2端核心程序
  - 后台读取日志文件和数据库
  - 提供HTTP API供平台拉取数据
  - 支持多日志源、两阶段确认、背压控制

- **config.production.json** - 生产环境配置
  - 已适配C2实际路径
  - 上线日志：`/home/irc_server/logs/user_activity.log`
  - 清除日志：`/home/irc_server/logs/reports.db`

#### 依赖管理
- **requirements.txt** - Python依赖包（如果不存在需创建）
  ```
  aiohttp>=3.8.0
  ```

## 二、C2服务器部署步骤

### 步骤1: 创建部署目录
```bash
# 在C2服务器上创建部署目录
mkdir -p /opt/botnet-c2
cd /opt/botnet-c2
```

### 步骤2: 上传文件
将以下文件上传到C2服务器的 `/opt/botnet-c2/` 目录：
```bash
# 方式1: 使用scp
scp c2_data_server.py user@c2-server:/opt/botnet-c2/
scp config.production.json user@c2-server:/opt/botnet-c2/config.json

# 方式2: 使用rsync
rsync -avz c2_data_server.py config.production.json user@c2-server:/opt/botnet-c2/
```

### 步骤3: 安装Python依赖
```bash
# 在C2服务器上执行
cd /opt/botnet-c2

# 安装aiohttp
pip3 install aiohttp

# 或者使用requirements.txt
pip3 install -r requirements.txt
```

### 步骤4: 配置API密钥（安全方式）
```bash
# 方式1: 设置环境变量（推荐）
export C2_API_KEY="your-secure-random-key-here"

# 方式2: 写入.bashrc或.bash_profile（永久生效）
echo 'export C2_API_KEY="your-secure-random-key-here"' >> ~/.bashrc
source ~/.bashrc

# 方式3: 如果一定要写在配置文件中
# 编辑 config.json，修改 http_server.api_key 字段
```

**生成安全的API密钥示例：**
```bash
# 生成32字符随机密钥
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 步骤5: 验证配置
```bash
# 检查日志文件是否存在
ls -lh /home/irc_server/logs/user_activity.log
ls -lh /home/irc_server/logs/reports.db

# 检查文件权限（需要读取权限）
# 如果没有权限，需要添加：
# sudo chmod +r /home/irc_server/logs/user_activity.log
# sudo chmod +r /home/irc_server/logs/reports.db
```

### 步骤6: 测试运行
```bash
# 前台运行测试
cd /opt/botnet-c2
python3 c2_data_server.py

# 查看输出，确认：
# ✓ 配置加载成功
# ✓ 日志源初始化成功
# ✓ HTTP服务器启动在 0.0.0.0:8888
# ✓ 后台日志读取任务启动
```

**测试输出示例：**
```
[INFO] 配置加载成功: /opt/botnet-c2/config.json
[INFO] Botnet类型: test
[INFO] 日志源配置: 2 个源 (online, cleanup)
[INFO] HTTP服务器启动: 0.0.0.0:8888
[INFO] 后台日志读取任务已启动
[INFO] [online] 开始读取日志...
[INFO] [cleanup] 开始读取数据库...
```

### 步骤7: 测试API访问
```bash
# 在另一个终端测试API（需要替换YOUR_API_KEY）
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8888/api/pull?limit=10

# 预期响应：
# {
#   "success": true,
#   "data": [...],
#   "count": 10,
#   "cursor": {...}
# }
```

### 步骤8: 后台运行（生产环境）

#### 方式1: 使用nohup（简单）
```bash
cd /opt/botnet-c2
nohup python3 c2_data_server.py > /tmp/c2_server.log 2>&1 &

# 查看进程
ps aux | grep c2_data_server

# 查看日志
tail -f /tmp/c2_server.log
```

#### 方式2: 使用systemd（推荐）
创建systemd服务文件 `/etc/systemd/system/botnet-c2.service`：

```ini
[Unit]
Description=Botnet C2 Data Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/botnet-c2
Environment="C2_API_KEY=your-secure-api-key"
ExecStart=/usr/bin/python3 /opt/botnet-c2/c2_data_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
# 重载systemd配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start botnet-c2

# 设置开机自启
sudo systemctl enable botnet-c2

# 查看服务状态
sudo systemctl status botnet-c2

# 查看日志
sudo journalctl -u botnet-c2 -f
```

#### 方式3: 使用supervisor（备选）
创建配置文件 `/etc/supervisor/conf.d/botnet-c2.conf`：

```ini
[program:botnet-c2]
command=/usr/bin/python3 /opt/botnet-c2/c2_data_server.py
directory=/opt/botnet-c2
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/botnet-c2.log
environment=C2_API_KEY="your-secure-api-key"
```

启动：
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start botnet-c2
sudo supervisorctl status botnet-c2
```

## 三、配置详解

### 关键配置项说明

#### 1. 日志源路径（已配置好）
```json
"online": {
  "path": "/home/irc_server/logs/user_activity.log"
},
"cleanup": {
  "path": "/home/irc_server/logs/reports.db"
}
```

#### 2. 上线日志正则表达式
```json
"pattern": "\\[(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2})\\] \\[JOIN\\s*\\].*?([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3})"
```
**说明**：
- 只匹配 `[JOIN ]` 类型的记录
- 忽略 `[EXIST]` 等其他类型
- 提取时间戳（第1组）和IP地址（第2组）

#### 3. HTTP服务器配置
```json
"http_server": {
  "host": "0.0.0.0",  // 监听所有网络接口
  "port": 8888        // 默认端口
}
```

#### 4. 缓存配置
```json
"cache": {
  "db_file": "/tmp/c2_data_cache.db",
  "max_cached_records": 10000,
  "retention_days": 7
}
```

## 四、平台端配置

在平台端的 `backend/config.py` 中配置C2端点：

```python
C2_ENDPOINTS = [
    {
        "name": "C2-Production",
        "url": "http://c2-server-ip:8888",  # 替换为C2实际IP
        "api_key": "与C2端相同的API_KEY",
        "botnet_type": "test",
        "enabled": True,
        "pull_interval": 60,  # 拉取间隔（秒）
        "batch_size": 500
    }
]
```

## 五、验证部署

### 1. 检查C2服务器状态
```bash
# 检查进程
ps aux | grep c2_data_server

# 检查端口监听
netstat -tulpn | grep 8888
# 或
ss -tulpn | grep 8888

# 检查日志
tail -f /tmp/c2_data_server.log
```

### 2. 测试数据拉取
```bash
# 在C2服务器本地测试
curl -H "X-API-Key: YOUR_API_KEY" \
     http://localhost:8888/api/pull?limit=5

# 从平台服务器测试
curl -H "X-API-Key: YOUR_API_KEY" \
     http://C2_SERVER_IP:8888/api/pull?limit=5
```

### 3. 查看统计信息
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
     http://localhost:8888/api/stats
```

**预期响应：**
```json
{
  "success": true,
  "stats": {
    "cached_records": 1234,
    "pulled_records": 567,
    "retention_days": 7,
    "log_sources": {
      "online": {"enabled": true, "status": "running"},
      "cleanup": {"enabled": true, "status": "running"}
    }
  }
}
```

## 六、故障排查

### 问题1: 文件权限错误
```
错误: Permission denied: '/home/irc_server/logs/user_activity.log'
解决: sudo chmod +r /home/irc_server/logs/user_activity.log
```

### 问题2: 数据库锁定
```
错误: database is locked
解决: 确保reports.db没有被其他进程独占写入
```

### 问题3: 端口被占用
```
错误: Address already in use
解决: 
  1. 检查占用进程: lsof -i :8888
  2. 杀死进程: kill -9 <PID>
  3. 或修改配置文件端口号
```

### 问题4: API认证失败
```
错误: 401 Unauthorized
解决: 
  1. 检查C2_API_KEY环境变量
  2. 确保平台端配置的api_key一致
```

### 问题5: 无法读取日志
```
错误: No such file or directory
解决: 
  1. 检查路径是否正确
  2. 检查文件是否存在
  3. 检查是否有读取权限
```

## 七、安全建议

### 1. API密钥管理
- ✅ 使用环境变量存储API_KEY
- ✅ 使用强随机密钥（至少32字符）
- ❌ 不要将密钥提交到Git仓库
- ❌ 不要在日志中打印密钥

### 2. 网络安全
- 配置防火墙，只允许平台服务器访问8888端口
- 如果可能，使用HTTPS加密传输（需要配置反向代理）
- 定期更换API密钥

### 3. 文件权限
- C2程序以非root用户运行
- 日志文件设置最小权限（只读）
- 缓存数据库文件权限600

## 八、监控与日志

### 查看实时日志
```bash
# systemd服务
sudo journalctl -u botnet-c2 -f

# nohup方式
tail -f /tmp/c2_server.log

# 程序日志
tail -f /tmp/c2_data_server.log
```

### 关键日志标识
- `[INFO]` - 正常信息
- `[WARNING]` - 警告（如缓存接近上限）
- `[ERROR]` - 错误（需要关注）

### 监控指标
- 缓存记录数（不应接近max_cached_records）
- 拉取成功率（>95%）
- 日志读取延迟（<5秒）

## 九、文件清单汇总

**最小部署**（只需这2个文件）：
```
c2_data_server.py
config.production.json → 重命名为 config.json
```

**完整部署**（推荐）：
```
c2_data_server.py
config.production.json → 重命名为 config.json
requirements.txt
DEPLOYMENT_GUIDE.md（本文档）
```

## 十、快速部署脚本

创建 `deploy.sh` 自动化部署脚本：

```bash
#!/bin/bash
# C2端快速部署脚本

echo "=== C2端部署脚本 ==="

# 1. 创建目录
echo "创建部署目录..."
mkdir -p /opt/botnet-c2
cd /opt/botnet-c2

# 2. 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    exit 1
fi

# 3. 安装依赖
echo "安装Python依赖..."
pip3 install aiohttp

# 4. 复制配置文件
echo "配置文件..."
cp config.production.json config.json

# 5. 设置API密钥
echo "设置API密钥..."
read -p "请输入API密钥（留空使用默认）: " api_key
if [ -n "$api_key" ]; then
    export C2_API_KEY="$api_key"
    echo "export C2_API_KEY=\"$api_key\"" >> ~/.bashrc
fi

# 6. 检查日志文件
echo "检查日志文件..."
if [ ! -r /home/irc_server/logs/user_activity.log ]; then
    echo "警告: 无法读取 user_activity.log"
fi
if [ ! -r /home/irc_server/logs/reports.db ]; then
    echo "警告: 无法读取 reports.db"
fi

# 7. 测试运行
echo "测试运行..."
timeout 5 python3 c2_data_server.py || true

echo "=== 部署完成 ==="
echo "启动服务: python3 c2_data_server.py"
echo "后台运行: nohup python3 c2_data_server.py > /tmp/c2_server.log 2>&1 &"
```

使用方式：
```bash
chmod +x deploy.sh
./deploy.sh
```
