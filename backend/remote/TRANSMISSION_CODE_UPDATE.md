# 远端数据传输代码修改说明

**修改日期**: 2024-12-17  
**修改文件**: `backend/remote/remote_uploader.py`, `backend/remote/config.json`

## 修改概述

根据需求对远端数据传输代码进行了三项重要修改，以支持详细的节点交互数据统计和提高数据传输的可靠性。

---

## 修改内容

### 1. 移除IP去重逻辑，传输所有数据

**修改原因**:  
接收端现在需要详细的节点交互数据（单个IP在长时间内的活跃数据、连接次数等），因此不能在传输端进行IP去重。

**主要修改**:

#### 1.1 `IPProcessor`类简化
- **移除全局去重缓存**: 删除了`global_ip_cache`和`ip_last_seen`等去重相关的数据结构
- **移除`daily_ips`字典**: 只保留`daily_ips_with_time`用于存储完整的IP数据
- **简化`process_line`方法**: 不再检查IP是否重复，直接将所有IP数据添加到待上传队列

```python
# 修改前：进行去重检查
if ip in self.global_ip_cache:
    # 跳过重复IP
    return

# 修改后：不再去重，传输所有数据
self.daily_ips_with_time[log_date].append(ip_data)
```

#### 1.2 缓存管理优化
- **`load_cache()`**: 改为空操作，不再加载去重缓存
- **`save_cache()`**: 改为空操作，不再保存去重缓存
- **`clear_uploaded_ips()`**: 简化逻辑，只清理已上传的数据记录

#### 1.3 统计信息更新
- 移除"重复IP"统计
- 移除"去重率"统计
- 添加"数据保留率: 100%"提示

**影响**:
- ✅ 所有IP连接记录都会被传输到本地服务器
- ✅ 支持详细的节点交互统计分析
- ⚠️ 数据量会显著增加，需要确保接收端能够处理

---

### 2. 改为每小时生成日志文件

**修改原因**:  
- 一天生成一个日志文件，数据量太大
- 当天的日志文件在实时写入，对读取与传输可能造成影响

**主要修改**:

#### 2.1 日志文件命名格式
```python
# 修改前：按天
log_file_pattern: "ramnit_{date}.log"
# 示例：ramnit_2024-12-17.log

# 修改后：按小时
log_file_pattern: "ramnit_{datetime}.log"
# 示例：ramnit_2024-12-17_14.log (表示14点的日志)
```

#### 2.2 文件扫描逻辑增强
- **`get_log_file_path()`**: 支持`{datetime}`占位符，生成小时级别的文件路径
- **`get_available_log_files()`**: 
  - 解析`YYYY-MM-DD_HH`格式的文件名
  - 自动过滤当前小时正在写入的文件
  - 只返回上一小时及更早的完整日志文件

```python
# 计算当前小时
current_hour = now.replace(minute=0, second=0, microsecond=0)

# 只处理上一小时及更早的文件
if file_datetime < current_hour:
    files.append((file_datetime, file_path))
else:
    logger.debug(f"跳过当前小时文件（正在写入）: {file_path}")
```

#### 2.3 兼容性
代码同时支持新旧两种格式：
- 新格式：`{datetime}` - 按小时
- 旧格式：`{date}` - 按天（向后兼容）

**影响**:
- ✅ 每小时生成独立的日志文件，文件大小更易管理
- ✅ 自动跳过当前小时正在写入的文件，避免读写冲突
- ✅ 数据传输更及时，延迟最多1小时

---

### 3. 修复IP解析问题

**修改原因**:  
接收端接收到了诸如"01.10.238.162"的非标准IP（带前导零）

**主要修改**:

#### 3.1 增强`is_valid_ip()`方法
```python
def is_valid_ip(self, ip: str) -> bool:
    """验证IP地址是否有效（增强版：拒绝前导零）"""
    for part in parts:
        # 检查是否有前导零（除了单独的"0"）
        if len(part) > 1 and part[0] == '0':
            logger.debug(f"拒绝带前导零的IP: {ip} (八位组: {part})")
            return False
        
        # 检查是否为空或包含非数字字符
        if not part or not part.isdigit():
            return False
```

#### 3.2 验证规则
- ❌ 拒绝：`01.10.238.162` (第一个八位组有前导零)
- ❌ 拒绝：`192.168.01.1` (第三个八位组有前导零)
- ✅ 接受：`1.10.238.162` (标准格式)
- ✅ 接受：`192.168.0.1` (单独的0是有效的)

**影响**:
- ✅ 过滤掉非标准格式的IP地址
- ✅ 提高数据质量
- ✅ 避免接收端处理异常IP时出错

---

## 配置文件修改

### `config.json`更新

```json
{
  "botnet": {
    "botnet_type": "ramnit",
    "log_dir": "/home/ubuntu",
    "log_file_pattern": "ramnit_{datetime}.log"  // 从 {date} 改为 {datetime}
  },
  "files": {
    "state_file": "/tmp/uploader_state.json",
    "duplicate_cache_file": "/tmp/ip_cache.json",
    "offset_state_file": "/tmp/file_offsets.json",
    "log_file": "/tmp/remote_uploader.log"  // 新增
  }
}
```

---

## 部署注意事项

### 1. 日志生成端修改
⚠️ **重要**: 蜜罐服务器上的日志生成代码也需要同步修改为每小时生成一个文件

**示例Python代码**:
```python
from datetime import datetime

# 旧代码：按天生成
log_filename = f"ramnit_{datetime.now().strftime('%Y-%m-%d')}.log"

# 新代码：按小时生成
log_filename = f"ramnit_{datetime.now().strftime('%Y-%m-%d_%H')}.log"
```

**或使用cron/logrotate定期轮转**:
```bash
# 每小时执行一次
0 * * * * /path/to/rotate_log.sh
```

### 2. 接收端修改（待处理）
⚠️ 接收端代码需要进行相应修改以处理不去重的数据：
- 数据库表结构可能需要调整
- 需要支持存储同一IP的多次连接记录
- 需要实现节点交互统计逻辑

### 3. 磁盘空间监控
由于不再去重，数据量会显著增加：
- 监控`/tmp/pending_upload_queue.json`文件大小
- 监控远端服务器的磁盘使用率
- 建议设置磁盘空间告警

### 4. 测试建议
在生产环境部署前，建议进行以下测试：

```bash
# 1. 测试连接
python remote_uploader.py test

# 2. 单次执行测试
python remote_uploader.py once

# 3. 检查日志文件扫描
# 应该能看到：
# - 扫描到的小时级别日志文件
# - 跳过当前小时的提示
# - 过滤掉带前导零的IP

# 4. 正式运行
python remote_uploader.py
```

---

## 数据流变化对比

### 修改前
```
日志文件生成 (按天) 
    ↓
读取完整日志 
    ↓
IP去重 (全局) 
    ↓
上传唯一IP 
    ↓
接收端存储
```

### 修改后
```
日志文件生成 (按小时) 
    ↓
读取完整日志 (跳过当前小时) 
    ↓
不去重，保留所有记录 
    ↓
上传所有IP数据 
    ↓
接收端存储并统计
```

---

## 性能影响评估

### 数据量变化
- **去重前**: 假设每天有10万条记录，去重后可能只有1万个唯一IP
- **去重后**: 每天传输完整的10万条记录
- **数据量增加**: 约10倍（具体取决于重复率）

### 传输频率变化
- **修改前**: 每天处理1个大文件
- **修改后**: 每天处理24个小文件
- **优势**: 更及时的数据传输，更小的单次传输负载

### 内存使用
代码中设置了内存保护机制：
```python
MAX_MEMORY_IPS = 10000  # 内存中最多保留的IP数量
FORCE_UPLOAD_THRESHOLD = 5000  # 达到此数量强制上传
MIN_UPLOAD_BATCH = 100  # 最小上传批次
```

---

## 回滚方案

如果需要回滚到旧版本：

1. 恢复配置文件：
```json
"log_file_pattern": "ramnit_{date}.log"  // 改回 {date}
```

2. 使用Git回滚代码：
```bash
cd backend/remote
git checkout HEAD~1 remote_uploader.py
```

3. 重启服务

---

## 后续工作

- [ ] 修改接收端代码以支持不去重的数据
- [ ] 修改数据库表结构（如果需要）
- [ ] 实现节点交互统计功能
- [ ] 更新监控和告警系统
- [ ] 编写接收端修改文档

---

## 联系人

如有问题，请联系开发团队。

**修改完成时间**: 2024-12-17
