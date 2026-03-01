# 快速开始指南 - API地址配置

## 🎯 问题已解决

前端硬编码 `http://localhost:8000` 的问题已完全修复，现在支持灵活的环境配置。

## 📋 快速部署

### 场景一：本地开发（无需配置）

```bash
cd fronted
npm install
npm run dev
```

✅ 自动使用 `http://localhost:8000`

---

### 场景二：Docker部署（内网/局域网）

```bash
# 直接启动，前端会自动使用当前访问域名
docker-compose up -d
```

访问示例：
- 访问 `http://192.168.1.100` → API: `http://192.168.1.100:8000`
- 访问 `http://your-server` → API: `http://your-server:8000`

---

### 场景三：公网部署（推荐Nginx反向代理）

**步骤1：** 配置Nginx反向代理（在宿主机上）

创建 `/etc/nginx/conf.d/botnet.conf`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 后端API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**步骤2：** 启动服务

```bash
docker-compose up -d
```

**步骤3：** 重载Nginx

```bash
nginx -t
nginx -s reload
```

✅ 访问 `http://your-domain.com` 即可

---

### 场景四：前后端分离部署（不同域名）

**步骤1：** 在 `.env` 文件中配置后端地址

```bash
echo "VITE_API_BASE_URL=https://api.yourdomain.com" >> .env
```

**步骤2：** 重新构建并启动

```bash
docker-compose down
docker-compose up -d --build
```

**步骤3：** 确保后端配置了CORS

在后端 `main.py` 中：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frontend.yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🔍 验证部署

### 1. 检查API地址

打开浏览器控制台（F12），应该看到：

```
API Base URL: https://your-domain.com  (或你配置的地址)
```

### 2. 测试登录

尝试登录系统，如果成功则说明配置正确。

### 3. 检查网络请求

在浏览器开发者工具的 **Network** 标签中，查看API请求地址是否正确。

---

## ⚙️ 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VITE_API_BASE_URL` | 后端API地址 | 空（使用当前域名） |

### 设置方式

#### 方式1：修改 .env 文件（推荐）

```bash
# 编辑 .env 文件
vim .env

# 添加或修改
VITE_API_BASE_URL=https://api.yourdomain.com
```

#### 方式2：命令行传入

```bash
VITE_API_BASE_URL=https://api.yourdomain.com docker-compose up -d --build
```

#### 方式3：docker-compose.yml 中配置

```yaml
services:
  frontend:
    build:
      args:
        VITE_API_BASE_URL: https://api.yourdomain.com
```

---

## 🚨 常见问题

### Q1: 仍然显示 localhost:8000

**原因：** Docker缓存未清除

**解决：**
```bash
docker-compose down
docker rmi botnet-frontend
docker-compose up -d --build
```

### Q2: CORS 跨域错误

**原因：** 前后端域名不同，后端未配置CORS

**解决：** 参考"场景四"配置后端CORS

### Q3: 登录后显示"网络错误"

**原因：** API地址配置错误

**解决：**
1. 检查浏览器控制台的 "API Base URL" 输出
2. 检查 Network 标签中的实际请求地址
3. 确认后端服务正常运行（`curl http://localhost:8000/api/province-amounts`）

---

## 📚 更多文档

- 📄 **详细部署文档：** [DEPLOYMENT.md](fronted/DEPLOYMENT.md)
- 📄 **修改总结：** [API_URL_FIX_SUMMARY.md](API_URL_FIX_SUMMARY.md)
- 📄 **环境变量示例：** [.env.example](fronted/.env.example)

---

## 💡 最佳实践

1. ✅ **推荐：** 使用Nginx反向代理（场景三）
   - 前后端同域名，无CORS问题
   - 统一入口，易于管理

2. ⚠️ **备选：** 前后端分离部署（场景四）
   - 需要配置CORS
   - 适合微服务架构

3. ❌ **不推荐：** 硬编码API地址
   - 已经修复，不要再改回去！

---

## 🎉 修改完成

所有 **46处硬编码** 已全部替换为配置化调用，现在可以灵活部署到任何环境！
