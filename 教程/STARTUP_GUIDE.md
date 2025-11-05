# 系统启动指南

## 🚀 快速启动

### Windows 系统

#### 方式1: 一键启动（推荐）
```batch
# 双击运行或在命令行执行
start_all.bat
```

这会自动打开3个窗口：
1. 日志处理器窗口
2. FastAPI后端窗口
3. 前端界面窗口

#### 方式2: 手动分别启动
```batch
# 窗口1: 日志处理器
cd log_processor
python main.py

# 窗口2: FastAPI后端
cd backend
python main.py

# 窗口3: 前端
cd fronted
npm start
```

### Linux/Mac 系统

#### 方式1: 一键启动（推荐）
```bash
# 添加执行权限（首次运行）
chmod +x start_all.sh stop_all.sh

# 启动所有服务
./start_all.sh
```

#### 方式2: 后台运行
```bash
# 启动
./start_all.sh

# 停止
./stop_all.sh

# 查看日志
tail -f log_processor/log_processor.log
tail -f backend.log
tail -f frontend.log
```

## 📊 验证服务状态

### 1. 检查日志处理器
```bash
# 查看日志
tail -f log_processor/log_processor.log

# 应该看到：
# Botnet Log Processor is running. Press Ctrl+C to stop.
# [asruex] Started monitoring: ...
# [mozi] Started monitoring: ...
```

### 2. 检查FastAPI后端
访问：http://localhost:8000/docs

应该看到 Swagger API 文档界面

### 3. 检查前端
访问：http://localhost:3000

应该看到僵尸网络监控可视化界面

## 🔍 测试数据流

### 1. 添加测试日志
```bash
# 添加一条测试日志
echo "2025-10-30 10:00:00,8.8.8.8,infection,test" >> logs/mozi/2025-10-30.txt
```

### 2. 观察日志处理器
几秒钟内应该看到：
```
[mozi] Processing 1 new lines from 2025-10-30.txt
[mozi] Flushed 1 nodes to database. Total: 1
```

### 3. 查询数据库
```sql
SELECT * FROM botnet_nodes_mozi ORDER BY id DESC LIMIT 1;
```

应该看到刚才添加的IP记录，包含完整的地理位置信息。

### 4. 刷新前端界面
在浏览器中刷新前端页面，应该能看到新增的节点数据。

## 🛑 停止服务

### Windows
在每个窗口中按 `Ctrl+C`

### Linux/Mac
```bash
# 使用停止脚本
./stop_all.sh

# 或手动停止
kill $(cat .log_processor.pid)
kill $(cat .backend.pid)
kill $(cat .frontend.pid)
```

## 🔧 常见问题

### Q1: 端口被占用
**症状**: `Address already in use`

**解决**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Q2: 日志处理器立即退出
**症状**: 启动后立即停止

**检查**:
1. 数据库配置是否正确（`log_processor/config.py`）
2. 数据库服务是否运行
3. 查看错误日志：`cat log_processor/log_processor.log`

### Q3: 前端无法连接后端
**症状**: 前端显示连接错误

**检查**:
1. FastAPI后端是否运行（访问 http://localhost:8000/docs）
2. 前端配置的API地址是否正确
3. 防火墙是否阻止了8000端口

### Q4: 没有数据显示
**症状**: 前端界面空白

**检查**:
1. 数据库中是否有数据：`SELECT COUNT(*) FROM botnet_nodes_asruex;`
2. 日志处理器是否正常运行
3. 日志文件是否存在且格式正确

## 📝 系统架构

```
┌─────────────────────────────────────────────────────┐
│  用户浏览器                                         │
│  http://localhost:3000                             │
└──────────────┬─────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────┐
│  前端服务 (fronted/)                                │
│  端口: 3000                                         │
│  npm start                                          │
└──────────────┬─────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────┐
│  FastAPI后端 (backend/main.py)                     │
│  端口: 8000                                         │
│  python main.py                                     │
└──────────────┬─────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────┐
│  MySQL数据库                                        │
└──────────────┬─────────────────────────────────────┘
               ↑
               │
┌──────────────┴─────────────────────────────────────┐
│  日志处理器 (log_processor/main.py)                │
│  无端口，后台运行                                   │
│  python main.py                                     │
└────────────────────────────────────────────────────┘
```

## 🎯 开发环境 vs 生产环境

### 开发环境（当前）
- 3个终端窗口分别运行
- 实时查看日志输出
- 方便调试

### 生产环境（推荐）
使用 systemd（Linux）或 Windows Service：

**Linux systemd 示例**:
```bash
# 创建服务文件
sudo nano /etc/systemd/system/botnet-processor.service
sudo nano /etc/systemd/system/botnet-api.service

# 启动服务
sudo systemctl start botnet-processor
sudo systemctl start botnet-api

# 开机自启
sudo systemctl enable botnet-processor
sudo systemctl enable botnet-api
```

详见 `MIGRATION_GUIDE.md` 的生产环境部署章节。

## 📚 相关文档

- [README_NEW_SYSTEM.md](README_NEW_SYSTEM.md) - 新系统使用指南
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 迁移指南
- [log_processor/README.md](log_processor/README.md) - 日志处理器详细说明
- [log_processor/QUICKSTART.md](log_processor/QUICKSTART.md) - 5分钟快速开始

## 💡 提示

1. **首次运行**：建议先运行测试脚本验证环境
   ```bash
   cd log_processor
   python test_processor.py
   ```

2. **查看实时统计**：日志处理器每60秒输出一次统计信息

3. **数据验证**：可以通过API文档（http://localhost:8000/docs）测试接口

4. **日志文件**：所有日志都保存在对应的 `.log` 文件中

5. **性能监控**：建议配置监控工具监控三个服务的运行状态



