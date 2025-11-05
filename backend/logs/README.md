# 僵尸网络日志目录

此目录用于接收各个僵尸网络传输过来的日志文件。

## 目录结构

```
logs/
├── asruex/          # Asruex僵尸网络日志
├── mozi/            # Mozi僵尸网络日志
├── andromeda/       # Andromeda僵尸网络日志
├── moobot/          # Moobot僵尸网络日志
├── ramnit/          # Ramnit僵尸网络日志
└── leethozer/       # Leethozer僵尸网络日志
```

## 日志格式规范

所有僵尸网络的日志文件应遵循统一的CSV格式：

```
timestamp,ip,event_type,extra_field1,extra_field2,...
```

### 字段说明

- **timestamp**: 时间戳（格式：YYYY-MM-DD HH:MM:SS）
- **ip**: IP地址（必需）
- **event_type**: 事件类型（必需，如：access、infection、beacon等）
- **extra_fields**: 可选的额外字段

### 示例

#### Asruex日志示例
```
2025-10-29 10:29:44,192.168.91.7,access,/content/faq.php?ql=b2
2025-10-29 10:32:01,192.168.91.7,clean1,6.1-x64,192.168.91.7
2025-10-29 10:31:55,192.168.91.7,qla0,S-1-8-68-140046984-1962685791-458280869-243
```

#### Mozi日志示例
```
2025-10-29 14:22:11,45.33.12.88,infection,bot_version_v1.2
2025-10-29 14:23:05,45.33.12.88,command,ddos_target
2025-10-29 14:25:30,45.33.12.88,beacon
```

#### Andromeda日志示例
```
2025-10-29 15:10:33,203.0.113.45,beacon
2025-10-29 15:11:12,203.0.113.45,download,payload.exe
2025-10-29 15:12:45,203.0.113.45,c2,command_received
```

## 日志文件命名

建议使用日期命名格式：`YYYY-MM-DD.txt`

例如：
- `2025-10-29.txt`
- `2025-10-30.txt`

## 日志传输方式

可以通过以下方式将远端日志传输到本地：

1. **SFTP/SCP**: 定期同步远端日志文件
2. **rsync**: 增量同步日志
3. **HTTP API**: 通过API上传日志
4. **日志收集工具**: 如Filebeat、Fluentd等

## 自动处理

日志处理程序会：
1. 实时监控各僵尸网络日志目录
2. 自动解析新增的日志行
3. 查询IP地理位置、ISP、ASN等信息
4. 批量写入数据库

## 注意事项

- 确保日志文件编码为UTF-8
- 日志文件应可追加写入
- 避免频繁创建新文件，建议每天一个文件
- 大文件会被自动分批处理


