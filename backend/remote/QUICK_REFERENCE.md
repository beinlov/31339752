# Remote Uploader 快速参考指南

## 🚀 快速开始

### 1. 测试改进
```bash
cd backend/remote
python test_improvements.py
```

### 2. 运行程序
```bash
# 测试模式（推荐首次运行）
python remote_uploader.py test

# 单次执行
python remote_uploader.py once

# 持续运行
python remote_uploader.py
```

---

## 🔍 关键改进速查

### 文件轮转检测
**触发条件**: 
- 文件 inode 变化（文件被替换）
- 文件大小变小（文件被截断）

**自动处理**:
- 重置偏移量为 0
- 清除不完整行缓存
- 记录警告日志

**日志示例**:
```
检测到文件轮转（inode变化）: /path/to/log.log
文件已轮转，从头开始读取
```

---

### 文件稳定性检查
**检查步骤**:
1. 修改时间 > 300秒
2. 文件大小连续两次检查不变（间隔5秒）

**配置调整**:
```python
FILE_STABILITY_MARGIN = 300  # 修改时间阈值
FILE_SIZE_STABLE_CHECK_INTERVAL = 5  # 大小检查间隔
```

---

### 事务性上传
**三阶段流程**:
```
1. 标记阶段: get_new_ips_for_upload()
   └─ 数据标记为 uploading_ips

2. 上传阶段: upload_ips()
   └─ 发送到服务器

3. 确认/回滚:
   ├─ 成功: confirm_uploaded_ips() → 清理数据
   └─ 失败: rollback_uploading_ips() → 保留数据
```

**数据安全保证**:
- 上传前持久化到磁盘
- 失败时数据保留在队列
- 崩溃后可从磁盘恢复

---

### 不完整行管理
**数据结构**:
```python
{
    'file_path': {
        'line': 'incomplete line content',
        'timestamp': 1702800000.0
    }
}
```

**自动清理**:
- 每次 `run_once()` 结束时触发
- 清理超过 24 小时的不完整行
- 兼容旧格式自动转换

**配置**:
```python
INCOMPLETE_LINES_MAX_AGE_HOURS = 24
```

---

### 时间戳提取策略
**三级回退**:
```
1. 解析日志行首时间戳
   ├─ 格式1: YYYY/MM/DD HH:MM:SS
   └─ 格式2: YYYY-MM-DD HH:MM:SS

2. 从文件名提取
   ├─ 格式1: *_YYYY-MM-DD_HH.*
   └─ 格式2: *_YYYY-MM-DD.*

3. 使用文件修改时间
   └─ file.stat().st_mtime

4. 最后使用当前时间（不推荐）
```

---

## 📊 监控指标

### 关键日志关键词
```bash
# 成功指标
grep "✓ 上传成功" /tmp/remote_uploader.log
grep "确认上传成功" /tmp/remote_uploader.log

# 问题指标
grep "文件轮转" /tmp/remote_uploader.log
grep "回滚" /tmp/remote_uploader.log
grep "上传失败" /tmp/remote_uploader.log
grep "清理过期" /tmp/remote_uploader.log
```

### 状态文件检查
```bash
# 查看待上传队列
cat /tmp/pending_upload_queue.json | jq '.count'

# 查看文件偏移量
cat /tmp/file_offsets.json | jq '.'

# 查看文件身份缓存
cat /tmp/file_identities.json | jq '.'

# 查看不完整行
cat /tmp/incomplete_lines.json | jq '.'
```

---

## 🛠️ 故障排查

### 问题1: 数据重复上传
**可能原因**:
- 文件轮转未检测到
- 偏移量保存失败

**排查步骤**:
```bash
# 1. 检查文件身份缓存
cat /tmp/file_identities.json

# 2. 检查偏移量
cat /tmp/file_offsets.json

# 3. 查看日志
grep "文件轮转\|偏移量" /tmp/remote_uploader.log
```

**解决方案**:
- 删除缓存文件重新开始
- 检查文件系统是否支持 inode

---

### 问题2: 数据丢失
**可能原因**:
- 上传成功但未确认
- 持久化失败

**排查步骤**:
```bash
# 1. 检查待上传队列
cat /tmp/pending_upload_queue.json | jq '.count'

# 2. 查看上传日志
grep "上传\|确认\|回滚" /tmp/remote_uploader.log | tail -20

# 3. 检查磁盘空间
df -h /tmp
```

**解决方案**:
- 数据在队列中：等待下次上传
- 队列为空但服务器无数据：检查上传日志确认是否真正成功

---

### 问题3: 内存占用过高
**可能原因**:
- 不完整行未清理
- 待上传队列过大

**排查步骤**:
```bash
# 1. 检查不完整行数量
cat /tmp/incomplete_lines.json | jq 'length'

# 2. 检查队列大小
ls -lh /tmp/pending_upload_queue.json

# 3. 查看内存使用
ps aux | grep remote_uploader
```

**解决方案**:
```python
# 手动清理不完整行
rm /tmp/incomplete_lines.json

# 强制上传队列数据
python remote_uploader.py once
```

---

### 问题4: 文件读取不完整
**可能原因**:
- 文件还在写入
- 稳定性检查不足

**排查步骤**:
```bash
# 查看跳过的文件
grep "跳过不稳定\|跳过当前小时" /tmp/remote_uploader.log
```

**解决方案**:
```python
# 增加稳定性检查时间
FILE_STABILITY_MARGIN = 600  # 改为10分钟
FILE_SIZE_STABLE_CHECK_INTERVAL = 10  # 改为10秒
```

---

## 🔧 配置优化建议

### 高频场景（每小时几万条）
```python
BATCH_SIZE = 1000  # 增大批次
FORCE_UPLOAD_THRESHOLD = 10000  # 提高阈值
MIN_UPLOAD_BATCH = 500  # 提高最小批次
FILE_SCAN_CACHE_TTL = 60  # 缩短缓存时间
```

### 低频场景（每小时几百条）
```python
BATCH_SIZE = 100  # 减小批次
FORCE_UPLOAD_THRESHOLD = 500  # 降低阈值
MIN_UPLOAD_BATCH = 50  # 降低最小批次
FILE_SCAN_CACHE_TTL = 600  # 延长缓存时间
```

### 不稳定网络
```python
MAX_RETRIES = 5  # 增加重试次数
RETRY_DELAY = 60  # 延长重试间隔
UPLOAD_FAILURE_BACKOFF = 120  # 延长退避时间
```

---

## 📈 性能基准

### 预期性能（参考值）
- **读取速度**: 10,000 行/秒
- **处理速度**: 8,000 IP/秒
- **上传速度**: 500 条/秒（取决于网络）
- **内存占用**: < 200MB（正常情况）

### 性能测试
```bash
# 测试读取性能
time python remote_uploader.py once

# 监控内存
watch -n 1 'ps aux | grep remote_uploader'

# 监控队列大小
watch -n 5 'cat /tmp/pending_upload_queue.json | jq .count'
```

---

## 🔐 安全检查清单

- [ ] API_KEY 已配置且保密
- [ ] 日志文件权限正确（600 或 640）
- [ ] 临时文件目录有足够空间（/tmp）
- [ ] 网络连接使用 HTTPS
- [ ] 定期清理旧日志文件
- [ ] 监控异常上传行为

---

## 📞 紧急处理

### 立即停止程序
```bash
pkill -f remote_uploader.py
```

### 保存当前状态
```bash
cp /tmp/pending_upload_queue.json ~/backup_queue_$(date +%Y%m%d_%H%M%S).json
cp /tmp/file_offsets.json ~/backup_offsets_$(date +%Y%m%d_%H%M%S).json
```

### 重置状态（谨慎）
```bash
rm /tmp/uploader_state.json
rm /tmp/file_offsets.json
rm /tmp/file_identities.json
rm /tmp/incomplete_lines.json
# 注意：不要删除 pending_upload_queue.json，除非确认数据已上传
```

---

## 📚 相关文档

- [完整改进说明](./IMPROVEMENTS_SUMMARY.md)
- [测试脚本](./test_improvements.py)
- [配置文件示例](./config.json)

---

**最后更新**: 2025-12-17  
**版本**: v2.0 (改进版)
