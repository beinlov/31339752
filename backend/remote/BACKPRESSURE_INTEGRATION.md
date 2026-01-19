# C2端缓存背压控制 - 集成指南

## 📊 问题背景

**当前问题**：
- C2端按固定时间间隔（60秒）读取日志
- 不管平台是否拉取，都会持续添加到缓存
- 如果平台拉取慢或不拉取，缓存会无限增长

**优化目标**：
- 动态控制日志读取速度
- 根据缓存量调整读取行为
- 防止内存和磁盘无限占用

---

## ✅ 解决方案：背压控制（Backpressure）

### 核心思想

```
                    全速读取区          节流区             暂停区
                  ←──────────────→  ←──────────→  ←──────────────→
缓存量:    0  ────────────  2000 ─────────  8000 ─────────  10000
           │               │              │              │
读取量:    5000条/次       按比例缩放      0条（暂停）    0条（超限）
           100%            100% → 0%      停止           停止
```

### 三种状态

| 缓存量 | 行为 | 读取量 | 说明 |
|-------|------|--------|------|
| 0 - 2000 | ✅ 全速读取 | 5000条 | 缓存充足，全速读取 |
| 2000 - 8000 | ⚠️ 节流读取 | 5000 → 0条 | 按比例缩减读取量 |
| 8000 - 10000 | ❌ 暂停读取 | 0条 | 背压触发，暂停读取 |
| > 10000 | 🚫 强制停止 | 0条 | 缓存超限，停止读取 |

---

## 📝 代码集成步骤

### 步骤1: 修改 `c2_data_server.py` 导入

在文件开头添加：

```python
# 在 c2_data_server.py 顶部导入
from cache_backpressure import BackpressureController
```

---

### 步骤2: 修改 `BackgroundLogReader` 初始化

```python
class BackgroundLogReader:
    """后台日志读取器"""
    
    def __init__(self, cache: DataCache):
        self.cache = cache
        self.log_reader = LogReader(LOG_DIR, LOG_FILE_PATTERN)
        self.ip_processor = IPProcessor(BOTNET_TYPE)
        self.running = False
        
        # 从配置读取参数
        cache_config = CONFIG.get('cache', {})
        self.read_interval = CONFIG.get('processing', {}).get('read_interval', 60)
        
        # 【新增】初始化背压控制器
        self.backpressure = BackpressureController({
            'max_cached_records': cache_config.get('max_cached_records', 10000),
            'high_watermark': cache_config.get('high_watermark', 8000),
            'low_watermark': cache_config.get('low_watermark', 2000),
            'read_batch_size': cache_config.get('read_batch_size', 5000),
            'adaptive_read': cache_config.get('adaptive_read', True)
        })
        
        logger.info(f"初始化日志读取器 (带背压控制):")
        logger.info(f"  - 读取间隔: {self.read_interval}秒")
```

---

### 步骤3: 修改 `read_logs()` 方法

```python
async def read_logs(self):
    """读取日志文件（支持背压控制）"""
    try:
        # 【新增】获取当前缓存量
        stats = self.cache.get_stats()
        current_cached = stats['cached_records']
        
        # 【新增】检查是否应该跳过读取
        should_skip, reason = self.backpressure.should_skip_read(current_cached)
        
        if should_skip:
            logger.info(f"⏸️  跳过本次读取: {reason}")
            return  # 提前返回，不读取日志
        
        # 【新增】计算本次应该读取的数量
        read_limit, read_reason = self.backpressure.calculate_read_size(current_cached)
        logger.info(f"📖 开始读取: {read_reason}, 限制{read_limit}条")
        
        # 获取日志文件（现有代码）
        log_files = await self.log_reader.get_available_log_files(
            days_back=self.lookback_config.get('max_days'),
            include_current=True
        )
        
        if not log_files:
            return
        
        new_records = []
        files_read = 0
        
        # 读取文件
        for file_datetime, file_path in log_files:
            # ... 现有的文件读取逻辑 ...
            
            # 【修改】限制读取量
            if len(new_records) >= read_limit:
                logger.info(f"达到读取限制 {read_limit} 条，停止本次读取")
                break
        
        # 添加到缓存
        if new_records:
            self.cache.add_records(new_records)
            new_stats = self.cache.get_stats()
            logger.info(f"✅ 新增 {len(new_records)} 条, 当前缓存: {new_stats['cached_records']} 条")
            
            # 【新增】每10次输出一次统计
            if files_read % 10 == 0:
                self.backpressure.log_stats()
    
    except Exception as e:
        logger.error(f"读取日志失败: {e}", exc_info=True)
```

---

## 🎯 配置示例

### 保守配置（适合小服务器）

```json
{
  "cache": {
    "max_cached_records": 5000,
    "high_watermark": 4000,
    "low_watermark": 1000,
    "read_batch_size": 2000,
    "adaptive_read": true
  }
}
```

### 标准配置（推荐）

```json
{
  "cache": {
    "max_cached_records": 10000,
    "high_watermark": 8000,
    "low_watermark": 2000,
    "read_batch_size": 5000,
    "adaptive_read": true
  }
}
```

### 激进配置（适合大服务器）

```json
{
  "cache": {
    "max_cached_records": 50000,
    "high_watermark": 40000,
    "low_watermark": 10000,
    "read_batch_size": 10000,
    "adaptive_read": true
  }
}
```

---

## 📊 运行效果

### 场景1: 平台正常拉取

```
[2026-01-16 14:00:00] 📖 开始读取: 全速读取(1500/2000), 限制5000条
[2026-01-16 14:00:05] ✅ 新增 5000 条, 当前缓存: 6500 条
[2026-01-16 14:01:00] 📖 开始读取: 节流读取(5000条,缩放50%), 限制2500条
[2026-01-16 14:01:05] ✅ 新增 2500 条, 当前缓存: 7500 条
[2026-01-16 14:02:00] 📖 开始读取: 全速读取(1000/2000), 限制5000条
```

### 场景2: 平台未拉取（触发背压）

```
[2026-01-16 14:00:00] 📖 开始读取: 全速读取(1500/2000), 限制5000条
[2026-01-16 14:00:05] ✅ 新增 5000 条, 当前缓存: 6500 条
[2026-01-16 14:01:00] 📖 开始读取: 节流读取(6500条,缩放25%), 限制1250条
[2026-01-16 14:01:05] ✅ 新增 1250 条, 当前缓存: 7750 条
[2026-01-16 14:02:00] ⏸️  跳过本次读取: 背压暂停(8500/8000)
[2026-01-16 14:03:00] ⏸️  跳过本次读取: 背压暂停(8500/8000)
[平台开始拉取...]
[2026-01-16 14:04:00] 📖 开始读取: 全速读取(1500/2000), 限制5000条
```

---

## 🔍 监控与调试

### 1. 查看背压统计

日志会每10次读取输出一次统计：

```
背压统计: 暂停15.0%, 节流30.0%, 全速55.0%
```

### 2. 查看缓存状态

访问 `/api/stats` 接口：

```json
{
  "cached_records": 6500,
  "pulled_records": 25000,
  "cache_full": false,
  "backpressure_stats": {
    "paused_rate": "15.0%",
    "throttled_rate": "30.0%",
    "full_speed_rate": "55.0%"
  }
}
```

### 3. 监控缓存趋势

```bash
# 实时监控缓存量
watch -n 5 'curl -s http://localhost:8888/api/stats | jq ".cached_records"'
```

---

## ⚙️ 调优建议

### 问题1: 缓存经常满

**症状**：日志显示频繁"暂停读取"

**解决**：
1. 增大 `max_cached_records`
2. 降低 `high_watermark` 比例（如改为60%）
3. 检查平台拉取频率是否过低

### 问题2: 缓存经常空

**症状**：日志显示频繁"全速读取"，但缓存量很低

**解决**：
1. 减小 `read_batch_size`
2. 增加 `read_interval`（降低读取频率）
3. 检查日志产生速度是否过慢

### 问题3: 数据延迟高

**症状**：平台查询的数据比实际日志滞后

**解决**：
1. 提高 `high_watermark`（延迟暂停时机）
2. 增大 `max_cached_records`
3. 提高平台拉取频率

---

## ✅ 总结

### 优点

| 特性 | 效果 |
|------|------|
| ✅ 防止内存溢出 | 缓存有上限 |
| ✅ 自动调节 | 根据拉取速度动态调整 |
| ✅ 平滑过渡 | 节流区避免频繁暂停/恢复 |
| ✅ 可配置 | 根据服务器性能调整 |
| ✅ 可观测 | 统计信息辅助调优 |

### 最佳实践

1. **高水位线** = 最大缓存 × 0.8
2. **低水位线** = 最大缓存 × 0.2
3. **读取批量** = 平台拉取量的1-2倍
4. **监控缓存量**：定期查看 `/api/stats`
5. **调整配置**：根据实际运行情况调优

---

## 🚀 快速开始

1. **复制文件**：
   ```bash
   cp cache_backpressure.py /your/c2/path/
   cp config_example_with_backpressure.json /your/c2/path/config.json
   ```

2. **修改配置**：根据服务器性能调整参数

3. **集成代码**：按照上述步骤修改 `c2_data_server.py`

4. **测试运行**：
   ```bash
   python cache_backpressure.py  # 测试背压控制器
   python c2_data_server.py      # 启动服务
   ```

5. **监控运行**：查看日志中的背压统计信息
