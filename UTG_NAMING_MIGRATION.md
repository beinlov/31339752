# UTG命名统一迁移文档

## 📋 概述

将所有 `utg-q-008`（连字符格式）统一修改为 `utg_q_008`（下划线格式），符合Python命名规范。

## 🎯 修改目标

统一使用下划线格式，消除命名不一致问题：
- ✅ 符合Python变量命名规范
- ✅ 简化代码逻辑，无需名称转换
- ✅ 减少潜在的命名混淆

## 📝 修改详情

### 1. 数据库修改

#### botnet_types 表
```sql
UPDATE botnet_types 
SET name = 'utg_q_008' 
WHERE name = 'utg-q-008';
```
- **修改前**: `name = 'utg-q-008'`
- **修改后**: `name = 'utg_q_008'`
- **影响**: 1条记录

#### server_management 表
```sql
UPDATE server_management 
SET Botnet_Name = 'utg_q_008' 
WHERE Botnet_Name = 'utg-q-008';
```
- **修改前**: `Botnet_Name = 'utg-q-008'`
- **修改后**: `Botnet_Name = 'utg_q_008'`
- **影响**: 1条记录（服务器ID: 11, IP: 43.99.37.118）

### 2. 配置文件修改

#### `backend/config.py`

```python
# 修改前
'utg-q-008': {
    'cleanup': '/admin/irc/cleanup',
    'status': '/admin/irc/status',
    'reset': '/admin/irc/reset'
}

# 修改后
'utg_q_008': {
    'cleanup': '/admin/irc/cleanup',
    'status': '/admin/irc/status',
    'reset': '/admin/irc/reset'
}
```

### 3. 代码简化

#### `backend/router/server.py`

**删除的代码**:
```python
def normalize_botnet_name(name: str) -> str:
    """标准化僵网名称，将连字符转换为下划线"""
    if name:
        return name.replace('-', '_')
    return name
```

**简化后的逻辑**:
```python
# 修改前
normalized_name = normalize_botnet_name(botnet_name)
table_name = f"botnet_nodes_{normalized_name}"

# 修改后（直接使用）
table_name = f"botnet_nodes_{botnet_name}"
```

#### `backend/router/cleanup.py`

**删除的代码**:
```python
def normalize_botnet_name(name: str) -> str:
    """标准化僵网名称，将下划线转换为连字符"""
    if name:
        return name.replace('_', '-')
    return name

def denormalize_botnet_name(name: str) -> str:
    """反标准化僵网名称，将连字符转换为下划线"""
    if name:
        return name.replace('-', '_')
    return name
```

**简化后的逻辑**:
```python
# 修改前
normalized_name = normalize_botnet_name(botnet_name)
c2_info = get_botnet_c2_info(normalized_name)
has_paths = normalized_name in C2_CLEANUP_CONFIG['botnet_paths']

# 修改后（直接使用）
c2_info = get_botnet_c2_info(botnet_name)
has_paths = botnet_name in C2_CLEANUP_CONFIG['botnet_paths']
```

## ✅ 验证结果

所有检查项目均通过：

1. ✅ **botnet_types表**: `name = 'utg_q_008'`
2. ✅ **server_management表**: `Botnet_Name = 'utg_q_008'`
3. ✅ **节点表**: `botnet_nodes_utg_q_008` 存在
4. ✅ **C2配置**: `C2_CLEANUP_CONFIG['botnet_paths']['utg_q_008']` 存在
5. ✅ **C2状态监控**: 能够正确查询节点数
6. ✅ **一键清除**: 能够识别权限和接口配置

## 📊 命名规范总结

| 位置 | 旧格式 | 新格式 |
|------|--------|--------|
| botnet_types.name | utg-q-008 | utg_q_008 |
| server_management.Botnet_Name | utg-q-008 | utg_q_008 |
| 节点表名 | botnet_nodes_utg_q_008 | ✅ 保持不变 |
| C2配置键名 | utg-q-008 | utg_q_008 |

## 🚀 部署步骤

1. **重启后端服务**
   ```bash
   # 停止现有服务
   # 启动新服务
   ```

2. **刷新前端页面**

3. **验证功能**
   - C2状态监控界面：应显示 utg_q_008 的节点数（0，不是Null）
   - 一键清除界面：应显示 utg_q_008 可以清除，有"查询"、"清除"、"重置"按钮

## 📁 相关文件

- ✅ `backend/config.py` - C2清除配置
- ✅ `backend/router/server.py` - C2状态监控逻辑
- ✅ `backend/router/cleanup.py` - 一键清除逻辑
- ✅ 数据库表: `botnet_types`, `server_management`

## 🎉 优势

1. **代码更简洁**: 删除了约40行名称转换代码
2. **逻辑更清晰**: 无需在连字符和下划线之间转换
3. **维护更容易**: 统一的命名规范，减少混淆
4. **性能更好**: 减少了字符串替换操作

## ⚠️ 注意事项

- 所有新添加的僵网都应使用下划线格式（`botnet_name`）
- 如果有其他地方使用了 `utg-q-008`，也需要相应修改
- 前端显示名称（display_name）可以保持任意格式

---

**迁移日期**: 2026-03-04  
**执行人**: Cascade AI Assistant  
**状态**: ✅ 完成并验证
