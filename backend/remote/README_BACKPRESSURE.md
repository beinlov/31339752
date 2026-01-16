# C2端缓存背压控制 - 使用说明

## 🎯 功能概述

已将背压控制逻辑直接集成到 `c2_data_server.py` 中，无需额外文件。

### 核心功能

✅ **智能背压控制**：根据缓存量动态调整日志读取速度  
✅ **防止内存溢出**：缓存有明确上限，不会无限增长  
✅ **平滑过渡**：三级水位线（全速/节流/暂停）避免频繁开关  
✅ **完全配置化**：通过 config.json 灵活调整参数  
✅ **实时监控**：统计信息帮助调优

---

## 📦 部署文件

只需要两个文件：

```
c2_data_server.py  ← C2服务器主程序（已集成背压控制）
config.json        ← 配置文件（包含背压参数）
```

---

## ⚙️ 配置说明

### 背压控制参数（cache 部分）

```json
{
  "cache": {
    "max_cached_records": 10000,   // 最大缓存（硬限制）
    "high_watermark": 8000,        // 高水位线（80%）
    "low_watermark": 2000,         // 低水位线（20%）
    "read_batch_size": 5000,       // 基础读取量
    "adaptive_read": true,         // 启用自适应模式
    "db_file": "/tmp/c2_data_cache.db",
    "retention_days": 7
  }
}
```

### 参数说明

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `max_cached_records` | 最大缓存记录数 | 10000（可根据内存调整） |
| `high_watermark` | 达到此值暂停读取 | max × 0.8 |
| `low_watermark` | 低于此值全速读取 | max × 0.2 |
| `read_batch_size` | 每次最多读取量 | 5000 |
| `adaptive_read` | 是否启用智能模式 | true（推荐） |

---

## 🚀 快速开始

### 1. 部署文件

```bash
# 上传两个文件到C2服务器
scp c2_data_server.py user@c2_server:/path/to/c2/
scp config.json user@c2_server:/path/to/c2/
```

### 2. 修改配置

```bash
# 编辑配置文件
vim config.json

# 必改项：
# - botnet.botnet_type: 僵尸网络类型
# - botnet.log_dir: 日志文件目录
# - botnet.log_file_pattern: 日志文件命名模式
# - http_server.api_key: API密钥（或使用环境变量）

# 可选项（根据服务器性能调整）：
# - cache.max_cached_records: 最大缓存量
# - cache.high_watermark: 高水位线
# - cache.low_watermark: 低水位线
```

### 3. 启动服务

```bash
# 方法1: 直接启动
python3 c2_data_server.py

# 方法2: 后台运行
nohup python3 c2_data_server.py > c2_server.log 2>&1 &

# 方法3: 使用systemd（推荐生产环境）
sudo systemctl start c2-data-server
```

---

## 📊 运行效果

### 场景1: 平台正常拉取

```
[2026-01-16 14:00:00] 背压控制器初始化:
[2026-01-16 14:00:00]   - 最大缓存: 10000 条
[2026-01-16 14:00:00]   - 高水位线: 8000 条 (80%)
[2026-01-16 14:00:00]   - 低水位线: 2000 条 (20%)
[2026-01-16 14:00:00]   - 基础读取量: 5000 条
[2026-01-16 14:00:00]   - 自适应模式: 启用

[2026-01-16 14:01:00] 📖 开始读取: 全速读取(1500/2000), 限制 5000 条
[2026-01-16 14:01:05] ✅ 新增 5000 条, 当前缓存: 6500 条

[2026-01-16 14:02:00] 📖 开始读取: 节流读取(缓存5000条,速度50%), 限制 2500 条
[2026-01-16 14:02:05] ✅ 新增 2500 条, 当前缓存: 7000 条

[2026-01-16 14:03:00] 📖 开始读取: 全速读取(1000/2000), 限制 5000 条
```

### 场景2: 平台未拉取（触发背压）

```
[2026-01-16 14:00:00] 📖 开始读取: 全速读取(1500/2000), 限制 5000 条
[2026-01-16 14:00:05] ✅ 新增 5000 条, 当前缓存: 6500 条

[2026-01-16 14:01:00] 📖 开始读取: 节流读取(缓存6500条,速度25%), 限制 1250 条
[2026-01-16 14:01:05] ✅ 新增 1250 条, 当前缓存: 7750 条

[2026-01-16 14:02:00] ⏸️  跳过本次读取: 背压暂停(8500/8000)
[2026-01-16 14:03:00] ⏸️  跳过本次读取: 背压暂停(8500/8000)

[平台开始拉取...]

[2026-01-16 14:04:00] 📖 开始读取: 全速读取(1500/2000), 限制 5000 条
```

---

## 🔍 监控与调试

### 1. 查看实时日志

```bash
# 查看最新日志
tail -f c2_server.log

# 过滤背压相关日志
tail -f c2_server.log | grep -E '背压|开始读取|跳过'
```

### 2. 查看统计信息

```bash
# 访问统计接口
curl -s http://localhost:8888/api/stats | jq

# 输出示例：
{
  "cached_records": 6500,          # 当前缓存量
  "pulled_records": 25000,         # 已拉取总数
  "total_generated": 31500,        # 总生成数
  "total_pulled": 25000,           # 总拉取数
  "cache_full": false,             # 是否缓存满
  "backpressure_stats": {          # 背压统计
    "total_decisions": 100,
    "paused_count": 15,
    "throttled_count": 30,
    "full_speed_count": 55,
    "paused_rate": "15.0%",        # 暂停比例
    "throttled_rate": "30.0%",     # 节流比例
    "full_speed_rate": "55.0%"     # 全速比例
  }
}
```

### 3. 监控缓存趋势

```bash
# 实时监控缓存量（每5秒刷新）
watch -n 5 'curl -s http://localhost:8888/api/stats | jq ".cached_records"'

# 监控背压状态
watch -n 5 'curl -s http://localhost:8888/api/stats | jq ".backpressure_stats"'
```

---

## 🔧 配置调优

### 场景1: 服务器内存小（< 2GB）

```json
{
  "cache": {
    "max_cached_records": 5000,
    "high_watermark": 4000,
    "low_watermark": 1000,
    "read_batch_size": 2000
  }
}
```

### 场景2: 标准服务器（2-8GB）

```json
{
  "cache": {
    "max_cached_records": 10000,
    "high_watermark": 8000,
    "low_watermark": 2000,
    "read_batch_size": 5000
  }
}
```

### 场景3: 大服务器（> 8GB）

```json
{
  "cache": {
    "max_cached_records": 50000,
    "high_watermark": 40000,
    "low_watermark": 10000,
    "read_batch_size": 10000
  }
}
```

### 场景4: 平台拉取慢

```json
{
  "cache": {
    "max_cached_records": 20000,    // 增大最大缓存
    "high_watermark": 18000,        // 延迟暂停时机
    "low_watermark": 5000,          // 提高全速阈值
    "read_batch_size": 5000
  }
}
```

---

## ⚠️ 常见问题

### Q1: 日志显示频繁"暂停读取"

**原因**：平台拉取速度慢，缓存持续满

**解决**：
1. 增大 `max_cached_records`（如20000）
2. 检查平台拉取频率和batch_size
3. 增加平台Worker数量

### Q2: 缓存量一直很低

**原因**：日志产生速度慢，或读取间隔过长

**解决**：
1. 检查日志文件是否有新数据
2. 减小 `processing.read_interval`（如30秒）
3. 检查 `botnet.log_file_pattern` 是否匹配

### Q3: 数据延迟高

**原因**：背压限制过于激进

**解决**：
1. 提高 `high_watermark`（如90%）
2. 增大 `max_cached_records`
3. 减小 `processing.read_interval`

### Q4: 简单模式 vs 自适应模式

**简单模式**（`adaptive_read: false`）：
- 优点：逻辑简单，易理解
- 缺点：可能频繁暂停/恢复
- 适用：测试环境、小规模部署

**自适应模式**（`adaptive_read: true`）：
- 优点：平滑过渡，避免震荡
- 缺点：略复杂
- 适用：生产环境、大规模部署

---

## 📈 性能对比

### 无背压控制

```
时间    缓存量      内存      状态
0s      1,500      15MB     正常
60s     6,500      65MB     正常
120s    11,500     115MB    正常
180s    16,500     165MB    正常
240s    21,500     215MB    ⚠️ 增长
300s    26,500     265MB    ❌ 可能OOM
```

### 有背压控制

```
时间    缓存量      内存      状态
0s      1,500      15MB     ✅ 全速读取
60s     6,500      65MB     ✅ 全速读取
120s    8,500      85MB     ⚠️ 背压暂停
180s    8,500      85MB     ⏸️ 等待拉取
240s    3,000      30MB     ✅ 恢复读取
300s    7,000      70MB     ⚠️ 节流读取（50%速度）
```

---

## ✅ 总结

### 优势

| 特性 | 效果 |
|------|------|
| ✅ 防止内存溢出 | 缓存有上限，不会OOM |
| ✅ 自动调节 | 根据拉取速度动态调整 |
| ✅ 平滑过渡 | 避免频繁暂停/恢复 |
| ✅ 完全配置化 | 灵活适配不同环境 |
| ✅ 实时监控 | 统计信息辅助调优 |
| ✅ 零额外文件 | 只需2个文件即可部署 |

### 最佳实践

1. **初始配置**：使用标准配置（10000/8000/2000）
2. **监控运行**：观察背压统计，看暂停/节流比例
3. **调整参数**：根据实际情况调优
4. **定期检查**：每周查看统计信息

---

## 🆘 技术支持

如有问题，请查看：
- 服务器日志：`c2_server.log`
- 统计接口：`http://C2_IP:8888/api/stats`
- 健康检查：`http://C2_IP:8888/health`
