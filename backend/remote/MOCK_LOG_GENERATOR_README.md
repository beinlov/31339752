# 模拟C2日志生成器使用指南

## 📋 简介

`mock_c2_log_generator.py` 是一个用于测试数据传输的日志生成器，模拟C2端生成每小时日志文件。

---

## ✨ 功能特性

- ✅ 自动生成符合格式的日志文件
- ✅ 每个文件包含4000-5000条随机日志
- ✅ 随机生成真实的公网IP地址
- ✅ 支持三种运行模式（历史、持续、快速）
- ✅ 自动排除私有IP段

---

## 📝 日志格式

### 文件名格式
```
test_2025-12-18_15.log
└──┬──┘ └─────┬─────┘ └┬┘
  前缀      日期      小时
```

### 日志内容格式
```
2025-12-03 15:59:08,171.233.146.163
└─────┬─────┘ └──┬──┘ └──────┬──────┘
    日期      时间        IP地址
```

---

## 🚀 使用方法

### 模式1: 生成历史日志（推荐用于初始化测试）

生成最近24小时的日志文件：

```bash
python mock_c2_log_generator.py --mode historical --hours 24
```

生成最近48小时的日志：

```bash
python mock_c2_log_generator.py --mode historical --hours 48
```

**输出示例**：
```
日志生成器初始化完成
  - 日志目录: D:\workspace\botnet\backend\remote\mock_logs
  - 文件前缀: test

开始生成历史日志（最近 24 小时）...
[生成] test_2026-01-07_12.log (4532 条日志)
  ✓ 完成: D:\workspace\botnet\backend\remote\mock_logs\test_2026-01-07_12.log
[生成] test_2026-01-07_13.log (4789 条日志)
  ✓ 完成: D:\workspace\botnet\backend\remote\mock_logs\test_2026-01-07_13.log
...
✓ 历史日志生成完成
```

---

### 模式2: 持续运行（推荐用于长期测试）

每小时自动生成新的日志文件：

```bash
python mock_c2_log_generator.py --mode continuous
```

自定义检查间隔（每10分钟检查一次）：

```bash
python mock_c2_log_generator.py --mode continuous --interval 600
```

**输出示例**：
```
开始持续运行模式（每 3600 秒检查一次）...
按 Ctrl+C 停止
[生成] test_2026-01-08_11.log (4321 条日志)
  ✓ 完成: D:\workspace\botnet\backend\remote\mock_logs\test_2026-01-08_11.log
[等待] 下次检查时间: 2026-01-08 13:00:00
```

---

### 模式3: 快速测试（推荐用于功能验证）

快速生成10个文件（每5秒一个）：

```bash
python mock_c2_log_generator.py --mode fast --count 10 --fast-interval 5
```

生成5个文件（每2秒一个）：

```bash
python mock_c2_log_generator.py --mode fast --count 5 --fast-interval 2
```

**输出示例**：
```
快速测试模式：生成 10 个文件（间隔 5 秒）...
[生成] test_2026-01-08_02.log (4612 条日志)
  ✓ 完成: ...
  等待 5 秒...
[生成] test_2026-01-08_03.log (4890 条日志)
  ✓ 完成: ...
...
✓ 快速测试完成
```

---

## ⚙️ 完整参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--log-dir` | 日志文件目录 | `./mock_logs` |
| `--prefix` | 文件名前缀 | `test` |
| `--mode` | 运行模式 | `historical` |
| `--hours` | 历史模式：生成小时数 | `24` |
| `--interval` | 持续模式：检查间隔（秒） | `3600` |
| `--count` | 快速模式：文件数量 | `10` |
| `--fast-interval` | 快速模式：文件间隔（秒） | `5` |

---

## 📦 完整部署示例

### Windows（开发环境）

```bash
# 1. 切换到工作目录
cd D:\workspace\botnet\backend\remote

# 2. 生成最近24小时的历史日志
python mock_c2_log_generator.py --mode historical --hours 24

# 3. 查看生成的文件
dir mock_logs

# 输出：
# test_2026-01-07_12.log
# test_2026-01-07_13.log
# ...
# test_2026-01-08_11.log
```

---

### Linux（C2服务器）

```bash
# 1. 上传脚本到C2服务器
scp mock_c2_log_generator.py ubuntu@101.32.11.139:/home/ubuntu/

# 2. SSH登录
ssh ubuntu@101.32.11.139

# 3. 生成日志到指定目录
cd /home/ubuntu
python3 mock_c2_log_generator.py \
    --log-dir /home/ubuntu/logs \
    --prefix ramnit \
    --mode historical \
    --hours 48

# 4. 查看生成的文件
ls -lh /home/ubuntu/logs/

# 输出：
# ramnit_2026-01-06_12.log  (约1-2MB)
# ramnit_2026-01-06_13.log
# ...

# 5. （可选）持续运行模式
nohup python3 mock_c2_log_generator.py \
    --log-dir /home/ubuntu/logs \
    --prefix ramnit \
    --mode continuous \
    > /tmp/log_generator.log 2>&1 &
```

---

## 🧪 测试完整数据流

### 步骤1: 生成测试日志

```bash
# C2端
cd /home/ubuntu
python3 mock_c2_log_generator.py \
    --log-dir /home/ubuntu/logs \
    --prefix ramnit \
    --mode historical \
    --hours 10
```

### 步骤2: 启动C2数据服务器

```bash
# C2端
export C2_API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
python3 c2_data_server.py
```

### 步骤3: 查看C2端读取日志

```bash
# 应该看到：
# [INFO] 读取日志文件: ramnit_2026-01-08_01.log
# [INFO]   ✓ 文件处理完成: 读取4532行，提取4532个IP
# [INFO] ✓ 新增 4532 条记录，当前缓存: 4532 条
```

### 步骤4: 启动本地拉取器

```bash
# 本地平台
cd D:\workspace\botnet\backend\log_processor
python main.py
```

### 步骤5: 查看拉取结果

```bash
# 应该看到：
# [INFO] [C2-Ramnit-1] ✓ 拉取成功: 4532 条
# [INFO] [OK] [ramnit] API数据处理完成: 成功 4532, 失败 0
```

---

## 📊 生成的日志示例

```
2026-01-08 11:00:15,203.45.67.89
2026-01-08 11:02:33,101.32.11.139
2026-01-08 11:05:48,171.233.146.163
2026-01-08 11:08:12,14.231.172.240
2026-01-08 11:11:27,182.156.79.234
...
（每个文件约4000-5000行）
```

---

## 🔧 自定义配置

### 修改文件前缀（匹配僵尸网络类型）

```bash
# 生成 ramnit 类型的日志
python mock_c2_log_generator.py --prefix ramnit --mode historical

# 生成 zeus 类型的日志
python mock_c2_log_generator.py --prefix zeus --mode historical
```

### 修改日志目录

```bash
# 生成到自定义目录
python mock_c2_log_generator.py --log-dir /data/botnet/logs --mode historical
```

---

## 📁 文件结构

```
backend/remote/
├── mock_c2_log_generator.py     ← 日志生成器脚本
├── MOCK_LOG_GENERATOR_README.md ← 本文档
└── mock_logs/                    ← 生成的日志文件（默认）
    ├── test_2026-01-08_01.log
    ├── test_2026-01-08_02.log
    └── ...
```

---

## ⚠️ 注意事项

1. **日志数量**：每个文件随机生成4000-5000条日志，符合真实场景
2. **IP地址**：自动排除私有IP段（10.x.x.x, 192.168.x.x等）
3. **时间分布**：日志时间在该小时内随机分布，更真实
4. **文件覆盖**：不会覆盖已存在的文件，避免数据丢失
5. **持续模式**：会生成**上一个小时**的日志（当前小时视为正在写入）

---

## 🎯 推荐使用流程

### 初次测试
```bash
# 1. 快速生成少量文件测试
python mock_c2_log_generator.py --mode fast --count 5

# 2. 启动C2服务器验证读取
python c2_data_server.py

# 3. 启动本地拉取器验证传输
python main.py
```

### 完整测试
```bash
# 1. 生成24小时历史数据
python mock_c2_log_generator.py --mode historical --hours 24

# 2. 启动C2服务器
python c2_data_server.py

# 3. 启动本地拉取器
python main.py

# 4. 验证数据库中的数据
```

### 长期测试
```bash
# 后台持续运行
nohup python3 mock_c2_log_generator.py --mode continuous > generator.log 2>&1 &
```

---

## ✅ 验证清单

- [ ] 文件名格式正确（`test_YYYY-MM-DD_HH.log`）
- [ ] 日志内容格式正确（`YYYY-MM-DD HH:MM:SS,IP`）
- [ ] IP地址为公网IP（无私有IP）
- [ ] 每个文件约4000-5000行
- [ ] C2服务器能正确读取日志
- [ ] 本地拉取器能成功拉取数据
- [ ] 数据库中能看到插入的IP记录

---

## 🎉 总结

这个脚本让你能够：
- ✅ 快速生成测试数据
- ✅ 验证完整的数据传输流程
- ✅ 不需要真实的C2蜜罐环境
- ✅ 灵活控制测试场景

**现在可以开始测试你的数据传输系统了！** 🚀
