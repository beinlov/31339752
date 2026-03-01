# 🔍 数据库问题诊断和解决方案

## 📋 问题诊断结果

### ✅ 发现的问题

1. **数据库表存在但无数据**
   - 表结构已创建（24个表）
   - 但所有表的数据为空（0行）
   - 原因：botnet.sql（686MB）导入未完成

2. **后端API查询错误**
   - 错误信息: `Unknown column 'table_name' in 'field list'`
   - 错误信息: `Unknown column 'event_time' in 'field list'`
   - 原因：缺少数据或字段不匹配

3. **前端显示无数据**
   - 原因：后端API查询失败返回空数据

---

## 🔧 正在执行的解决方案

### 当前操作

```bash
# 1. 已删除旧数据库并重新创建
DROP DATABASE botnet;
CREATE DATABASE botnet CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 2. 正在导入完整的botnet.sql（686MB）
sudo docker exec -i mysql mysql -uroot -pMatrix123 botnet < botnet.sql
```

### 导入进度

- **文件大小**: 686 MB
- **预计时间**: 3-5分钟（取决于服务器性能）
- **当前状态**: 🔄 导入进行中...
- **已创建表**: 5个（持续增加中）

---

## 📊 导入完成后应有的表结构

### 核心业务表

1. **僵尸网络节点表**
   - `botnet_nodes_asruex`
   - `botnet_nodes_mozi`
   - `botnet_nodes_ramnit`
   - 等各个僵尸网络类型的节点表

2. **通信记录表**
   - `botnet_communications_asruex`
   - `botnet_communications_mozi`
   - `botnet_communications_ramnit`
   - 等各个僵尸网络类型的通信表

3. **全球统计表**
   - `global_botnet_asruex`
   - `global_botnet_mozi`
   - 等全球分布统计表

4. **时间序列表**
   - `botnet_timeset_asruex`
   - `botnet_timeset_mozi`
   - 等时间序列数据表

5. **系统管理表**
   - `users` - 用户表
   - `user_events` - 用户事件表
   - `Server_Management` - 服务器管理表
   - `domain_blacklist` - 域名黑名单
   - `ip_blacklist` - IP黑名单

---

## ✅ 导入完成后的验证步骤

### 1. 使用检查脚本

```bash
./check_database_status.sh
```

### 2. 手动验证关键表

```bash
# 检查节点数据
sudo docker exec mysql mysql -uroot -pMatrix123 -e "USE botnet; SELECT COUNT(*) FROM botnet_nodes_asruex;"

# 检查通信数据
sudo docker exec mysql mysql -uroot -pMatrix123 -e "USE botnet; SELECT COUNT(*) FROM botnet_communications_asruex;"

# 检查用户数据
sudo docker exec mysql mysql -uroot -pMatrix123 -e "USE botnet; SELECT COUNT(*) FROM users;"
```

### 3. 重启后端服务

```bash
# 停止当前服务
./stop_all_services.sh

# 等待数据库导入完成
# 然后重新启动
./start_all_services.sh
```

---

## 🚨 如果导入失败

### 方案A: 检查导入错误日志

```bash
# 查看导入日志
cat import_log.txt

# 查看MySQL错误日志
sudo docker logs mysql
```

### 方案B: 分批导入

如果完整导入失败，可以尝试：

```bash
# 1. 只导入表结构
grep -E "CREATE TABLE|DROP TABLE" botnet.sql > schema.sql
sudo docker exec -i mysql mysql -uroot -pMatrix123 botnet < schema.sql

# 2. 再导入数据
grep "INSERT INTO" botnet.sql > data.sql
sudo docker exec -i mysql mysql -uroot -pMatrix123 botnet < data.sql
```

### 方案C: 使用init.sql创建基础结构

```bash
# 如果botnet.sql无法完整导入，使用项目自带的init.sql
sudo docker exec -i mysql mysql -uroot -pMatrix123 botnet < init.sql

# 然后手动运行数据库迁移脚本
cd backend/migrations
python3 run_migrations.py
```

---

## 📈 监控导入进度

### 实时查看表数量

```bash
watch -n 5 'sudo docker exec mysql mysql -uroot -pMatrix123 -e "USE botnet; SHOW TABLES;" 2>/dev/null | wc -l'
```

### 查看数据库大小

```bash
sudo docker exec mysql mysql -uroot -pMatrix123 -e "
SELECT 
    table_schema AS 'Database',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables 
WHERE table_schema = 'botnet'
GROUP BY table_schema;
"
```

---

## ⏱️ 预计完成时间

- **开始时间**: [检查时间]
- **文件大小**: 686 MB
- **预计耗时**: 3-5分钟
- **当前进度**: 检查中...

---

## 🎯 完成后的操作

1. ✅ 验证数据库导入完成
2. ✅ 运行检查脚本确认数据
3. ✅ 重启所有后端服务
4. ✅ 访问前端验证数据显示
5. ✅ 检查API接口响应正常

---

## 📞 如需帮助

如果导入过程中遇到问题：

1. 查看导入日志: `cat import_log.txt`
2. 运行诊断脚本: `./check_database_status.sh`
3. 查看MySQL日志: `sudo docker logs mysql`

---

*正在进行数据库导入，请耐心等待...*
