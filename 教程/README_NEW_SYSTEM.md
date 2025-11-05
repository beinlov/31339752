# 统一僵尸网络日志处理系统 - 使用指南

## 📦 新系统文件结构

```
backend/
├── log_processor/              # 🆕 统一日志处理模块
│   ├── __init__.py             # 模块初始化
│   ├── config.py               # 配置管理
│   ├── parser.py               # 日志解析器
│   ├── enricher.py             # IP信息增强器
│   ├── db_writer.py            # 数据库写入器
│   ├── watcher.py              # 文件监控器
│   ├── main.py                 # 主程序入口
│   ├── test_processor.py       # 测试脚本
│   ├── start.sh                # Linux启动脚本
│   ├── start.bat               # Windows启动脚本
│   ├── README.md               # 模块详细说明
│   ├── QUICKSTART.md           # 快速开始指南
│   ├── ARCHITECTURE.md         # 架构设计文档
│   └── SUMMARY.md              # 改造总结
│
├── logs/                       # 🆕 日志接收目录
│   ├── README.md               # 日志格式规范
│   ├── asruex/                 # Asruex日志
│   │   └── 2025-10-29.txt      # 示例日志
│   ├── mozi/                   # Mozi日志
│   │   └── 2025-10-29.txt      # 示例日志
│   ├── andromeda/              # Andromeda日志
│   ├── moobot/                 # Moobot日志
│   ├── ramnit/                 # Ramnit日志
│   └── leethozer/              # Leethozer日志
│
├── MIGRATION_GUIDE.md          # 🆕 迁移指南
│
├── ip_location/                # ✅ IP查询模块（保留，新系统依赖）
│   ├── ip_query.py
│   └── IP_city_single_WGS84.awdb
│
├── router/                     # ✅ API路由（保留，查询功能）
│   ├── botnet.py
│   ├── node.py
│   └── ...
│
├── main.py                     # ✅ FastAPI主程序（保留）
│
└── ashttpd/                    # ⚠️  可选保留（如果还在运行C2服务器）
    ├── httpd.py                # C2服务器
    ├── logtail.py              # ❌ 可废弃（被log_processor替代）
    ├── dbhlp_access.py         # ❌ 可废弃
    └── dbhlp_clean.py          # ❌ 可废弃
```

## 🚀 快速开始（5分钟）

### 1. 安装依赖
```bash
pip install pymysql watchdog awaits
```

### 2. 配置数据库
编辑 `log_processor/config.py`：
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "你的密码",  # 修改这里
    "database": "botnet"
}
```

### 3. 运行测试
```bash
cd backend/log_processor
python test_processor.py
```

预期输出：
```
✅ 所有测试完成！
```

### 4. 启动处理器
```bash
# Windows
start.bat

# Linux/Mac
./start.sh

# 或直接运行
python main.py
```

预期输出：
```
Starting Botnet Log Processor
================================
[asruex] Started monitoring: E:\zombie2.0\botnet\backend\logs\asruex
[mozi] Started monitoring: E:\zombie2.0\botnet\backend\logs\mozi
...
Started monitoring 6 botnet log directories
Botnet Log Processor is running. Press Ctrl+C to stop.
```

## 📝 添加日志数据

### 方式1: 实时追加（推荐）
```bash
# 追加新日志行
echo "2025-10-29 15:30:00,8.8.8.8,infection,botv1.0" >> logs/mozi/2025-10-29.txt

# 几秒钟后查看处理日志
tail -f log_processor.log
```

### 方式2: 批量复制
```bash
# 复制已有日志文件
cp /path/to/remote/logs/*.txt logs/asruex/

# 处理器会自动检测并处理
```

### 方式3: 远程同步
```bash
# 使用rsync增量同步
rsync -avz remote:/var/log/asruex/ logs/asruex/

# 设置定时任务（Linux）
*/5 * * * * rsync -avz remote:/var/log/mozi/ /path/to/backend/logs/mozi/
```

## 🔍 验证数据

### 查看数据库
```sql
-- 查看节点数据
SELECT * FROM botnet_nodes_asruex LIMIT 10;
SELECT * FROM botnet_nodes_mozi LIMIT 10;

-- 统计数据量
SELECT COUNT(*) as total FROM botnet_nodes_asruex;

-- 查看地理分布
SELECT country, COUNT(*) as count 
FROM botnet_nodes_asruex 
GROUP BY country 
ORDER BY count DESC;

-- 查看中国各省分布
SELECT province, city, COUNT(*) as count 
FROM botnet_nodes_asruex 
WHERE is_china = 1
GROUP BY province, city 
ORDER BY count DESC;
```

### 查看处理日志
```bash
# 实时查看
tail -f log_processor.log

# 查看统计信息
tail -f log_processor.log | grep "STATISTICS"

# 查看错误
grep ERROR log_processor.log
```

## 🔧 添加新的僵尸网络

只需3步：

### 1. 编辑配置
`log_processor/config.py`：
```python
BOTNET_CONFIG = {
    # ... 现有配置 ...
    'new_botnet': {
        'log_dir': os.path.join(LOGS_DIR, 'new_botnet'),
        'important_events': ['infection', 'beacon', 'attack'],
        'enabled': True,
        'description': '新僵尸网络描述'
    }
}
```

### 2. 创建目录
```bash
mkdir logs/new_botnet
```

### 3. 重启处理器
```bash
# 停止 (Ctrl+C)
# 重新启动
python main.py
```

## 📊 日志格式规范

所有僵尸网络日志必须遵循统一的CSV格式：

```
timestamp,ip,event_type,extra_field1,extra_field2,...
```

### 示例

**Asruex:**
```
2025-10-29 10:29:44,192.168.91.7,access,/content/faq.php?ql=b2
2025-10-29 10:32:01,192.168.91.7,clean1,6.1-x64,192.168.91.7
```

**Mozi:**
```
2025-10-29 14:22:11,45.33.12.88,infection,bot_version_v1.2
2025-10-29 14:23:05,45.33.12.88,command,ddos_target
```

**Andromeda:**
```
2025-10-29 15:10:33,203.0.113.45,beacon
2025-10-29 15:11:12,203.0.113.45,download,payload.exe
```

详见 `logs/README.md`

## 🔄 从旧系统迁移

### Asruex迁移

**选项A: 修改httpd.py输出目录**
```python
# ashttpd/httpd.py
logdir = '../logs/asruex'  # 修改这一行
```

**选项B: 配置日志传输**
```bash
# 从远程C2服务器同步日志
rsync -avz remote:/path/to/ashttpd/logdir/ logs/asruex/
```

**选项C: 复制已有日志**
```bash
cp ashttpd/logdir/*.txt logs/asruex/
```

### 其他僵尸网络迁移

**Excel转日志（可选）:**
```python
import pandas as pd
from datetime import datetime

df = pd.read_excel('moobot2024.xlsx')
with open('logs/moobot/2025-10-29.txt', 'w') as f:
    for _, row in df.iterrows():
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ip = row['IP地址']
        f.write(f"{timestamp},{ip},infection\n")
```

**配置远端蜜罐日志传输（推荐）:**
```bash
# 在远端蜜罐上设置日志输出为CSV格式
# 然后使用rsync同步
rsync -avz remote:/var/log/mozi/ logs/mozi/
```

详细迁移步骤见 `MIGRATION_GUIDE.md`

## 📈 性能监控

### 查看实时统计
```bash
# 每60秒输出一次统计
tail -f log_processor.log | grep "STATISTICS" -A 20
```

输出示例：
```
============================================================
STATISTICS
============================================================
Uptime: 0:05:23.456789
Total lines: 1234
Processed lines: 987
Errors: 2
IP queries: 345
Cache hit rate: 85.50%
[asruex] Written: 456, Buffer: 12
[mozi] Written: 531, Buffer: 0
============================================================
```

### 查看文件位置
```bash
cat log_processor/.file_positions.json
```

### 查看缓存统计
在Python交互环境：
```python
from log_processor.enricher import IPEnricher
enricher = IPEnricher()
# ... 使用后 ...
print(enricher.get_stats())
```

## 🛑 停止和重启

### 优雅停止
```bash
# 按 Ctrl+C
# 或发送SIGTERM信号
kill -TERM <pid>
```

会触发：
1. 停止文件监控
2. 刷新所有缓冲数据
3. 打印最终统计
4. 退出

### 重启
```bash
python main.py
```

会自动：
1. 从上次位置继续读取
2. 恢复IP缓存
3. 继续处理

## 🔥 生产环境部署

### 使用systemd（Linux）
```bash
# 创建服务文件
sudo nano /etc/systemd/system/botnet-processor.service
```

内容：
```ini
[Unit]
Description=Botnet Log Processor
After=network.target mysql.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/backend/log_processor
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动：
```bash
sudo systemctl daemon-reload
sudo systemctl enable botnet-processor
sudo systemctl start botnet-processor
sudo systemctl status botnet-processor
```

### 使用nohup
```bash
cd log_processor
nohup python main.py > processor.log 2>&1 &
```

## 📚 文档索引

| 文档 | 说明 |
|------|------|
| [QUICKSTART.md](log_processor/QUICKSTART.md) | 5分钟快速开始 |
| [README.md](log_processor/README.md) | 模块详细说明 |
| [ARCHITECTURE.md](log_processor/ARCHITECTURE.md) | 系统架构设计 |
| [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) | 详细迁移指南 |
| [SUMMARY.md](log_processor/SUMMARY.md) | 改造总结 |
| [logs/README.md](logs/README.md) | 日志格式规范 |

## ⚠️ 注意事项

1. **日志格式必须正确**：`timestamp,ip,event_type,extras...`
2. **文件编码必须是UTF-8**
3. **数据库用户需要CREATE TABLE权限**
4. **确保IP数据库文件存在**：`ip_location/IP_city_single_WGS84.awdb`
5. **建议配置监控告警**

## 🐛 常见问题

### Q: 日志没有被处理？
**A:** 检查：
1. 文件是否在正确目录？
2. 文件名是`.txt`结尾？
3. 文件编码是UTF-8？
4. 查看`log_processor.log`错误信息

### Q: IP信息都是"未知"？
**A:** 检查：
1. `IP_city_single_WGS84.awdb`文件存在？
2. 运行`test_processor.py`测试

### Q: 数据库连接失败？
**A:** 检查：
1. MySQL服务运行中？
2. 数据库配置正确？
3. 用户权限足够？

### Q: 处理器占用内存太高？
**A:** 调整配置：
```python
# config.py
IP_CACHE_SIZE = 5000    # 减小缓存
DB_BATCH_SIZE = 50      # 减小批量
```

## 🎯 核心优势

✅ **统一架构** - 所有僵尸网络使用相同流程
✅ **完整IP信息** - 所有僵尸网络都有地理位置
✅ **实时处理** - 文件监控，即时响应
✅ **高性能** - 缓存+批量处理
✅ **易扩展** - 添加新僵尸网络仅需配置
✅ **断点续传** - 重启后自动恢复
✅ **文档完善** - 详细的使用说明

## 📞 技术支持

遇到问题？
1. 查看 `log_processor.log`
2. 运行 `test_processor.py` 测试
3. 检查文档中的故障排查部分
4. 查看架构文档了解原理

---

**祝使用愉快！** 🎉

