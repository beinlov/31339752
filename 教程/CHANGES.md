# 更新日志

## 2025-10-30 - 数据去重机制实现

### 🎯 新增功能：双层数据去重

为防止日志重复处理导致数据库重复记录，实现了完善的双层去重机制。

#### 1. 应用层去重（内存缓存）

**实现位置**: `backend/log_processor/db_writer.py`

**特性**:
- 为每条记录生成唯一标识：`f"{ip}|{timestamp}|{event_type}"`
- 使用 `set` 数据结构快速检查是否已处理
- 实时统计重复记录数量
- 避免不必要的数据库操作

**限制**: 仅在当前运行期间有效，重启后缓存清空

#### 2. 数据库层去重（唯一约束）

**实现方式**:
- 在表创建时添加唯一约束：`UNIQUE KEY idx_unique_record (ip, created_at)`
- 使用 `INSERT IGNORE` 自动跳过重复记录
- 统计数据库层跳过的记录数

**优势**: 永久有效，即使系统重启也能防止重复

#### 3. 部署工具

新增以下文件：

| 文件 | 用途 |
|------|------|
| `clean_duplicates.sql` | 清理现有重复数据的SQL脚本 |
| `add_unique_constraint.sql` | 为现有表添加唯一约束 |
| `setup_deduplication.sh` | Linux/Mac自动部署脚本 |
| `setup_deduplication.bat` | Windows自动部署脚本 |
| `DEDUPLICATION.md` | 详细技术文档（9个场景分析） |
| `DEDUPLICATION_SUMMARY.md` | 快速参考指南 |

#### 4. 统计信息增强

**输出示例**:
```
[asruex] Written: 1000, Duplicates: 50 (4.76%), Buffer: 0
```

**新增字段**:
- `duplicate_count`: 重复记录数
- `duplicate_rate`: 去重率百分比
- `processed_cache_size`: 缓存大小

#### 5. 文档更新

更新了以下文档：
- ✅ `QUICKSTART.md` - 添加去重部署步骤
- ✅ `README.md` - 说明去重机制
- ✅ `CHANGES.md` - 本更新日志

### 📦 修改的文件

1. **backend/log_processor/db_writer.py**
   - 添加 `processed_records` 集合
   - 添加 `duplicate_count` 计数器
   - 在 `add_node()` 中实现应用层去重检查
   - 修改 `_insert_nodes()` 使用 `INSERT IGNORE`
   - 在表创建时添加唯一约束
   - 更新 `get_stats()` 包含去重信息

2. **backend/log_processor/main.py**
   - 更新统计信息输出格式
   - 显示去重率和重复记录数

### 🚀 部署步骤

#### 新系统（全新安装）
无需额外操作，新表自动包含唯一约束 ✅

#### 现有系统（迁移）

**步骤 1**: 备份数据库
```bash
mysqldump -u root -p botnet > botnet_backup.sql
```

**步骤 2**: 清理重复数据
```bash
# Linux/Mac
mysql -u root -p botnet < log_processor/clean_duplicates.sql

# Windows
mysql -u root -p botnet < log_processor\clean_duplicates.sql
```

**步骤 3**: 添加唯一约束
```bash
# Linux/Mac
mysql -u root -p botnet < log_processor/add_unique_constraint.sql

# Windows
mysql -u root -p botnet < log_processor\add_unique_constraint.sql
```

**一键部署（推荐）**:
```bash
# Linux/Mac
cd backend/log_processor
./setup_deduplication.sh

# Windows
cd backend\log_processor
setup_deduplication.bat
```

### ✅ 验证

#### 1. 检查唯一约束
```sql
SHOW INDEX FROM botnet_nodes_asruex WHERE Key_name = 'idx_unique_record';
```

#### 2. 验证无重复数据
```sql
SELECT ip, created_at, COUNT(*) as count
FROM botnet_nodes_asruex
GROUP BY ip, created_at
HAVING count > 1;
-- 应返回0行
```

#### 3. 查看去重统计
```bash
tail -f log_processor.log | grep "Duplicates"
```

### 📊 去重效果预期

| 去重率 | 状态 | 说明 |
|--------|------|------|
| 0-5% | ✅ 正常 | 偶尔的重复，属于正常范围 |
| 5-20% | ⚠️ 关注 | 可能有日志重传，需要关注 |
| >20% | ❌ 异常 | 日志传输配置可能有问题 |

### 🎓 技术要点

1. **去重键设计**: 使用 `(ip, created_at)` 而非 `(ip, created_at, event_type)`
   - 原因：同一IP在同一秒通常不会产生多个不同事件
   - 好处：更严格的去重，避免数据膨胀
   - 如有需要可调整为三字段组合

2. **性能考虑**:
   - 应用层：O(1) 查找，几乎无性能影响
   - 数据库层：唯一索引略降插入速度（约5-10%），但整体收益大于成本

3. **内存管理**:
   - 每条记录约100字节
   - 100万条记录约100MB内存
   - 可配置定期清理策略

### 📚 相关文档

- **详细说明**: `backend/log_processor/DEDUPLICATION.md`
- **快速参考**: `backend/log_processor/DEDUPLICATION_SUMMARY.md`
- **快速开始**: `backend/log_processor/QUICKSTART.md`

---

## 2025-10-30 - Bug修复和启动脚本

### 🐛 Bug修复

#### 1. 修复事件循环错误
**问题**: 启动时出现 `RuntimeError: no running event loop`

**修复**:
- 修改 `log_processor/watcher.py` 的 `process_existing_logs()` 方法为异步方法
- 修改 `log_processor/main.py` 使用 `loop.run_until_complete()` 调用

**影响文件**:
- `backend/log_processor/watcher.py` (第177-202行)
- `backend/log_processor/main.py` (第183行)

### 🚀 新增功能

#### 1. 一键启动脚本

**Windows (`start_all.bat`)**:
- 自动启动日志处理器
- 自动启动FastAPI后端
- 自动启动前端界面
- 每个服务在独立窗口运行

**Linux/Mac (`start_all.sh`)**:
- 后台启动所有服务
- 保存PID到文件
- 输出日志到 `.log` 文件
- 提供停止脚本 (`stop_all.sh`)

#### 2. 系统启动指南

新增 `STARTUP_GUIDE.md` 文档，包含：
- 快速启动方法
- 服务验证步骤
- 数据流测试
- 常见问题解决
- 开发/生产环境配置

### 📝 使用说明

#### 快速启动（Windows）
```batch
# 在 backend 目录下双击或运行
start_all.bat
```

#### 快速启动（Linux/Mac）
```bash
# 在 backend 目录下
chmod +x start_all.sh stop_all.sh
./start_all.sh

# 停止所有服务
./stop_all.sh
```

#### 验证服务
1. 日志处理器: 查看窗口输出，应显示 "Botnet Log Processor is running"
2. FastAPI后端: 访问 http://localhost:8000/docs
3. 前端界面: 访问 http://localhost:3000

### 🔧 技术细节

#### 修复前的错误
```python
# watcher.py (错误)
def process_existing_logs(self):
    # ...
    asyncio.create_task(handler._process_file(filepath))  # ❌ 事件循环未运行
```

#### 修复后的代码
```python
# watcher.py (正确)
async def process_existing_logs(self):
    # ...
    await handler._process_file(filepath)  # ✅ 直接await调用
```

```python
# main.py (正确)
# 在事件循环中运行
loop.run_until_complete(self.watcher.process_existing_logs())  # ✅
```

### 📊 系统架构说明

系统需要**3个组件同时运行**：

```
1. log_processor/main.py  - 日志处理器（监控日志，写入数据库）
2. backend/main.py        - FastAPI后端（提供API接口）
3. fronted/               - 前端界面（可视化展示）
```

**数据流**:
```
远端日志 → logs/ → 日志处理器 → 数据库 → FastAPI后端 → 前端界面
```

### ⚠️ 重要提示

1. **必须同时运行3个服务**
   - 日志处理器负责数据写入
   - FastAPI后端负责数据查询
   - 前端负责数据展示

2. **启动顺序建议**
   - 先启动日志处理器
   - 再启动FastAPI后端
   - 最后启动前端

3. **数据库配置**
   - 确保 `log_processor/config.py` 中数据库配置正确
   - 确保MySQL服务运行中

4. **端口占用**
   - FastAPI后端: 8000
   - 前端: 3000（或npm配置的端口）
   - 日志处理器: 无端口（后台运行）

### 📚 相关文档

- [STARTUP_GUIDE.md](STARTUP_GUIDE.md) - 系统启动指南
- [README_NEW_SYSTEM.md](README_NEW_SYSTEM.md) - 新系统使用指南
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 迁移指南

### 🎯 下一步

1. 运行启动脚本测试系统
2. 添加测试日志验证数据流
3. 查看前端界面确认数据显示
4. 配置远端日志传输（如需要）

### 🐛 已知问题

无

### 💡 建议

1. 开发环境使用 `start_all.bat/sh` 快速启动
2. 生产环境使用 systemd 或 Windows Service
3. 定期查看日志文件排查问题
4. 配置监控告警系统

---

**更新完成！** 现在可以使用一键启动脚本快速启动整个系统了。

