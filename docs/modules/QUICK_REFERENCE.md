# C2端部署快速参考卡

## 📦 需要拷贝的文件（2个）

```
c2_data_server.py          ← 核心程序
config.production.json     ← 配置文件（部署时改名为config.json）
```

## 📍 C2服务器路径配置（已配置好）

| 项目 | 路径 | 说明 |
|------|------|------|
| 上线日志 | `/home/irc_server/logs/user_activity.log` | 只读取[JOIN]记录 |
| 清除日志 | `/home/irc_server/logs/reports.db` | SQLite数据库 |
| 部署目录 | `/opt/botnet-c2/` | 推荐部署位置 |
| 缓存数据库 | `/tmp/c2_data_cache.db` | 运行时自动创建 |
| 程序日志 | `/tmp/c2_data_server.log` | 运行时自动创建 |

## ⚡ 快速部署命令

```bash
# 1. 上传文件
scp c2_data_server.py config.production.json user@c2-server:/opt/botnet-c2/

# 2. SSH登录C2
ssh user@c2-server

# 3. 重命名配置
cd /opt/botnet-c2
mv config.production.json config.json

# 4. 安装依赖
pip3 install aiohttp

# 5. 设置API密钥
export C2_API_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
echo "API Key: $C2_API_KEY"  # 记下这个密钥！

# 6. 后台运行
nohup python3 c2_data_server.py > /tmp/c2_server.log 2>&1 &

# 7. 验证
ps aux | grep c2_data_server
curl -H "X-API-Key: $C2_API_KEY" http://localhost:8888/api/stats
```

## 🔑 API密钥配置

**C2端设置：**
```bash
export C2_API_KEY="生成的密钥"
```

**平台端配置（backend/config.py）：**
```python
C2_ENDPOINTS = [{
    "url": "http://C2_IP:8888",
    "api_key": "与C2端相同的密钥",
    "botnet_type": "test"
}]
```

## 🧪 测试命令

```bash
# 测试API拉取（替换YOUR_KEY）
curl -H "X-API-Key: YOUR_KEY" http://localhost:8888/api/pull?limit=5

# 查看统计信息
curl -H "X-API-Key: YOUR_KEY" http://localhost:8888/api/stats

# 查看日志
tail -f /tmp/c2_server.log

# 查看进程
ps aux | grep c2_data_server

# 查看端口
netstat -tulpn | grep 8888
```

## 🔍 日志格式

**上线日志（只匹配JOIN）：**
```
[2026-03-03 16:36:49] [JOIN ] #bot            vn409                14.19.132.125  ← 提取
[2026-03-03 16:36:59] [EXIST] #bot            vn409                (existing)      ← 忽略
```

**清除日志（数据库）：**
```sql
-- 从 reports 表提取
client_ip    | timestamp
-------------|-------------------
14.19.132.125| 2026-03-03T16:38:34
```

## 🛑 停止服务

```bash
# 查找进程
ps aux | grep c2_data_server | grep -v grep

# 停止进程
kill <PID>

# 或强制停止
pkill -f c2_data_server
```

## 📊 监控命令

```bash
# 实时查看日志
tail -f /tmp/c2_server.log

# 查看缓存大小
ls -lh /tmp/c2_data_cache.db

# 查看API统计
watch -n 5 'curl -s -H "X-API-Key: YOUR_KEY" http://localhost:8888/api/stats'
```

## ⚠️ 常见问题

| 问题 | 解决方法 |
|------|----------|
| Permission denied | `chmod +r /home/irc_server/logs/*.log` |
| Address in use | `lsof -i :8888` 查看占用 |
| 401 Unauthorized | 检查API_KEY是否正确 |
| No module 'aiohttp' | `pip3 install aiohttp` |

## 📁 完整文件列表

```
backend/remote/
├── c2_data_server.py              ← 必需：核心程序
├── config.production.json         ← 必需：配置文件
├── requirements.txt               ← 推荐：依赖列表
├── deploy_to_c2.sh                ← 推荐：自动部署脚本
├── README_DEPLOY.md               ← 文档：部署总结
├── DEPLOYMENT_GUIDE.md            ← 文档：详细指南
├── QUICK_REFERENCE.md             ← 文档：本文件
└── FILES_TO_DEPLOY.txt            ← 文档：文件清单
```

## 💡 记住这3个命令

```bash
# 1. 启动
nohup python3 c2_data_server.py > /tmp/c2_server.log 2>&1 &

# 2. 查看日志
tail -f /tmp/c2_server.log

# 3. 测试API
curl -H "X-API-Key: YOUR_KEY" http://localhost:8888/api/pull?limit=5
```

---
**详细文档请参考：README_DEPLOY.md 和 DEPLOYMENT_GUIDE.md**
