# 数据库重构部署指南

## 📋 概述

本次重构实现了从**单表设计**到**双表设计**的迁移：
- **节点表** (`botnet_nodes_{type}`)：存储节点汇总信息
- **通信记录表** (`botnet_communications_{type}`)：存储所有通信历史

### 核心变更
✅ C2端不再去重，传输所有日志  
✅ 平台记录全部通信信息  
✅ 前端零改动（API兼容层）  
✅ 支持历史数据迁移  

---

## 📁 已修改的文件

### 1. 后端核心文件
- ✅ `log_processor/db_writer.py` - 双表插入逻辑
- ✅ `router/botnet.py` - 表初始化逻辑
- ✅ `router/node.py` - API兼容层 + 新接口
- ✅ `migrate_single_botnet.py` - 数据库迁移脚本（新）

### 2. 文档文件
- ✅ `DATABASE_REDESIGN_PROPOSAL.md` - 完整设计方案
- ✅ `CODE_MODIFICATION_GUIDE.md` - 代码修改指南
- ✅ `FRONTEND_IMPACT_ANALYSIS.md` - 前端影响分析
- ✅ `database_migration.sql` - SQL迁移脚本
- ✅ `migrate_all_botnets.sh/bat` - 批量迁移脚本
- ✅ `api_compatibility_example.py` - API兼容示例

---

## 🚀 部署步骤

### 准备工作

1. **备份数据库**（重要！）
```bash
mysqldump -uroot -proot botnet > botnet_backup_$(date +%Y%m%d).sql
```

2. **停止相关服务**
```bash
# Linux
./stop_all_services.sh

# Windows
.\stop_all_services.bat
```

### 方案A: 单个僵尸网络类型迁移（推荐用于测试）

适用于逐个迁移，风险最小：

```bash
cd backend
python migrate_single_botnet.py asruex
```

迁移流程：
1. 检查节点表是否存在
2. 创建通信记录表
3. 修改节点表结构（字段重命名+新增字段）
4. 迁移历史数据
5. 更新统计表
6. 数据验证

### 方案B: 批量迁移所有类型

适用于一次性迁移所有僵尸网络：

```bash
# Linux/Mac
cd backend
chmod +x migrate_all_botnets.sh
./migrate_all_botnets.sh

# Windows
cd backend
.\migrate_all_botnets.bat
```

### 验证迁移结果

```sql
-- 查看表结构
SHOW CREATE TABLE botnet_nodes_asruex;
SHOW CREATE TABLE botnet_communications_asruex;

-- 验证数据
SELECT 
    (SELECT COUNT(*) FROM botnet_nodes_asruex) as node_count,
    (SELECT COUNT(*) FROM botnet_communications_asruex) as comm_count;

-- 验证通信次数一致性
SELECT n.ip, n.communication_count, COUNT(c.id) as actual
FROM botnet_nodes_asruex n
LEFT JOIN botnet_communications_asruex c ON n.id = c.node_id
GROUP BY n.id
HAVING n.communication_count != COUNT(c.id);
```

### 启动服务

```bash
# Linux
./start_all_services.sh

# Windows
.\start_all_services.bat
```

---

## 🔧 API接口变更

### 现有接口（兼容）

**无需修改前端代码！**

#### `/api/node-details`
```javascript
// 返回字段（保持向后兼容）
{
  "ip": "1.2.3.4",
  "active_time": "2024-01-01 10:00:00",  // 映射自 first_seen
  "last_active": "2024-01-08 12:00:00"   // 映射自 last_seen
}
```

### 新增接口

#### 1. `/api/node-communications` - 通信记录查询
```bash
GET /api/node-communications?botnet_type=asruex&ip=1.2.3.4&page=1&page_size=100
```

返回：
```json
{
  "code": 200,
  "data": {
    "total": 150,
    "page": 1,
    "page_size": 100,
    "communications": [
      {
        "id": 1,
        "ip": "1.2.3.4",
        "communication_time": "2024-01-08 12:00:00",
        "received_at": "2024-01-08 12:05:00",
        "country": "中国",
        "province": "北京",
        ...
      }
    ]
  }
}
```

参数：
- `botnet_type`: 僵尸网络类型（必填）
- `ip`: 筛选IP（可选）
- `start_time`: 开始时间（可选）
- `end_time`: 结束时间（可选）
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认100，最大1000）

#### 2. `/api/node-communication-stats` - 通信统计
```bash
GET /api/node-communication-stats?botnet_type=asruex&ip=1.2.3.4
```

返回：
```json
{
  "code": 200,
  "data": {
    "ip": "1.2.3.4",
    "total_communications": 150,
    "first_seen": "2024-01-01 10:00:00",
    "last_seen": "2024-01-08 12:00:00",
    "communication_timeline": [
      {"date": "2024-01-01", "count": 50},
      {"date": "2024-01-02", "count": 30},
      ...
    ]
  }
}
```

---

## 📊 数据库表结构

### 节点表 (botnet_nodes_{type})

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| ip | VARCHAR(15) | IP地址（唯一） |
| longitude, latitude | FLOAT | 地理坐标 |
| country, province, city | VARCHAR | 地理位置 |
| **first_seen** | TIMESTAMP | 首次发现时间 ⭐ |
| **last_seen** | TIMESTAMP | 最后通信时间 ⭐ |
| **communication_count** | INT | 通信次数 ⭐ |
| created_at | TIMESTAMP | 记录创建时间 |
| updated_at | TIMESTAMP | 记录更新时间 |

### 通信记录表 (botnet_communications_{type})

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键（自增） |
| node_id | INT | 关联节点ID |
| ip | VARCHAR(15) | 节点IP（冗余） |
| **communication_time** | TIMESTAMP | 通信时间 ⭐ |
| received_at | TIMESTAMP | 接收时间 |
| country, province, city | VARCHAR | 地理位置 |
| event_type | VARCHAR | 事件类型 |
| ... | | 其他字段 |

---

## ⚠️ 注意事项

### 存储空间

通信记录表会快速增长，建议：

1. **监控磁盘空间**
```sql
SELECT 
    table_name,
    ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb
FROM information_schema.tables
WHERE table_schema = 'botnet'
AND table_name LIKE 'botnet_communications_%';
```

2. **定期归档**（建议保留3-6个月数据）
```sql
-- 归档6个月前的数据
INSERT INTO botnet_communications_asruex_archive
SELECT * FROM botnet_communications_asruex
WHERE communication_time < DATE_SUB(NOW(), INTERVAL 6 MONTH);

DELETE FROM botnet_communications_asruex
WHERE communication_time < DATE_SUB(NOW(), INTERVAL 6 MONTH);
```

3. **使用分区**（可选，适用于大数据量）
```sql
ALTER TABLE botnet_communications_asruex
PARTITION BY RANGE (TO_DAYS(communication_time)) (
    PARTITION p202401 VALUES LESS THAN (TO_DAYS('2024-02-01')),
    PARTITION p202402 VALUES LESS THAN (TO_DAYS('2024-03-01')),
    ...
);
```

### 性能优化

1. **索引优化**
   - 已创建复合索引 `idx_composite (ip, communication_time)`
   - 根据查询模式添加其他索引

2. **查询优化**
   - 使用时间范围过滤
   - 使用分页（避免全表扫描）

3. **连接池配置**
   - `db_writer.py` 中已启用连接池
   - 根据并发量调整池大小

---

## 🔄 回滚方案

如果出现问题，可以回滚：

### 1. 停止服务
```bash
./stop_all_services.sh
```

### 2. 恢复数据库
```bash
mysql -uroot -proot botnet < botnet_backup_YYYYMMDD.sql
```

### 3. 回滚代码
```bash
git reset --hard HEAD~1  # 或指定commit
```

### 4. 重启服务
```bash
./start_all_services.sh
```

---

## ✅ 测试检查清单

### 功能测试
- [ ] 节点列表正常显示
- [ ] 地图节点正常显示
- [ ] 统计数据准确
- [ ] 时间字段显示正常
- [ ] 新接口返回数据正常

### 性能测试
- [ ] 查询响应时间 < 2秒
- [ ] 批量插入性能正常
- [ ] 数据库连接池正常

### 数据完整性
- [ ] 节点数量正确
- [ ] 通信记录数量正确
- [ ] `communication_count` 统计准确
- [ ] 时间字段数据正确

---

## 📞 故障排查

### 问题1: 节点表字段不存在

**错误**: `Unknown column 'first_seen'`

**解决**: 
```sql
-- 检查字段是否存在
SHOW COLUMNS FROM botnet_nodes_asruex LIKE 'first_seen';

-- 如果不存在，手动添加
ALTER TABLE botnet_nodes_asruex 
ADD COLUMN first_seen TIMESTAMP NULL DEFAULT NULL 
COMMENT '首次发现时间（日志时间）';
```

### 问题2: 通信记录表不存在

**错误**: `Table 'botnet_communications_asruex' doesn't exist`

**解决**: 运行迁移脚本
```bash
python migrate_single_botnet.py asruex
```

### 问题3: API返回字段缺失

**现象**: 前端显示"未知"或空白

**解决**: 检查 `node.py` 中的字段映射
```python
# 确保有这段代码
COALESCE(n.last_seen, n.created_at, NOW()) as last_active,
COALESCE(n.first_seen, n.created_at, NOW()) as active_time,
```

---

## 📈 后续优化建议

1. **添加数据归档任务**（定时脚本）
2. **监控磁盘空间**（告警阈值80%）
3. **优化查询性能**（根据慢查询日志）
4. **实现分区表**（数据量>1000万时）
5. **添加数据分析接口**（按时间段统计等）

---

## 📝 更新日志

### v2.0.0 (2024-01-08)
- ✅ 实现双表设计（节点表+通信记录表）
- ✅ 移除所有去重逻辑
- ✅ 字段重命名：`active_time` → `first_seen`、`updated_at` → `last_seen`
- ✅ 新增 `communication_count` 字段
- ✅ 新增通信记录查询接口
- ✅ 前端零改动（API兼容层）
- ✅ 提供完整迁移工具

---

## 🎯 总结

### 成功标准
✅ 所有服务正常启动  
✅ 前端功能正常使用  
✅ 数据完整无丢失  
✅ 查询性能满足要求  
✅ 新接口可用  

### 完成后
- 监控系统运行24小时
- 检查错误日志
- 验证数据准确性
- 通知团队部署完成

**祝部署顺利！** 🚀
