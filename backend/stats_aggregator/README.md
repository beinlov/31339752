# 统计数据聚合器

## 📖 功能说明

统计数据聚合器负责定期从原始节点表（`botnet_nodes_{type}`）聚合统计数据到展示表：
- **中国统计表**：`china_botnet_{type}` - 按省市统计僵尸网络节点数量
- **全球统计表**：`global_botnet_{type}` - 按国家统计僵尸网络节点数量

前端从这两个统计表读取数据进行展示。

## 🔄 数据流程

```
远端日志 → logs/mozi/YYYY-MM-DD.txt
                    ↓
              日志处理器读取
                    ↓
         写入 botnet_nodes_mozi (节点原始表)
                    ↓
         【统计聚合器】定时聚合 ← 你在这里！
                    ↓
    ┌───────────────┴────────────────┐
    ↓                                 ↓
china_botnet_mozi           global_botnet_mozi
(省市统计表)                   (国家统计表)
    ↓                                 ↓
    └───────────────┬────────────────┘
                    ↓
                前端展示
```

## 🚀 使用方法

### 方式一：守护进程模式（推荐 - 生产环境）

**自动定时聚合，持续运行**

```bash
# Windows
cd backend
start_aggregator.bat

# Linux/Mac
cd backend
chmod +x start_aggregator.sh
./start_aggregator.sh
```

**自定义聚合间隔：**
```bash
# 每5分钟聚合一次
python stats_aggregator/aggregator.py daemon 5

# 每小时聚合一次
python stats_aggregator/aggregator.py daemon 60

# 默认30分钟
python stats_aggregator/aggregator.py daemon
```

### 方式二：单次执行模式（测试/手动触发）

```bash
cd backend

# 聚合所有僵尸网络
python stats_aggregator/aggregator.py once

# 只聚合指定类型
python stats_aggregator/aggregator.py once mozi
python stats_aggregator/aggregator.py once asruex
```

### 方式三：一键启动所有服务

**Windows：**
```bash
# 在项目根目录下运行
start_all_services.bat
```

**Linux/Mac：**
```bash
# 在项目根目录下运行
chmod +x start_all_services.sh
./start_all_services.sh

# 停止所有服务
chmod +x stop_all_services.sh
./stop_all_services.sh
```

## 📊 支持的僵尸网络类型

- `asruex`
- `mozi`
- `andromeda`
- `moobot`
- `ramnit`
- `leethozer`

## 📝 日志文件

日志保存在：`backend/stats_aggregator.log`

**查看实时日志：**
```bash
# Linux/Mac
tail -f backend/stats_aggregator.log

# Windows (PowerShell)
Get-Content backend/stats_aggregator.log -Wait -Tail 50
```

## ⚙️ 配置说明

### 修改聚合间隔

编辑启动脚本中的时间参数：

**start_aggregator.bat (Windows):**
```batch
python stats_aggregator\aggregator.py daemon 30
                                              ↑
                                         修改这个数字（分钟）
```

**start_aggregator.sh (Linux/Mac):**
```bash
python3 stats_aggregator/aggregator.py daemon 30
                                              ↑
                                         修改这个数字（分钟）
```

### 修改数据库配置

数据库配置在 `backend/config.py` 中统一管理：

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "botnet"
}
```

## 🔧 聚合逻辑说明

### 中国地区统计

```sql
-- 从节点表按省市分组统计
SELECT 
    TRIM(TRAILING '省' FROM province) as province,
    TRIM(TRAILING '市' FROM city) as municipality,
    COUNT(*) as infected_num
FROM botnet_nodes_mozi
WHERE country = '中国'
GROUP BY province, city
```

**特殊处理：**
- 去除省份后缀的"省"字（如：河北省 → 河北）
- 去除城市后缀的"市"字（如：石家庄市 → 石家庄）
- 直辖市保持原样（北京、天津、上海、重庆）

### 全球统计

```sql
-- 从节点表按国家分组统计
SELECT 
    country,
    COUNT(*) as infected_num
FROM botnet_nodes_mozi
GROUP BY country
```

## 📈 性能考虑

### 完全重建 vs 增量更新

当前采用**完全重建**策略：
- ✅ 优点：数据准确，不会累积误差
- ✅ 优点：实现简单，易于维护
- ⚠️ 缺点：每次都扫描全表

对于数据量不大的场景（< 100万条记录），完全重建策略足够高效。

### 优化建议

如果节点表数据量很大（> 100万条），可以考虑：

1. **增加索引**（已实现）
   ```sql
   INDEX idx_location (country, province, city)
   INDEX idx_is_china (is_china)
   ```

2. **使用物化视图**（MySQL 不原生支持，需要手动实现）

3. **分区表**（按时间分区）
   ```sql
   PARTITION BY RANGE (YEAR(created_at)) (
       PARTITION p2024 VALUES LESS THAN (2025),
       PARTITION p2025 VALUES LESS THAN (2026)
   )
   ```

## 🐛 常见问题

### Q1: 前端显示的数据不更新？

**原因：** 统计聚合器未运行或出错

**解决：**
```bash
# 1. 检查聚合器是否在运行
# Windows: 任务管理器中查找 python.exe (aggregator.py)
# Linux/Mac: ps aux | grep aggregator

# 2. 查看日志
cat backend/stats_aggregator.log

# 3. 手动执行一次聚合
cd backend
python stats_aggregator/aggregator.py once
```

### Q2: 聚合器报错 "Table doesn't exist"

**原因：** 节点表不存在

**解决：**
```bash
# 确保日志处理器已经运行并处理了日志
# 日志处理器会自动创建节点表

# 检查表是否存在
mysql -u root -p123456 botnet
mysql> SHOW TABLES LIKE 'botnet_nodes_%';
```

### Q3: 统计表中数据为 0

**原因：** 节点表中没有数据

**解决：**
```bash
# 1. 检查节点表
mysql> SELECT COUNT(*) FROM botnet_nodes_mozi;

# 2. 如果为0，检查日志处理器
cd backend/log_processor
python main.py

# 3. 检查日志文件是否存在
ls -l backend/logs/mozi/
```

### Q4: 如何修改聚合间隔？

直接修改启动命令中的时间参数（单位：分钟）：

```bash
# 改为每10分钟
python stats_aggregator/aggregator.py daemon 10
```

## 📚 相关文件

- `aggregator.py` - 主程序
- `config.yaml` - 配置文件（可选）
- `../config.py` - 数据库配置
- `start_aggregator.bat` - Windows 启动脚本
- `start_aggregator.sh` - Linux/Mac 启动脚本
- `stats_aggregator.log` - 运行日志

## 🔗 相关模块

- **日志处理器**: `backend/log_processor/` - 负责读取日志并写入节点表
- **FastAPI 后端**: `backend/main.py` - 提供 API 接口给前端
- **前端**: `fronted/` - 展示统计数据

## 💡 最佳实践

1. **生产环境**：使用守护进程模式，每30分钟聚合一次
2. **开发环境**：可以缩短间隔到5分钟，便于测试
3. **监控日志**：定期检查日志文件，确保聚合正常运行
4. **备份数据**：定期备份数据库，特别是节点表
5. **性能优化**：如果数据量大，考虑在低峰期聚合（如凌晨）

## 🆘 技术支持

遇到问题？
1. 查看日志文件：`backend/stats_aggregator.log`
2. 检查数据库配置：`backend/config.py`
3. 测试数据库连接：`mysql -u root -p123456 botnet`
4. 手动执行聚合：`python stats_aggregator/aggregator.py once`



