# 🚀 Botnet Platform - 启动指南

**一键启动，简单高效！**

---

## 📋 服务清单

启动后将运行以下5个服务：

1. ✅ **Redis Server** (端口: 6379) - 消息队列
2. ✅ **日志处理器** (内置Worker) - 数据拉取与处理
3. ✅ **平台后端API** (端口: 8000) - FastAPI服务
4. ✅ **统计聚合器** - 数据统计（30分钟间隔）
5. ✅ **前端界面** (端口: 5173) - Web界面

---

## ⚡ 快速启动

### Windows 用户

```batch
# 双击运行即可
start_all_v3.bat
```

### Linux/Mac 用户

```bash
# 赋予执行权限（首次）
chmod +x start_all_v3.sh

# 启动
./start_all_v3.sh
```

---

## 🌐 访问地址

启动成功后访问：

- **前端界面**: http://localhost:9000
- **API文档**: http://localhost:8000/docs
- **后端API**: http://localhost:8000

---

## 🛑 停止服务

### Windows

```batch
stop_all.bat
```

### Linux/Mac

```bash
./stop_all.sh
```

---

## ✅ 环境要求

- **Python** 3.9+ (必须)
- **Redis** (必须)
- **MySQL** (必须)
- **Node.js** 16+ (可选，仅前端需要)

---

## 📚 详细文档

- 📖 **完整使用说明**: [一键启动使用说明.md](一键启动使用说明.md)
- 🔧 **配置指南**: [backend/QUICK_START.md](backend/QUICK_START.md)
- 🏗️ **架构说明**: [backend/INTERNAL_WORKER_MIGRATION.md](backend/INTERNAL_WORKER_MIGRATION.md)

---

## 🆘 遇到问题？

### 1. 运行诊断工具

```bash
# 检查队列状态
python backend/scripts/check_queue_status.py

# 检查数据
python backend/scripts/check_test_data.py
```

### 2. 查看日志

```bash
# Windows: 查看弹出的命令窗口

# Linux/Mac: 查看日志文件
tail -f backend/logs/log_processor.log
tail -f backend/logs/stats_aggregator.log
```

### 3. 常见问题

- **Redis未启动**: 手动运行 `redis-server`
- **端口被占用**: 检查并关闭占用端口的程序
- **前端无法启动**: 安装Node.js或跳过前端，直接使用API

---

## 🎯 新手指南

第一次使用？按以下步骤操作：

### 1️⃣ 检查环境

```bash
# 检查Python
python --version  # 应该 >= 3.9

# 检查Redis
redis-cli ping    # 应该返回 PONG

# 检查MySQL
mysql --version   # 确认已安装
```

### 2️⃣ 配置数据库

编辑 `backend/config.py`:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '你的密码',  # ⚠️ 修改这里
    'database': 'botnet'
}
```

### 3️⃣ 启动平台

```batch
# Windows
start_all_v3.bat

# Linux/Mac
./start_all_v3.sh
```

### 4️⃣ 验证

打开浏览器访问: http://localhost:5173

---

## 🎉 就这么简单！

一键启动，自动检测环境，智能启动所有服务。

**问题反馈**: 查看日志文件或运行诊断工具

---

**版本**: v3.0 (内置Worker架构)  
**最后更新**: 2026-01-15
