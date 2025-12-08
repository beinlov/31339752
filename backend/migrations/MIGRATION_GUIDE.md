# 📚 数据库迁移管理指南

## 🎯 为什么需要数据库迁移？

在协同开发中，多个开发者可能会：
- ✅ 添加新表
- ✅ 修改表结构
- ✅ 更新数据
- ✅ 创建索引

数据库无法直接通过 Git 上传，因此需要**版本化的迁移脚本**来管理数据库变更。

---

## 🚀 快速开始

### 1. 新项目初始化

```bash
# 方法一：使用完整初始结构
cd backend/migrations
mysql -u root -p botnet < schema/init.sql

# 方法二：使用迁移系统（推荐）
python migrations/run_migrations.py
```

### 2. 查看迁移状态

```bash
cd backend
python migrations/run_migrations.py
```

输出示例：
```
============================================================
数据库迁移状态
============================================================

已执行的迁移 (1 个):
  ✓ 001_initial_setup
    描述: 初始化数据库基础结构和配置
    时间: 2024-12-08 14:30:00 (耗时: 123ms)

待执行的迁移 (2 个):
  ○ 002_add_user_permissions.sql
  ○ 003_optimize_indexes.sql
```

### 3. 执行待执行的迁移

```bash
python migrations/run_migrations.py
# 会提示确认后自动执行所有待执行的迁移
```

---

## 👨‍💻 开发者工作流程

### 场景1: 你需要修改数据库结构

#### 步骤1: 创建迁移文件

```bash
cd backend/migrations/versions

# 查看当前最新编号
ls -la
# 假设最新是 003_xxx.sql

# 创建新迁移（编号 004）
touch 004_add_statistics_table.sql
```

#### 步骤2: 编写迁移脚本

```sql
-- ============================================================
-- Migration: 004_add_statistics_table
-- Description: 添加统计分析所需的聚合表
-- Author: 张三
-- Date: 2024-12-08
-- ============================================================

SELECT '开始执行迁移 004...' as status;

-- 创建统计表
CREATE TABLE IF NOT EXISTS botnet_statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    botnet_type VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    total_nodes INT DEFAULT 0,
    active_nodes INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_type_date (botnet_type, date),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='僵尸网络统计表';

SELECT '迁移 004 执行完成！' as status;

-- 回滚脚本
-- DROP TABLE IF EXISTS botnet_statistics;
```

#### 步骤3: 本地测试

```bash
# 测试迁移
cd backend
python migrations/run_migrations.py

# 验证表是否创建成功
mysql -u root -p -e "SHOW TABLES LIKE 'botnet_statistics';" botnet
```

#### 步骤4: 提交到 Git

```bash
git add backend/migrations/versions/004_add_statistics_table.sql
git commit -m "feat: add statistics table for data aggregation"
git push origin main
```

---

### 场景2: 同步其他人的数据库变更

#### 步骤1: 拉取最新代码

```bash
git pull origin main
```

#### 步骤2: 检查迁移状态

```bash
cd backend
python migrations/run_migrations.py
```

你会看到：
```
待执行的迁移 (2 个):
  ○ 004_add_statistics_table.sql
  ○ 005_update_node_indexes.sql
```

#### 步骤3: 执行迁移

```bash
python migrations/run_migrations.py
# 输入 yes 确认执行
```

完成！你的本地数据库已同步到最新状态。

---

### 场景3: 多人同时开发冲突

**问题**：
- 开发者A创建了 `004_feature_a.sql`
- 开发者B也创建了 `004_feature_b.sql`

**解决方法**：

```bash
# 开发者B发现冲突（后提交的人）
git pull  # 发现有冲突

# 重命名自己的迁移文件
cd backend/migrations/versions
mv 004_feature_b.sql 005_feature_b.sql

# 更新文件内容中的版本号
# Migration: 004_feature_b -> 005_feature_b

# 重新提交
git add 005_feature_b.sql
git commit -m "fix: rename migration to avoid conflict"
git push
```

---

## 📋 迁移文件模板

创建新迁移时使用此模板：

```sql
-- ============================================================
-- Migration: {编号}_{简短描述}
-- Description: {详细说明这个迁移做了什么}
-- Author: {你的名字}
-- Date: {日期}
-- ============================================================

-- 迁移前信息
SELECT '开始执行迁移 {编号}...' as status;

-- ============================================================
-- 主要变更
-- ============================================================

-- 在这里写你的 SQL 语句
CREATE TABLE IF NOT EXISTS your_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- 字段定义...
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表说明';

-- ============================================================
-- 验证
-- ============================================================

SELECT COUNT(*) as verification 
FROM information_schema.tables 
WHERE table_schema = DATABASE() AND table_name = 'your_table';

SELECT '迁移 {编号} 执行完成！' as status;

-- ============================================================
-- 回滚脚本（注释形式保存）
-- ============================================================
-- DROP TABLE IF EXISTS your_table;
```

---

## ⚠️ 重要注意事项

### ✅ 推荐做法

1. **每个功能一个迁移文件**
   - ❌ 不要在一个迁移中做太多事情
   - ✅ 每个迁移专注于一个功能

2. **使用 `IF NOT EXISTS`**
   ```sql
   CREATE TABLE IF NOT EXISTS xxx (...)
   ```
   - 避免重复执行时出错

3. **先本地测试，再提交**
   ```bash
   # 测试迁移
   python migrations/run_migrations.py
   
   # 验证数据
   mysql -u root -p botnet -e "SELECT * FROM schema_migrations"
   ```

4. **编写详细注释**
   - 说明为什么需要这个变更
   - 记录回滚方法

5. **包含验证查询**
   ```sql
   -- 验证表是否创建成功
   SELECT COUNT(*) FROM information_schema.tables 
   WHERE table_name = 'xxx';
   ```

### ❌ 避免做法

1. **不要修改已提交的迁移**
   - ❌ 已经执行的迁移不能修改
   - ✅ 如需更改，创建新的迁移文件

2. **不要使用 `DROP TABLE`（除非确定要删除）**
   ```sql
   -- ❌ 危险
   DROP TABLE important_data;
   
   -- ✅ 安全
   -- DROP TABLE IF EXISTS temporary_table;  -- 注释形式
   ```

3. **不要在迁移中包含大量业务数据**
   - ❌ INSERT 10000 行数据
   - ✅ 结构变更为主，数据变更要谨慎

4. **不要跳过版本号**
   ```bash
   # ❌ 错误
   001_xxx.sql
   002_xxx.sql
   005_xxx.sql  # 跳过了 003 和 004
   
   # ✅ 正确
   001_xxx.sql
   002_xxx.sql
   003_xxx.sql
   004_xxx.sql
   ```

---

## 🔧 常见问题

### Q1: 迁移执行失败怎么办？

**A**: 检查错误信息，手动回滚

```bash
# 1. 查看错误日志
python migrations/run_migrations.py

# 2. 连接数据库检查
mysql -u root -p botnet

# 3. 查看迁移记录
SELECT * FROM schema_migrations ORDER BY id DESC LIMIT 5;

# 4. 如果需要回滚，找到迁移文件中的回滚脚本
# 执行回滚 SQL

# 5. 删除迁移记录
DELETE FROM schema_migrations WHERE version = '问题版本号';

# 6. 修复迁移文件后重新执行
python migrations/run_migrations.py
```

### Q2: 如何查看当前数据库版本？

```sql
SELECT version, executed_at 
FROM schema_migrations 
ORDER BY id DESC 
LIMIT 1;
```

### Q3: 生产环境如何执行迁移？

```bash
# 1. 备份数据库
mysqldump -u root -p botnet > backup_$(date +%Y%m%d).sql

# 2. 测试迁移（在测试环境）
python migrations/run_migrations.py

# 3. 验证无误后，在生产环境执行
python migrations/run_migrations.py
```

### Q4: Docker 环境如何初始化数据库？

```bash
# 方法一：使用 init.sql（首次部署）
# docker-compose.yml 已配置自动执行

# 方法二：使用迁移系统（推荐）
docker-compose exec backend python migrations/run_migrations.py
```

---

## 📚 相关文档

- [迁移文件详细说明](backend/migrations/README.md)
- [数据库配置](backend/config.py)
- [Docker 部署指南](DOCKER_DEPLOYMENT.md)
- [项目结构说明](backend/项目结构说明.md)

---

## 🎯 总结

使用迁移系统的好处：

| 传统方式 | 迁移系统 |
|---------|---------|
| ❌ 手动执行 SQL | ✅ 自动化执行 |
| ❌ 难以追踪变更 | ✅ 版本化管理 |
| ❌ 团队同步困难 | ✅ Git 即可同步 |
| ❌ 容易遗漏更新 | ✅ 系统检测待执行 |
| ❌ 回滚困难 | ✅ 记录回滚脚本 |

**记住**：数据库结构即代码（Database as Code），用版本控制管理！
