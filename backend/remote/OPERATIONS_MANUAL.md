# 运维手册

## 📋 日常检查清单

### 每日检查（5分钟）
- [ ] 检查程序是否正常运行
- [ ] 查看今日处理日志
- [ ] 确认上传成功次数
- [ ] 检查待上传队列大小

### 每周检查（15分钟）
- [ ] 检查磁盘空间
- [ ] 清理过期日志文件
- [ ] 查看去重效率
- [ ] 检查持久化文件大小

### 每月检查（30分钟）
- [ ] 性能分析和优化
- [ ] 检查是否需要调整阈值
- [ ] 备份重要配置文件
- [ ] 检查系统资源使用

---

## 🔍 监控指标

### 关键指标

#### 1. 待上传IP数量
```bash
# 查看实时数据
tail -f /tmp/remote_uploader.log | grep "待上传IP"
```

**健康标准**：
- ✅ 正常: < 1000
- ⚠️ 警告: 1000 - 5000
- 🔴 严重: > 5000

**处理方法**：
```bash
# 如果持续高位，检查网络
ping your-server.com

# 检查上传日志
grep "上传" /tmp/remote_uploader.log | tail -20
```

---

#### 2. 队列文件大小
```bash
# 查看队列文件大小
ls -lh /tmp/pending_upload_queue.json
```

**健康标准**：
- ✅ 正常: < 10MB
- ⚠️ 警告: 10 - 50MB
- 🔴 严重: > 50MB

**处理方法**：
```bash
# 查看队列内容
cat /tmp/pending_upload_queue.json | python -m json.tool | head -50

# 如果积压严重，手动触发上传
python3 remote_uploader.py once
```

---

#### 3. 上传失败率
```bash
# 统计失败次数
grep "上传失败" /tmp/remote_uploader.log | wc -l
```

**健康标准**：
- ✅ 正常: 0
- ⚠️ 警告: 1-3次/天
- 🔴 严重: > 3次/天

**处理方法**：
```bash
# 查看失败原因
grep "上传失败\|认证失败\|权限不足" /tmp/remote_uploader.log

# 检查网络连接
curl -I https://your-server.com
```

---

#### 4. 内存使用
```bash
# 查看程序内存使用
top -p $(pgrep -f remote_uploader)

# 或者
ps aux | grep remote_uploader
```

**健康标准**：
- ✅ 正常: < 200MB
- ⚠️ 警告: 200 - 500MB
- 🔴 严重: > 500MB

**处理方法**：
```bash
# 检查是否有内存压力告警
grep "内存压力" /tmp/remote_uploader.log

# 如果持续高位，考虑降低阈值
# 编辑 remote_uploader.py
MAX_MEMORY_IPS = 5000  # 降低到5000
```

---

## 🚨 告警处理

### 告警1: 内存压力警告
```
⚠️ 内存压力警告: 待上传数据 8000 超过阈值 5000
```

**原因**：
- 上传速度 < 读取速度
- 网络不稳定
- 服务器响应慢

**处理**：
1. 检查网络连接
2. 查看服务器负载
3. 等待自动强制上传
4. 如果持续，调整 `FORCE_UPLOAD_THRESHOLD`

---

### 告警2: 服务器离线
```
⚠️ 服务器离线（第 5 次检测），将在 60 秒后重试...
```

**原因**：
- 服务器宕机
- 网络故障
- API端点变更

**处理**：
```bash
# 1. 检查服务器状态
curl -I https://your-server.com

# 2. 检查网络
ping your-server.com

# 3. 检查API密钥
grep "API_KEY" config.json

# 4. 查看详细错误
grep "服务器" /tmp/remote_uploader.log | tail -20
```

---

### 告警3: 认证失败
```
✗ 认证失败: API密钥无效
```

**原因**：
- API密钥错误
- API密钥过期
- 服务器配置变更

**处理**：
```bash
# 1. 检查config.json中的API密钥
cat config.json | grep api_key

# 2. 联系服务器管理员确认密钥
# 3. 更新密钥后重启
```

---

### 告警4: 队列积压
```
💾 队列文件: 45.2 MB
```

**原因**：
- 长时间上传失败
- 网络长时间中断
- 服务器长时间离线

**处理**：
```bash
# 1. 检查是什么原因导致积压
grep "上传失败\|服务器离线" /tmp/remote_uploader.log

# 2. 解决根本问题后，手动运行
python3 remote_uploader.py once

# 3. 观察队列是否减少
watch -n 10 'ls -lh /tmp/pending_upload_queue.json'
```

---

## 🛠️ 常见问题处理

### 问题1: 程序无响应
```bash
# 1. 检查进程
ps aux | grep remote_uploader

# 2. 查看最后的日志
tail -50 /tmp/remote_uploader.log

# 3. 如果卡住，强制退出
kill -9 $(pgrep -f remote_uploader)

# 4. 重启（数据会自动恢复）
python3 remote_uploader.py once &
```

---

### 问题2: 数据一直不上传
```bash
# 1. 检查待上传数量
grep "待上传IP" /tmp/remote_uploader.log | tail -1

# 2. 检查是否达到上传阈值
# 默认需要100条才开始上传

# 3. 强制上传（修改阈值）
# 临时解决：手动触发
python3 remote_uploader.py once
```

---

### 问题3: 重复处理相同文件
```bash
# 1. 检查偏移量文件
cat /tmp/file_offsets.json | python -m json.tool

# 2. 查看是否正常递增
# 应该看到文件路径和对应的偏移量

# 3. 如果偏移量没更新，检查上传日志
grep "安全保存偏移量" /tmp/remote_uploader.log
```

---

### 问题4: 不完整行越来越多
```bash
# 1. 查看不完整行缓存
cat /tmp/incomplete_lines.json | python -m json.tool

# 2. 正常情况：1-3个文件
# 3. 如果过多，可能是日志格式问题
# 4. 检查日志文件格式是否正确
```

---

## 📝 日志分析

### 查看处理进度
```bash
# 实时查看
tail -f /tmp/remote_uploader.log

# 查看今日统计
grep "处理统计报告" /tmp/remote_uploader.log | tail -1 -A 30

# 查看上传记录
grep "✓ 上传成功" /tmp/remote_uploader.log | wc -l
```

---

### 查看错误信息
```bash
# 查看所有错误
grep "ERROR\|✗\|失败" /tmp/remote_uploader.log

# 查看最近的错误
grep "ERROR\|✗\|失败" /tmp/remote_uploader.log | tail -20

# 按时间筛选今天的错误
grep "$(date +%Y-%m-%d)" /tmp/remote_uploader.log | grep ERROR
```

---

### 分析处理效率
```bash
# 查看去重率
grep "去重率" /tmp/remote_uploader.log | tail -10

# 查看处理速度
grep "批次处理" /tmp/remote_uploader.log | tail -20

# 查看上传频率
grep "准备上传" /tmp/remote_uploader.log | tail -20
```

---

## 🔧 维护操作

### 清理操作

#### 清理日志文件（每月）
```bash
# 备份当前日志
cp /tmp/remote_uploader.log /tmp/remote_uploader_$(date +%Y%m%d).log

# 清空日志
> /tmp/remote_uploader.log

# 或删除旧备份（保留最近7天）
find /tmp -name "remote_uploader_*.log" -mtime +7 -delete
```

#### 重置状态（谨慎操作）
```bash
# 备份当前状态
mkdir -p /tmp/backup_$(date +%Y%m%d)
cp /tmp/*.json /tmp/backup_$(date +%Y%m%d)/

# 清空队列（会丢失未上传数据！）
rm /tmp/pending_upload_queue.json

# 重置偏移量（会重新读取文件！）
rm /tmp/file_offsets.json

# 重置缓存（会重新统计！）
rm /tmp/ip_cache.json
```

#### 手动恢复数据
```bash
# 如果误删除了队列文件
# 从备份恢复
cp /tmp/backup_*/pending_upload_queue.json /tmp/

# 重启程序
python3 remote_uploader.py once
```

---

### 性能优化

#### 调整上传策略（高速网络）
```python
# 编辑 remote_uploader.py 或 config.json
BATCH_SIZE = 1000              # 增加批次大小
FORCE_UPLOAD_THRESHOLD = 10000 # 提高强制阈值
MIN_UPLOAD_BATCH = 500         # 提高最小批次
```

#### 调整上传策略（低速网络）
```python
BATCH_SIZE = 200               # 减小批次大小
FORCE_UPLOAD_THRESHOLD = 2000  # 降低强制阈值
MIN_UPLOAD_BATCH = 50          # 降低最小批次
```

#### 调整内存限制（大内存服务器）
```python
MAX_MEMORY_IPS = 50000         # 增加内存限制
FORCE_UPLOAD_THRESHOLD = 20000 # 提高上传阈值
```

#### 调整缓存时间
```python
FILE_SCAN_CACHE_TTL = 600      # 文件缓存10分钟（更长）
# 或
FILE_SCAN_CACHE_TTL = 60       # 文件缓存1分钟（更短）
```

---

## 📊 性能监控脚本

### 创建监控脚本
```bash
cat > /tmp/monitor.sh << 'EOF'
#!/bin/bash

echo "========================================="
echo "远程上传器监控报告"
echo "时间: $(date)"
echo "========================================="

# 检查进程
if pgrep -f remote_uploader > /dev/null; then
    echo "✓ 程序运行中"
    PID=$(pgrep -f remote_uploader)
    echo "  PID: $PID"
    
    # 内存使用
    MEM=$(ps aux | grep $PID | grep -v grep | awk '{print $4}')
    echo "  内存: $MEM%"
else
    echo "✗ 程序未运行"
fi

# 队列文件大小
if [ -f /tmp/pending_upload_queue.json ]; then
    SIZE=$(du -h /tmp/pending_upload_queue.json | cut -f1)
    echo "✓ 队列文件: $SIZE"
else
    echo "ℹ 队列文件: 不存在"
fi

# 最近的统计
echo ""
echo "最近统计:"
tail -100 /tmp/remote_uploader.log | grep "待上传IP\|累计上传" | tail -5

# 最近错误
ERRORS=$(grep "ERROR\|失败" /tmp/remote_uploader.log | tail -5)
if [ -n "$ERRORS" ]; then
    echo ""
    echo "⚠️ 最近错误:"
    echo "$ERRORS"
fi

echo "========================================="
EOF

chmod +x /tmp/monitor.sh
```

### 使用监控脚本
```bash
# 运行
/tmp/monitor.sh

# 定时运行（每小时）
echo "0 * * * * /tmp/monitor.sh >> /tmp/monitor_report.log 2>&1" | crontab -

# 查看监控历史
tail -100 /tmp/monitor_report.log
```

---

## 🔔 告警脚本

### 创建告警脚本
```bash
cat > /tmp/alert.sh << 'EOF'
#!/bin/bash

# 检查队列大小
QUEUE_SIZE=$(stat -c%s /tmp/pending_upload_queue.json 2>/dev/null || echo 0)
QUEUE_MB=$((QUEUE_SIZE / 1024 / 1024))

if [ $QUEUE_MB -gt 50 ]; then
    echo "🔴 告警: 队列文件过大 ($QUEUE_MB MB)"
    # 这里可以发送邮件或其他通知
fi

# 检查错误率
ERROR_COUNT=$(grep "ERROR" /tmp/remote_uploader.log | tail -100 | wc -l)
if [ $ERROR_COUNT -gt 10 ]; then
    echo "🔴 告警: 错误率过高 ($ERROR_COUNT 个错误)"
fi

# 检查进程
if ! pgrep -f remote_uploader > /dev/null; then
    echo "🔴 告警: 程序未运行"
fi
EOF

chmod +x /tmp/alert.sh
```

---

## 📚 快速参考

### 常用命令
```bash
# 启动程序（单次）
python3 remote_uploader.py once

# 启动程序（持续）
python3 remote_uploader.py forever &

# 查看实时日志
tail -f /tmp/remote_uploader.log

# 查看统计报告
grep "处理统计报告" /tmp/remote_uploader.log | tail -1 -A 30

# 查看队列大小
ls -lh /tmp/pending_upload_queue.json

# 重启程序
kill $(pgrep -f remote_uploader); python3 remote_uploader.py once &
```

### 重要文件位置
```
程序文件: remote_uploader.py
配置文件: config.json
运行日志: /tmp/remote_uploader.log
队列文件: /tmp/pending_upload_queue.json
偏移量:   /tmp/file_offsets.json
IP缓存:   /tmp/ip_cache.json
不完整行: /tmp/incomplete_lines.json
```

---

## 📞 联系支持

### 故障升级流程
1. 尝试自行解决（参考本手册）
2. 收集日志和错误信息
3. 联系技术支持
4. 提供详细的环境信息

### 需要提供的信息
- 错误日志（最近100行）
- 配置文件（隐藏API密钥）
- 系统信息（内存、磁盘、网络）
- 复现步骤

---

**定期查看本手册，保持系统健康运行！** 📖
