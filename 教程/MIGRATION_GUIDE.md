# 僵尸网络日志处理系统迁移指南

## 概述

本文档说明如何从旧的分散式日志处理系统迁移到新的统一日志处理架构。

## 系统对比

### 旧系统架构
```
Asruex: 远端C2服务器 → ashttpd/logtail.py → dbhlp_access.py → 数据库
其他: Excel文件 → generate_ip.py → data_num.py → 数据库
```

**问题：**
- 数据来源不统一（日志 vs Excel）
- 代码分散，难以维护
- 仅asruex有IP地理信息查询
- 其他僵尸网络为批量导入，非实时

### 新系统架构
```
所有僵尸网络: 远端蜜罐 → 日志传输 → logs/{type}/ → log_processor → 数据库
```

**优势：**
- 统一的日志处理流程
- 所有僵尸网络都有IP地理信息
- 实时处理所有日志
- 模块化设计，易于维护和扩展

## 迁移步骤

### 步骤1: 准备工作

#### 1.1 安装新依赖
```bash
pip install pymysql watchdog awaits
```

#### 1.2 验证IP查询模块
确认 `backend/ip_location/IP_city_single_WGS84.awdb` 文件存在：
```bash
ls -l backend/ip_location/IP_city_single_WGS84.awdb
```

#### 1.3 配置数据库
编辑 `backend/log_processor/config.py`，确认数据库配置正确：
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_password",  # 修改为实际密码
    "database": "botnet"
}
```

### 步骤2: 配置远端日志传输

#### 2.1 Asruex日志传输
将原来的 `ashttpd` C2服务器的日志传输到本地：

**选项A: 使用rsync（推荐）**
```bash
# 在远端服务器上设置定时任务
*/5 * * * * rsync -avz /path/to/remote/logdir/ user@local:/path/to/botnet/backend/logs/asruex/
```

**选项B: 使用scp**
```bash
# 定时脚本
scp remote:/path/to/logdir/*.txt /path/to/botnet/backend/logs/asruex/
```

**选项C: 直接在本地运行C2服务器**
修改 `ashttpd/httpd.py` 的日志输出目录：
```python
logdir = '../logs/asruex'  # 修改为新的日志目录
```

#### 2.2 其他僵尸网络日志传输
为Mozi、Andromeda等僵尸网络配置日志传输：

1. **在远端蜜罐上配置日志输出**
   确保日志格式为：`timestamp,ip,event_type,extras...`

2. **设置日志同步**
   ```bash
   # 示例：Mozi日志同步
   rsync -avz remote:/var/log/mozi/ /path/to/botnet/backend/logs/mozi/
   ```

3. **验证日志格式**
   ```bash
   # 查看示例日志
   head backend/logs/mozi/2025-10-29.txt
   ```

### 步骤3: 数据迁移（可选）

#### 3.1 迁移现有Excel数据
如果需要将现有的Excel数据转换为日志格式：

```python
# 示例脚本：excel_to_log.py
import pandas as pd
from datetime import datetime

df = pd.read_excel('moobot2024.xlsx')
with open('backend/logs/moobot/2025-10-29.txt', 'w') as f:
    for _, row in df.iterrows():
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ip = row['IP地址']
        f.write(f"{timestamp},{ip},infection\n")
```

#### 3.2 迁移已有日志数据
```bash
# 复制asruex现有日志
cp -r backend/ashttpd/logdir/*.txt backend/logs/asruex/
```

### 步骤4: 启动新系统

#### 4.1 测试运行
```bash
cd backend/log_processor
python main.py
```

观察输出，确认：
- ✅ 日志目录被正确监控
- ✅ 日志被正确解析
- ✅ IP信息查询正常
- ✅ 数据成功写入数据库

#### 4.2 验证数据库
```sql
-- 检查节点数据
SELECT * FROM botnet_nodes_asruex LIMIT 10;
SELECT * FROM botnet_nodes_mozi LIMIT 10;

-- 检查数据量
SELECT COUNT(*) as count FROM botnet_nodes_asruex;
SELECT COUNT(*) as count FROM botnet_nodes_mozi;
```

#### 4.3 查看日志
```bash
tail -f log_processor.log
```

### 步骤5: 生产环境部署

#### 5.1 使用systemd（Linux）
创建服务文件 `/etc/systemd/system/botnet-processor.service`：
```ini
[Unit]
Description=Botnet Log Processor
After=network.target mysql.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/botnet/backend/log_processor
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable botnet-processor
sudo systemctl start botnet-processor
sudo systemctl status botnet-processor
```

#### 5.2 使用screen/tmux
```bash
cd backend/log_processor
screen -S botnet-processor
python main.py
# 按 Ctrl+A, D 分离会话

# 重新连接
screen -r botnet-processor
```

#### 5.3 使用nohup
```bash
cd backend/log_processor
nohup python main.py > processor.log 2>&1 &
```

### 步骤6: 废弃旧系统

#### 6.1 停止旧程序
```bash
# 停止asruex日志处理
pkill -f logtail.py

# 停止其他处理脚本
# ...
```

#### 6.2 备份旧代码（可选）
```bash
mkdir -p backup/old_system
cp -r backend/ashttpd backup/old_system/
cp backend/generate_ip.py backup/old_system/
cp backend/data_num.py backup/old_system/
```

#### 6.3 清理说明
以下文件可以废弃（但建议先备份）：
- `backend/ashttpd/logtail.py` - 被log_processor替代
- `backend/ashttpd/dbhlp_access.py` - 被db_writer.py替代
- `backend/ashttpd/dbhlp_clean.py` - 被db_writer.py替代
- `backend/generate_ip.py` - Excel导入方式已废弃
- `backend/data_num.py` - 统计功能已集成
- `backend/log_db/dblog.py` - 测试模块，已废弃

保留的文件：
- `backend/ashttpd/httpd.py` - C2服务器（如果还在使用）
- `backend/ip_location/` - IP查询模块（新系统依赖）
- `backend/router/` - API路由（查询功能）
- `backend/main.py` - FastAPI主程序

## 配置新僵尸网络

添加新的僵尸网络类型非常简单：

### 1. 编辑配置文件
在 `backend/log_processor/config.py` 中添加：
```python
'new_botnet': {
    'log_dir': os.path.join(LOGS_DIR, 'new_botnet'),
    'important_events': ['infection', 'beacon', 'attack'],
    'enabled': True,
    'description': '新僵尸网络描述'
}
```

### 2. 创建日志目录
```bash
mkdir -p backend/logs/new_botnet
```

### 3. 配置日志传输
将远端日志传输到 `backend/logs/new_botnet/`

### 4. 重启处理器
```bash
# 重启服务即可自动识别新的僵尸网络
sudo systemctl restart botnet-processor
```

## 监控和维护

### 查看实时统计
```bash
tail -f log_processor.log | grep "STATISTICS"
```

### 检查文件位置记录
```bash
cat backend/log_processor/.file_positions.json
```

### 清空缓存（如果需要）
```python
# 在Python交互环境中
from log_processor.enricher import IPEnricher
enricher = IPEnricher()
enricher.clear_cache()
```

### 手动刷新数据库
如果需要强制刷新所有缓冲数据：
```bash
# 发送SIGTERM信号会触发优雅关闭和最终刷新
kill -TERM <pid>
```

## 故障排查

### 问题1: 日志文件未被处理
**症状**: 新日志文件添加后没有被处理

**解决方案**:
1. 检查文件权限：`ls -l backend/logs/*/`
2. 检查文件编码：`file backend/logs/*/2025-10-29.txt`
3. 查看日志：`grep ERROR log_processor.log`

### 问题2: IP查询失败
**症状**: 大量"Failed to query IP info"错误

**解决方案**:
1. 确认awdb文件存在：`ls -l backend/ip_location/IP_city_single_WGS84.awdb`
2. 测试IP查询模块：
   ```bash
   cd backend/ip_location
   python ip_query.py
   ```

### 问题3: 数据库写入失败
**症状**: "Error flushing to database"错误

**解决方案**:
1. 检查数据库连接：`mysql -h localhost -u root -p`
2. 检查用户权限：
   ```sql
   SHOW GRANTS FOR 'root'@'localhost';
   ```
3. 检查表是否存在：
   ```sql
   SHOW TABLES LIKE 'botnet_nodes_%';
   ```

### 问题4: 内存使用过高
**症状**: 处理器占用内存过多

**解决方案**:
1. 减小缓存大小：编辑`config.py`
   ```python
   IP_CACHE_SIZE = 5000  # 从10000减小
   ```
2. 减小批量大小：
   ```python
   DB_BATCH_SIZE = 50  # 从100减小
   ```

## 性能优化建议

### 1. 数据库优化
```sql
-- 为常用查询添加索引
ALTER TABLE botnet_nodes_asruex ADD INDEX idx_country_city (country, city);
ALTER TABLE botnet_nodes_asruex ADD INDEX idx_timestamp (created_at);
```

### 2. 日志轮转
定期清理旧日志文件：
```bash
# 删除30天前的日志
find backend/logs/ -name "*.txt" -mtime +30 -delete
```

### 3. 分表策略
对于数据量特别大的僵尸网络，考虑按月分表：
```sql
CREATE TABLE botnet_nodes_asruex_202510 LIKE botnet_nodes_asruex;
CREATE TABLE botnet_nodes_asruex_202511 LIKE botnet_nodes_asruex;
```

## 回滚方案

如果新系统出现严重问题，可以临时回滚：

### 1. 停止新系统
```bash
sudo systemctl stop botnet-processor
```

### 2. 恢复旧脚本
```bash
cd backend/ashttpd
python logtail.py --logdir=./logdir
```

### 3. 排查问题
查看新系统日志，找出问题根源

### 4. 修复后重新启动
```bash
sudo systemctl start botnet-processor
```

## 总结

新系统的主要改进：
✅ 统一的日志处理架构
✅ 所有僵尸网络都有完整的IP地理信息
✅ 实时处理，无需手动导入
✅ 模块化设计，易于扩展
✅ 更好的性能（缓存、批量处理）
✅ 完善的监控和统计

如有问题，请查看：
- `backend/log_processor/README.md` - 模块说明
- `backend/logs/README.md` - 日志格式规范
- `log_processor.log` - 运行日志



