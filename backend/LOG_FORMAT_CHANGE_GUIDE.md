# 日志格式变更与断点续传增强指南

**变更日期**: 2026-01-13  
**版本**: v2.0  
**变更类型**: 日志格式优化 + 断点续传增强

---

## 📋 变更概述

### 1. 日志生成频率变更
```
旧方案：按小时生成
文件名：ramnit_2026-01-13_14.log (每天24个文件)

新方案：按天生成 (推荐)
文件名：ramnit_20260113.log (每天1个文件)
```

### 2. C2端读取逻辑增强
```
旧逻辑：硬编码48小时回溯（超过48小时的数据会丢失）
新逻辑：支持无限回溯（可读取所有历史数据）
```

### 3. 文件处理机制优化
```
旧机制：processed_files标记（一个文件只读一次）
新机制：file_positions指针（同一文件可增量读取）
```

---

## ✅ 解决的核心问题

### 问题1：平台长时间停运导致数据丢失 ❌
**场景**:
```
Day 1-5: 平台停运维护
Day 6:   平台恢复上线
结果：   旧逻辑只能回溯48小时，Day 1-3的数据丢失
```

**解决方案** ✅:
```python
# config.py
C2_LOG_LOOKBACK_CONFIG = {
    'mode': 'unlimited',  # 无限回溯模式
    'max_days': 90,       # 或限制为90天
}

# C2端会读取所有未处理的历史日志
# 即使停运7天，恢复后也能完整拉取
```

### 问题2：按天日志无法持续读取新内容 ❌
**场景**:
```
ramnit_20260113.log
├─ 14:00 写入100行 → C2读取 → 标记为processed
├─ 15:00 写入100行 → C2跳过（已标记）❌
└─ 16:00 写入100行 → C2跳过（已标记）❌
```

**解决方案** ✅:
```python
# 改用文件指针模式
self.file_positions = {
    '/var/log/botnet/ramnit_20260113.log': 12345  # 上次读到第12345字节
}

# 每次从上次位置继续读取
await f.seek(last_position)  # 跳到上次位置
# ... 读取新内容 ...
self.file_positions[file_key] = await f.tell()  # 保存新位置
```

---

## 🔧 配置文件变更

### 新增配置项 (`backend/config.py`)

```python
# ============================================================
# C2端日志读取配置
# ============================================================

C2_LOG_LOOKBACK_CONFIG = {
    'mode': 'unlimited',  # 'unlimited': 无限回溯, 'limited': 限制天数
    'max_days': 90,       # limited模式下的最大回溯天数
    'description': '无限回溯模式：C2端会读取所有未处理的历史日志文件，适合长时间停运后恢复'
}
```

### 配置说明

| 模式 | 适用场景 | 说明 |
|------|----------|------|
| `unlimited` | 生产环境（推荐） | 读取所有历史日志，无论多久之前 |
| `limited` | 测试环境/磁盘受限 | 只回溯指定天数（如90天） |

---

## 📝 代码变更详情

### 1. LogReader类 (`backend/remote/c2_data_server.py`)

**变更前**:
```python
async def get_available_log_files(self, hours_back: int = 48):
    earliest_time = now - timedelta(hours=hours_back)  # 固定48小时
    # ...
```

**变更后**:
```python
async def get_available_log_files(self, days_back: int = None):
    if days_back is None:
        earliest_time = datetime(2000, 1, 1)  # 无限回溯
    else:
        earliest_time = now - timedelta(days=days_back)
    # ...
```

### 2. 日志文件名格式支持

**新增按天格式（优先）**:
```python
# 支持 {date} 格式（按天）- 推荐
if '{date}' in self.file_pattern:
    file_date = datetime.strptime(date_str, '%Y%m%d')
    # 例如: ramnit_20260113.log
```

**保留按小时格式（兼容）**:
```python
# 支持 {datetime} 格式（按小时）- 兼容旧格式
elif '{datetime}' in self.file_pattern:
    file_datetime = datetime.strptime(datetime_str, '%Y-%m-%d_%H')
    # 例如: ramnit_2026-01-13_14.log
```

### 3. BackgroundLogReader类

**变更前**:
```python
self.processed_files = set()  # 标记已处理的文件

for file_path in log_files:
    if file_path in self.processed_files:
        continue  # 跳过已处理的文件
    
    # 读取整个文件...
    self.processed_files.add(file_path)  # 标记为已处理
```

**变更后**:
```python
self.file_positions = {}  # 记录文件读取位置

for file_path in log_files:
    last_position = self.file_positions.get(file_path, 0)
    
    # 从上次位置继续读取
    await f.seek(last_position)
    # ... 读取新内容 ...
    self.file_positions[file_path] = await f.tell()  # 保存新位置
```

---

## 🚀 部署步骤

### 步骤1：修改C2端日志生成逻辑

**方案A：修改日志配置（推荐）**
```bash
# 修改logrotate或日志生成脚本
# 旧格式：ramnit_YYYYMMDD_HH.log
# 新格式：ramnit_YYYYMMDD.log

# 例如：修改僵尸网络程序的日志配置
LOG_FILE=/var/log/botnet/ramnit_$(date +%Y%m%d).log
```

**方案B：保持不变（兼容模式）**
```bash
# 如果无法修改C2端日志生成逻辑
# 可以继续使用按小时格式
# 新代码完全兼容旧格式
```

### 步骤2：更新C2端服务代码

```bash
# 1. 停止C2服务
pkill -f c2_data_server.py

# 2. 备份旧代码
cp c2_data_server.py c2_data_server.py.bak

# 3. 更新代码
# (将新的c2_data_server.py上传到C2服务器)

# 4. 更新配置文件
# (将新的config.py中的C2_LOG_LOOKBACK_CONFIG添加进去)

# 5. 启动服务
python3 c2_data_server.py &
```

### 步骤3：验证功能

```bash
# 检查C2端日志
tail -f /var/log/c2_data_server.log

# 应该看到类似输出：
# [INFO] 回溯配置: unlimited
# [INFO] 无限回溯模式：将读取所有历史日志文件
# [INFO] 发现 7 个可处理的日志文件
# [INFO] 读取日志文件: ramnit_20260106.log (从位置 0 继续)
# [INFO] 读取日志文件: ramnit_20260107.log (从位置 0 继续)
# ...
```

---

## 📊 验证测试

### 测试用例1：长时间停运后恢复

**测试步骤**:
```bash
# 1. 模拟平台停运7天
# 停止平台日志处理器（C2端继续运行）

# 2. C2端持续产生日志
# 7天内会产生7个日志文件（按天模式）

# 3. 7天后恢复平台
python backend/log_processor/main.py

# 4. 观察拉取情况
# 应该能看到从7天前开始拉取数据
```

**预期结果**:
```
✅ C2端SQLite积累了7天的数据
✅ 平台从断点（last_seq_id）继续拉取
✅ 所有7天的数据最终都被拉取到平台
✅ 没有数据丢失
```

### 测试用例2：同一天文件持续读取

**测试步骤**:
```bash
# 1. 查看初始状态
# C2: file_positions = {'/var/log/botnet/ramnit_20260113.log': 0}

# 2. 产生100行新日志（14:00）
# C2读取后: file_positions = {... : 12345}

# 3. 产生100行新日志（15:00）
# C2读取后: file_positions = {... : 24680}

# 4. 产生100行新日志（16:00）
# C2读取后: file_positions = {... : 37015}
```

**预期结果**:
```
✅ 每次都能读取新增的内容
✅ 不会重复读取已处理的行
✅ file_position持续增长
```

### 测试用例3：兼容旧格式

**测试步骤**:
```bash
# 1. 不修改C2端日志生成逻辑
# 继续使用按小时格式: ramnit_2026-01-13_14.log

# 2. 启动新版C2服务

# 3. 观察是否正常工作
```

**预期结果**:
```
✅ 自动识别按小时格式
✅ 正常读取和处理
✅ 完全兼容
```

---

## 🎯 断点续传完整流程示意

### 场景：平台停运5天后恢复

```
时间线：
Day 1 ┌────────────────────────────────────┐
      │ C2: 产生日志 → ramnit_20260108.log │
      │ 平台: 停运维护 ❌                   │
      └────────────────────────────────────┘
      
Day 2 ┌────────────────────────────────────┐
      │ C2: 产生日志 → ramnit_20260109.log │
      │ 平台: 停运维护 ❌                   │
      └────────────────────────────────────┘
      
Day 3-5: 同上...

Day 6 ┌────────────────────────────────────┐
      │ 平台: 恢复上线 ✅                   │
      │                                    │
      │ [C2端行为]                         │
      │ 1. 读取5天前的日志文件              │
      │    (无限回溯模式)                   │
      │ 2. 全部存入SQLite缓存              │
      │    - ramnit_20260108.log → SQLite  │
      │    - ramnit_20260109.log → SQLite  │
      │    - ... 共5天数据                 │
      │                                    │
      │ [平台端行为]                       │
      │ 1. 读取状态文件: last_seq_id=12000│
      │ 2. 请求C2: since_seq=12000        │
      │ 3. C2返回: seq 12001-17000 (5天数据) │
      │ 4. 平台处理并存入数据库             │
      │ 5. 更新状态: last_seq_id=17000    │
      │                                    │
      │ 结果: 5天数据完整拉取 ✅           │
      └────────────────────────────────────┘
```

### 数据流向图

```
┌─────────────────────────────────────────────────────┐
│                C2端 (您的服务器)                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  日志文件 (按天)                                     │
│  ┌──────────────────┐                              │
│  │ ramnit_20260108  │ ←── Day 1                   │
│  │ ramnit_20260109  │ ←── Day 2                   │
│  │ ramnit_20260110  │ ←── Day 3                   │
│  │ ramnit_20260111  │ ←── Day 4                   │
│  │ ramnit_20260112  │ ←── Day 5                   │
│  └──────────────────┘                              │
│          ↓                                          │
│  BackgroundLogReader (无限回溯)                     │
│  ┌─────────────────────────────┐                   │
│  │ file_positions:             │                   │
│  │  20260108.log → EOF (读完)  │                   │
│  │  20260109.log → EOF (读完)  │                   │
│  │  20260112.log → 50% (进行中)│                   │
│  └─────────────────────────────┘                   │
│          ↓                                          │
│  SQLite缓存 (持久化)                                │
│  ┌─────────────────────────────┐                   │
│  │ seq_id | ip           | ...  │                   │
│  │ 12001  | 45.123.45.67 | ...  │                   │
│  │ 12002  | 45.123.45.68 | ...  │                   │
│  │ ...    | ...          | ...  │                   │
│  │ 17000  | 45.123.45.99 | ...  │                   │
│  └─────────────────────────────┘                   │
│          ↓                                          │
│  HTTP API                                           │
│  GET /api/pull?since_seq=12000                     │
│  Response: {data: [...], max_seq_id: 17000}        │
└─────────────────────────────────────────────────────┘
          ↓ (HTTP请求)
┌─────────────────────────────────────────────────────┐
│               平台端 (数据中心)                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  RemotePuller                                       │
│  ┌─────────────────────────────┐                   │
│  │ 读取状态: last_seq_id=12000  │                   │
│  │ 请求: since_seq=12000       │                   │
│  │ 收到: seq 12001-17000       │                   │
│  │ 保存状态: last_seq_id=17000  │                   │
│  └─────────────────────────────┘                   │
│          ↓                                          │
│  IPEnricher (富化)                                  │
│  MySQL (存储)                                       │
│                                                     │
│  结果: 5天数据完整恢复 ✅                            │
└─────────────────────────────────────────────────────┘
```

---

## ⚠️ 注意事项

### 1. 磁盘空间管理

**问题**: 无限回溯可能读取大量历史文件
**解决**: 
```bash
# 定期清理旧日志（推荐30天）
find /var/log/botnet -name "*.log" -mtime +30 -delete

# 或使用logrotate自动管理
/var/log/botnet/*.log {
    daily
    rotate 30
    compress
    delaycompress
}
```

### 2. 首次部署

**场景**: 首次部署时可能有大量历史日志

**建议**:
```bash
# 方案A: 只处理最近7天（推荐）
# 修改配置为limited模式
C2_LOG_LOOKBACK_CONFIG = {
    'mode': 'limited',
    'max_days': 7
}

# 方案B: 清理过期日志后再启动
find /var/log/botnet -name "*.log" -mtime +7 -delete
```

### 3. 性能考虑

**单次读取限制**:
```python
# 代码中已实现限流
if len(new_records) >= 5000:
    break  # 单次最多5000条

if files_read >= 10:
    break  # 单次最多10个文件
```

**后果**: 如果积压太多，可能需要多个轮次才能追上

**解决**: 正常情况，5-10分钟即可追上进度

---

## 📋 验收清单

部署完成后，请确认以下项目：

- [ ] C2端日志已改为按天生成（或保持按小时兼容）
- [ ] C2端配置已添加`C2_LOG_LOOKBACK_CONFIG`
- [ ] C2端服务重启后正常运行
- [ ] 查看日志确认"无限回溯模式"已启用
- [ ] 模拟平台停运，验证数据不丢失
- [ ] 验证同一天文件可持续读取新内容
- [ ] 检查`file_positions`记录正确
- [ ] 平台能从断点正确拉取数据
- [ ] 数据库中没有重复数据
- [ ] 监控指标正常（拉取成功率>99%）

---

## 🔍 故障排查

### 问题1: C2端报错"无法加载回溯配置"

**日志**:
```
[WARNING] 无法加载回溯配置，使用默认值（无限回溯）
```

**原因**: config.py中未添加`C2_LOG_LOOKBACK_CONFIG`

**解决**: 添加配置项到config.py

### 问题2: 读取不到历史日志

**日志**:
```
[DEBUG] 发现 0 个可处理的日志文件
```

**原因**: 日志文件名格式不匹配

**检查**:
```python
# 确认LOG_FILE_PATTERN配置
# 按天格式: ramnit_{date}.log
# 按小时格式: ramnit_{datetime}.log

# 确认实际文件名
ls /var/log/botnet/
```

### 问题3: 数据重复

**现象**: 数据库中出现重复记录

**原因**: file_positions没有正确保存

**检查**:
```python
# 查看file_positions变量
logger.info(f"当前file_positions: {self.file_positions}")

# 应该看到位置持续增长
```

---

## 📚 相关文档

- `OPTIMIZATION_SUMMARY.md` - 优化总结（技术细节）
- `DATA_TRANSMISSION_GUIDE.md` - 数据传输原理（管理员版）
- `backend/config.py` - 配置文件
- `backend/remote/c2_data_server.py` - C2端源代码

---

**文档版本**: v2.0  
**最后更新**: 2026-01-13  
**变更人**: Backend Team  
**审核状态**: ✅ 待测试验证
