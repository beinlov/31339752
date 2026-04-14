# Backend Scripts 目录说明

**最后更新**: 2026-03-20 10:25

本目录包含平台运维所需的必需脚本和工具脚本，共 22 个 Python 脚本 + 1 个 Shell 脚本。

---

## 📂 目录分类

### 🔴 [必需 - 运行时] - 1个文件

这个脚本被平台服务启动脚本调用，**删除会导致平台无法正常启动**。

| 文件 | 用途 | 调用位置 |
|------|------|---------|
| `ensure_timeset_data.py` | 确保 timeset 数据完整性（每天运行） | `start_all_services.sh` |

---

### 🟢 [工具脚本] - 21个文件

这些脚本用于日常运维、数据处理、监控等。

#### 数据生成与处理（4个）
| 文件 | 用途 |
|------|------|
| `generate_timeset_from_communications.py` | 从通信记录生成历史 timeset 数据（支持所有僵尸网络） |
| `generate_30days_data.py` | 生成30天测试数据 |
| `add_historical_data.py` | 添加历史数据 |
| `manual_record_today.py` | 手动记录今日数据 |

#### 数据清理与归档（6个）
| 文件 | 用途 |
|------|------|
| `cleanup_old_data.py` | 清理旧数据（默认保留180天） |
| `cleanup_old_data.sh` | Shell包装脚本，用于crontab定时任务 |
| `data_archiver.py` | 数据归档功能 |
| `data_cleaner.py` | 数据清理核心模块 |
| `data_retention_config.py` | 数据保留策略配置 |
| `retention_manager.py` | 统一的数据保留管理器（整合清理+归档） |

#### 聚合与统计（4个）
| 文件 | 用途 |
|------|------|
| `rebuild_aggregation.py` | 重建聚合统计表（数据修复时使用） |
| `start_takeover_stats_aggregator.py` | 启动接管节点统计聚合服务 |
| `daily_node_counter.py` | 每日节点计数器 |
| `daily_node_counter_simple.py` | 简化版每日节点计数器 |

#### 数据库工具（4个）
| 文件 | 用途 |
|------|------|
| `add_aggregation_indexes.py` | 为聚合器添加优化索引 |
| `create_timeset_tables.py` | 创建 timeset 表 |
| `update_timeset_schema.py` | 更新 timeset 表结构 |
| `backup_and_import_db.py` | 数据库备份和导入工具 |

#### 监控与检查（3个）
| 文件 | 用途 |
|------|------|
| `monitor_c2_connection.py` | 监控 C2 服务器连接健康状态 |
| `check_backend_status.py` | 检查后端服务状态 |
| `data_num.py` | 数据统计工具 |

#### 其他工具（1个）
| 文件 | 用途 |
|------|------|
| `reset_pull_state.py` | 重置远程拉取器状态 |

---

## 📊 统计汇总

| 类别 | 数量 | 说明 |
|------|------|------|
| **必需运行时** | 1 | 删除会导致平台无法启动 |
| **工具脚本** | 21 | 日常运维和数据处理 |
| **Shell 脚本** | 1 | cleanup_old_data.sh |
| **总计** | 23 | - |

---

## 💡 使用建议

### 常用脚本

1. **生成历史 timeset 数据**：
   ```bash
   cd /home/spider/31339752/backend/scripts
   python3 generate_timeset_from_communications.py 30
   ```

2. **清理旧数据**：
   ```bash
   python3 cleanup_old_data.py --days 180
   # 或使用 shell 脚本
   ./cleanup_old_data.sh
   ```

3. **重建聚合统计**：
   ```bash
   python3 rebuild_aggregation.py
   ```

4. **监控 C2 连接**：
   ```bash
   python3 monitor_c2_connection.py
   ```

5. **数据保留管理**：
   ```bash
   python3 retention_manager.py --mode daily --dry-run
   ```

---

## ⚠️ 注意事项

1. **ensure_timeset_data.py** 被 `start_all_services.sh` 调用，**绝对不能删除**
2. 所有脚本都需要在 backend 目录下运行，或正确设置 Python 路径
3. 数据库操作脚本执行前建议先备份数据
4. 清理和归档操作建议先使用 `--dry-run` 参数测试

---

## 🗑️ 已清理的文件

以下类型的文件已从本目录清除：
- ✅ 测试文件（27个）
- ✅ 验证工具（11个）
- ✅ 数据库维护脚本（13个）
- ✅ 示例代码（1个）
- ✅ Windows 专用文件（3个）

**总计清理**: 55 个文件

---

## 🔗 相关文档

- [平台服务启动脚本](../../start_all_services.sh) - 查看哪些脚本被调用
- [清理总结](../../CLEANUP_SUMMARY.md) - 详细的清理记录
