# 🐳 Docker 部署 - 快速参考

## 🚀 快速启动

### Linux/Mac
```bash
chmod +x docker-start.sh
./docker-start.sh
```

### Windows
```cmd
docker-start.bat
```

## 📋 手动部署

```bash
# 1. 复制环境变量配置
cp .env.example .env

# 2. 编辑配置（可选）
nano .env

# 3. 启动服务
docker-compose up -d

# 4. 查看状态
docker-compose ps
```

## 🌐 访问系统

- **前端**: http://localhost
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **默认账户**: admin / admin

## 🔧 常用命令

```bash
# 查看日志
docker-compose logs -f

# 停止服务
docker-compose stop

# 重启服务
docker-compose restart

# 更新部署
docker-compose down
docker-compose build
docker-compose up -d

# 完全清除（包括数据）
docker-compose down -v
```

## 📚 完整文档

详细部署指南请查看: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)

## 🐞 故障排查

### 端口冲突
```bash
# 检查端口占用
netstat -tuln | grep 80
netstat -tuln | grep 8000
netstat -tuln | grep 3306

# 解决: 修改.env中的端口配置
```

### 服务无法启动
```bash
# 查看详细日志
docker-compose logs backend
docker-compose logs mysql

# 等待MySQL完全启动（通常需要30-60秒）
```

### 数据库连接失败
```bash
# 检查MySQL状态
docker-compose exec mysql mysqladmin ping -h localhost -u root -p

# 重启MySQL
docker-compose restart mysql
```

## ⚠️ 生产环境注意事项

1. ✅ 修改 `.env` 中的所有密码和密钥
2. ✅ 启用IP白名单
3. ✅ 配置HTTPS反向代理
4. ✅ 设置资源限制
5. ✅ 配置自动备份
6. ✅ 启用日志轮转

详见: [DOCKER_DEPLOYMENT.md - 生产环境建议](DOCKER_DEPLOYMENT.md#生产环境建议)


