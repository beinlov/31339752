# C2端部署总结

## 📋 一、需要拷贝到C2的文件

### 最小部署（仅2个文件）
```
backend/remote/
├── c2_data_server.py          ← 核心程序（必需）
└── config.production.json     ← 配置文件（必需，重命名为config.json）
```

### 推荐部署（4个文件）
```
backend/remote/
├── c2_data_server.py          ← 核心程序
├── config.production.json     ← 配置文件（重命名为config.json）
├── requirements.txt           ← Python依赖列表
└── DEPLOYMENT_GUIDE.md        ← 部署指南
```

## ✅ 二、配置文件说明

### `config.production.json` 已根据C2实际路径配置好：

#### 上线日志配置
```json
"online": {
  "path": "/home/irc_server/logs/user_activity.log",
  "pattern": "\\[(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2})\\] \\[JOIN\\s*\\].*?([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3})"
}
```
- ✅ 路径：`/home/irc_server/logs/user_activity.log`
- ✅ 只匹配 `[JOIN ]` 类型的记录
- ✅ 忽略 `[EXIST]` 等其他类型

#### 清除日志配置
```json
"cleanup": {
  "path": "/home/irc_server/logs/reports.db",
  "db_config": {
    "table": "reports",
    "query": "SELECT client_ip, timestamp FROM reports WHERE id > ? ORDER BY id ASC LIMIT ?"
  },
  "field_mapping": {
    "ip_field": "client_ip",
    "timestamp_field": "timestamp"
  }
}
```
- ✅ 路径：`/home/irc_server/logs/reports.db`
- ✅ 表名：`reports`
- ✅ IP字段：`client_ip`
- ✅ 时间字段：`timestamp`

## 🚀 三、快速部署方式

### 方式1: 使用自动化脚本（推荐）
```bash
# 在本地执行
cd backend/remote
chmod +x deploy_to_c2.sh
./deploy_to_c2.sh user@c2-server-ip

# 示例
./deploy_to_c2.sh ubuntu@192.168.1.100
```

### 方式2: 手动部署
```bash
# 1. 上传文件
scp c2_data_server.py config.production.json user@c2-server:/opt/botnet-c2/

# 2. SSH登录C2服务器
ssh user@c2-server

# 3. 重命名配置文件
cd /opt/botnet-c2
mv config.production.json config.json

# 4. 安装依赖
pip3 install aiohttp

# 5. 设置API密钥
export C2_API_KEY="your-secret-key-here"

# 6. 启动服务
nohup python3 c2_data_server.py > /tmp/c2_server.log 2>&1 &
```

## 📝 四、部署后验证

### 1. 检查进程
```bash
ps aux | grep c2_data_server
```

### 2. 检查端口
```bash
netstat -tulpn | grep 8888
```

### 3. 查看日志
```bash
tail -f /tmp/c2_server.log
```

### 4. 测试API
```bash
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8888/api/pull?limit=5
```

**预期响应：**
```json
{
  "success": true,
  "data": [
    {
      "ip": "14.19.132.125",
      "timestamp": "2026-03-03T16:36:49",
      "log_type": "online"
    }
  ],
  "count": 5,
  "cursor": {
    "online": {"position": 1234},
    "cleanup": {"position": 56}
  }
}
```

## 🔧 五、配置API密钥（重要）

### 方式1: 环境变量（推荐）
```bash
export C2_API_KEY="your-secret-key-here"

# 永久生效
echo 'export C2_API_KEY="your-secret-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 方式2: 修改配置文件
```bash
# 编辑 config.json
vim /opt/botnet-c2/config.json

# 修改 http_server.api_key 字段
"http_server": {
  "api_key": "your-secret-key-here"
}
```

### 生成安全密钥
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 📡 六、平台端配置

在平台端 `backend/config.py` 中添加C2端点：

```python
C2_ENDPOINTS = [
    {
        "name": "IRC-C2-Production",
        "url": "http://C2_SERVER_IP:8888",  # ← 替换为C2实际IP
        "api_key": "与C2端相同的API_KEY",   # ← 与C2端保持一致
        "botnet_type": "test",
        "enabled": True,
        "pull_interval": 60,
        "batch_size": 500
    }
]
```

## 🔍 七、日志格式示例

### 上线日志（user_activity.log）
```
[2026-03-03 16:36:49] [JOIN ] #bot            vn409                14.19.132.125
[2026-03-03 16:36:59] [EXIST] #bot            vn409                (existing)      ← 忽略
[2026-03-03 16:37:08] [EXIST] #bot            vn409                (existing)      ← 忽略
[2026-03-03 16:38:15] [JOIN ] #bot            vn410                192.168.1.100
```
**只提取 `[JOIN ]` 类型的记录**

### 清除日志（reports.db）
```sql
SELECT client_ip, timestamp FROM reports;
-- 14.19.132.125 | 2026-03-03T16:38:34
-- 192.168.1.100  | 2026-03-03T16:40:12
```

## ⚙️ 八、systemd服务配置（生产环境推荐）

创建服务文件 `/etc/systemd/system/botnet-c2.service`：

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
sudo systemctl daemon-reload
sudo systemctl start botnet-c2
sudo systemctl enable botnet-c2
sudo systemctl status botnet-c2
```

## 🛠️ 九、故障排查

### 问题1: 文件权限错误
```
错误: Permission denied: '/home/irc_server/logs/user_activity.log'
解决: sudo chmod +r /home/irc_server/logs/user_activity.log
```

### 问题2: 端口被占用
```
错误: Address already in use
解决: 
  lsof -i :8888        # 查看占用进程
  kill -9 <PID>        # 杀死进程
```

### 问题3: API认证失败
```
错误: 401 Unauthorized
解决: 检查C2_API_KEY是否设置，是否与平台端一致
```

## 📚 十、相关文档

- **DEPLOYMENT_GUIDE.md** - 详细部署指南
- **MULTI_SOURCE_README.md** - 多日志源功能说明
- **FILES_TO_DEPLOY.txt** - 文件清单
- **deploy_to_c2.sh** - 自动化部署脚本

## 🎯 十一、部署检查清单

部署前：
- [ ] 准备好C2服务器SSH访问权限
- [ ] 确认日志文件路径正确
- [ ] 生成安全的API密钥

部署中：
- [ ] 上传 `c2_data_server.py`
- [ ] 上传并重命名 `config.production.json` → `config.json`
- [ ] 安装 `aiohttp` 依赖
- [ ] 设置 `C2_API_KEY` 环境变量

部署后：
- [ ] 测试进程是否运行
- [ ] 测试端口是否监听（8888）
- [ ] 测试API是否可访问
- [ ] 查看日志是否正常
- [ ] 配置平台端C2端点

## ✨ 十二、总结

**只需2个文件即可部署：**
1. `c2_data_server.py` - 核心程序
2. `config.production.json` - 配置文件（重命名为config.json）

**配置已优化好，无需修改：**
- ✅ 上线日志路径：`/home/irc_server/logs/user_activity.log`
- ✅ 清除日志路径：`/home/irc_server/logs/reports.db`
- ✅ 正则表达式：只匹配 `[JOIN ]` 记录
- ✅ HTTP端口：8888
- ✅ 支持两阶段确认、背压控制、多日志源

**开箱即用，部署即可运行！** 🎉
