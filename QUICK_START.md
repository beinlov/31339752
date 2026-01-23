# ⚡ 快速启动指南

## 🚀 一键启动所有服务

```bash
./start_all_services.sh
```

## 🛑 一键停止所有服务

```bash
./stop_all_services.sh
```

## 🔍 检查服务状态

```bash
./check_services_status.sh
```

---

## 📋 五个核心服务

1. **平台后端API** (8000端口)
2. **日志处理器** (需要Redis)
3. **统计聚合器** (30分钟间隔)
4. **Timeset数据确保器** (3小时间隔)
5. **前端界面** (9000端口)

---

## 🌐 访问地址

- **前端**: http://localhost:9000/
- **API文档**: http://localhost:8000/docs
- **API**: http://localhost:8000/

---

## ✅ 环境要求

| 组件 | 状态 | 说明 |
|------|------|------|
| MySQL | ✅ Docker容器 | 端口3306 |
| Redis | ✅ 已安装配置 | 端口6379 |
| Python | ✅ 3.8+ | 依赖已安装 |
| Node.js | ✅ v18.20.8 | 前端需要 |

---

## 📝 日志文件

```bash
# 查看实时日志
tail -f backend/logs/api_backend.log      # 后端API
tail -f backend/logs/log_processor.log    # 日志处理器
tail -f backend/logs/aggregator.log       # 统计聚合器
tail -f backend/logs/timeset_ensurer.log  # Timeset确保器
```

---

## 🆘 故障排查

### Redis未运行
```bash
sudo systemctl start redis-server
redis-cli ping  # 应返回PONG
```

### MySQL未运行
```bash
sudo docker start mysql
sudo docker ps | grep mysql
```

### 端口被占用
```bash
sudo lsof -i :8000  # 后端
sudo lsof -i :9000  # 前端
```

---

## 📚 详细文档

- **完整指南**: [COMPLETE_SERVICES_GUIDE.md](COMPLETE_SERVICES_GUIDE.md)
- **Redis配置**: [REDIS_CONFIGURATION_SUMMARY.md](REDIS_CONFIGURATION_SUMMARY.md)
- **部署架构**: [CURRENT_DEPLOYMENT_GUIDE.md](CURRENT_DEPLOYMENT_GUIDE.md)

---

**就这么简单！一个命令启动整个平台。** 🎉
