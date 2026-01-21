# 数据保留策略实施工具集

## 📁 文件清单

```
backend/
├── scripts/
│   ├── data_retention_config.py    # 配置管理（核心配置文件）
│   ├── data_archiver.py            # 数据归档工具
│   ├── data_cleaner.py             # 数据清理工具
│   ├── retention_manager.py        # 保留策略管理器（主入口）
│   ├── check_data_size.py          # 数据量评估工具
│   └── DATA_RETENTION_README.md    # 本文件
├── 数据保留策略建议.md              # 完整的策略建议文档
├── 数据保留策略快速开始.md          # 快速入门指南
└── run_retention.bat               # Windows定时任务脚本
```

---

## 🎯 核心功能

### 1. 数据分层管理
- **热数据（1个月）**：实时查询，高性能
- **温数据（1-6个月）**：历史分析
- **冷数据（>6个月）**：归档存储

### 2. 自动化流程
- 定期归档旧数据
- 自动清理已归档数据
- 生成维护报告

### 3. 安全保护
- 归档前验证
- 分批删除
- 演练模式测试

---

## 🚀 快速使用

### 第一步：评估现状
```bash
python scripts/check_data_size.py
```

### 第二步：配置策略
编辑 `scripts/data_retention_config.py`：
```python
HOT_DATA_DAYS = 30       # 保留30天热数据
WARM_DATA_DAYS = 180     # 保留180天温数据
ENABLE_ARCHIVE = True    # 启用归档
CLEANUP_ENABLED = True   # 启用清理
```

### 第三步：初始化
```bash
python scripts/retention_manager.py --mode init
```

### 第四步：测试运行
```bash
python scripts/retention_manager.py --mode daily --dry-run
```

### 第五步：实际执行
```bash
python scripts/retention_manager.py --mode daily
```

---

## 📚 详细文档

请查看以下文档了解更多信息：

1. **数据保留策略建议.md** - 完整的策略分析和建议
2. **数据保留策略快速开始.md** - 详细的使用指南
3. 每个脚本的 `--help` 参数

---

## 🔧 工具说明

### data_retention_config.py
**配置管理模块**

包含所有策略配置：
- 保留天数
- 归档路径
- 清理参数
- 僵尸网络类型列表

### data_archiver.py
**数据归档工具**

功能：
- 按月归档通信记录
- 生成Parquet/JSON压缩文件
- 验证归档完整性
- 生成归档元数据

使用示例：
```bash
# 自动归档上个月数据
python scripts/data_archiver.py --mode auto

# 归档指定月份
python scripts/data_archiver.py --mode month --year 2024 --month 1

# 批量归档
python scripts/data_archiver.py --mode range \
    --start-year 2024 --start-month 1 \
    --end-year 2024 --end-month 6
```

### data_cleaner.py
**数据清理工具**

功能：
- 分批删除旧数据
- 标记已归档数据
- 添加archived字段
- 演练模式测试

使用示例：
```bash
# 自动清理（使用配置的天数）
python scripts/data_cleaner.py --mode auto

# 自定义清理
python scripts/data_cleaner.py --mode custom --botnet-type mozi --days 60

# 演练模式
python scripts/data_cleaner.py --mode auto --dry-run

# 添加archived字段
python scripts/data_cleaner.py --mode add-column
```

### retention_manager.py
**保留策略管理器（推荐使用）**

整合归档和清理功能，提供统一入口。

功能：
- 每日维护任务（归档 + 清理）
- 初始化表结构
- 手动归档/清理

使用示例：
```bash
# 每日维护任务
python scripts/retention_manager.py --mode daily

# 演练模式
python scripts/retention_manager.py --mode daily --dry-run

# 初始化表结构
python scripts/retention_manager.py --mode init

# 手动归档指定月份
python scripts/retention_manager.py --mode archive --year 2024 --month 1

# 手动清理
python scripts/retention_manager.py --mode cleanup --days 60
```

### check_data_size.py
**数据量评估工具**

功能：
- 查看各表大小
- 分析时间分布
- 统计可清理数据

使用示例：
```bash
python scripts/check_data_size.py
```

---

## 📅 推荐定时任务配置

### Windows
```powershell
# 创建计划任务（每天凌晨2点）
schtasks /create /tn "BotnetDataRetention" /tr "D:\workspace\botnet\backend\run_retention.bat" /sc daily /st 02:00 /ru SYSTEM
```

### Linux
```bash
# 编辑crontab
crontab -e

# 添加定时任务（每天凌晨2点）
0 2 * * * cd /path/to/botnet/backend && python scripts/retention_manager.py --mode daily >> /var/log/botnet/retention.log 2>&1
```

---

## 🛡️ 安全建议

### 1. 备份优先
在首次运行清理前，务必备份数据库：
```bash
mysqldump -u root -p botnet > botnet_backup_$(date +%Y%m%d).sql
```

### 2. 使用演练模式
首次运行前，使用 `--dry-run` 查看影响：
```bash
python scripts/retention_manager.py --mode daily --dry-run
```

### 3. 启用归档
确保 `ENABLE_ARCHIVE=True`，删除前先归档

### 4. 监控日志
定期检查日志文件：
```bash
tail -f /var/log/botnet/retention_manager.log
```

---

## 📊 性能参考

### 数据量与处理时间

| 数据量 | 归档时间 | 清理时间 | 建议批次大小 |
|--------|---------|---------|-------------|
| 100万  | 2-5分钟 | 5-10分钟 | 10,000 |
| 500万  | 10-20分钟 | 20-40分钟 | 20,000 |
| 1000万 | 20-40分钟 | 40-80分钟 | 50,000 |

### 存储节省

| 保留策略 | 数据量（6个月） | 存储空间 |
|---------|---------------|---------|
| 全保留  | ~4500万条 | ~25GB |
| 保留1个月 | ~150万条 | ~4GB |
| 保留3个月 | ~1350万条 | ~12GB |

---

## ❓ 常见问题

### Q1: 如何暂停自动清理？
```python
# 编辑 data_retention_config.py
CLEANUP_ENABLED = False  # 禁用清理，仅归档
```

### Q2: 如何恢复归档数据？
```python
import pandas as pd
from sqlalchemy import create_engine

# 读取归档文件
df = pd.read_parquet('/archive/mozi_communications_202401.parquet')

# 导入数据库
engine = create_engine('mysql+pymysql://user:pass@localhost/botnet')
df.to_sql('botnet_communications_mozi', engine, if_exists='append', index=False)
```

### Q3: 如何调整清理速度？
```python
# 编辑 data_retention_config.py

# 加快清理（高性能服务器）
CLEANUP_BATCH_SIZE = 50000  # 增大批次
CLEANUP_DELAY_SECONDS = 0   # 取消延迟

# 减慢清理（低性能服务器）
CLEANUP_BATCH_SIZE = 5000   # 减小批次
CLEANUP_DELAY_SECONDS = 3   # 增加延迟
```

### Q4: 归档文件存在哪里？
默认路径：`/data/archive/botnet/YYYY/MM/`

目录结构：
```
/data/archive/botnet/
├── 2024/
│   ├── 01/
│   │   ├── mozi_communications_202401.parquet
│   │   ├── mozi_communications_202401.parquet.meta.json
│   │   ├── asruex_communications_202401.parquet
│   │   └── ...
│   ├── 02/
│   └── ...
```

---

## 📞 技术支持

遇到问题时：
1. 查看日志：`/var/log/botnet/*.log`
2. 使用演练模式测试
3. 检查配置文件
4. 查阅详细文档

---

## ✅ 版本历史

### v1.0 (2024-01-20)
- 初始版本
- 支持数据归档（Parquet/JSON/CSV）
- 支持分批清理
- 演练模式
- 完整性验证
- 自动化定时任务

---

**祝您使用顺利！**

如有疑问，请查看 `数据保留策略建议.md` 和 `数据保留策略快速开始.md` 获取更多帮助。
