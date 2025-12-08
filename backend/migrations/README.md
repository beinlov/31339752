# 数据库迁移文件说明

## 📁 目录结构

```
migrations/
├── README.md           # 本文件
├── schema/            # 完整数据库结构
│   └── init.sql       # 初始数据库结构
└── versions/          # 增量迁移脚本
    ├── 001_create_base_tables.sql
    ├── 002_add_botnet_feature.sql
    ├── 003_fix_time_fields.sql
    └── ...
```

## 🔄 迁移文件命名规范

```
{序号}_{简短描述}.sql
```

示例：
- `001_create_base_tables.sql` - 创建基础表
- `002_add_user_permissions.sql` - 添加用户权限
- `003_fix_xinjiang_region.sql` - 修复新疆地区数据

## 📝 迁移文件格式

每个迁移文件应包含：

```sql
-- ============================================================
-- Migration: 002_add_botnet_feature
-- Description: 添加动态创建僵尸网络功能所需的表结构
-- Author: [开发者名称]
-- Date: 2024-12-08
-- ============================================================

-- 迁移前检查
SELECT 'Starting migration 002...' as status;

-- 执行迁移
CREATE TABLE IF NOT EXISTS botnet_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='僵尸网络类型表';

-- 验证
SELECT COUNT(*) as table_count 
FROM information_schema.tables 
WHERE table_schema = DATABASE() AND table_name = 'botnet_types';

-- 回滚脚本（注释形式保存）
-- DROP TABLE IF EXISTS botnet_types;

SELECT 'Migration 002 completed successfully!' as status;
```

## 🚀 使用流程

### 1. 开发者A创建迁移

```bash
# 1. 创建新的迁移文件
cd backend/migrations/versions
# 查看最新编号
ls -la

# 2. 创建新迁移（假设当前最新是 003）
touch 004_add_new_feature.sql

# 3. 编写 SQL 迁移脚本
# 4. 本地测试
mysql -u root -p botnet < 004_add_new_feature.sql

# 5. 提交到 Git
git add migrations/versions/004_add_new_feature.sql
git commit -m "feat: add migration for new feature"
git push
```

### 2. 开发者B同步迁移

```bash
# 1. 拉取最新代码
git pull

# 2. 查看新的迁移文件
ls migrations/versions/

# 3. 执行迁移
cd backend/migrations
python run_migrations.py  # 自动执行所有未执行的迁移
```

## ⚙️ 迁移管理表

为了追踪哪些迁移已执行，创建管理表：

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    version VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INT,
    INDEX idx_version (version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据库迁移记录表';
```

## 📌 最佳实践

### ✅ DO（推荐做法）

1. **每个功能一个迁移文件**
2. **包含完整的注释和说明**
3. **先在本地/测试环境验证**
4. **使用 `IF NOT EXISTS` 避免重复创建**
5. **记录回滚脚本**
6. **按顺序编号，不要跳号**

### ❌ DON'T（避免做法）

1. ❌ 不要修改已提交的迁移文件
2. ❌ 不要在迁移中包含业务数据（除非必要）
3. ❌ 不要在迁移中使用 `DROP TABLE`（除非明确需要）
4. ❌ 不要跳过版本号

## 🔧 冲突解决

如果两个开发者同时创建了相同编号的迁移：

```bash
# 开发者A: 004_feature_a.sql
# 开发者B: 004_feature_b.sql （冲突！）

# 解决方法：
# 后提交的开发者将文件重命名
mv 004_feature_b.sql 005_feature_b.sql
# 更新文件内的版本号注释
# 重新提交
```

## 📊 迁移状态查询

```sql
-- 查看已执行的迁移
SELECT * FROM schema_migrations ORDER BY executed_at DESC;

-- 查看最新迁移版本
SELECT version, executed_at FROM schema_migrations ORDER BY id DESC LIMIT 1;
```

## 🆘 回滚操作

如果迁移出错，需要回滚：

```sql
-- 1. 找到问题迁移的回滚脚本（在迁移文件注释中）
-- 2. 手动执行回滚
-- 3. 删除迁移记录
DELETE FROM schema_migrations WHERE version = '004_problematic_migration';
```

## 🔗 相关文档

- [数据库迁移执行脚本](./run_migrations.py)
- [初始数据库结构](./schema/init.sql)
- [项目结构说明](../项目结构说明.md)
