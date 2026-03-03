# 清除日志处理功能说明

## 概述

平台端新增了对清除日志（cleanup log）的处理能力，当C2端传输被清除节点信息时，后端会执行严格的处理流程，更新数据库状态并同步缓存。

## 功能特性

### 1. 自动识别日志类型
- ✅ 根据 `log_type` 字段自动分流处理
- ✅ `log_type="online"` → 正常上线日志处理流程
- ✅ `log_type="cleanup"` → 清除日志处理流程

### 2. 数据处理流程
```
C2端 → RemotePuller → LogProcessor → 
├─ online记录 → IP增强 → 数据库写入（add_node）
└─ cleanup记录 → 状态更新 → 批量UPDATE + Redis同步
```

### 3. 清除日志处理步骤

#### Step 1: 数据接收与校验
```python
# 提取IP和清除时间
for record in cleanup_records:
    ip = record.get('ip')          # 必需
    timestamp = record.get('timestamp')  # 清除时间
```

**校验规则：**
- 验证IP字段存在且非空
- 解析清除时间（ISO格式），失败则使用当前时间

#### Step 2: 开启数据库事务
```python
conn.begin()  # 开启事务，确保原子性
```

#### Step 3: 批量更新节点状态
```sql
-- 先检查哪些IP存在且状态为active
SELECT ip FROM botnet_nodes_{type}
WHERE ip IN (...) AND status = 'active';

-- 批量更新状态
UPDATE botnet_nodes_{type}
SET status = 'cleaned',        -- 标记为cleaned（已清除）
    cleaned_time = ?,          -- 记录清除时间
    updated_at = NOW()
WHERE ip = ? AND status = 'active';
```

**注意事项：**
- 只更新状态为 `active` 的节点
- 使用 `executemany` 批量更新，提高效率
- 使用专用的 `cleaned` 状态和 `cleaned_time` 字段

#### Step 4: 提交事务
```python
conn.commit()  # 提交事务
```

**异常处理：**
- 任何步骤失败都会回滚事务
- 确保数据一致性

#### Step 5: 同步Redis缓存
```python
# 更新活跃节点计数
redis_client.incrby(f"botnet:active_count:{botnet_type}", -updated_count)
```

**Redis缓存键：**
- `botnet:active_count:{botnet_type}` - 活跃节点总数
- 每次清除成功后，减少相应数量

## 代码架构

### 1. main.py (LogProcessor)

#### `process_api_data()` - 数据分流
```python
async def process_api_data(self, botnet_type: str, ip_data: List[Dict]):
    # 检测数据类型
    cleanup_records = []
    online_records = []
    
    for record in ip_data:
        log_type = record.get('log_type', 'online')
        if log_type == 'cleanup':
            cleanup_records.append(record)
        else:
            online_records.append(record)
    
    # 分别处理
    if cleanup_records:
        asyncio.create_task(self._handle_cleanup_records(...))
    if online_records:
        # 正常处理...
```

#### `_handle_cleanup_records()` - 清除处理
```python
async def _handle_cleanup_records(self, botnet_type: str, cleanup_records: List[Dict]):
    """
    处理流程：
    1. 数据校验（IP、时间戳）
    2. 调用writer.update_nodes_to_cleaned()
    3. 更新Redis缓存
    4. 输出处理日志
    """
```

#### `_update_active_count_cache()` - Redis同步
```python
async def _update_active_count_cache(self, botnet_type: str, delta: int):
    """
    参数：
    - delta: 增量（负数表示减少）
    
    功能：
    - 更新Redis中活跃节点计数
    - 自动处理负数情况（不小于0）
    """
```

### 2. db_writer.py (BotnetDBWriter)

#### `update_nodes_to_cleaned()` - 批量更新（异步）
```python
async def update_nodes_to_cleaned(self, ip_list: List[str], 
                                    cleanup_time_map: Dict[str, datetime]) -> int:
    """
    返回：实际更新的记录数
    """
```

#### `_do_update_nodes_to_cleaned_sync()` - 同步执行
```python
def _do_update_nodes_to_cleaned_sync(self, ip_list, cleanup_time_map):
    """
    在后台线程中执行SQL操作
    保证事务完整性
    """
```

## 数据流示例

### 输入数据（C2端）
```json
{
  "success": true,
  "data": [
    {
      "ip": "14.19.132.125",
      "timestamp": "2026-03-03T16:38:34",
      "log_type": "cleanup",  // ← 关键字段
      "botnet_type": "test"
    },
    {
      "ip": "192.168.1.100",
      "timestamp": "2026-03-03T16:40:00",
      "log_type": "online",
      "botnet_type": "test"
    }
  ]
}
```

### 处理日志
```
[test] 检测到 1 条清除日志
[test] 处理 1 条上线日志
[test] [清除] 开始处理 1 条清除记录...
[test] [清除] 校验完成：1 个有效IP
[test] [清除] 开始批量更新 1 个节点状态...
[test] [清除] 事务已开启
[test] [清除] 状态检查: 1/1 个节点状态为active
[test] [清除] SQL执行完成: 受影响行数 1
[test] [清除] 事务已提交
[test] [清除] 批量更新完成: 1/1 条, 耗时 0.05秒
[test] [清除] Redis缓存已更新：活跃节点数 -1
[test] [清除] 处理完成: 接收 1 条, 有效 1 条, 更新 1 条, 耗时 0.06秒
```

### 数据库变化
```sql
-- 更新前
SELECT ip, status, cleaned_time FROM botnet_nodes_test WHERE ip = '14.19.132.125';
-- ip: 14.19.132.125, status: active, cleaned_time: NULL

-- 更新后
SELECT ip, status, cleaned_time FROM botnet_nodes_test WHERE ip = '14.19.132.125';
-- ip: 14.19.132.125, status: cleaned, cleaned_time: 2026-03-03 16:38:34
```

### Redis缓存变化
```bash
# 更新前
redis-cli> GET botnet:active_count:test
"1000"

# 更新后
redis-cli> GET botnet:active_count:test
"999"
```

## 关键设计说明

### 1. 数据库Schema设计
**节点状态定义**：
```sql
status ENUM('active', 'inactive', 'cleaned') DEFAULT 'active'
```

**状态说明**：
- `active` - 节点活跃，正常通信中
- `inactive` - 节点不活跃（长时间未通信）
- `cleaned` - 节点已被清除

**清除时间字段**：
```sql
cleaned_time TIMESTAMP NULL DEFAULT NULL COMMENT '节点清除时间'
```

**索引优化**：
```sql
INDEX idx_status (status),
INDEX idx_cleaned_time (cleaned_time)
```
- `idx_status` - 加速按状态查询（如查询所有已清除节点）
- `idx_cleaned_time` - 加速按清除时间范围查询

### 2. 为什么需要Redis缓存同步？
**问题背景**：
- 大屏显示活跃节点数时，直接查询数据库会很慢
- 使用Redis缓存可以实现毫秒级响应

**同步时机**：
- 新增节点 → `incrby +1`
- 清除节点 → `incrby -N`
- 节点过期 → 定期同步修正

**容错机制**：
- Redis更新失败不影响数据库操作
- 定期从数据库重新计算并更新缓存

### 3. 事务的重要性
**确保原子性**：
- 所有IP要么全部更新成功，要么全部回滚
- 避免部分成功导致的数据不一致

**隔离级别**：
- 使用默认的 `REPEATABLE READ`
- 防止并发更新冲突

## 配置要求

### Redis配置（可选）
在 `backend/config.py` 中添加：
```python
REDIS_CONFIG = {
    'enabled': True,
    'host': 'localhost',
    'port': 6379,
    'password': None,
    'db': 0
}
```

如果Redis未启用或连接失败：
- 系统会跳过缓存更新
- 只记录警告日志
- 不影响数据库操作

## 性能优化

### 1. 批量操作
- 使用 `executemany` 批量UPDATE
- 一次事务处理多个IP
- 避免逐条UPDATE的网络开销

### 2. 索引优化
```sql
-- 确保有status索引
INDEX idx_status (status)

-- 确保有IP唯一索引
UNIQUE KEY idx_unique_ip (ip)
```

### 3. 异步处理
```python
# 在后台线程执行SQL操作，不阻塞事件循环
await asyncio.to_thread(self._do_update_nodes_to_cleaned_sync, ...)
```

## 监控与日志

### 关键日志输出
```
[INFO] [test] 检测到 100 条清除日志
[INFO] [test] [清除] 开始处理 100 条清除记录...
[INFO] [test] [清除] 校验完成：98 个有效IP
[INFO] [test] [清除] 状态检查: 95/98 个节点状态为active
[INFO] [test] [清除] SQL执行完成: 受影响行数 95
[INFO] [test] [清除] 批量更新完成: 95/98 条, 耗时 0.35秒
[INFO] [test] Redis缓存已更新：活跃节点数 -95
[INFO] [test] [清除] 处理完成: 接收 100 条, 有效 98 条, 更新 95 条, 耗时 0.40秒
```

### 异常情况日志
```
[WARNING] [test] [清除] 记录缺少IP字段: {'timestamp': '...'}
[WARNING] [test] [清除] 没有需要更新的节点
[WARNING] [test] [清除] Redis缓存更新失败: Connection refused
[ERROR] [test] [清除] 批量更新失败: (1213, 'Deadlock found...')
[ERROR] [test] [清除] 事务已回滚
```

## 测试建议

### 1. 单元测试
```python
# 测试数据校验
cleanup_records = [
    {'ip': '1.1.1.1', 'timestamp': '2026-03-03T16:00:00'},
    {'timestamp': '2026-03-03T16:00:00'},  # 缺少IP
    {'ip': '2.2.2.2'}  # 缺少时间戳
]
# 预期：有效IP = 2个
```

### 2. 集成测试
```bash
# 1. 准备测试数据：在数据库中插入active节点
# 2. 发送cleanup日志到C2端
# 3. 验证：
#    - 数据库status是否变为inactive
#    - Redis计数是否正确减少
#    - 事务是否正确提交/回滚
```

### 3. 压力测试
```python
# 测试批量更新性能
- 1000个IP: 预期 <1秒
- 10000个IP: 预期 <5秒
- 事务超时: 预期自动回滚
```

## 未来扩展

### 1. 支持更多清除原因
```python
# 在cleanup记录中添加reason字段
{
    'ip': '1.1.1.1',
    'log_type': 'cleanup',
    'reason': 'manual',  # manual, auto, expired
    'operator': 'admin'
}
```

### 2. 清除历史记录表
```sql
CREATE TABLE cleanup_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(15) NOT NULL,
    botnet_type VARCHAR(50),
    cleaned_time TIMESTAMP NOT NULL COMMENT '清除时间',
    reason VARCHAR(50) COMMENT '清除原因',
    operator VARCHAR(50) COMMENT '操作人',
    INDEX idx_ip (ip),
    INDEX idx_cleaned_time (cleaned_time),
    INDEX idx_botnet_type (botnet_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 
COMMENT='节点清除历史记录表';
```

### 3. 自动清除策略
- 节点超过N天未活跃 → 自动标记为inactive
- 定期清理无效节点
- 通知管理员

## 注意事项

### ⚠️ 重要提醒

1. **事务隔离**：清除操作与新增节点操作可能并发，确保正确的事务隔离级别
2. **幂等性**：相同的cleanup记录多次处理，只会更新一次（WHERE status='active'）
3. **数据一致性**：Redis同步失败不影响数据库操作，但需要定期校准
4. **性能考虑**：大批量清除时（>10000个IP），考虑分批处理
5. **监控告警**：清除失败率过高时，应触发告警

## 总结

清除日志处理功能完整实现了：
- ✅ **数据接收与校验** - 确保数据合法性
- ✅ **事务化更新** - 保证数据一致性
- ✅ **批量操作** - 提高处理效率
- ✅ **缓存同步** - 保持Redis与数据库一致
- ✅ **完善日志** - 便于监控和调试
- ✅ **异常处理** - 失败自动回滚

该功能已做好生产环境部署准备，具备良好的性能和可靠性。
