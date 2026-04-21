# VPN访问配置指南

## 问题说明

平台具有高安全性要求，需要通过VPN访问服务器 `10.61.241.38`。

### 配置问题
- 前端默认配置调用 `http://localhost:8000/api`
- 实际后端服务在 `http://10.61.241.38:8000/api`
- 用户通过VPN访问前端时，浏览器会尝试连接**本地**的localhost，导致无法连接后端

---

## 解决方案汇总

### 方案一：直接指定服务器IP（已实施）✅

**适用场景**: 所有用户通过VPN访问同一台服务器

**配置位置**: 
- `/home/spider/31339752/fronted/.env`
- `/home/spider/31339752/fronted/.env.production`

**当前配置**:
```bash
VITE_API_BASE_URL=http://10.61.241.38:8000
```

**优点**:
- 配置简单明确
- 所有通过VPN的用户都能正常访问
- 适合固定服务器IP的场景

**缺点**:
- 如果服务器IP变更，需要重新构建前端

**使用方法**:
```bash
cd /home/spider/31339752/fronted
npm run build  # 重新构建前端
```

---

### 方案二：使用相对路径（通过Nginx反向代理）

**适用场景**: 前端和后端部署在同一域名下，通过Nginx统一代理

**配置步骤**:

1. **前端配置** - 留空API地址，使用相对路径:
```bash
# .env.production
VITE_API_BASE_URL=
```

2. **Nginx配置示例**:
```nginx
server {
    listen 80;
    server_name 10.61.241.38;

    # 前端静态资源
    location / {
        root /path/to/fronted/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**优点**:
- 前后端同域，避免CORS问题
- 配置灵活，修改后端地址只需改Nginx配置
- 更安全（后端不直接暴露）

**缺点**:
- 需要配置Nginx
- 增加一层反向代理

---

### 方案三：智能切换配置（本地开发+VPN访问）

**适用场景**: 开发人员需要本地开发，普通用户通过VPN访问

**配置方法**:

1. **保留开发环境配置** - `.env.development`:
```bash
VITE_API_BASE_URL=http://localhost:8000
```

2. **生产环境使用服务器IP** - `.env.production`:
```bash
VITE_API_BASE_URL=http://10.61.241.38:8000
```

3. **开发时**:
```bash
npm run dev  # 使用.env.development配置
```

4. **构建部署时**:
```bash
npm run build  # 使用.env.production配置
```

**优点**:
- 开发和生产环境分离
- 开发人员本地测试方便
- VPN用户访问正常

---

## 部署流程

### 当前推荐流程（方案一）

1. **确认配置**:
```bash
cat /home/spider/31339752/fronted/.env
# 应显示: VITE_API_BASE_URL=http://10.61.241.38:8000
```

2. **重新构建前端**:
```bash
cd /home/spider/31339752/fronted
npm run build
```

3. **部署构建产物**:
```bash
# dist目录包含所有前端资源
# 将dist目录部署到Web服务器
```

4. **验证访问**:
- 连接VPN
- 访问前端地址（如 http://10.61.241.38:9000）
- 检查浏览器开发者工具的Network标签
- 确认API请求指向 `http://10.61.241.38:8000/api`

---

## 常见问题

### Q1: 修改配置后前端仍然连接localhost?
**A**: 需要重新构建前端。Vite在构建时会将环境变量嵌入到代码中。
```bash
cd /home/spider/31339752/fronted
npm run build
```

### Q2: 开发时如何连接远程后端?
**A**: 临时修改 `.env.development`:
```bash
VITE_API_BASE_URL=http://10.61.241.38:8000
```
或使用环境变量覆盖:
```bash
VITE_API_BASE_URL=http://10.61.241.38:8000 npm run dev
```

### Q3: 如何调试API连接问题?
**A**: 查看浏览器控制台日志:
```javascript
// src/config/api.js 会打印以下信息:
[API Config] 环境变量 VITE_API_BASE_URL: http://10.61.241.38:8000
[API Config] 最终API Base URL: http://10.61.241.38:8000
[API Config] 生成完整URL: http://10.61.241.38:8000/api/xxx
```

### Q4: 服务器IP变更怎么办?
**A**: 修改配置文件并重新构建:
```bash
# 1. 修改配置
vim /home/spider/31339752/fronted/.env
# 2. 重新构建
cd /home/spider/31339752/fronted
npm run build
# 3. 重新部署
```

---

## 安全建议

1. **HTTPS加密**: 在生产环境使用HTTPS保护数据传输
2. **API密钥保护**: 确保API_KEY不暴露在前端代码中
3. **VPN访问控制**: 保持VPN作为唯一访问通道
4. **CORS配置**: 后端配置允许的访问来源

---

## 相关文件

- `/home/spider/31339752/fronted/.env` - 主要配置文件
- `/home/spider/31339752/fronted/.env.development` - 开发环境配置
- `/home/spider/31339752/fronted/.env.production` - 生产环境配置
- `/home/spider/31339752/fronted/src/config/api.js` - API配置逻辑
- `/home/spider/31339752/fronted/vite.config.js` - Vite配置（含代理设置）

---

## 更新日志

- 2026-04-16: 初始版本，配置VPN访问支持
- 已修改配置文件，将API地址从localhost改为10.61.241.38
