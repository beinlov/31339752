# URL参数免登录集成指南

## 概述

本系统提供了基于URL参数的免登录机制，允许外部平台通过特定格式的URL直接访问僵尸网络展示处置平台，无需经过登录页面。

**适用场景**：其他平台需要集成本系统，希望用户点击链接后直接进入系统主界面。

---

## 快速开始

### 免登录链接格式

```
http://localhost:9000/login?username=<用户名>&password=<密码>
```

### 示例（op1用户）

```
http://localhost:9000/login?username=op1&password=123456
```

用户点击此链接后，系统会：
1. 自动检测URL参数
2. 调用后端验证接口
3. 验证成功后自动登录
4. 根据用户角色跳转到对应页面：
   - **管理员** → `/admin` （后台管理页面）
   - **操作员/访客** → `/index` （僵尸网络展示平台）

---

## 技术实现

### 1. 后端接口

**接口地址**：`GET /api/user/auto-login`

**请求参数**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码（明文） |

**响应示例**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "操作员",
  "username": "op1"
}
```

**错误响应**：
```json
{
  "detail": "用户名或密码错误"
}
```

### 2. 前端自动登录流程

前端登录页面会自动检测URL参数：
1. 提取 `username` 和 `password` 参数
2. 调用 `/api/user/auto-login` 接口
3. 保存返回的 token 到 localStorage
4. 清除URL中的密码参数（安全考虑）
5. 根据角色自动跳转

---

## 集成示例

### HTML页面集成

```html
<!DOCTYPE html>
<html>
<head>
    <title>跳转到僵尸网络平台</title>
</head>
<body>
    <h1>僵尸网络管理系统</h1>
    <a href="http://localhost:9000/login?username=op1&password=123456">
        点击进入僵尸网络展示平台
    </a>
</body>
</html>
```

### JavaScript动态跳转

```javascript
// 方式1：直接跳转
function jumpToBotnetPlatform() {
    const username = 'op1';
    const password = '123456';
    window.location.href = `http://localhost:9000/login?username=${username}&password=${password}`;
}

// 方式2：新窗口打开
function openBotnetPlatform() {
    const username = 'op1';
    const password = '123456';
    window.open(`http://localhost:9000/login?username=${username}&password=${password}`, '_blank');
}
```

### iframe嵌入

```html
<iframe 
    src="http://localhost:9000/login?username=op1&password=123456" 
    width="100%" 
    height="800px"
    frameborder="0">
</iframe>
```

---

## 用户账号信息

### 默认账号

| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| op1 | 123456 | 操作员 | 推荐用于外部平台集成 |
| admin | admin123 | 管理员 | 仅用于系统管理 |

### 创建新用户

如需为外部平台创建专用账号，请联系系统管理员通过后台管理页面创建。

---

## 安全建议

### ⚠️ 重要安全提示

1. **HTTPS传输**
   - 生产环境必须使用HTTPS，避免密码在URL中明文传输被窃取
   - 示例：`https://your-domain.com/login?username=op1&password=123456`

2. **URL参数清理**
   - 前端会在登录成功后自动清除URL中的密码参数
   - 避免密码残留在浏览器历史记录中

3. **访问控制**
   - 建议为外部平台创建专用账号，权限设置为"操作员"或"访客"
   - 不要使用管理员账号进行集成

4. **IP白名单**（可选）
   - 如需更高安全性，可在后端配置IP白名单
   - 修改 `backend/config.py` 中的相关配置

5. **密码强度**
   - 为集成账号设置强密码
   - 定期更换密码

6. **链接保护**
   - 不要在公开页面直接暴露免登录链接
   - 建议在需要时动态生成链接

### 推荐做法

```javascript
// 推荐：后端动态生成免登录链接
async function getBotnetPlatformLink() {
    // 从你的后端获取加密的跳转链接
    const response = await fetch('/api/get-botnet-link');
    const { link } = await response.json();
    window.location.href = link;
}

// 不推荐：前端硬编码密码
// const link = 'http://localhost:9000/login?username=op1&password=123456';
```

---

## 生产环境配置

### 1. 修改前端API地址

编辑 `fronted/src/components/loginPage.js`：

```javascript
// 开发环境
const API_BASE_URL = 'http://localhost:8000';

// 生产环境（修改为实际域名）
const API_BASE_URL = 'https://your-domain.com';
```

### 2. 配置CORS

编辑 `backend/main.py`，修改允许的源：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-external-platform.com"],  # 外部平台域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 故障排查

### 问题1：自动登录失败

**可能原因**：
- 用户名或密码错误
- 后端服务未启动
- 网络连接问题

**解决方法**：
1. 检查浏览器控制台错误信息
2. 确认后端服务运行在 `http://localhost:8000`
3. 验证用户名密码是否正确

### 问题2：登录后立即跳转到登录页

**可能原因**：
- Token未正确保存到localStorage
- 前端路由守卫拦截

**解决方法**：
1. 打开浏览器开发者工具 → Application → Local Storage
2. 确认 `token`、`role`、`username` 已保存
3. 检查浏览器控制台是否有错误

### 问题3：CORS跨域错误

**错误信息**：`Access to XMLHttpRequest at 'http://localhost:8000/api/user/auto-login' from origin 'http://localhost:9000' has been blocked by CORS policy`

**解决方法**：
- 确认后端CORS配置正确
- 检查 `backend/main.py` 中的 `allow_origins` 设置

---

## API文档

完整的API文档可访问：
```
http://localhost:8000/docs
```

在该页面可以测试 `/api/user/auto-login` 接口。

---

## 联系支持

如有问题，请联系系统管理员。

---

## 更新日志

### v1.0 (2026-01-20)
- 实现URL参数免登录功能
- 删除旧的SSO免登录机制
- 新增自动登录接口 `/api/user/auto-login`
- 前端支持URL参数自动检测和登录
