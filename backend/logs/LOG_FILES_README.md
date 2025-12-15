# 应用日志文件说明

## 日志文件位置统一

所有应用日志文件现已统一存放在 `backend/logs/` 目录中。

## 当前日志文件

| 日志文件 | 说明 | 生成模块 |
|---------|------|---------|
| `log_processor.log` | 日志处理器运行日志 | log_processor/main.py |
| `stats_aggregator.log` | 统计聚合器运行日志 | stats_aggregator/aggregator.py |
| `remote_uploader.log` | 远程上传器运行日志 | remote/remote_uploader.py |
| `main_app.log` | 主应用日志（预留） | main.py |

## 日志目录结构

```
backend/logs/
├── log_processor.log       # 应用日志文件
├── stats_aggregator.log    # 应用日志文件
├── remote_uploader.log     # 应用日志文件
├── main_app.log            # 应用日志文件（预留）
├── asruex/                 # 僵尸网络数据日志
├── mozi/                   # 僵尸网络数据日志
├── andromeda/              # 僵尸网络数据日志
├── moobot/                 # 僵尸网络数据日志
├── ramnit/                 # 僵尸网络数据日志
└── leethozer/              # 僵尸网络数据日志
```

## 配置说明

日志文件路径在 `backend/config.py` 中统一配置：

```python
# 应用日志目录
APP_LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# 各模块日志文件路径
LOG_PROCESSOR_LOG_FILE = os.path.join(APP_LOGS_DIR, 'log_processor.log')
STATS_AGGREGATOR_LOG_FILE = os.path.join(APP_LOGS_DIR, 'stats_aggregator.log')
REMOTE_UPLOADER_LOG_FILE = os.path.join(APP_LOGS_DIR, 'remote_uploader.log')
MAIN_APP_LOG_FILE = os.path.join(APP_LOGS_DIR, 'main_app.log')
```

## 日志文件管理

### 查看日志

```bash
# 查看日志处理器日志
tail -f backend/logs/log_processor.log

# 查看聚合器日志
tail -f backend/logs/stats_aggregator.log

# 查看远程上传器日志
tail -f backend/logs/remote_uploader.log
```

### 清理日志

日志文件会自动追加，建议定期清理：

```bash
# Linux/Mac
cd backend/logs
> log_processor.log
> stats_aggregator.log
> remote_uploader.log

# Windows
cd backend\logs
type nul > log_processor.log
type nul > stats_aggregator.log
type nul > remote_uploader.log
```

或者使用提供的清理脚本：

```bash
# Linux/Mac
./backend/logs/clean_logs.sh

# Windows
.\backend\logs\clean_logs.bat
```

## 日志轮转

建议配置日志轮转（logrotate）来自动管理日志文件大小。

### Linux logrotate配置示例

创建 `/etc/logrotate.d/botnet`：

```
/path/to/botnet/backend/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
    create 0644 user group
}
```

## 旧日志文件迁移

如果存在以下旧位置的日志文件，可以安全删除：

- ❌ `backend/log_processor.log` （旧位置）
- ❌ `backend/stats_aggregator.log` （旧位置）
- ❌ `backend/log_processor/log_processor.log` （旧位置）
- ❌ `/tmp/remote_uploader.log` （临时目录）

使用提供的清理脚本自动删除旧日志文件。

## 注意事项

1. ✅ 日志文件会自动创建，无需手动创建
2. ✅ 日志目录如果不存在会自动创建
3. ⚠️ 日志文件可能增长很快，建议定期清理或配置轮转
4. ⚠️ 不要删除僵尸网络数据日志目录（asruex、mozi等）

## 远程部署配置

如果将 `remote_uploader.py` 部署到远程服务器：

1. 复制 `backend/remote/config.json.local` 为 `config.json`
2. 修改配置文件中的 `files.log_file` 路径
3. 例如：`"log_file": "/var/log/botnet/remote_uploader.log"`

---
**最后更新**: 2025-12-15
