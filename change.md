2025.12.15 应用日志文件统一
1. **日志文件位置统一**
   - 所有应用日志文件现统一存放在 `backend/logs/` 目录
   - 原分散在多处的日志文件已迁移
2. **统一的日志文件**
   - `log_processor.log` - 日志处理器运行日志
   - `stats_aggregator.log` - 统计聚合器运行日志
   - `remote_uploader.log` - 远程上传器运行日志
   - `main_app.log` - 主应用日志（预留）
3. **配置统一**
   - 在 `backend/config.py` 中添加日志文件路径配置
   - 同步更新 `backend/config_docker.py`
   - `remote_uploader.py` 支持通过配置文件设置日志路径
4. **文件变更**
   - 修改 `log_processor/main.py` - 使用统一日志路径
   - 修改 `stats_aggregator/aggregator.py` - 使用统一日志路径
   - 修改 `remote/remote_uploader.py` - 支持配置日志路径
5. **新增文档和工具**
   - `backend/logs/LOG_FILES_README.md` - 日志文件说明文档
   - `backend/logs/clean_logs.bat` - Windows日志清理脚本
   - `backend/logs/clean_logs.sh` - Linux/Mac日志清理脚本
   - `backend/remote/config.json.local` - 本地部署配置示例
6. **优势**
   - 便于查找和管理所有日志文件
   - 统一的日志备份和清理
   - 支持统一的日志轮转配置

2025.12.15 系统配置统一（第二阶段：聚合器配置）
1. **聚合器配置统一**
   - 将 `backend/stats_aggregator/config.yaml` 的配置合并到 `backend/config.py`
   - 移除 `aggregator.py` 和 `incremental_aggregator.py` 中硬编码的 `BOTNET_TYPES`
   - 现在从统一的 `BOTNET_CONFIG` 动态获取僵尸网络类型
2. **智能配置管理**
   - 只需在 `BOTNET_CONFIG` 中设置 `enabled: False/True` 即可控制：
     * 日志处理（log_processor）
     * 数据聚合（stats_aggregator）
   - 不需要在多个文件中分别修改
3. **文件变更**
   - 弃用 `backend/stats_aggregator/config.yaml`（已重命名为 config.yaml.deprecated）
   - 修改 `aggregator.py` 和 `incremental_aggregator.py` 使用统一配置
   - 同步更新 `backend/config_docker.py`
4. **新增文档和测试**
   - `backend/stats_aggregator/CONFIG_MIGRATION_NOTICE.md` - 聚合器配置迁移说明
   - `backend/test_aggregator_config.py` - 聚合器配置测试脚本
   - 更新 `CONFIG_GUIDE.md` 和 `QUICK_CONFIG_REFERENCE.md`
5. **优势**
   - 统一控制点：修改一处即可同时影响日志处理和聚合
   - 配置一致性：避免不同模块配置不同步的问题
   - 更易维护：减少配置文件数量

2025.12.15 系统配置统一（第一阶段：日志处理器）
1. **重大改进：统一配置文件**
   - 将 `backend/log_processor/config.py` 的所有配置合并到 `backend/config.py`
   - 现在部署到新服务器时，只需修改一个配置文件即可
   - 同步更新了 `backend/config_docker.py`，支持环境变量配置
2. **文件变更**
   - 弃用 `backend/log_processor/config.py`（已重命名为 config.py.deprecated）
   - 修改 `backend/log_processor/main.py` 的导入语句
   - 更新 `README.md` 配置说明
3. **新增文档**
   - `CONFIG_GUIDE.md` - 详细的配置使用指南
   - `backend/CONFIG_UNIFICATION_SUMMARY.md` - 配置统一变更总结
   - `backend/log_processor/CONFIG_MIGRATION_NOTICE.md` - 迁移通知
   - `backend/test_config.py` - 配置测试脚本
4. **优势**
   - 简化部署流程
   - 避免配置不一致
   - 便于维护和管理
   - 完全向后兼容
