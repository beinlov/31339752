# SQL 脚本说明

本目录包含所有数据库相关的 SQL 脚本。

---

## 📄 文件列表

| 文件 | 大小 | 用途 | 何时使用 |
|------|------|------|---------|
| `init.sql` | 3 KB | 初始化数据库脚本 | 首次部署时，创建基础表结构和初始数据 |
| `create_tables.sql` | 812 B | 创建表结构 | 需要重建某些表时 |
| `optimize_indexes.sql` | 3.7 KB | 索引优化脚本 | 提升查询性能，优化聚合器速度 |

---

## 🚀 使用说明

### 1. 初始化数据库

首次部署时执行：

```bash
mysql -u root -p botnet < sql/init.sql
```

### 2. 创建表结构

如果需要单独创建某些表：

```bash
mysql -u root -p botnet < sql/create_tables.sql
```

### 3. 优化索引

提升查询性能（特别是聚合器慢时）：

```bash
mysql -u root -p botnet < sql/optimize_indexes.sql
```

---

## ⚠️ 注意事项

1. **备份优先**: 执行任何 SQL 脚本前，务必先备份数据库
   ```bash
   mysqldump -u root -p botnet > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **检查脚本**: 建议先查看 SQL 文件内容，了解将要执行的操作

3. **测试环境**: 重要操作建议先在测试环境验证

4. **索引优化**: `optimize_indexes.sql` 适用于数据量较大时执行

---

## 📊 其他数据库文件

### 数据库备份

- **位置**: 项目根目录 `/botnet.sql` (60 MB)
- **用途**: 完整数据库备份
- **使用**: `mysql -u root -p botnet < botnet.sql`

**建议**: 大型备份文件应存储在项目外部或使用版本控制的 LFS。

---

## 🔗 相关文档

- **数据库 Schema**: `/backend/database/schema.py`
- **数据库迁移**: `/backend/migrations/`
- **运维脚本**: `/backend/scripts/README.md`

---

**最后更新**: 2026-03-20
