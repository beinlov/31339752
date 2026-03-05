# UTG_Q_008 数据库表结构修复总结

## 修复日期
2026-03-05

## 问题描述
用户反映 `utg_q_008` 的 `timeset` 数据库表（`botnet_timeset_utg_q_008`）与其他僵网的 `timeset` 表不一致：
- 其他僵网有 `global_count` 和 `china_count` 两个字段
- `botnet_timeset_utg_q_008` 只有 `count` 一个字段

## 修复过程

### 1. 修复 timeset 表结构
**问题：** `botnet_timeset_utg_q_008` 使用旧的字段名 `count`，而标准定义要求使用 `global_count` 和 `china_count`

**解决方案：**
- 运行 `update_timeset_schema.py` 脚本
- 将 `count` 字段重命名为 `global_count`
- 添加 `china_count` 字段
- 添加缺失的 `global_count_active` 字段

**结果：** ✓ `botnet_timeset_utg_q_008` 表结构已与其他僵网一致

### 2. 更新表创建脚本
**修改文件：** `create_timeset_tables.py`

**更改：**
```python
# 旧版本（错误）
count INT NOT NULL DEFAULT 0 COMMENT '节点数量'

# 新版本（正确）
global_count INT NOT NULL DEFAULT 0 COMMENT '全球节点数量'
china_count INT NOT NULL DEFAULT 0 COMMENT '中国节点数量'
```

**结果：** ✓ 今后创建的 timeset 表将直接使用正确的字段结构

### 3. 发现并修复其他表结构差异
在检查过程中发现，实际上是其他僵网（asruex, mozi, andromeda, moobot, ramnit, leethozer）的表缺少字段，而 `utg_q_008` 的表是符合标准定义的。

#### 3.1 china_botnet 表
**问题：** 其他僵网缺少 `communication_count` 字段

**解决方案：**
- 运行 `fix_other_botnets_tables.py` 脚本
- 为所有其他僵网的 `china_botnet` 表添加 `communication_count` 字段

**结果：** ✓ 所有僵网的 `china_botnet` 表结构现已一致

#### 3.2 global_botnet 表
**问题：**
- 其他僵网缺少 `communication_count` 字段
- `country` 字段类型为 `varchar(50)`，应为 `varchar(100)`

**解决方案：**
- 运行 `fix_other_botnets_tables.py` 脚本
- 为所有其他僵网的 `global_botnet` 表添加 `communication_count` 字段
- 将 `country` 字段类型从 `varchar(50)` 修改为 `varchar(100)`

**结果：** ✓ 所有僵网的 `global_botnet` 表结构现已一致

### 4. 更新标准 schema 定义
**修改文件：** `backend/database/schema.py`

**更改：**
- 在 `CHINA_BOTNET_TABLE_SCHEMA` 中添加 `active_num` 和 `cleaned_num` 字段
- 在 `GLOBAL_BOTNET_TABLE_SCHEMA` 中添加 `active_num` 和 `cleaned_num` 字段

**结果：** ✓ schema 定义现在与实际使用的表结构完全一致

## 最终验证
运行 `check_table_structures.py` 验证所有表结构：

```
[一致] nodes 表结构一致
[一致] communications 表结构一致
[一致] china_botnet 表结构一致
[一致] global_botnet 表结构一致
[一致] timeset 表结构一致

✓ 所有表结构检查完成，utg_q_008 与其他僵网表结构一致
```

## 涉及的脚本文件
1. **update_timeset_schema.py** - 更新所有 timeset 表结构
2. **create_timeset_tables.py** - 创建 timeset 表（已更新）
3. **fix_utg_q_008_tables.py** - 修复 utg_q_008 的表结构
4. **fix_other_botnets_tables.py** - 修复其他僵网的表结构
5. **check_table_structures.py** - 检查表结构一致性
6. **verify_fields.py** - 验证表字段详情

## 标准表结构定义

### botnet_timeset_{type} 表
```sql
CREATE TABLE botnet_timeset_{type} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    global_count INT NOT NULL DEFAULT 0 COMMENT '全球节点数量',
    china_count INT NOT NULL DEFAULT 0 COMMENT '中国节点数量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    china_active INT NOT NULL DEFAULT 0,
    global_active INT NOT NULL DEFAULT 0,
    china_cleaned INT NOT NULL DEFAULT 0,
    global_cleaned INT NOT NULL DEFAULT 0,
    global_count_active INT NOT NULL DEFAULT 0 COMMENT '全球节点数量（仅活跃）',
    INDEX idx_date (date)
);
```

### china_botnet_{type} 表
```sql
CREATE TABLE china_botnet_{type} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    province VARCHAR(50) NOT NULL,
    municipality VARCHAR(50) NOT NULL,
    infected_num INT DEFAULT 0 COMMENT '感染数量（节点数）',
    communication_count INT DEFAULT 0 COMMENT '通信总次数',
    created_at TIMESTAMP NULL DEFAULT NULL,
    updated_at TIMESTAMP NULL DEFAULT NULL,
    active_num INT DEFAULT 0 COMMENT 'active状态节点数量',
    cleaned_num INT DEFAULT 0 COMMENT 'cleaned状态节点数量',
    UNIQUE KEY idx_location (province, municipality)
);
```

### global_botnet_{type} 表
```sql
CREATE TABLE global_botnet_{type} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    country VARCHAR(100) NOT NULL,
    infected_num INT DEFAULT 0 COMMENT '感染数量（节点数）',
    communication_count INT DEFAULT 0 COMMENT '通信总次数',
    created_at TIMESTAMP NULL DEFAULT NULL,
    updated_at TIMESTAMP NULL DEFAULT NULL,
    active_num INT DEFAULT 0 COMMENT 'active状态节点数量',
    cleaned_num INT DEFAULT 0 COMMENT 'cleaned状态节点数量',
    UNIQUE KEY idx_country (country)
);
```

## 总结
✓ 所有表结构问题已修复
✓ utg_q_008 的所有表（nodes, communications, china_botnet, global_botnet, timeset）现已与其他僵网完全一致
✓ 标准 schema 定义已更新，与实际使用的表结构保持同步
✓ 创建表的脚本已更新，今后创建的表将直接使用正确的结构
