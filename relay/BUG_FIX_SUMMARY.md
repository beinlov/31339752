# 中转服务器推送失败问题修复总结

## 🐛 问题描述

**现象**：中转服务器在尝试几次上传失败后就不再上传那批数据了

**根本原因**：重试条件判断错误，导致失败3轮后的数据永久被放弃

---

## 🔧 修复内容

### 1. 核心逻辑修复

**文件**: `data_storage.py`

**修改前**：
```python
# retry_count < 3 的条件过于严格
cursor.execute("""
    UPDATE data_records 
    SET status = 'pending'
    WHERE status = 'failed' AND retry_count < ?
""", (max_retries,))  # max_retries 默认为 3
```

**修改后**：
```python
# ✅ 使用 <= 并增加默认重试轮数到 20
cursor.execute("""
    UPDATE data_records 
    SET status = 'pending'
    WHERE status = 'failed' AND retry_count <= ?
""", (max_retries,))  # max_retries 默认改为 20
```

**效果**：
- 修复前：推送失败3轮（retry_count=3）后，数据永久被放弃
- 修复后：最多重试20轮（100分钟），给网络恢复充足时间

---

### 2. 添加告警机制

**新增功能**：当数据重试次数超过阈值时自动告警

```python
# 统计即将被放弃的数据
if abandoned_count > 0:
    logger.warning("=" * 70)
    logger.warning(f"⚠️ 数据推送告警")
    logger.warning(f"   {abandoned_count} 条数据已超过最大重试次数")
    logger.warning("=" * 70)
```

**效果**：运维人员能及时发现问题

---

### 3. 配置参数优化

**新增配置项**: `storage_max_retries`

```json
{
  "pusher": {
    "max_retries": 3,              // 单次推送的立即重试次数
    "storage_max_retries": 20      // 失败数据的最大重试轮数（新增）
  }
}
```

**说明**：
- `max_retries`：每次推送失败时立即重试3次（2秒、4秒、8秒）
- `storage_max_retries`：定期重试失败数据，最多20轮（每轮间隔5分钟）

---

### 4. 监控工具

**新增脚本**: `check_failed_data.py`

```bash
# 查看失败数据统计
python3 check_failed_data.py

# 指定数据库路径
python3 check_failed_data.py --db ./relay_cache.db

# 手动重置所有失败数据
python3 check_failed_data.py --reset

# 重置高重试次数的数据
python3 check_failed_data.py --reset-threshold 20
```

**功能**：
- 查看失败数据统计
- 按重试次数分组
- 识别即将被放弃的数据
- 手动重置失败数据

---

## 📊 修复前后对比

### 时间轴对比

| 时间 | 修复前 | 修复后 |
|------|--------|--------|
| T=0 | 拉取100条数据 | 拉取100条数据 |
| T=5s | 推送失败，retry_count=1 | 推送失败，retry_count=1 |
| T=305s | 重试（retry_count < 3 ✅） | 重试（retry_count <= 20 ✅） |
| T=310s | 推送失败，retry_count=2 | 推送失败，retry_count=2 |
| T=605s | 重试（retry_count < 3 ✅） | 重试（retry_count <= 20 ✅） |
| T=610s | 推送失败，retry_count=3 | 推送失败，retry_count=3 |
| T=905s | ❌ 不重试（retry_count=3 不满足 < 3） | ✅ 重试（retry_count=3 满足 <= 20） |
| T=1205s | ❌ 永久放弃 | ✅ 继续重试（最多20轮） |
| ... | ❌ 数据丢失 | ✅ 数据持续重试，直到成功或超过20轮 |

### 重试次数对比

| 场景 | 修复前 | 修复后 |
|------|--------|--------|
| **最大重试轮数** | 3轮 | 20轮 |
| **总重试时间** | 15分钟 | 100分钟 |
| **每轮间隔** | 5分钟 | 5分钟 |
| **数据丢失风险** | 高（15分钟后放弃） | 低（100分钟后才放弃） |

---

## ✅ 验证方法

### 1. 模拟平台不可达

```bash
# 1. 启动C2服务器
cd /home/spider/31339752/pull_mode
./start_c2_server.sh

# 2. 不启动平台服务器（模拟不可达）

# 3. 启动中转服务器
cd /home/spider/31339752/relay
./start_relay.sh

# 4. 观察日志（等待15分钟）
tail -f relay_service.log | grep -E "重试|失败"
```

**预期结果**：
- 修复前：15分钟后停止重试，数据被放弃
- 修复后：持续重试100分钟

### 2. 检查失败数据

```bash
cd /home/spider/31339752/relay

# 查看当前状态
python3 check_failed_data.py

# 输出示例：
# 【失败数据统计（按重试次数）】
# 重试次数     数量        最早创建
# 1           50         2026-04-14 10:10:00
# 2           30         2026-04-14 10:15:00
# 3           20         2026-04-14 10:20:00  ← 修复前会停在这里
# 4           10         2026-04-14 10:25:00  ← 修复后继续
```

### 3. 网络恢复测试

```bash
# 在上述测试运行中（数据已积累失败）
# 启动平台服务器
cd /home/spider/31339752/backend
python3 main.py

# 观察中转服务器日志
# 预期：下一轮maintenance_cycle时（最多5分钟）
#       失败数据被改回pending并成功推送
```

---

## 📋 部署清单

### 已修改文件

1. ✅ `relay/data_storage.py` - 核心逻辑修复
2. ✅ `relay/relay_service.py` - 配置参数调整
3. ✅ `relay/relay_config.json` - 添加新配置项
4. ✅ `relay/relay_config_example.json` - 配置示例更新

### 新增文件

1. ✅ `relay/check_failed_data.py` - 失败数据监控工具
2. ✅ `relay/WORKFLOW_ANALYSIS.md` - 详细流程分析文档
3. ✅ `relay/BUG_FIX_SUMMARY.md` - 本文档

### 需要操作

1. 停止中转服务器（如果正在运行）
2. 更新代码（已完成）
3. 检查配置文件中的 `storage_max_retries` 参数（默认20）
4. 重启中转服务器

```bash
cd /home/spider/31339752/relay

# 停止服务（如果正在运行）
pkill -f relay_service.py

# 检查配置
grep storage_max_retries relay_config.json

# 启动服务
./start_relay.sh

# 监控日志
tail -f relay_service.log
```

---

## 🔍 故障排查

### 如果仍然有数据被放弃

**原因**：可能 `storage_max_retries` 设置过小

**解决**：
```bash
# 1. 检查配置
cat relay_config.json | grep storage_max_retries

# 2. 增加重试轮数
vim relay_config.json
# 修改 "storage_max_retries": 50

# 3. 手动重置被放弃的数据
python3 check_failed_data.py --reset-threshold 20

# 4. 重启服务
pkill -f relay_service.py
./start_relay.sh
```

### 如果需要永久重试

**方案**：设置极大的重试轮数

```json
{
  "pusher": {
    "storage_max_retries": 999999  // 实际上永不放弃
  }
}
```

**风险**：数据库可能积累大量失败数据，需定期清理

---

## 📊 监控建议

### 定期检查（建议每日）

```bash
# 检查失败数据状态
cd /home/spider/31339752/relay
python3 check_failed_data.py > daily_check.txt

# 如果有告警，及时处理
```

### 告警阈值

- **警告**：retry_count > 10（50分钟未成功）
- **严重**：retry_count > 20（100分钟未成功，即将放弃）

### Cron任务示例

```bash
# 每小时检查一次
0 * * * * cd /home/spider/31339752/relay && python3 check_failed_data.py | grep -E "警告|严重" && echo "需要关注" | mail -s "中转服务器告警" admin@example.com
```

---

## 🎯 总结

### 问题根源
- ❌ 重试条件 `retry_count < 3` 过于严格
- ❌ 推送失败3轮后数据被永久放弃

### 修复效果
- ✅ 改为 `retry_count <= 20`，支持20轮重试
- ✅ 总重试时间从15分钟增加到100分钟
- ✅ 添加告警机制，及时发现问题
- ✅ 提供监控工具，方便故障排查

### 生产环境建议
1. 设置 `storage_max_retries = 50`（250分钟 = 4小时）
2. 配置告警通知（邮件/钉钉）
3. 定期运行 `check_failed_data.py` 检查
4. 监控平台服务器可用性

---

**修复完成！现在数据不会轻易被放弃了。** ✅
