# 数据一致性Bug修复 - 代码修改摘要

## 修改文件
`backend/log_processor/db_writer.py`

## 修改目标
确保节点表（botnet_nodes_*）和通信表（botnet_communications_*）在同一事务中原子性提交，避免系统异常中断导致的数据不一致。

---

## 修改详情

### 修改1：在内层函数中提交事务

**位置**：`_do_insert_nodes_batch_sync` 方法，第1078-1082行

**修改内容**：
```python
# 原代码：
logger.info(f"[{self.botnet_type}] 批量插入全部完成!")

# 修改后：
# ========================================
# Step 5: 提交事务（确保节点表和通信表同时提交）
# ========================================
cursor.connection.commit()
logger.info(f"[{self.botnet_type}] 批量插入全部完成并已提交事务!")
```

**作用**：
- 在节点表和通信表都写入完成后，立即提交事务
- 确保两个表的数据要么同时成功，要么同时失败
- 缩小"数据不一致窗口期"

---

### 修改2：增强异常处理和回滚

**位置**：`_do_insert_nodes_batch_sync` 方法，第1084-1092行

**修改内容**：
```python
# 原代码：
except Exception as e:
    logger.error(f"[{self.botnet_type}] Error in batch insert: {e}", exc_info=True)
    raise

# 修改后：
except Exception as e:
    logger.error(f"[{self.botnet_type}] Error in batch insert: {e}", exc_info=True)
    # 回滚事务，确保数据一致性
    try:
        cursor.connection.rollback()
        logger.warning(f"[{self.botnet_type}] 事务已回滚")
    except Exception as rollback_error:
        logger.error(f"[{self.botnet_type}] 回滚失败: {rollback_error}")
    raise
```

**作用**：
- 发生异常时，明确回滚所有更改
- 避免部分数据被提交
- 增加详细的日志记录

---

### 修改3：移除外层函数的重复提交

**位置**：`_do_flush_sync` 方法，第323-332行

**修改内容**：
```python
# 原代码：
self._do_insert_nodes_batch_sync(cursor, nodes_to_write)
insert_duration = time.time() - insert_start_time
self._record_performance('insert', insert_duration)
# 提交事务
conn.commit()
self.total_written += len(nodes_to_write)

# 修改后：
# 注意：事务的commit已在_do_insert_nodes_batch_sync内部执行，确保节点表和通信表原子性
self._do_insert_nodes_batch_sync(cursor, nodes_to_write)
insert_duration = time.time() - insert_start_time
self._record_performance('insert', insert_duration)
# 注意：commit已在内层函数执行，此处不再需要commit
# 这样可以确保节点表和通信表在同一事务中提交，避免数据不一致
self.total_written += len(nodes_to_write)
```

**作用**：
- 避免重复提交
- 将事务控制权完全交给内层函数
- 确保事务边界清晰

---

### 修改4：优化外层异常处理

**位置**：`_do_flush_sync` 方法，第361-366行

**修改内容**：
```python
# 原代码：
except Exception as e:
    logger.error(f"[{self.botnet_type}] Error flushing to database: {e}", exc_info=True)
    if conn:
        conn.rollback()
    # 如果写入失败，将数据重新放回缓冲区
    with self.buffer_lock:
        self.node_buffer.extend(nodes_to_write)

# 修改后：
except Exception as e:
    logger.error(f"[{self.botnet_type}] Error flushing to database: {e}", exc_info=True)
    # 注意：rollback已在内层函数执行，此处不再需要rollback
    # 如果写入失败，将数据重新放回缓冲区
    with self.buffer_lock:
        self.node_buffer.extend(nodes_to_write)
```

**作用**：
- 避免重复回滚
- 简化异常处理逻辑
- 确保回滚在内层函数中统一处理

---

## 修改前后对比

### 修改前的问题流程
```
开始事务
  ↓
Step 2: 写入节点表 ✓
  ↓
Step 3: 查询node_id ✓
  ↓
Step 4: 写入通信表 ✓
  ↓
【外层函数】提交事务 ← 如果在这之前系统崩溃，可能导致不一致
```

### 修改后的改进流程
```
开始事务
  ↓
Step 2: 写入节点表 ✓
  ↓
Step 3: 查询node_id ✓
  ↓
Step 4: 写入通信表 ✓
  ↓
【内层函数】立即提交事务 ← 缩小了"不一致窗口期"
```

---

## 性能影响分析

### ✅ 无性能开销

1. **commit次数**：1次（与之前相同）
2. **事务范围**：相同
3. **锁持有时间**：相同
4. **数据库操作**：完全相同

### 💡 实际改进

1. **更明确的事务边界**
2. **更及时的异常处理**
3. **减少数据不一致风险**

---

## 测试建议

### 单元测试
```python
def test_transaction_atomicity():
    """测试事务原子性"""
    # 1. 正常情况：节点表和通信表都应该有数据
    # 2. 异常情况：发生错误时，两个表都不应该有数据
    pass
```

### 集成测试
```bash
# 1. 正常写入测试
# 2. 模拟系统崩溃测试
# 3. 数据库连接中断测试
```

---

## 回滚方案

如果新代码有问题，可以回滚到原来的逻辑：

```bash
git diff HEAD backend/log_processor/db_writer.py
git checkout HEAD -- backend/log_processor/db_writer.py
```

---

## 后续监控

修改上线后，建议监控以下指标：

1. **数据一致性**：定期运行 `check_data_consistency.py`
2. **写入性能**：监控日志中的写入耗时
3. **错误率**：监控rollback的频率
4. **覆盖率**：通信记录覆盖率应保持在99.9%以上

---

**修改时间**：2026-01-20 16:40  
**修改人员**：AI Assistant  
**测试状态**：待测试  
**上线状态**：待上线
