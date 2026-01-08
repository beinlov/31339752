# 使用本地C2服务器进行测试

## 🎯 目的
在本地快速测试，避免修改远程服务器配置。

---

## 📝 步骤

### 1️⃣ 生成测试数据

创建测试日志文件：

```bash
cd d:\workspace\botnet\backend\remote

# 创建测试日志目录
mkdir -p test_logs

# 生成测试数据
python mock_c2_log_generator.py
```

编辑 `mock_c2_log_generator.py`，确保生成test类型的数据：
```python
BOTNET_TYPE = "test"  # 改为test
LOG_DIR = "./test_logs"
```

### 2️⃣ 启动本地C2服务器

```bash
cd d:\workspace\botnet\backend\remote

# 确认config.json配置
# botnet_type: test
# log_dir: ./test_logs 或绝对路径

# 启动C2服务器（监听8888端口）
python c2_data_server.py
```

**预期输出**：
```
[INFO] 加载配置文件: config.json
[INFO] 僵尸网络类型: test
[INFO] 日志目录: ./test_logs
[INFO] C2数据服务器启动在 http://0.0.0.0:8888
```

### 3️⃣ 修改后端配置使用本地C2

编辑 `d:\workspace\botnet\backend\config.py`：

```python
C2_ENDPOINTS = [
    {
        'name': 'C2-test-local',
        'url': 'http://localhost:8888',  # 改为localhost
        'api_key': 'KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4',
        'enabled': True,
        'pull_interval': 60,
        'batch_size': 1000,
        'timeout': 30,
    },
]
```

### 4️⃣ 重启后端服务

```bash
cd d:\workspace\botnet\backend

# 停止当前后端（Ctrl+C）

# 重启
python main.py
```

### 5️⃣ 验证数据流

**查看后端日志**：
```
2026-01-08 16:XX:XX - __main__ - INFO - [test] 收到 1000 个IP，开始处理...  ← test而不是ramnit
```

**检查数据库**：
```bash
python check_processing.py
```

**预期输出**：
```
TEST:
  节点数: 1000  ← 有数据了
  通信记录数: 1000
  最新数据时间: 2026-01-08 16:XX:XX

RAMNIT:
  节点数: 115039  ← 不再增长
```

---

## 🔧 故障排查

### 问题1：C2服务器无法启动

**错误**: `Address already in use`

**解决**:
```bash
# Windows
netstat -ano | findstr :8888
taskkill /F /PID <进程ID>

# Linux
lsof -i :8888
kill -9 <进程ID>
```

### 问题2：后端连接失败

**错误**: `Cannot connect to host localhost:8888`

**检查**:
1. C2服务器是否在运行？
2. 端口是否正确（8888）？
3. 防火墙是否阻止？

**验证**:
```bash
curl http://localhost:8888/api/health
```

### 问题3：数据仍然是ramnit

**可能原因**:
1. C2服务器的config.json没改
2. C2服务器没重启
3. 日志文件中的数据本身就是ramnit类型

**解决**:
```bash
# 检查C2服务器配置
cat config.json | grep botnet_type

# 重启C2服务器
# Ctrl+C 停止
python c2_data_server.py
```

---

## ✅ 成功标志

1. **C2服务器日志**：
   ```
   [INFO] 僵尸网络类型: test
   [INFO] 找到日志文件: test_2026010816.log
   [INFO] 拉取请求: 返回 1000 条记录
   ```

2. **后端日志**：
   ```
   [INFO] [test] 收到 1000 个IP，开始处理...
   [INFO] [test] 批量写入 200 条节点数据
   ```

3. **数据库**：
   ```sql
   SELECT COUNT(*) FROM botnet_nodes_test;  -- 有数据
   SELECT COUNT(*) FROM botnet_communications_test;  -- 有数据
   ```

---

## 🎯 测试完成后

如果本地测试成功，可以：
1. 将相同配置应用到远程C2服务器
2. 或继续使用本地C2进行开发测试

---

**建议**：先用本地C2测试，确认逻辑正确后再修改远程服务器。
