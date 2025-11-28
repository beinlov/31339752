# 🚀 僵尸网络监控系统 - 部署指南

**适用场景**: 频繁改动的开发阶段

提供两种部署方案：
- **方案A（Docker）**: 环境隔离，适合有 Docker 基础的用户
- **方案B（直接部署）**: 简单快速，适合快速迭代

---

## 📋 部署前准备

### 服务器要求

- **操作系统**: Linux (Ubuntu 20.04+ 推荐)
- **内存**: 至少 2GB
- **磁盘**: 至少 10GB 可用空间
- **网络**: 开放端口 80 (前端) 和 8000 (后端API)

### 必需软件

#### 方案A（Docker）需要：
- Git
- Docker
- Docker Compose

#### 方案B（直接部署）需要：
- Git
- Python 3.9+
- Node.js 16+
- MySQL 8.0+
- Nginx 或 serve (可选)

---

## 🚀 方案A: Docker 部署（推荐）

### 优点

- ✅ **环境隔离**: 不污染服务器环境
- ✅ **快速更新**: 代码挂载，修改后重启即可（< 10秒）
- ✅ **易于管理**: 一键启停，统一管理
- ✅ **环境一致**: 开发和生产环境完全一致

### 部署步骤

#### 1. 安装 Docker

```bash
# Ubuntu
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER
newgrp docker

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. 克隆项目

```bash
cd ~
git clone https://github.com/your-username/botnet.git
cd botnet
```

#### 3. 配置环境变量

```bash
cp test/.env.example .env
nano .env  # 修改数据库密码等配置
```

#### 4. 首次部署

```bash
cd test
bash docker-deploy.sh
```

#### 5. 后续更新（修改代码后）

```bash
# 在本地修改代码后，推送到 Git
git add .
git commit -m "修复bug"
git push

# 在服务器上更新
cd ~/botnet/test
bash docker-deploy.sh
```

**时间**: 约 30 秒完成更新

### Docker 常用命令

```bash
# 进入项目目录
cd ~/botnet/test

# 查看服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看日志
docker logs -f botnet-backend   # 后端
docker logs -f botnet-frontend  # 前端
docker logs -f botnet-mysql     # 数据库

# 重启服务
docker-compose -f docker-compose.dev.yml restart

# 停止服务
docker-compose -f docker-compose.dev.yml stop

# 启动服务
docker-compose -f docker-compose.dev.yml up -d

# 进入容器
docker exec -it botnet-backend bash

# 清理所有（删除数据）
docker-compose -f docker-compose.dev.yml down -v
```

---

## 🔧 方案B: 直接部署（最简单）

### 优点

- ✅ **极速更新**: 修改代码后 30 秒完成部署
- ✅ **易于调试**: 直接查看日志和进程
- ✅ **无需 Docker**: 降低学习成本

### 部署步骤

#### 1. 安装依赖

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python
sudo apt install -y python3 python3-pip python3-venv

# 安装 Node.js
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs

# 安装 MySQL
sudo apt install -y mysql-server
sudo mysql_secure_installation

# 安装 serve (用于前端)
sudo npm install -g serve
```

#### 2. 配置 MySQL

```bash
sudo mysql -u root -p

# 在 MySQL 中执行
CREATE DATABASE botnet_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'botnet'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON botnet_db.* TO 'botnet'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 3. 克隆项目

```bash
cd ~
git clone https://github.com/your-username/botnet.git
cd botnet
```

#### 4. 配置后端

```bash
cd backend

# 修改配置文件
nano config.py  # 修改数据库配置

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 5. 首次部署

```bash
cd ~/botnet/test
bash deploy-direct.sh
```

#### 6. 后续更新（修改代码后）

```bash
# 方式1: 使用更新脚本（推荐）
cd ~/botnet/test
bash update-code.sh

# 方式2: 手动更新
cd ~/botnet
git pull
bash test/stop-services.sh
cd fronted && npm run build && cd ..
bash test/start-services.sh
```

**时间**: 约 30 秒完成更新

### 直接部署常用命令

```bash
# 启动所有服务
bash ~/botnet/test/start-services.sh

# 停止所有服务
bash ~/botnet/test/stop-services.sh

# 更新代码并重启
bash ~/botnet/test/update-code.sh

# 查看日志
tail -f ~/botnet/backend/logs/backend.log           # 后端
tail -f ~/botnet/backend/log_processor/log_processor.log  # 日志处理器
tail -f ~/botnet/backend/stats_aggregator.log       # 聚合器

# 查看进程状态
ps aux | grep python
ps aux | grep serve
```

---

## 📊 方案对比

| 特性 | 方案A (Docker) | 方案B (直接部署) |
|------|---------------|----------------|
| **更新速度** | 10-30秒 | 30秒 |
| **学习成本** | 需要了解 Docker | 无需额外知识 |
| **环境隔离** | ✅ 完全隔离 | ❌ 可能冲突 |
| **调试难度** | 中等 (需进入容器) | 简单 (直接查看) |
| **资源占用** | 中等 | 低 |
| **适用场景** | 多项目并存 | 单一项目 |
| **推荐度** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**建议**: 
- 初期使用**方案B**，快速迭代
- 稳定后升级到**方案A**，更专业

---

## 🔄 日常工作流程

### 开发流程

```bash
# 1. 在本地修改代码
git pull
# ... 修改代码 ...
git add .
git commit -m "新功能: xxx"
git push

# 2. 在服务器上更新
# 方案A (Docker):
cd ~/botnet/test && bash docker-deploy.sh

# 方案B (直接):
cd ~/botnet/test && bash update-code.sh
```

### 查看服务状态

```bash
# 方案A (Docker):
cd ~/botnet/test
docker-compose -f docker-compose.dev.yml ps
docker logs -f botnet-backend

# 方案B (直接):
ps aux | grep python
tail -f ~/botnet/backend/logs/backend.log
```

### 重启服务

```bash
# 方案A (Docker):
cd ~/botnet/test
docker-compose -f docker-compose.dev.yml restart

# 方案B (直接):
bash ~/botnet/test/stop-services.sh
bash ~/botnet/test/start-services.sh
```

---

## 🐛 故障排查

### 常见问题1: 后端启动失败

**症状**: 访问 http://服务器IP:8000 无响应

**排查**:
```bash
# Docker
docker logs botnet-backend

# 直接部署
tail -f ~/botnet/backend/logs/backend.log
```

**常见原因**:
- 数据库连接失败: 检查 config.py 或 .env
- 端口被占用: `netstat -tlnp | grep 8000`
- 依赖未安装: 重新运行部署脚本

### 常见问题2: 前端显示空白

**症状**: 访问 http://服务器IP 显示空白或404

**排查**:
```bash
# 检查 dist 目录是否存在
ls -la ~/botnet/fronted/dist

# 重新构建
cd ~/botnet/fronted
npm run build
```

### 常见问题3: 数据不同步

**症状**: 后台管理系统和处置平台数据不一致

**解决**:
```bash
# 检查聚合器是否运行
ps aux | grep aggregator

# 手动触发聚合
cd ~/botnet/backend/stats_aggregator
python aggregator.py once
```

---

## 📝 配置文件说明

### backend/config.py

核心配置文件，包含：
- 数据库连接信息
- API密钥
- IP白名单

### test/.env

Docker 环境变量，包含：
- MySQL 密码
- 数据库名称
- 时区设置

---

## 🔐 安全建议

1. **修改默认密码**: 部署后立即修改所有默认密码
2. **配置防火墙**: 只开放必需端口 (80, 8000, 3306)
3. **使用 HTTPS**: 生产环境建议配置 SSL 证书
4. **IP白名单**: 设置 `ALLOWED_UPLOAD_IPS` 限制数据上传来源
5. **定期备份**: 备份数据库和配置文件

---

## 📚 附录

### 文件清单

```
test/
├── docker-compose.dev.yml    # Docker 配置
├── docker-deploy.sh          # Docker 部署脚本
├── deploy-direct.sh          # 直接部署脚本
├── start-services.sh         # 启动服务脚本
├── stop-services.sh          # 停止服务脚本
├── update-code.sh            # 快速更新脚本
├── .env.example              # 环境变量示例
└── README-DEPLOYMENT.md      # 本文档
```

### 服务端口

- **80**: 前端 Web 界面
- **8000**: 后端 API
- **3306**: MySQL 数据库 (仅内部访问)

### 日志位置

- **后端**: `backend/logs/backend.log`
- **日志处理器**: `backend/log_processor/log_processor.log`
- **聚合器**: `backend/stats_aggregator.log`
- **前端**: `backend/logs/frontend.log` (直接部署)

---

## 🎉 快速开始

### Docker 部署（一键）

```bash
# 1. 克隆项目
git clone https://github.com/your-username/botnet.git && cd botnet

# 2. 配置环境
cp test/.env.example .env && nano .env

# 3. 部署
cd test && bash docker-deploy.sh
```

### 直接部署（一键）

```bash
# 1. 克隆项目
git clone https://github.com/your-username/botnet.git && cd botnet

# 2. 部署
cd test && bash deploy-direct.sh
```

---

**部署完成后**:
- 前端: http://服务器IP
- 后端API: http://服务器IP:8000
- API文档: http://服务器IP:8000/docs

**需要帮助？** 查看日志或联系开发者。

---

**版本**: 1.0  
**最后更新**: 2025-11-27
