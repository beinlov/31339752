# 前端部署说明文档

## 环境变量配置

前端项目已支持通过环境变量配置API基础URL，解决了硬编码导致的部署问题。

### 配置文件说明

- **`.env.development`** - 开发环境配置（默认使用 `http://localhost:8000`）
- **`.env.production`** - 生产环境配置（默认为空，使用当前访问域名）
- **`.env.example`** - 环境变量示例文件

### 环境变量

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `VITE_API_BASE_URL` | API服务器基础URL | `http://localhost:8000` 或 `https://api.yourdomain.com` |

## 部署方式

### 方式一：本地开发

```bash
# 1. 安装依赖
npm install

# 2. 启动开发服务器（自动使用 .env.development 配置）
npm run dev

# 访问 http://localhost:9000
```

### 方式二：生产构建（传统部署）

```bash
# 1. 配置生产环境变量（可选）
# 方法A: 修改 .env.production 文件
echo "VITE_API_BASE_URL=https://your-backend-domain.com" > .env.production

# 方法B: 或在构建时直接指定
export VITE_API_BASE_URL=https://your-backend-domain.com

# 2. 构建生产版本
npm run build

# 3. 部署 dist 目录到 Nginx/Apache 等服务器
```

### 方式三：Docker 部署（推荐）

#### 场景1：内网部署（前后端同一域名）

```bash
# 不传递任何环境变量，前端会自动使用当前访问域名
docker-compose up -d
```

访问 `http://your-server-ip`，前端会自动请求 `http://your-server-ip:8000/api/...`

#### 场景2：公网部署（推荐Nginx反向代理）

**步骤1：配置Nginx反向代理**

创建 `nginx-proxy.conf`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态资源
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 后端API代理（重要！）
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**步骤2：启动服务**

```bash
# 不需要传递API地址，前端会使用相对路径
docker-compose up -d
```

**步骤3：访问**

访问 `http://your-domain.com`，所有API请求会通过Nginx转发到后端。

#### 场景3：前后端分离部署（不同域名）

```bash
# 在 .env 文件中指定后端完整地址
echo "VITE_API_BASE_URL=https://api.yourdomain.com" > .env

# 构建并启动
docker-compose up -d --build
```

或直接在命令行指定：

```bash
VITE_API_BASE_URL=https://api.yourdomain.com docker-compose up -d --build
```

### 方式四：直接修改 Dockerfile 构建

```bash
# 构建时传入API地址
docker build \
  --build-arg VITE_API_BASE_URL=https://your-backend-domain.com \
  -t botnet-frontend \
  ./fronted

# 运行容器
docker run -d -p 80:80 botnet-frontend
```

## 验证部署

### 1. 检查API配置是否生效

打开浏览器控制台（F12），刷新页面，查看输出：

```
API Base URL: https://your-backend-domain.com
```

### 2. 检查网络请求

在浏览器开发者工具的 Network 标签中，确认所有 API 请求的 URL 是否正确。

### 3. 测试登录功能

尝试登录系统，确认能够正常访问后端接口。

## 故障排查

### 问题1：仍然请求 localhost:8000

**原因：** 环境变量未生效或构建时未传入

**解决：**
```bash
# 清除旧的构建缓存
docker-compose down
docker rmi botnet-frontend

# 重新构建
VITE_API_BASE_URL=https://your-domain.com docker-compose up -d --build
```

### 问题2：CORS 跨域错误

**原因：** 前后端域名不同，后端未配置 CORS

**解决：** 在后端 `main.py` 中确保配置了正确的 CORS：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 问题3：API 请求 404

**原因：** Nginx 反向代理配置错误

**解决：** 检查 Nginx 配置中的 `location /api/` 是否正确代理到后端。

## 最佳实践建议

### 1. 生产环境推荐配置

- ✅ **推荐：** 使用 Nginx 反向代理，前后端同域名，留空 `VITE_API_BASE_URL`
- ⚠️ **可选：** 前后端分离部署，明确指定后端完整URL

### 2. 安全建议

- 生产环境使用 HTTPS
- 配置后端 CORS 白名单
- 不要在前端代码中暴露敏感信息

### 3. 性能优化

- 启用 Nginx gzip 压缩
- 配置静态资源缓存
- 使用 CDN 加速静态资源

## 环境变量优先级

```
命令行环境变量 > .env.local > .env.production > .env.development > 代码默认值
```

## 相关文件

- `src/config/api.js` - API配置核心模块
- `.env.development` - 开发环境配置
- `.env.production` - 生产环境配置
- `Dockerfile` - Docker构建配置
- `docker-compose.yml` - Docker编排配置

## 技术支持

如有问题，请检查：
1. 浏览器控制台的 `API Base URL` 输出
2. Network 标签中的实际请求地址
3. 后端服务是否正常运行
4. 网络连接和防火墙设置
