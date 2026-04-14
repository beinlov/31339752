# 僵尸网络接管集成平台 - 文档中心

**最后更新**: 2026-03-20

欢迎来到僵尸网络接管集成平台的文档中心！所有项目文档已统一整理到此目录。

---

## 📚 文档目录

### 📡 API 接口文档 (api/)

| 文档 | 说明 |
|------|------|
| [INTEGRATION_API_GUIDE.md](api/INTEGRATION_API_GUIDE.md) | 大平台集成免登录接口使用指南 |
| [THIRD_PARTY_INTEGRATION_API_GUIDE.md](api/THIRD_PARTY_INTEGRATION_API_GUIDE.md) | 第三方平台集成 API 完整指南 |
| [TAKEOVER_STATS_API_GUIDE.md](api/TAKEOVER_STATS_API_GUIDE.md) | 接管节点统计 API 使用指南 |

### 🏗️ 架构设计文档 (architecture/)

| 文档 | 说明 |
|------|------|
| [WORKFLOW_ANALYSIS.md](architecture/WORKFLOW_ANALYSIS.md) | 系统工作流程分析 |
| [SOLUTION_SERIAL_PROCESSING.md](architecture/SOLUTION_SERIAL_PROCESSING.md) | 串行处理解决方案 |

### 🔧 模块文档 (modules/)

| 文档 | 说明 |
|------|------|
| **日志处理模块** | |
| [CLEANUP_LOG_PROCESSING.md](modules/CLEANUP_LOG_PROCESSING.md) | 清除日志处理说明 |
| [PROCESSING_ORDER.md](modules/PROCESSING_ORDER.md) | 日志处理顺序说明 |
| **C2 远程服务模块** | |
| [DEPLOYMENT_GUIDE.md](modules/DEPLOYMENT_GUIDE.md) | C2 服务部署指南 |
| [MULTI_SOURCE_README.md](modules/MULTI_SOURCE_README.md) | 多源数据处理说明 |
| [QUICK_REFERENCE.md](modules/QUICK_REFERENCE.md) | C2 服务快速参考 |
| [README_DEPLOY.md](modules/README_DEPLOY.md) | C2 部署说明 |
| **前端模块** | |
| [frontend-deployment.md](modules/frontend-deployment.md) | 前端部署文档 |

---

## 🚀 快速开始

### 1. 了解系统架构

建议按以下顺序阅读：

1. [WORKFLOW_ANALYSIS.md](architecture/WORKFLOW_ANALYSIS.md) - 了解整体工作流程
2. [SOLUTION_SERIAL_PROCESSING.md](architecture/SOLUTION_SERIAL_PROCESSING.md) - 理解串行处理机制

### 2. 集成接口开发

如果需要将平台集成到其他系统：

1. [INTEGRATION_API_GUIDE.md](api/INTEGRATION_API_GUIDE.md) - 免登录接口
2. [THIRD_PARTY_INTEGRATION_API_GUIDE.md](api/THIRD_PARTY_INTEGRATION_API_GUIDE.md) - 完整 API 参考
3. [TAKEOVER_STATS_API_GUIDE.md](api/TAKEOVER_STATS_API_GUIDE.md) - 统计数据接口

### 3. 部署和运维

部署相关文档：

1. [frontend-deployment.md](modules/frontend-deployment.md) - 前端部署
2. [DEPLOYMENT_GUIDE.md](modules/DEPLOYMENT_GUIDE.md) - C2 服务部署
3. [README_DEPLOY.md](modules/README_DEPLOY.md) - 详细部署说明

### 4. 模块开发

了解各个功能模块：

- **日志处理**: [CLEANUP_LOG_PROCESSING.md](modules/CLEANUP_LOG_PROCESSING.md), [PROCESSING_ORDER.md](modules/PROCESSING_ORDER.md)
- **C2 服务**: [MULTI_SOURCE_README.md](modules/MULTI_SOURCE_README.md), [QUICK_REFERENCE.md](modules/QUICK_REFERENCE.md)

---

## 📂 相关目录

- **代码**: `/backend` - 后端代码
- **前端**: `/fronted` - 前端代码
- **脚本**: `/backend/scripts` - 运维脚本（见 [backend/scripts/README.md](../backend/scripts/README.md)）
- **SQL**: `/sql` - 数据库脚本

---

## 💡 文档规范

### 文档组织原则

- **api/**: 所有 API 接口文档
- **architecture/**: 系统架构和设计文档
- **modules/**: 各功能模块的详细文档

### 新增文档

新增文档时，请遵循以下规范：

1. 确定文档类型（API/架构/模块）
2. 放入对应的子目录
3. 更新本 README.md 的文档列表
4. 使用清晰的文件命名

---

## 🔗 其他资源

- **项目主页**: `/README.md`（待创建）
- **代码优化分析**: `/CODE_STRUCTURE_OPTIMIZATION_ANALYSIS.md`
- **脚本说明**: `/backend/scripts/README.md`

---

**文档整理完成日期**: 2026-03-20  
**整理说明**: 从项目各处收集并统一整理到 docs/ 目录
