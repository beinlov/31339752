# C2端多日志源功能说明

## 概述

C2数据服务器现在支持同时从多个日志源读取数据，包括：
- **文件日志源**：支持文本日志文件（如 user_activity.log）
- **数据库日志源**：支持SQLite数据库（如 reports.db）

每条数据都会标记 `log_type` 字段，用于区分数据类型（如"online"上线日志、"cleanup"清除日志）。

## 功能特性

### 1. 多日志源支持
- ✅ 同时读取多个日志源
- ✅ 支持文件和数据库两种存储类型
- ✅ 每个日志源独立配置路径、格式、字段映射
- ✅ 自动标记数据类型（log_type字段）

### 2. 配置化读取
- ✅ 通过 config.json 配置所有日志源
- ✅ 支持自定义正则表达式解析文本日志
- ✅ 支持自定义SQL查询读取数据库
- ✅ 支持自定义字段映射（IP字段、时间字段）

### 3. 兼容性
- ✅ 完全向后兼容旧配置（单日志源模式）
- ✅ 自动识别配置类型并切换模式
- ✅ 保留原有的所有功能（背压控制、断点续传等）

## 配置说明

### config.json 配置示例

```json
{
  "log_sources": {
    "online": {
      "enabled": true,
      "log_type": "online",
      "storage_type": "file",
      "path": "./user_activity.log",
      "format": "line",
      "field_mapping": {
        "ip_field": "ip",
        "timestamp_field": "timestamp",
        "line_parser": {
          "type": "regex",
          "pattern": "\\[(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2})\\].*?([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3})",
          "timestamp_group": 1,
          "ip_group": 2,
          "timestamp_format": "%Y-%m-%d %H:%M:%S"
        }
      }
    },
    "cleanup": {
      "enabled": true,
      "log_type": "cleanup",
      "storage_type": "database",
      "path": "./reports.db",
      "db_config": {
        "type": "sqlite",
        "table": "reports",
        "query": "SELECT client_ip, timestamp FROM reports WHERE id > ? ORDER BY id ASC LIMIT ?",
        "position_field": "id"
      },
      "field_mapping": {
        "ip_field": "client_ip",
        "timestamp_field": "timestamp",
        "timestamp_format": "%Y-%m-%dT%H:%M:%S"
      }
    }
  }
}
```

### 配置项详解

#### 文件日志源 (storage_type: "file")

| 字段 | 说明 | 示例 |
|------|------|------|
| `enabled` | 是否启用此日志源 | `true` / `false` |
| `log_type` | 日志类型标识 | `"online"` / `"cleanup"` |
| `storage_type` | 存储类型 | `"file"` |
| `path` | 文件路径（绝对或相对） | `"./user_activity.log"` |
| `format` | 日志格式 | `"line"` (逐行) / `"json"` |
| `field_mapping.line_parser.type` | 解析器类型 | `"regex"` |
| `field_mapping.line_parser.pattern` | 正则表达式模式 | 见示例 |
| `field_mapping.line_parser.timestamp_group` | 时间戳捕获组编号 | `1` |
| `field_mapping.line_parser.ip_group` | IP地址捕获组编号 | `2` |
| `field_mapping.line_parser.timestamp_format` | 时间戳格式 | `"%Y-%m-%d %H:%M:%S"` |

#### 数据库日志源 (storage_type: "database")

| 字段 | 说明 | 示例 |
|------|------|------|
| `enabled` | 是否启用此日志源 | `true` / `false` |
| `log_type` | 日志类型标识 | `"cleanup"` |
| `storage_type` | 存储类型 | `"database"` |
| `path` | 数据库文件路径 | `"./reports.db"` |
| `db_config.type` | 数据库类型 | `"sqlite"` |
| `db_config.table` | 表名 | `"reports"` |
| `db_config.query` | SQL查询语句 | 见示例 |
| `db_config.position_field` | 位置字段（用于断点续传） | `"id"` |
| `field_mapping.ip_field` | IP字段名 | `"client_ip"` |
| `field_mapping.timestamp_field` | 时间戳字段名 | `"timestamp"` |
| `field_mapping.timestamp_format` | 时间戳格式 | `"%Y-%m-%dT%H:%M:%S"` |

## API 接口

### 拉取数据

**请求：**
```bash
GET /api/pull?limit=1000
Authorization: Bearer YOUR_API_KEY
```

**响应：**
```json
{
  "success": true,
  "count": 2,
  "data": [
    {
      "ip": "14.19.132.125",
      "timestamp": "2026-03-03T16:38:34",
      "date": "2026-03-03",
      "log_hour": "2026-03-03_16",
      "botnet_type": "test",
      "log_type": "cleanup",  // ← 新增字段：标识日志类型
      "seq_id": 1
    },
    {
      "ip": "192.168.1.100",
      "timestamp": "2026-03-03T16:36:49",
      "date": "2026-03-03",
      "log_hour": "2026-03-03_16",
      "botnet_type": "test",
      "log_type": "online",    // ← 新增字段：标识日志类型
      "seq_id": 2
    }
  ]
}
```

**关键字段说明：**
- `log_type`: 数据类型标识，可用于区分上线日志和清除日志
- 其他字段保持不变，完全向后兼容

## 使用场景

### 场景1：同时处理上线和清除日志

```json
{
  "log_sources": {
    "online": {
      "enabled": true,
      "log_type": "online",
      "storage_type": "file",
      "path": "./user_activity.log"
    },
    "cleanup": {
      "enabled": true,
      "log_type": "cleanup",
      "storage_type": "database",
      "path": "./reports.db"
    }
  }
}
```

### 场景2：只处理上线日志（兼容旧模式）

```json
{
  "log_sources": {
    "online": {
      "enabled": true,
      "log_type": "online",
      "storage_type": "file",
      "path": "./user_activity.log"
    },
    "cleanup": {
      "enabled": false
    }
  }
}
```

### 场景3：适配新的日志格式

只需修改配置即可：

```json
{
  "log_sources": {
    "new_source": {
      "enabled": true,
      "log_type": "custom_type",
      "storage_type": "file",
      "path": "./new_format.log",
      "field_mapping": {
        "line_parser": {
          "pattern": "YOUR_CUSTOM_REGEX",
          "timestamp_group": 1,
          "ip_group": 2
        }
      }
    }
  }
}
```

## 测试验证

### 1. 检查配置
```bash
python test_multi_source.py
```

### 2. 启动服务器
```bash
python c2_data_server.py
```

### 3. 验证数据
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8888/api/pull?limit=10
```

检查返回数据中是否包含 `log_type` 字段。

## 核心代码说明

### 1. DatabaseReader 类
负责从SQLite数据库读取日志：
- 支持自定义SQL查询
- 支持断点续传（基于position_field）
- 自动字段映射

### 2. LogReader 类增强
新增配置化解析功能：
- 支持正则表达式配置
- `parse_line()` 方法：解析单行日志
- 灵活的字段提取

### 3. BackgroundLogReader 类改造
- 支持多日志源初始化
- `read_logs_multi_source()` 方法：并行读取多个日志源
- 自动标记 `log_type` 字段
- 保持向后兼容（兼容模式）

## 注意事项

1. **配置文件编码**：config.json 必须使用 UTF-8 编码
2. **路径格式**：Windows系统建议使用相对路径或正斜杠（`./path` 或 `/path`）
3. **正则表达式**：在JSON中需要转义反斜杠（`\\d` 而不是 `\d`）
4. **数据库查询**：SQL语句中使用 `?` 作为占位符
5. **向后兼容**：如果未配置 `log_sources`，自动使用旧的单日志源模式

## 扩展性

系统设计为高度可扩展：

1. **添加新的日志类型**：只需在 config.json 中添加新的日志源配置
2. **支持新的存储类型**：可以扩展 DatabaseReader 支持 MySQL、PostgreSQL等
3. **支持新的日志格式**：可以添加新的解析器类型（如JSON、XML等）
4. **自定义字段**：可以在 field_mapping 中添加更多字段映射

## 故障排查

### 问题1：服务器使用兼容模式而不是多日志源模式
**原因**：config.json 加载失败或 log_sources 配置为空
**解决**：
1. 检查 config.json 语法是否正确
2. 确认文件编码为 UTF-8
3. 运行 `python debug_config.py` 检查配置加载

### 问题2：数据库读取失败
**原因**：数据库路径错误或表结构不匹配
**解决**：
1. 确认数据库文件存在
2. 检查表名和字段名是否正确
3. 查看日志中的错误信息

### 问题3：文件日志解析失败
**原因**：正则表达式不匹配
**解决**：
1. 使用在线正则测试工具验证表达式
2. 注意JSON中需要双重转义（`\\d`）
3. 检查捕获组编号是否正确

## 总结

多日志源功能为C2数据服务器提供了强大的灵活性：

✅ **易于配置**：纯配置文件，无需修改代码
✅ **高度灵活**：支持文件和数据库，可扩展到其他存储类型  
✅ **完全兼容**：不影响现有功能，平滑升级
✅ **类型标记**：自动标记 log_type，便于平台端区分处理

这为后续接收不同格式、不同类型的日志数据提供了完善的基础架构。
