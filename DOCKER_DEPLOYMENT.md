# 🐳 僵尸网络接管集成平台 - Docker 部署指南

## 📋 目录
- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [详细部署步骤](#详细部署步骤)
- [配置说明](#配置说明)
- [常用命令](#常用命令)
- [故障排查](#故障排查)
- [生产环境建议](#生产环境建议)

---

## 📦 系统要求

### 硬件要求
- **CPU**: 2核心及以上
- **内存**: 4GB及以上
- **磁盘**: 20GB可用空间

### 软件要求
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### 检查Docker安装
```bash
docker --version
docker-compose --version
```

---

## 🚀 快速开始

### 一键部署（适合开发/测试环境）

```bash
# 1. 克隆或复制项目到本地
cd botnet

# 2. 复制环境变量配置文件
cp .env.example .env

# 3. 启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f
```

### 访问系统
- **前端界面**: http://localhost
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

### 默认账户
- **用户名**: admin
- **密码**: admin

---

## 📝 详细部署步骤

### 1️⃣ 准备工作

```bash
# 确保Docker服务正在运行
sudo systemctl status docker

# 如果未运行，启动Docker服务
sudo systemctl start docker
```

### 2️⃣ 配置环境变量

编辑 `.env` 文件，修改关键配置：

```bash
# 数据库密码（生产环境必须修改）
MYSQL_ROOT_PASSWORD=your_strong_password_here

# API密钥（用于日志上传认证）
API_KEY=your_api_key_here

# 用户同步接口密钥
SYNC_API_KEY=your_sync_api_key_here
```

**生成强密钥**：
```bash
# Linux/Mac
openssl rand -hex 32

# Windows PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

### 3️⃣ 构建并启动服务

```bash
# 构建镜像（首次部署或代码更新后）
docker-compose build

# 启动所有服务（后台运行）
docker-compose up -d

# 查看启动日志
docker-compose logs -f
```

### 4️⃣ 验证部署

```bash
# 检查所有容器状态（应该都是 Up 状态）
docker-compose ps

# 检查后端健康状态
curl http://localhost:8000/api/province-amounts

# 检查前端
curl http://localhost
```

### 5️⃣ 查看日志

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mysql

# 实时跟踪日志
docker-compose logs -f backend
```

---

## ⚙️ 配置说明

### 目录结构

```
botnet/
├── docker-compose.yml          # Docker编排配置
├── .env                        # 环境变量配置
├── .env.example                # 环境变量示例
├── init.sql                    # 数据库初始化脚本
├── .dockerignore               # Docker忽略文件
├── backend/                    # 后端代码
│   ├── Dockerfile              # 后端镜像构建文件
│   ├── requirements.txt        # Python依赖
│   ├── .dockerignore           # 后端忽略文件
│   └── ...
└── fronted/                    # 前端代码
    ├── Dockerfile              # 前端镜像构建文件
    ├── nginx.conf              # Nginx配置
    ├── .dockerignore           # 前端忽略文件
    └── ...
```

### 服务说明

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| MySQL | botnet-mysql | 3306 | 数据库服务 |
| Backend | botnet-backend | 8000 | 后端API + 日志处理器 + 统计聚合器 |
| Frontend | botnet-frontend | 80 | 前端Web界面 |

### 数据持久化

系统使用Docker volumes持久化以下数据：

1. **mysql-data**: MySQL数据库文件
2. **backend-state**: 日志处理器状态文件
3. **logs目录**: 挂载到宿主机 `./backend/logs`

---

## 🔧 常用命令

### 服务管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose stop

# 重启服务
docker-compose restart

# 停止并删除容器（数据保留）
docker-compose down

# 停止并删除容器和数据卷（清空所有数据）
docker-compose down -v
```

### 查看状态

```bash
# 查看服务状态
docker-compose ps

# 查看资源占用
docker stats

# 查看网络
docker-compose network ls
```

### 日志管理

```bash
# 查看所有日志
docker-compose logs

# 查看最近100行
docker-compose logs --tail=100

# 实时查看日志
docker-compose logs -f

# 查看特定服务
docker-compose logs backend
```

### 进入容器

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入MySQL容器
docker-compose exec mysql bash

# 进入前端容器
docker-compose exec frontend sh
```

### 数据库操作

```bash
# 连接MySQL
docker-compose exec mysql mysql -uroot -p123456 botnet

# 备份数据库
docker-compose exec mysql mysqldump -uroot -p123456 botnet > backup.sql

# 恢复数据库
docker-compose exec -T mysql mysql -uroot -p123456 botnet < backup.sql
```

### 更新部署

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
docker-compose build

# 3. 重启服务（会使用新镜像）
docker-compose up -d

# 4. 清理旧镜像
docker image prune -f
```

---

## 🔍 故障排查

### 问题1: 容器无法启动

```bash
# 查看详细错误日志
docker-compose logs backend

# 检查端口占用
netstat -tuln | grep 8000
netstat -tuln | grep 3306

# 解决方法：修改 .env 中的端口配置
```

### 问题2: 数据库连接失败

```bash
# 检查MySQL是否ready
docker-compose exec mysql mysqladmin ping -h localhost -u root -p

# 查看MySQL日志
docker-compose logs mysql

# 等待MySQL完全启动（通常需要30-60秒）
```

### 问题3: 前端无法连接后端

```bash
# 检查后端是否正常
curl http://localhost:8000/api/province-amounts

# 检查网络连接
docker-compose exec frontend ping backend

# 查看nginx错误日志
docker-compose exec frontend cat /var/log/nginx/error.log
```

### 问题4: 日志处理器不工作

```bash
# 进入后端容器检查
docker-compose exec backend bash

# 查看日志处理器进程
ps aux | grep log_processor

# 手动测试
python log_processor/main.py
```

### 问题5: 磁盘空间不足

```bash
# 清理未使用的镜像
docker image prune -a

# 清理未使用的容器
docker container prune

# 清理未使用的数据卷
docker volume prune

# 查看Docker占用空间
docker system df
```

---

## 🏭 生产环境建议

### 1. 安全配置

```bash
# .env 文件
# ✅ 使用强密码
MYSQL_ROOT_PASSWORD=$(openssl rand -hex 32)

# ✅ 修改默认端口
MYSQL_PORT=13306
BACKEND_PORT=18000

# ✅ 启用IP白名单
SSO_ENABLE_IP_WHITELIST=true
SYNC_ENABLE_IP_WHITELIST=true
```

### 2. 反向代理（推荐使用Nginx）

```nginx
# /etc/nginx/sites-available/botnet
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. 资源限制

修改 `docker-compose.yml`，添加资源限制：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 4. 日志轮转

```bash
# 配置Docker日志大小限制
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}

# 重启Docker
sudo systemctl restart docker
```

### 5. 自动备份

```bash
# 创建备份脚本 backup.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T mysql mysqldump -uroot -p$MYSQL_ROOT_PASSWORD botnet > backup_$DATE.sql
find . -name "backup_*.sql" -mtime +7 -delete

# 添加到crontab
0 2 * * * /path/to/backup.sh
```

### 6. 监控和告警

```bash
# 使用Prometheus + Grafana监控
# 或使用简单的健康检查脚本

#!/bin/bash
# health_check.sh
curl -f http://localhost:8000/api/province-amounts || echo "Backend is down!" | mail -s "Alert" admin@example.com
```

### 7. 使用Docker Swarm或Kubernetes（大规模部署）

```bash
# Docker Swarm部署
docker stack deploy -c docker-compose.yml botnet

# Kubernetes部署（需要转换为K8s配置）
kompose convert -f docker-compose.yml
kubectl apply -f ./
```

---

## 📚 相关文档

- [后端API文档](http://localhost:8000/docs)
- [集成接口使用指南](backend/集成接口使用指南.md)
- [项目结构说明](backend/项目结构说明.md)
- [日志格式说明](backend/logs/日志格式说明.md)

---

## 🆘 获取帮助

如遇到问题，请按以下顺序排查：

1. ✅ 查看容器日志：`docker-compose logs`
2. ✅ 检查服务状态：`docker-compose ps`
3. ✅ 查看本文档的[故障排查](#故障排查)部分
4. ✅ 检查环境变量配置
5. ✅ 确认Docker版本兼容性

---

## 📄 许可证

本项目仅供学习和研究使用。

---

**🎉 部署完成！祝使用愉快！**


