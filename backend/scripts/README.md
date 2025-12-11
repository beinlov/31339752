# 数据维护脚本使用指南

本目录包含用于维护僵尸网络节点数据的工具脚本。

## 脚本列表

### 1. `deduplicate_nodes.py` - 数据去重工具

清理原始表中的重复IP记录，保留每个IP最新的记录。

**用法：**
```bash
# 仅分析，不执行去重
python deduplicate_nodes.py --analyze-only

# 模拟运行（查看将要删除的记录）
python deduplicate_nodes.py

# 真正执行去重
python deduplicate_nodes.py --execute

# 去重特定僵尸网络
python deduplicate_nodes.py --execute --botnet ramnit
```

**参数：**
- `--analyze-only`: 仅分析重复情况，不执行去重
- `--execute`: 真正执行去重（默认为模拟运行）
- `--botnet <name>`: 指定僵尸网络类型（默认处理所有）

### 2. `rebuild_aggregation.py` - 聚合表重建工具

清空并重新生成聚合表，确保统计数据一致。

**用法：**
```bash
# 重建所有聚合表
python rebuild_aggregation.py

# 重建特定僵尸网络的聚合表
python rebuild_aggregation.py --botnet ramnit
```

**参数：**
- `--botnet <name>`: 指定僵尸网络类型（默认处理所有）

### 3. `fix_all.bat` - 一键修复脚本（Windows）

自动化执行数据去重和聚合表重建的完整流程。

**用法：**
```bash
fix_all.bat
```

## 典型使用场景

### 场景1：首次发现数据不一致

```bash
# 1. 分析重复情况
python deduplicate_nodes.py --analyze-only

# 2. 备份数据库（重要！）
# 使用MySQL客户端或管理工具备份

# 3. 执行完整修复
python deduplicate_nodes.py --execute
python rebuild_aggregation.py
```

### 场景2：只想看看有多少重复数据

```bash
python deduplicate_nodes.py --analyze-only
```

### 场景3：针对单个僵尸网络修复

```bash
# 分析
python deduplicate_nodes.py --analyze-only --botnet ramnit

# 去重
python deduplicate_nodes.py --execute --botnet ramnit

# 重建聚合表
python rebuild_aggregation.py --botnet ramnit
```

### 场景4：定期维护

```bash
# 使用一键脚本
fix_all.bat
```

## 注意事项

### ⚠️ 重要警告

1. **必须先备份数据库**，去重操作不可逆
2. 建议在**低峰期**执行，避免影响服务
3. 去重后**必须重建聚合表**，否则数据仍不一致
4. 确保有足够的**数据库操作权限**

### 📋 前置要求

- Python 3.7+
- pymysql 库
- 数据库连接配置正确（`config.py`）
- 足够的磁盘空间（用于临时操作）

### 🔍 验证步骤

修复完成后，验证数据一致性：

```sql
-- 检查原始表去重后的数量
SELECT COUNT(DISTINCT ip) FROM botnet_nodes_ramnit;

-- 检查聚合表总数
SELECT SUM(infected_num) FROM global_botnet_ramnit;

-- 两者应该相等或非常接近
```

## 执行流程建议

### 标准流程（推荐）

```
1. 分析重复数据
   ↓
2. 备份数据库（重要！）
   ↓
3. 执行去重
   ↓
4. 重建聚合表
   ↓
5. 验证数据一致性
```

### 快速流程（已备份）

```bash
# 一条命令完成
python deduplicate_nodes.py --execute && python rebuild_aggregation.py
```

## 预期结果

### 修复前
- 原始表：约108,960条记录
- 唯一IP：约76,186
- 三个平台数据不一致（差异约555个节点）

### 修复后
- 原始表：约76,186条记录（减少30%）
- 唯一IP：约76,186
- 三个平台数据一致

## 故障排查

### 问题：权限不足

```
错误：Access denied for user
解决：检查config.py中的数据库配置，确保有DELETE和INSERT权限
```

### 问题：表不存在

```
错误：Table doesn't exist
解决：检查僵尸网络类型名称是否正确，表名是否匹配
```

### 问题：执行时间过长

```
解决：
1. 为ip和updated_at字段添加索引
2. 减少单批处理的数据量
3. 在服务器本地执行，减少网络延迟
```

## 定期维护建议

### 预防重复数据

建议添加唯一索引（去重后）：

```sql
ALTER TABLE botnet_nodes_ramnit 
ADD UNIQUE INDEX idx_unique_ip (ip);
```

### 定期聚合

设置定时任务，定期更新聚合表：

```bash
# crontab (Linux)
*/5 * * * * cd /path/to/backend/stats_aggregator && python incremental_aggregator.py

# 任务计划程序 (Windows)
# 每5分钟运行 incremental_aggregator.py
```

## 技术支持

如有问题，请检查：

1. 日志输出中的错误信息
2. 数据库连接是否正常
3. Python依赖是否完整
4. 操作系统权限是否足够

## 版本历史

- **v1.0** (2024-12-11): 初始版本
  - 数据去重功能
  - 聚合表重建功能
  - 一键修复脚本

---

**维护者：** Cascade AI Assistant  
**最后更新：** 2024-12-11
