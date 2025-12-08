# 更新聚合器僵尸网络列表指南

## 📋 何时需要更新

当通过前端界面添加新的僵尸网络类型后，需要手动更新聚合器配置，使其能够聚合新僵尸网络的数据。

## 🔧 更新步骤

### 步骤1: 更新 aggregator.py

**文件位置**: `backend/stats_aggregator/aggregator.py`

**修改位置**: 第35行左右

```python
# 修改前
BOTNET_TYPES = ['asruex', 'andromeda', 'mozi', 'leethozer', 'ramnit', 'moobot']

# 修改后（添加新僵尸网络 'newbot'）
BOTNET_TYPES = ['asruex', 'andromeda', 'mozi', 'leethozer', 'ramnit', 'moobot', 'newbot']
```

### 步骤2: 更新 config.yaml

**文件位置**: `backend/stats_aggregator/config.yaml`

**修改位置**: botnet_types 部分

```yaml
# 修改前
botnet_types:
  - asruex
  - andromeda
  - mozi
  - leethozer
  - ramnit
  - moobot

# 修改后（添加新僵尸网络 'newbot'）
botnet_types:
  - asruex
  - andromeda
  - mozi
  - leethozer
  - ramnit
  - moobot
  - newbot
```

### 步骤3: 重启聚合器服务

如果聚合器正在运行，需要重启：

```bash
# 停止当前运行的聚合器（Ctrl+C）

# 重新启动聚合器（守护进程模式，每5分钟聚合一次）
python stats_aggregator/aggregator.py daemon 5

# 或者执行一次性聚合测试
python stats_aggregator/aggregator.py once
```

## 🎯 验证更新

### 方法1: 查看日志输出

启动聚合器后，应该看到类似输出：

```
INFO - ============================================================
INFO - 统计聚合器启动（守护进程模式）
INFO - 聚合间隔: 5 分钟
INFO - 监控的僵尸网络: asruex, andromeda, mozi, leethozer, ramnit, moobot, newbot
INFO - ============================================================
```

### 方法2: 检查聚合结果

```
INFO - [newbot] 开始聚合统计数据...
INFO - [newbot] 节点表共有 XXX 条记录
INFO - [newbot] 聚合完成：节点 XXX -> 中国统计 XX 条，全球统计 XX 条
```

如果节点表为空或不存在，会显示：

```
INFO - [newbot] 节点表为空，跳过聚合
# 或
WARNING - [newbot] 节点表 botnet_nodes_newbot 不存在，跳过
```

## 📝 完整示例

假设添加了名为 `mirai` 的新僵尸网络：

### 1. 修改 aggregator.py
```python
class StatsAggregator:
    """统计数据聚合器"""
    
    # 支持的僵尸网络类型
    BOTNET_TYPES = ['asruex', 'andromeda', 'mozi', 'leethozer', 'ramnit', 'moobot', 'mirai']
```

### 2. 修改 config.yaml
```yaml
botnet_types:
  - asruex
  - andromeda
  - mozi
  - leethozer
  - ramnit
  - moobot
  - mirai
```

### 3. 重启并验证
```bash
# 重启聚合器
python stats_aggregator/aggregator.py daemon 5

# 查看日志确认 mirai 已被包含
# 应该看到: "监控的僵尸网络: asruex, andromeda, mozi, leethozer, ramnit, moobot, mirai"
```

## ⚠️ 注意事项

1. **名称一致性**: 确保添加的名称与数据库表名一致（不包含前缀）
   - 数据库表: `botnet_nodes_mirai`
   - 配置中: `mirai`

2. **顺序无关**: 列表中的顺序不影响聚合功能

3. **空表处理**: 如果新添加的僵尸网络还没有数据，聚合器会跳过，不会报错

4. **实时生效**: 修改配置后必须重启聚合器才能生效

## 🔄 自动化建议

未来可以考虑实现自动更新机制：

1. 聚合器启动时从数据库读取 `botnet_types` 表
2. 动态构建 `BOTNET_TYPES` 列表
3. 无需手动修改配置文件

**示例代码**（未实现）:
```python
def get_botnet_types_from_db():
    """从数据库获取所有僵尸网络类型"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM botnet_types")
    types = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return types

# 在 __init__ 中使用
BOTNET_TYPES = get_botnet_types_from_db()
```

## 📊 当前支持的僵尸网络

截至最后更新，系统支持以下僵尸网络：

1. **asruex** - Asruex僵尸网络
2. **andromeda** - Andromeda僵尸网络
3. **mozi** - Mozi僵尸网络
4. **leethozer** - Leethozer僵尸网络
5. **ramnit** - Ramnit僵尸网络
6. **moobot** - Moobot僵尸网络

---

**最后更新**: 2025-12-04
