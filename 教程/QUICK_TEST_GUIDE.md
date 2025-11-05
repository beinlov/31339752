# 日志上传接口快速测试指南

## ⚡ 5分钟快速测试

### 前置条件
- ✅ Python 3.7+
- ✅ MySQL数据库运行中
- ✅ 已安装依赖: `pip install fastapi uvicorn pymysql requests`

---

## 🚀 步骤1: 配置API密钥（30秒）

编辑 `backend/config.py`，找到这一行：

```python
API_KEY = "your-secret-api-key-change-this-in-production"
```

**开发测试**: 保持默认即可

**生产环境**: 修改为强密钥（建议32字符以上）

生成强密钥：
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🚀 步骤2: 启动服务（1分钟）

### 方式1: 一键启动（推荐）

```bash
cd backend

# Windows
start_all.bat

# Linux/Mac
chmod +x start_all.sh
./start_all.sh
```

### 方式2: 手动启动

**窗口1 - 启动后端API**:
```bash
cd backend
python main.py
```

**窗口2 - 启动日志处理器**:
```bash
cd backend/log_processor
python main.py
```

**验证服务已启动**:
```bash
# 浏览器访问或curl
curl http://localhost:8000/api/upload-status
```

应该看到类似输出：
```json
{
  "api_status": "running",
  "timestamp": "2025-10-30 15:30:00",
  ...
}
```

---

## 🚀 步骤3: 运行测试（2分钟）

### 3.1 本地测试

```bash
# 在项目根目录运行
python test_upload.py
```

**预期输出**:
```
============================================================
  僵尸网络日志上传接口测试工具
============================================================

📊 测试1: 查询上传接口状态
============================================================
状态码: 200
API状态: running
✅ 状态查询成功！

📤 测试: 上传 Mozi 僵尸网络日志
============================================================
✅ 上传成功！
  - 接收数量: 3
  - 保存位置: backend/logs/mozi/2025-10-30.txt

...

🎉 所有测试通过！接口工作正常。
```

### 3.2 查看上传的日志文件

```bash
# Windows
type backend\logs\mozi\2025-10-30.txt

# Linux/Mac
cat backend/logs/mozi/2025-10-30.txt
```

应该看到测试上传的日志行。

### 3.3 查看日志处理器输出

查看日志处理器是否自动处理了上传的日志：

```bash
# Windows
type backend\log_processor.log | findstr "mozi"

# Linux/Mac
tail -f backend/log_processor.log | grep "mozi"
```

应该看到类似：
```
[mozi] Processing 3 new lines from 2025-10-30.txt
[mozi] Flushed 3 nodes to database. Total: 3
```

### 3.4 验证数据已入库

```bash
# 连接数据库
mysql -u root -p botnet

# 查询数据
SELECT * FROM botnet_nodes_mozi 
WHERE created_at > NOW() - INTERVAL 10 MINUTE
ORDER BY created_at DESC 
LIMIT 5;
```

应该看到刚才上传的测试数据。

---

## 🎯 常见问题快速解决

### ❌ 问题1: 连接被拒绝

```
Connection refused to localhost:8000
```

**解决**:
```bash
# 检查后端是否运行
netstat -an | grep 8000  # Linux/Mac
netstat -an | findstr 8000  # Windows

# 如果没有运行，启动后端
cd backend
python main.py
```

---

### ❌ 问题2: 401认证失败

```
❌ 认证失败！
原因: API密钥无效
```

**解决**:
确保 `test_upload.py` 中的 `API_KEY` 与 `backend/config.py` 一致：

```python
# test_upload.py (第20行)
API_KEY = "your-secret-api-key-change-this-in-production"

# backend/config.py (第15行)
API_KEY = "your-secret-api-key-change-this-in-production"
```

---

### ❌ 问题3: 403 IP未授权

```
❌ 权限不足！
原因: IP未在白名单中
```

**解决**:
编辑 `backend/config.py`，清空IP白名单（开发环境）：

```python
ALLOWED_UPLOAD_IPS = []  # 空列表 = 允许所有IP
```

然后重启后端服务。

---

### ❌ 问题4: 日志文件已保存但未处理

```
# 日志文件存在
backend/logs/mozi/2025-10-30.txt ✓

# 但数据库无数据 ✗
```

**解决**:
```bash
# 检查日志处理器是否运行
ps aux | grep log_processor  # Linux/Mac
tasklist | findstr python    # Windows

# 如果没运行，启动它
cd backend/log_processor
python main.py
```

---

## 🌐 测试远端上传（可选）

如果需要测试从远端服务器上传：

### 1. 配置远端脚本

编辑 `remote_uploader.py`：

```python
# 第20行：修改为本地服务器IP
LOCAL_SERVER_HOST = "你的本地IP"  # 如：192.168.1.100

# 第25行：确保API密钥一致
API_KEY = "your-secret-api-key-change-this-in-production"

# 第28行：选择僵尸网络类型
BOTNET_TYPE = "mozi"

# 第31行：指定日志文件路径
LOG_FILE_PATH = "/path/to/your/honeypot.log"
```

### 2. 测试连接

在远端服务器上运行：

```bash
python remote_uploader.py test
```

**预期输出**:
```
测试连接到本地服务器...
✅ 连接成功!
服务器状态: running

测试上传功能...
✅ 上传测试成功!

🎉 所有测试通过！可以运行正式模式
```

### 3. 启动上传器

```bash
# 前台运行（测试）
python remote_uploader.py

# 后台运行（生产）
nohup python remote_uploader.py > /tmp/uploader.log 2>&1 &
```

---

## ✅ 测试完成检查清单

- [ ] 后端API运行正常（`http://localhost:8000/api/upload-status` 可访问）
- [ ] 日志处理器运行正常
- [ ] `test_upload.py` 所有测试通过
- [ ] 日志文件已保存到 `backend/logs/{type}/`
- [ ] 数据已写入数据库
- [ ] 日志处理器日志显示处理成功
- [ ] 远端上传测试成功（如适用）

---

## 📚 下一步

测试成功后，继续阅读：

- **详细文档**: `LOG_UPLOAD_API_GUIDE.md`
- **API接口说明**: `http://localhost:8000/docs`（FastAPI自动生成）
- **去重机制**: `backend/log_processor/DEDUPLICATION.md`
- **系统架构**: `backend/log_processor/ARCHITECTURE.md`

---

## 🎉 测试成功！

如果所有测试都通过，说明日志上传接口已经可以正常工作了！

现在你可以：
1. ✅ 将远端脚本部署到蜜罐服务器
2. ✅ 配置生产环境的API密钥和白名单
3. ✅ 开始接收真实的日志数据
4. ✅ 在前端界面查看统计数据

**祝使用愉快！** 🚀



