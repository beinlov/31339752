# 添加新僵尸网络功能实现文档

## 📋 功能概述

实现了完整的添加新僵尸网络功能，包括前后端联动，自动创建数据库表结构。

## 🔧 修复的问题

### 1. JWT认证错误修复
**问题**: `AttributeError: module 'jwt' has no attribute 'JWTError'`

**原因**: PyJWT库中不存在`JWTError`异常类，应该使用`InvalidSignatureError`和其他具体异常。

**修复位置**: `backend/auth_middleware.py`

**修改内容**:
```python
# 修改前
except jwt.JWTError:
    raise HTTPException(...)

# 修改后
except jwt.InvalidSignatureError:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证令牌签名"
    )
except Exception as e:
    logger.error(f"Token verification error: {e}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证令牌"
    )
```

### 2. 表创建逻辑优化
**问题**: 原代码依赖模板表(`china_botnet_template`, `global_botnet_template`)，这些表可能不存在。

**修复位置**: `backend/router/botnet.py` - `ensure_botnet_table_exists()`函数

**修改内容**: 改为直接使用CREATE TABLE语句创建表，不依赖模板。

## 🎯 实现的功能

### 后端 (Backend)

#### 1. API端点: POST `/api/botnet-types`
**功能**: 注册新的僵尸网络类型

**权限**: 需要管理员权限 (`require_admin`)

**请求参数**:
```json
{
  "name": "botnet_name",           // 僵尸网络名称（小写字母、数字、下划线）
  "display_name": "显示名称",       // 中文显示名称
  "description": "详细描述",        // 僵尸网络描述
  "table_name": "china_botnet_xxx", // 表名（自动生成）
  "clean_methods": ["clear", "suppress"]  // 支持的清理方法
}
```

**响应**:
```json
{
  "status": "success",
  "message": "Botnet type xxx registered successfully",
  "data": {
    "name": "xxx",
    "display_name": "XXX僵尸网络",
    "table_name": "china_botnet_xxx"
  }
}
```

#### 2. 自动创建的数据库表

##### 表1: `botnet_nodes_{name}`
节点原始数据表，存储所有感染节点的详细信息。

**字段结构**:
```sql
CREATE TABLE botnet_nodes_{name} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(15) NOT NULL,                    -- IP地址
    longitude FLOAT,                            -- 经度
    latitude FLOAT,                             -- 纬度
    country VARCHAR(50),                        -- 国家
    province VARCHAR(50),                       -- 省份
    city VARCHAR(50),                           -- 城市
    continent VARCHAR(50),                      -- 大洲
    isp VARCHAR(255),                           -- ISP运营商
    asn VARCHAR(50),                            -- ASN号
    status ENUM('active', 'inactive') DEFAULT 'active',  -- 状态
    active_time TIMESTAMP NULL DEFAULT NULL COMMENT '节点激活时间（日志中的时间）',
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '节点首次写入数据库的时间',
    updated_at TIMESTAMP NULL DEFAULT NULL COMMENT '节点最新一次响应时间（日志中的时间）',
    is_china BOOLEAN DEFAULT FALSE,             -- 是否中国节点
    UNIQUE KEY idx_unique_ip (ip),
    INDEX idx_location (country, province, city),
    INDEX idx_status (status),
    INDEX idx_active_time (active_time),
    INDEX idx_created_time (created_time),
    INDEX idx_updated_at (updated_at),
    INDEX idx_is_china (is_china)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

##### 表2: `china_botnet_{name}`
中国地区统计表，按省市聚合。

**字段结构**:
```sql
CREATE TABLE china_botnet_{name} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    province VARCHAR(50) NOT NULL,              -- 省份
    municipality VARCHAR(50) NOT NULL,          -- 城市
    infected_num INT DEFAULT 0 COMMENT '感染数量',
    created_at TIMESTAMP NULL DEFAULT NULL COMMENT '该地区第一个节点的创建时间',
    updated_at TIMESTAMP NULL DEFAULT NULL COMMENT '该地区最新节点的更新时间',
    UNIQUE KEY idx_location (province, municipality),
    INDEX idx_province (province),
    INDEX idx_infected_num (infected_num),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

##### 表3: `global_botnet_{name}`
全球统计表，按国家聚合。

**字段结构**:
```sql
CREATE TABLE global_botnet_{name} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    country VARCHAR(100) NOT NULL,              -- 国家
    infected_num INT DEFAULT 0 COMMENT '感染数量',
    created_at TIMESTAMP NULL DEFAULT NULL COMMENT '该国家第一个节点的创建时间',
    updated_at TIMESTAMP NULL DEFAULT NULL COMMENT '该国家最新节点的更新时间',
    UNIQUE KEY idx_country (country),
    INDEX idx_infected_num (infected_num),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### 3. botnet_types表更新
在`botnet_types`表中添加新记录，包含:
- `name`: 僵尸网络名称
- `display_name`: 显示名称
- `description`: 描述
- `table_name`: 表名
- `clean_methods`: 清理方法（JSON格式）
- `created_at`: 创建时间
- `updated_at`: 更新时间

### 前端 (Frontend)

#### 组件: `BotnetRegistration.js`
**位置**: `fronted/src/components/BotnetRegistration.js`

**功能**:
1. 提供表单输入僵尸网络信息
2. 自动生成显示名称（输入name后自动填充）
3. 自动生成表名（`china_botnet_{name}`）
4. 验证输入格式（只允许小写字母、数字、下划线）
5. 发送请求到后端API
6. 显示成功/错误消息

**使用的认证**:
- 从`localStorage`获取token
- 在请求头中添加`Authorization: Bearer {token}`

**表单字段**:
- 僵尸网络名称 (必填)
- 显示名称 (自动生成，可修改)
- 描述 (可选)

## 📝 使用流程

### 1. 前端操作
1. 管理员登录系统
2. 进入"添加新僵尸网络"页面
3. 填写表单:
   - 输入僵尸网络名称（如：`mirai`）
   - 系统自动生成显示名称（如：`Mirai僵尸网络`）
   - 输入描述信息
4. 点击"添加新僵尸网络"按钮
5. 系统显示成功消息

### 2. 后端处理
1. 验证JWT token（管理员权限）
2. 验证输入数据
3. 检查僵尸网络名称是否已存在
4. 创建三个数据库表:
   - `botnet_nodes_{name}`
   - `china_botnet_{name}`
   - `global_botnet_{name}`
5. 在`botnet_types`表中插入记录
6. 返回成功响应

### 3. 数据库变化
- 新增3个数据表
- `botnet_types`表新增1条记录
- 所有表都有完整的索引和约束

## 🧪 测试方法

### 方法1: 使用测试脚本
```bash
cd backend
python test_add_botnet.py
```

测试脚本会:
1. 登录获取token
2. 添加测试僵尸网络`testbot`
3. 验证数据库表是否创建
4. 验证表结构是否正确
5. 验证`botnet_types`记录
6. 测试获取僵尸网络列表
7. 提供清理选项

### 方法2: 手动测试
1. 启动后端服务: `python main.py`
2. 启动前端服务: `cd fronted && npm start`
3. 浏览器访问前端页面
4. 使用管理员账号登录
5. 进入添加新僵尸网络页面
6. 填写并提交表单

### 方法3: API测试
使用Postman或curl测试API:

```bash
# 1. 登录
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 2. 添加僵尸网络（替换{TOKEN}为实际token）
curl -X POST http://localhost:8000/api/botnet-types \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {TOKEN}" \
  -d '{
    "name": "testbot",
    "display_name": "TestBot僵尸网络",
    "description": "测试僵尸网络",
    "table_name": "china_botnet_testbot",
    "clean_methods": ["clear", "suppress"]
  }'
```

## ⚠️ 注意事项

1. **权限要求**: 只有管理员可以添加新僵尸网络
2. **名称规则**: 僵尸网络名称只能包含小写字母、数字和下划线
3. **唯一性**: 僵尸网络名称不能重复
4. **表名格式**: 表名必须以`china_botnet_`开头
5. **数据库权限**: 确保数据库用户有CREATE TABLE权限

## 🔄 与聚合器集成

添加新僵尸网络后，需要更新聚合器配置:

### 1. 更新 `aggregator.py`
```python
BOTNET_TYPES = ['asruex', 'andromeda', 'mozi', 'leethozer', 'ramnit', 'moobot', 'newbot']
```

### 2. 更新 `config.yaml`
```yaml
botnet_types:
  - asruex
  - andromeda
  - mozi
  - leethozer
  - ramnit
  - moobot
  - newbot  # 新添加的僵尸网络
```

### 3. 重启聚合器
```bash
python stats_aggregator/aggregator.py daemon 5
```

## 📊 数据流程

```
用户输入 → 前端验证 → 发送请求(带token) → 后端验证权限 
→ 创建数据库表 → 插入botnet_types记录 → 返回成功 
→ 前端显示成功消息
```

## 🐛 常见问题

### Q1: 提示"认证令牌签名无效"
**A**: 检查token是否正确，或重新登录获取新token

### Q2: 提示"Botnet type already exists"
**A**: 该僵尸网络名称已存在，请使用其他名称

### Q3: 表创建失败
**A**: 检查数据库用户是否有CREATE TABLE权限

### Q4: 前端无法连接后端
**A**: 确保后端服务正在运行，检查端口是否正确(默认8000)

## 📚 相关文件

- `backend/auth_middleware.py` - JWT认证中间件
- `backend/router/botnet.py` - 僵尸网络路由
- `fronted/src/components/BotnetRegistration.js` - 前端组件
- `backend/test_add_botnet.py` - 测试脚本
- `backend/stats_aggregator/aggregator.py` - 数据聚合器

## ✅ 完成状态

- [x] JWT错误修复
- [x] 后端API实现
- [x] 数据库表自动创建
- [x] 前端组件更新
- [x] 认证集成
- [x] 测试脚本
- [x] 文档编写

---

**最后更新**: 2025-12-04
**版本**: 1.0
