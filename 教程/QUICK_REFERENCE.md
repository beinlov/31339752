# 快速参考卡片

## 🚀 启动命令

### Windows
```batch
start_all.bat
```

### Linux/Mac
```bash
./start_all.sh
```

## 🔍 验证服务

| 服务 | 验证方式 | 预期结果 |
|------|----------|----------|
| 日志处理器 | 查看窗口输出 | "Botnet Log Processor is running" |
| FastAPI后端 | http://localhost:8000/docs | Swagger文档界面 |
| 前端界面 | http://localhost:3000 | 可视化监控界面 |

## 📂 关键目录

```
backend/
├── log_processor/          # 日志处理器
│   ├── main.py            # 启动: python main.py
│   └── config.py          # 配置数据库
├── logs/                  # 日志接收目录
│   ├── asruex/           # Asruex日志
│   ├── mozi/             # Mozi日志
│   └── ...
├── main.py               # FastAPI后端
└── start_all.bat/sh      # 一键启动
```

## 🔧 常用命令

### 添加测试日志
```bash
echo "2025-10-30 10:00:00,8.8.8.8,infection" >> logs/mozi/2025-10-30.txt
```

### 查看日志
```bash
tail -f log_processor/log_processor.log
tail -f backend.log
```

### 查询数据库
```sql
SELECT * FROM botnet_nodes_mozi LIMIT 10;
SELECT COUNT(*) FROM botnet_nodes_asruex;
```

### 停止服务
```bash
# Linux/Mac
./stop_all.sh

# Windows
按 Ctrl+C 在每个窗口
```

## 📊 日志格式

```
timestamp,ip,event_type,extra_fields...
```

示例：
```
2025-10-30 10:00:00,192.168.1.1,infection,botv1.0
2025-10-30 10:01:00,8.8.8.8,beacon
```

## 🐛 故障排查

| 问题 | 检查 | 解决 |
|------|------|------|
| 立即退出 | 数据库配置 | 修改 `config.py` |
| 端口占用 | `netstat -ano` | 关闭占用进程 |
| 无数据 | 数据库有数据吗 | 添加测试日志 |
| 连接失败 | 后端运行吗 | 访问 :8000/docs |

## 📞 获取帮助

1. 查看 [STARTUP_GUIDE.md](STARTUP_GUIDE.md)
2. 查看 [README_NEW_SYSTEM.md](README_NEW_SYSTEM.md)
3. 运行测试: `python log_processor/test_processor.py`
4. 查看日志文件

## 🎯 核心配置

### 数据库 (`log_processor/config.py`)
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "你的密码",  # 修改这里
    "database": "botnet"
}
```

### 添加新僵尸网络
```python
BOTNET_CONFIG = {
    'new_botnet': {
        'log_dir': os.path.join(LOGS_DIR, 'new_botnet'),
        'important_events': ['infection', 'beacon'],
        'enabled': True
    }
}
```

## ⚡ 性能参数

```python
IP_CACHE_SIZE = 10000      # IP缓存大小
DB_BATCH_SIZE = 100        # 批量写入大小
DB_COMMIT_INTERVAL = 60    # 提交间隔（秒）
```

## 📈 监控指标

- 处理速度: ~1000行/秒
- IP缓存命中率: 70-90%
- 内存占用: 50-200MB
- CPU占用: 5-20%

---

**提示**: 首次运行建议先运行 `python log_processor/test_processor.py` 测试环境！



