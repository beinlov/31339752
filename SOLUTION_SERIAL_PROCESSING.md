# 串行处理解决方案（不阻塞拉取循环）

## 🎯 目标

实现"先上线，后清除"的串行处理，同时满足：
1. ✅ 保证处理顺序：上线日志 → 清除日志
2. ✅ 不阻塞拉取循环：拉取可以继续进行
3. ✅ 避免竞态条件：同一IP的上线和清除按顺序处理

---

## ⚠️ 问题分析

### 当前代码的问题

**方式1：完全串行（当前实现）- 会阻塞**
```python
# 在process_api_data中直接await
await self._process_data_in_background(botnet_type, online_records)  # 等待2-3秒
await self._handle_cleanup_records(botnet_type, cleanup_records)     # 等待0.5秒
# ↑ 总共等待3-4秒，拉取循环被阻塞
```

**问题：**
- 处理100条IP可能需要3-4秒
- 这期间无法拉取新数据
- C2端数据积压

**方式2：完全并发（禁用队列前的实现）- 有竞态**
```python
# 创建异步任务，立即返回
asyncio.create_task(self._process_data_in_background(...))
asyncio.create_task(self._handle_cleanup_records(...))
# ↑ 两个任务并发执行，无法保证顺序
```

**问题：**
- 如果同一IP既上线又清除，最终状态不确定
- 可能先执行清除，后执行上线 → 状态错误

---

## ✅ 推荐解决方案：使用异步锁（AsyncLock）

### 原理

```
拉取循环（不阻塞）
    ↓
推送到后台任务队列（立即返回）
    ↓
后台任务获取锁（同一时间只有一个任务执行）
    ↓
任务内部：串行处理上线 → 清除
    ↓
释放锁，下一个任务开始
```

### 代码实现

```python
# backend/log_processor/main.py

class LogProcessor:
    def __init__(self, ...):
        # ... 其他初始化代码 ...
        
        # 添加处理锁，确保串行处理
        self._processing_lock = asyncio.Lock()
        
        # 存储待处理的任务
        self._processing_tasks = []
        
        logger.info("[串行处理] 已启用异步锁机制")
    
    async def process_api_data(self, botnet_type: str, ip_data: List[Dict]):
        """
        处理来自API的结构化IP数据（异步串行：不阻塞拉取，但内部串行）
        """
        if botnet_type not in self.writers:
            logger.warning(f"Unknown botnet type: {botnet_type}")
            return

        # 分流数据
        cleanup_records = []
        online_records = []
        
        for record in ip_data:
            log_type = record.get('log_type', 'online')
            if log_type == 'cleanup':
                cleanup_records.append(record)
            else:
                online_records.append(record)
        
        logger.info(
            f"[{botnet_type}] 接收数据: "
            f"上线 {len(online_records)} 条, 清除 {len(cleanup_records)} 条"
        )
        
        # 创建后台任务（不等待，立即返回）
        # 但在任务内部使用锁确保串行处理
        task = asyncio.create_task(
            self._process_with_lock(botnet_type, online_records, cleanup_records)
        )
        
        # 记录任务，用于优雅关闭
        self._processing_tasks.append(task)
        
        # 清理已完成的任务
        self._processing_tasks = [t for t in self._processing_tasks if not t.done()]
        
        logger.debug(f"[{botnet_type}] 已提交后台处理任务，当前待处理任务数: {len(self._processing_tasks)}")
        
        # 立即返回，不阻塞拉取循环
        return
    
    async def _process_with_lock(
        self, 
        botnet_type: str, 
        online_records: List[Dict], 
        cleanup_records: List[Dict]
    ):
        """
        带锁的串行处理：确保同一时间只有一个批次在处理
        
        这样可以：
        1. 不阻塞拉取循环（create_task立即返回）
        2. 保证处理顺序（锁确保串行）
        3. 避免竞态条件（同一IP的上线和清除按顺序处理）
        """
        # 获取锁（如果有其他任务在处理，这里会等待）
        async with self._processing_lock:
            try:
                logger.info(f"[{botnet_type}] [锁定] 开始串行处理...")
                
                # Step 1: 先处理上线日志
                if online_records:
                    logger.info(f"[{botnet_type}] [1/2] 处理上线日志 {len(online_records)} 条...")
                    await self._process_data_in_background(botnet_type, online_records)
                    logger.info(f"[{botnet_type}] [1/2] 上线日志处理完成")
                
                # Step 2: 再处理清除日志
                if cleanup_records:
                    logger.info(f"[{botnet_type}] [2/2] 处理清除日志 {len(cleanup_records)} 条...")
                    await self._handle_cleanup_records(botnet_type, cleanup_records)
                    logger.info(f"[{botnet_type}] [2/2] 清除日志处理完成")
                
                logger.info(f"[{botnet_type}] [解锁] 数据处理流程完成")
                
            except Exception as e:
                logger.error(f"[{botnet_type}] [错误] 处理失败: {e}", exc_info=True)
    
    async def stop(self):
        """
        优雅停止：等待所有处理任务完成
        """
        if self._processing_tasks:
            logger.info(f"等待 {len(self._processing_tasks)} 个处理任务完成...")
            await asyncio.gather(*self._processing_tasks, return_exceptions=True)
            logger.info("所有处理任务已完成")
```

---

## 📊 方案对比

| 方案 | 拉取阻塞 | 处理顺序 | 竞态条件 | 推荐 |
|------|----------|----------|----------|------|
| 完全串行await | ❌ 严重阻塞 | ✅ 保证 | ✅ 无 | ❌ |
| 完全并发create_task | ✅ 不阻塞 | ❌ 不保证 | ❌ 有 | ❌ |
| **异步锁方案** | ✅ 不阻塞 | ✅ 保证 | ✅ 无 | ✅ |
| Redis队列+等待 | ✅ 不阻塞 | ⚠️ 复杂 | ✅ 无 | ⚠️ |

---

## 🔍 工作流程示例

### 场景：连续拉取3次数据

```
时间轴：
T0: 拉取#1 (100条上线 + 10条清除)
    ├─ process_api_data 调用 (立即返回，不阻塞)
    └─ 创建任务#1 → 等待获取锁...

T0+0.1秒: 任务#1获取锁
    ├─ 处理上线日志 (2秒)
    ├─ 处理清除日志 (0.5秒)
    └─ 释放锁 (T0+2.6秒)

T10: 拉取#2 (50条上线 + 5条清除)  ← 不阻塞！
    ├─ process_api_data 调用 (立即返回)
    └─ 创建任务#2 → 等待获取锁...
                      ↑ 任务#1还在处理，等待中

T0+2.6秒: 任务#2获取锁
    ├─ 处理上线日志 (1秒)
    ├─ 处理清除日志 (0.2秒)
    └─ 释放锁 (T0+3.8秒)

T20: 拉取#3 (200条上线 + 20条清除)  ← 不阻塞！
    ├─ process_api_data 调用 (立即返回)
    └─ 创建任务#3 → 等待获取锁...

T0+3.8秒: 任务#3获取锁
    └─ 开始处理...
```

**关键点：**
- ✅ 拉取循环不阻塞（每10秒拉取一次）
- ✅ 处理按顺序进行（任务#1 → 任务#2 → 任务#3）
- ✅ 每个任务内部保证：先上线，后清除

---

## ⚠️ 注意事项

### 1. 任务积压问题

**如果处理速度 < 拉取速度：**
```
拉取速度：每10秒一批
处理速度：每批需要3秒

正常情况：没问题
极端情况（每批需要15秒）：会积压
```

**监控指标：**
```python
# 在process_api_data中添加
if len(self._processing_tasks) > 5:
    logger.warning(f"⚠️  处理任务积压: {len(self._processing_tasks)} 个待处理")
```

**解决方案：**
- 增加处理性能（更多数据库连接、批量写入）
- 减少拉取频率（从10秒改为30秒）
- 增加拉取批量（一次拉取更多，但降低频率）

### 2. 优雅关闭

确保程序退出时等待所有任务完成：

```python
# 在main.py的信号处理函数中
async def shutdown(sig):
    logger.info(f"接收到退出信号: {sig}")
    
    # 停止拉取
    if processor.remote_puller:
        await processor.remote_puller.stop()
    
    # 等待处理任务完成
    await processor.stop()
    
    # 关闭数据库
    for writer in processor.writers.values():
        await writer.close()
```

### 3. 锁的粒度

**当前方案：全局锁（所有botnet_type共享）**
```python
self._processing_lock = asyncio.Lock()
```

**优化方案：每个botnet_type一个锁**
```python
self._processing_locks = {}  # {botnet_type: Lock}

# 使用时
lock = self._processing_locks.setdefault(botnet_type, asyncio.Lock())
async with lock:
    # 处理...
```

**对比：**
- 全局锁：简单，但不同botnet_type会相互阻塞
- 分离锁：复杂，但不同botnet_type可以并发处理

---

## 🎯 实施步骤

### 1. 修改代码（今天）
```bash
# 备份原文件
cp backend/log_processor/main.py backend/log_processor/main.py.backup

# 应用新代码（见上面的完整实现）
```

### 2. 测试验证（今天）
```bash
# 启动系统
python backend/log_processor/main.py

# 观察日志
tail -f backend/log_processor/logs/processor.log | grep "锁定\|解锁"
```

**预期输出：**
```
[test] [锁定] 开始串行处理...
[test] [1/2] 处理上线日志 100 条...
[test] [1/2] 上线日志处理完成
[test] [2/2] 处理清除日志 10 条...
[test] [2/2] 清除日志处理完成
[test] [解锁] 数据处理流程完成
```

### 3. 性能监控（本周）
```bash
# 监控任务积压
grep "处理任务积压" backend/log_processor/logs/processor.log

# 监控处理时间
grep "处理完成" backend/log_processor/logs/processor.log | awk '{print $NF}'
```

---

## 📈 性能预期

### 正常场景
```
拉取间隔：10秒
每批数据：100条上线 + 10条清除
处理时间：2-3秒

结果：✅ 无积压，实时性良好
```

### 高负载场景
```
拉取间隔：10秒
每批数据：1000条上线 + 100条清除
处理时间：15-20秒

结果：⚠️  任务积压，需要优化
解决：减少拉取频率或增加处理能力
```

---

## ✅ 总结

**这个方案的优势：**
1. ✅ 拉取不阻塞 → 实时性好
2. ✅ 处理有顺序 → 数据正确
3. ✅ 避免竞态 → 状态一致
4. ✅ 代码简单 → 易维护
5. ✅ 资源可控 → 不会积压过多

**唯一缺点：**
- 如果处理速度慢于拉取速度，会有任务积压
- 解决：监控 + 性能优化

**推荐使用！** 🎉
