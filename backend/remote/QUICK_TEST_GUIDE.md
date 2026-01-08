# 快速测试指南 - 5分钟验证数据传输

## 🎯 目标

快速验证从C2端到本地平台的完整数据传输流程。

---

## ⚡ 快速开始（Windows）

### 方式1: 一键测试脚本

```bash
cd d:\workspace\botnet\backend\remote
test_data_flow.bat
```

### 方式2: 手动执行

```bash
# 1. 生成5个测试日志文件
python mock_c2_log_generator.py --mode fast --count 5

# 2. 查看生成的文件
dir mock_logs

# 3. 查看日志内容
type mock_logs\test_*.log | more
```

---

## ⚡ 快速开始（Linux/Mac）

### 方式1: 一键测试脚本

```bash
cd /path/to/botnet/backend/remote
chmod +x test_data_flow.sh
./test_data_flow.sh
```

### 方式2: 手动执行

```bash
# 1. 生成5个测试日志文件
python3 mock_c2_log_generator.py --mode fast --count 5

# 2. 查看生成的文件
ls -lh mock_logs/

# 3. 查看日志内容
head -n 20 mock_logs/test_*.log
```

---

## 🧪 完整测试流程

### 场景1: 本地测试（开发环境）

```bash
# Step 1: 生成测试日志
cd D:\workspace\botnet\backend\remote
python mock_c2_log_generator.py --mode fast --count 5 --log-dir ./test_logs

# Step 2: 修改 config.json，指向测试日志
# "log_dir": "D:/workspace/botnet/backend/remote/test_logs",
# "log_file_pattern": "test_{datetime}.log"

# Step 3: 启动C2数据服务器
python c2_data_server_standalone.py

# 应该看到：
# [INFO] 读取日志文件: test_2026-01-08_07.log
# [INFO]   ✓ 文件处理完成: 读取4532行，提取4532个IP
# [INFO] ✓ 新增 4532 条记录，当前缓存: 4532 条

# Step 4: 测试拉取接口
curl -H "X-API-Key: KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4" ^
     "http://localhost:8888/api/pull?limit=10&confirm=true"

# 应该返回JSON数据：
# {"success":true,"count":10,"data":[...]}
```

---

### 场景2: 模拟真实环境（C2在服务器）

**C2端（101.32.11.139）**:

```bash
# 1. 上传脚本
scp mock_c2_log_generator.py ubuntu@101.32.11.139:/home/ubuntu/

# 2. SSH登录
ssh ubuntu@101.32.11.139

# 3. 生成测试日志到实际目录
python3 mock_c2_log_generator.py \
    --log-dir /home/ubuntu/logs \
    --prefix ramnit \
    --mode fast \
    --count 10

# 输出:
# [生成] ramnit_2026-01-08_01.log (4532 条日志)
# [生成] ramnit_2026-01-08_02.log (4789 条日志)
# ...

# 4. 启动C2数据服务器
export C2_API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
python3 c2_data_server.py

# 应该看到读取日志并缓存数据
```

**本地平台**:

```bash
# 1. 确认 config.py 配置正确
# C2_ENDPOINTS = [{
#     'url': 'http://101.32.11.139:8888',
#     'api_key': 'KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4',
#     'enabled': True,
# }]

# 2. 启动日志处理器
cd D:\workspace\botnet\backend\log_processor
python main.py

# 应该看到:
# [INFO] [OK] 远程拉取器已初始化（1 个C2端点）
# [INFO] [C2-Ramnit-1] ✓ 拉取成功: 4532 条
# [INFO] [OK] [ramnit] API数据处理完成: 成功 4532, 失败 0

# 3. 验证数据库
# 登录MySQL查看数据是否正确插入
```

---

## 📊 生成的测试数据示例

```bash
# 文件: test_2026-01-08_11.log
# 大小: 约 1-2 MB
# 行数: 4000-5000 行

# 内容示例:
2026-01-08 11:00:15,203.45.67.89
2026-01-08 11:02:33,101.32.11.139
2026-01-08 11:05:48,171.233.146.163
2026-01-08 11:08:12,14.231.172.240
2026-01-08 11:11:27,182.156.79.234
...
```

---

## ✅ 验证步骤

### 1. 验证日志生成

```bash
# 检查文件数量
ls mock_logs/*.log | wc -l
# 应该等于生成的数量（默认5个）

# 检查文件大小
ls -lh mock_logs/
# 每个文件应该约 1-2 MB

# 检查行数
wc -l mock_logs/test_*.log
# 每个文件应该约 4000-5000 行
```

### 2. 验证C2端读取

```bash
# C2服务器日志应该显示:
[INFO] 读取日志文件: test_2026-01-08_07.log
[INFO]   ✓ 文件处理完成: 读取4532行，提取4532个IP
[INFO] ✓ 新增 4532 条记录，当前缓存: 22660 条

# 测试统计接口
curl http://101.32.11.139:8888/stats
# 返回: {"cached_records":22660,"total_generated":22660,...}
```

### 3. 验证数据拉取

```bash
# 本地日志处理器应该显示:
[INFO] [C2-Ramnit-1] ✓ 拉取成功: 1000 条
[INFO] [OK] [ramnit] API数据处理完成: 成功 1000, 失败 0

# 多次拉取后，C2端缓存应该减少
curl http://101.32.11.139:8888/stats
# 返回: {"cached_records":21660,...}
```

### 4. 验证数据库插入

```sql
-- 登录MySQL
mysql -u root -p

-- 选择数据库
USE botnet;

-- 查看插入的IP数量
SELECT COUNT(*) FROM ip_info WHERE botnet_type = 'ramnit';
-- 应该能看到刚才拉取的IP数量

-- 查看最近插入的IP
SELECT ip, first_seen, botnet_type 
FROM ip_info 
WHERE botnet_type = 'ramnit' 
ORDER BY id DESC 
LIMIT 10;

-- 验证IP格式正确（无前导零）
SELECT ip FROM ip_info WHERE ip LIKE '0%' OR ip LIKE '%.0%';
-- 应该返回空（没有前导零）
```

---

## 🎯 常见测试场景

### 测试场景1: 验证IP规范化

```bash
# 手动创建包含前导零IP的日志
echo "2026-01-08 12:00:00,01.10.238.162" > test_logs/test_manual.log
echo "2026-01-08 12:01:00,192.168.001.1" >> test_logs/test_manual.log

# 验证C2端是否正确规范化
# 01.10.238.162 应该被规范化为 1.10.238.162
# 192.168.001.1 应该被过滤（私有IP）
```

### 测试场景2: 验证按小时过滤

```bash
# 生成包含当前小时的日志
python mock_c2_log_generator.py --mode fast --count 3

# C2服务器应该跳过当前小时的文件
# 只读取上一小时及更早的文件
```

### 测试场景3: 压力测试

```bash
# 生成大量日志（48小时）
python mock_c2_log_generator.py --mode historical --hours 48

# 预期生成约 48 个文件，共 19-24万条日志
# 测试C2端和本地平台的处理能力
```

---

## 🔧 故障排查

### 问题1: 生成的日志为空

```bash
# 检查脚本输出
python mock_c2_log_generator.py --mode fast --count 1

# 如果看到 "[跳过] 文件已存在"
# 删除旧文件: rm mock_logs/*.log
# 重新生成
```

### 问题2: C2端不读取日志

```bash
# 检查日志目录配置
cat config.json | grep log_dir

# 检查文件名模式
cat config.json | grep log_file_pattern

# 确保生成的文件名匹配模式
# 例如: ramnit_{datetime}.log 匹配 ramnit_2026-01-08_11.log
```

### 问题3: 拉取失败（404错误）

```bash
# 检查API路径
# 确保C2服务器注册了 /api/pull 路径

# 测试健康检查
curl http://101.32.11.139:8888/health

# 测试拉取接口
curl -H "X-API-Key: KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4" \
     http://101.32.11.139:8888/api/pull?limit=1
```

---

## 📋 测试清单

- [ ] 脚本能正常生成日志文件
- [ ] 文件名格式正确（`prefix_YYYY-MM-DD_HH.log`）
- [ ] 日志内容格式正确（`YYYY-MM-DD HH:MM:SS,IP`）
- [ ] IP地址为公网IP（无私有IP）
- [ ] 每个文件约4000-5000行
- [ ] C2服务器能读取并缓存数据
- [ ] 本地拉取器能成功拉取数据
- [ ] IP地址被正确规范化（去除前导零）
- [ ] 数据库中能查询到插入的IP
- [ ] 拉取后C2端缓存数据减少

---

## 🎉 成功标志

当你看到以下输出时，说明数据传输完全正常：

**C2端**:
```
[INFO] ✓ 新增 4532 条记录，当前缓存: 4532 条
[INFO] 拉取请求: 返回并确认 1000 条记录
```

**本地平台**:
```
[INFO] [C2-Ramnit-1] ✓ 拉取成功: 1000 条
[INFO] [OK] [ramnit] API数据处理完成: 成功 1000, 失败 0
```

**数据库**:
```sql
SELECT COUNT(*) FROM ip_info WHERE botnet_type = 'ramnit';
-- 返回: 1000（或更多）
```

恭喜！你的数据传输系统工作正常！🎉
