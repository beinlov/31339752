# 大平台集成免登录接口使用指南

## 概述

本文档说明如何通过免登录接口将僵尸网络管理平台集成到大型平台系统中。

## 接口列表

### 1. 跳转到大屏展示处置平台

**用途**：直接跳转到僵尸网络展示处置平台（大屏视图）

**URL**：
```
http://localhost:9000/login?username=op1&password=123456
```

**用户角色**：操作员（op1）

**跳转页面**：`/index`（大屏展示页面）

---

### 2. 跳转到后台管理系统首页

**用途**：跳转到后台管理系统，默认显示"受控节点监控"界面

**URL**：
```
http://localhost:9000/login?username=admin&password=123456
```

**用户角色**：管理员（admin）

**跳转页面**：`/admin`（默认菜单：受控节点监控）

---

### 3. 节点分布 - 跳转到"受控节点分布情况"

**用途**：直接跳转到后台管理系统的"受控节点分布情况"界面

**URL**：
```
http://localhost:9000/login?username=admin&password=123456&menu=node_distribution
```

**用户角色**：管理员（admin）

**跳转页面**：`/admin`（自动切换到：受控节点分布情况）

**menu 参数值**：`node_distribution`

---

### 4. 节点清除 - 跳转到"受控节点监控"

**用途**：直接跳转到后台管理系统的"受控节点监控"界面

**URL**：
```
http://localhost:9000/login?username=admin&password=123456&menu=clear
```

**用户角色**：管理员（admin）

**跳转页面**：`/admin`（自动切换到：受控节点监控）

**menu 参数值**：`clear`

---

### 5. C2监管 - 跳转到"C2状态监控"

**用途**：直接跳转到后台管理系统的"C2状态监控"界面

**URL**：
```
http://localhost:9000/login?username=admin&password=123456&menu=server
```

**用户角色**：管理员（admin）

**跳转页面**：`/admin`（自动切换到：C2状态监控）

**menu 参数值**：`server`

---

## 参数说明

### 基础参数

| 参数名 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| username | ✅ | 用户名 | admin / op1 |
| password | ✅ | 密码（明文） | 123456 |
| menu | ❌ | 目标菜单ID（仅管理员角色有效） | clear / node_distribution / server |

### menu 参数可选值

适用于管理员角色，控制登录后直接跳转到的功能页面：

| menu 值 | 对应功能 | 分组 |
|---------|----------|------|
| `clear` | 受控节点监控 | 僵尸网络管理 |
| `node_distribution` | 受控节点分布情况 | 僵尸网络管理 |
| `suppression` | 抑制阻断策略 | 僵尸网络管理 |
| `report` | 节点失控日志 | 僵尸网络管理 |
| `register_botnet` | 僵尸网络添加 | 僵尸网络管理 |
| `server` | C2状态监控 | 僵尸网络管理 |
| `user` | 用户管理 | 系统管理 |
| `log` | 操作日志 | 系统管理 |

---

## 技术实现说明

### 工作流程

1. **URL 参数检测**（LoginPage）
   - 检测 URL 中的 `username`、`password`、`menu` 参数
   - 如果存在，触发自动登录流程

2. **自动登录**
   - 调用后端接口：`GET /api/user/auto-login?username=xxx&password=xxx`
   - 验证成功后获取 JWT token 和用户角色

3. **menu 参数处理**
   - 如果存在 `menu` 参数且用户为管理员，将其保存到 `localStorage`
   - 清除 URL 参数（安全考虑）

4. **页面跳转**
   - 根据用户角色跳转到对应页面
   - 管理员 → `/admin`
   - 操作员 → `/index`

5. **菜单自动选择**（AdminPage）
   - 检测 `localStorage` 中的 `initialMenu` 参数
   - 如果存在，自动切换到对应菜单
   - 清除已使用的参数

### 安全机制

- ✅ 登录后立即清除 URL 参数，避免敏感信息暴露
- ✅ menu 参数仅对管理员角色生效
- ✅ 使用 JWT token 进行后续请求认证
- ✅ 支持 IP 白名单（可在 backend/config.py 配置）

---

## 集成示例

### 示例 1：在大平台中嵌入链接

```html
<!-- 大屏展示入口 -->
<a href="http://localhost:9000/login?username=op1&password=123456" target="_blank">
  僵尸网络展示处置平台
</a>

<!-- 后台管理入口 -->
<a href="http://localhost:9000/login?username=admin&password=123456" target="_blank">
  僵尸网络管理后台
</a>

<!-- 节点分布入口 -->
<a href="http://localhost:9000/login?username=admin&password=123456&menu=node_distribution" target="_blank">
  受控节点分布
</a>
```

### 示例 2：使用 iframe 嵌入

```html
<iframe 
  src="http://localhost:9000/login?username=admin&password=123456&menu=server"
  width="100%" 
  height="800px" 
  frameborder="0">
</iframe>
```

### 示例 3：JavaScript 动态跳转

```javascript
// 根据条件跳转到不同页面
function openBotnetPage(type) {
  const baseUrl = 'http://localhost:9000/login?username=admin&password=123456';
  
  const menuMap = {
    'distribution': 'node_distribution',  // 节点分布
    'monitor': 'clear',                   // 节点监控
    'c2': 'server'                        // C2监控
  };
  
  const menu = menuMap[type];
  const url = menu ? `${baseUrl}&menu=${menu}` : baseUrl;
  
  window.open(url, '_blank');
}

// 使用示例
openBotnetPage('distribution'); // 打开节点分布页面
openBotnetPage('c2');           // 打开C2监控页面
```

---

## 注意事项

1. **生产环境配置**
   - 将 `localhost:9000` 替换为实际域名
   - 修改默认用户名和密码
   - 启用 IP 白名单（`backend/config.py` → `SSO_CONFIG.enable_ip_whitelist = True`）

2. **跨域问题**
   - 如果大平台和本系统不在同一域名，需要配置 CORS
   - 已在 `backend/main.py` 中配置 CORS 中间件

3. **安全建议**
   - 不要在公网环境使用明文密码传递
   - 建议使用 HTTPS 协议
   - 定期更换密码和 JWT SECRET_KEY

4. **兼容性**
   - menu 参数是可选的，不影响原有接口
   - 如果 menu 值无效，系统会显示默认页面（受控节点监控）

---

## 修改记录

### 版本 1.0（2026-02-09）

- ✅ 实现基础免登录接口（username + password）
- ✅ 支持角色区分（管理员/操作员）
- ✅ 添加 menu 参数支持直接跳转到指定功能
- ✅ 修改 LoginPage.js 处理 menu 参数
- ✅ 修改 AdminPage.js 实现自动菜单切换

### 技术变更

**文件：`fronted/src/components/loginPage.js`**
- 添加 menu 参数检测
- 将 menu 参数保存到 localStorage

**文件：`fronted/src/components/adminPage.js`**
- 添加 useEffect 检测 initialMenu
- 自动调用 handleMenuClick 切换菜单
- 使用后清除 localStorage 中的参数

---

## 联系支持

如有问题，请查看：
- 后端日志：`backend/logs/`
- 前端控制台：浏览器开发者工具 → Console
- 配置文件：`backend/config.py`
