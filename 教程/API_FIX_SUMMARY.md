# API 数据库连接问题修复总结

## 🐛 问题描述

前端无法显示数据，包括：
- 地图上的节点信息
- 左侧各城市的僵尸网络节点数量
- 其他统计信息

API 返回错误：
```
{"detail":"cannot access local variable 'cursor' where it is not associated with a value"}
```

## 🔍 问题根因

### 1. 数据库配置不统一
- `backend/main.py` 中定义了一个 `DB_CONFIG`（密码：root）
- `backend/config.py` 中也定义了 `DB_CONFIG`（密码：123456）
- 所有路由器（router/*）都使用 `config.py` 中的配置
- 但 `main.py` 中的 API 端点使用的是本地定义的配置

### 2. finally 块中的变量访问错误
在多个函数中，`finally` 块试图访问可能未初始化的变量：

**错误代码示例：**
```python
async def get_botnet_tables():
    try:
        conn = pymysql.connect(**DB_CONFIG)  # 如果这里失败
        cursor = conn.cursor()               # cursor 未创建
        ...
    finally:
        cursor.close()  # ❌ 错误！cursor 可能不存在
        conn.close()    # ❌ 错误！conn 可能不存在
```

当数据库连接失败时（比如密码错误），`conn` 和 `cursor` 变量还没有被创建，但 `finally` 块尝试关闭它们，导致 `NameError` 或 `UnboundLocalError`。

## ✅ 修复方案

### 1. 统一数据库配置

**修改 `backend/main.py` 第22行：**
```python
# 修改前：
from config import API_KEY, ALLOWED_UPLOAD_IPS, MAX_LOGS_PER_UPLOAD, ALLOWED_BOTNET_TYPES

# 修改后：
from config import API_KEY, ALLOWED_UPLOAD_IPS, MAX_LOGS_PER_UPLOAD, ALLOWED_BOTNET_TYPES, DB_CONFIG
```

**删除 `backend/main.py` 第46-52行的重复定义：**
```python
# 删除以下内容：
# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "botnet"
}
```

### 2. 修复所有 finally 块

在所有数据库操作函数中，修改为以下模式：

**正确的代码模式：**
```python
async def some_function():
    conn = None      # ✅ 在 try 之前初始化
    cursor = None    # ✅ 在 try 之前初始化
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # ... 数据库操作 ...
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        if cursor:      # ✅ 检查是否存在
            cursor.close()
        if conn:        # ✅ 检查是否存在
            conn.close()
```

### 3. 修复的函数列表

以下函数已修复：
1. ✅ `get_botnet_tables()` - 第597行
2. ✅ `get_province_amounts()` - 第277行
3. ✅ `get_world_amounts()` - 第350行
4. ✅ `get_user_events()` - 第430行
5. ✅ `get_anomaly_reports()` - 第472行
6. ✅ `update_global_botnet()` - 第626行
7. ✅ `get_country_botnet()` - 第667行

## 🧪 测试验证

### 1. 确认数据库密码
```bash
# 测试连接
mysql -u root -p123456 botnet
```

### 2. 确认配置文件
`backend/config.py` 中的密码应该是：
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",  # ✅ 正确的密码
    "database": "botnet"
}
```

### 3. 测试数据库连接
```bash
cd backend
python test_db.py
```

### 4. 测试 API 端点
```bash
# 测试省份统计接口
curl http://localhost:8000/api/province-amounts

# 运行完整测试
python test_api_fix.py
```

### 5. 重启后端服务
```bash
cd backend
python main.py
```

### 6. 访问前端
打开浏览器访问前端，检查：
- ✅ 地图是否显示节点
- ✅ 左侧城市统计是否显示
- ✅ 右侧数据面板是否显示

## 📊 预期结果

修复后，API 应该正常返回数据：

**正常的响应示例：**
```json
{
  "asruex": [
    {"province": "北京", "amount": 1234},
    {"province": "上海", "amount": 5678}
  ],
  "mozi": [
    {"province": "北京", "amount": 890},
    {"province": "上海", "amount": 456}
  ]
}
```

## 🚨 如果问题仍然存在

### 1. 检查数据库表是否存在
```sql
USE botnet;
SHOW TABLES LIKE 'botnet_nodes_%';
SHOW TABLES LIKE 'china_botnet_%';
SHOW TABLES LIKE 'global_botnet_%';
SELECT * FROM botnet_types;
```

### 2. 检查表中是否有数据
```sql
SELECT COUNT(*) FROM botnet_nodes_asruex;
SELECT COUNT(*) FROM china_botnet_asruex;
```

### 3. 查看后端日志
启动后端时观察日志输出，看是否有错误信息。

### 4. 检查浏览器控制台
按 F12 打开浏览器控制台，查看：
- Network 标签：API 请求是否成功
- Console 标签：是否有 JavaScript 错误

## 📝 技术说明

### 为什么会出现这个错误？

Python 中，如果在 `try` 块内定义的变量在某些条件下没有被创建（比如在创建之前抛出异常），那么在 `finally` 块中访问这个变量会导致 `NameError`。

**错误流程：**
1. `pymysql.connect(**DB_CONFIG)` 失败（密码错误）
2. 抛出异常，`conn` 和 `cursor` 未被创建
3. 进入 `finally` 块
4. 尝试 `cursor.close()` → `NameError: name 'cursor' is not defined`
5. FastAPI 捕获这个错误，返回 "cannot access local variable 'cursor'..."

**解决方法：**
- 在 `try` 之前初始化变量为 `None`
- 在 `finally` 中检查变量是否为 `None` 后再操作

## ✨ 总结

通过这次修复，我们：
1. ✅ 统一了数据库配置，消除了配置冲突
2. ✅ 修复了 7 个函数的异常处理逻辑
3. ✅ 提高了代码的健壮性和容错能力
4. ✅ 确保前端能够正常获取和显示数据

现在系统应该可以正常工作了！🎉

