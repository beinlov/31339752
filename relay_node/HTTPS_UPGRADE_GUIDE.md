# HTTPS 升级指南

从HTTP升级到HTTPS的完整指南

---

## 📋 为什么需要HTTPS？

### HTTP vs HTTPS

| 特性 | HTTP | HTTPS |
|------|------|-------|
| 数据加密 | ❌ 明文传输 | ✅ SSL/TLS加密 |
| 身份认证 | ❌ 无法验证 | ✅ 证书验证 |
| 数据完整性 | ❌ 可被篡改 | ✅ 防篡改 |
| 安全性 | 低 | 高 |

### 使用场景

- ✅ **生产环境**：强烈推荐使用HTTPS
- ✅ **公网传输**：必须使用HTTPS
- ⚠️ **内网测试**：可以使用HTTP

---

## 🔧 SSL证书选择

### 选项1: 自签名证书（测试/开发）

**优点**：
- ✅ 免费
- ✅ 快速生成
- ✅ 适合测试

**缺点**：
- ❌ 浏览器会警告"不安全"
- ❌ 需要客户端信任证书
- ❌ 不适合生产环境

### 选项2: Let's Encrypt（生产推荐）

**优点**：
- ✅ 免费
- ✅ 自动续期
- ✅ 浏览器信任
- ✅ 适合生产环境

**缺点**：
- ⚠️ 需要域名
- ⚠️ 需要80/443端口

### 选项3: 商业证书

**优点**：
- ✅ 技术支持
- ✅ 保险服务
- ✅ 高级验证

**缺点**：
- ❌ 需要付费

---

## 🚀 快速升级步骤

### 步骤1: 生成SSL证书

#### 选项A: 自签名证书（测试用）

```bash
# 生成自签名证书（有效期365天）
openssl req -x509 -newkey rsa:4096 \
  -keyout key.pem \
  -out cert.pem \
  -days 365 \
  -nodes \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=RelayNode/CN=relay.example.com"

# 验证证书
openssl x509 -in cert.pem -text -noout

# 设置权限
chmod 600 key.pem
chmod 644 cert.pem
```

#### 选项B: Let's Encrypt（生产用）

```bash
# 安装certbot
sudo apt update
sudo apt install certbot

# 获取证书（需要域名和80端口）
sudo certbot certonly --standalone \
  -d relay.yourdomain.com \
  --email your@email.com \
  --agree-tos

# 证书位置
# /etc/letsencrypt/live/relay.yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/relay.yourdomain.com/privkey.pem

# 复制证书到relay_node目录
sudo cp /etc/letsencrypt/live/relay.yourdomain.com/fullchain.pem ./cert.pem
sudo cp /etc/letsencrypt/live/relay.yourdomain.com/privkey.pem ./key.pem
sudo chown $USER:$USER cert.pem key.pem
chmod 600 key.pem
chmod 644 cert.pem

# 设置自动续期
sudo certbot renew --dry-run
```

### 步骤2: 修改配置

编辑 `relay_node_config.json`：

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8888,
    "api_key": "your_api_key",
    
    "use_https": true,
    "ssl_cert": "./cert.pem",
    "ssl_key": "./key.pem"
  }
}
```

或使用环境变量：

```bash
export USE_HTTPS=true
export SSL_CERT=./cert.pem
export SSL_KEY=./key.pem
```

### 步骤3: 重启服务

```bash
# 停止旧服务
pkill -f relay_data_server.py

# 启动HTTPS服务
./start_relay_node.sh

# 或者
python3 relay_data_server.py
```

### 步骤4: 验证HTTPS

```bash
# 测试HTTPS连接
curl -k -H "X-API-Key: your_api_key" \
     https://localhost:8888/health

# 使用自签名证书需要 -k 参数（忽略证书验证）
# 使用Let's Encrypt证书不需要 -k 参数

# 检查证书信息
openssl s_client -connect localhost:8888 -showcerts
```

### 步骤5: 更新平台配置

修改平台的 `backend/config.py`：

```python
C2_ENDPOINTS = [
    {
        'id': 'relay-node-1',
        'url': 'https://中继节点IP:8888',  # 改成https://
        'api_key': 'your_relay_node_api_key',
        'botnet_type': 'utg_q_008',
        'enabled': True
    }
]
```

**如果使用自签名证书**，平台可能需要禁用证书验证：

```python
# backend/log_processor/remote_puller.py
# 在创建session时添加
import ssl
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

session = aiohttp.ClientSession(
    connector=aiohttp.TCPConnector(ssl=ssl_context)
)
```

---

## 🔐 安全配置建议

### 1. 使用强加密套件

创建 `ssl_config.py`（可选）：

```python
import ssl

def get_ssl_context(cert_file, key_file):
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(cert_file, key_file)
    
    # 仅使用TLS 1.2和1.3
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    
    # 设置加密套件
    ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
    
    return ssl_context
```

### 2. 防火墙配置

```bash
# 仅允许必要的端口
sudo ufw allow 8888/tcp comment 'Relay Node HTTPS'
sudo ufw deny 8888/tcp from 0.0.0.0/0 comment 'Block HTTP'

# 限制访问源
sudo ufw allow from 平台服务器IP to any port 8888
```

### 3. 定期更新证书

Let's Encrypt证书有效期90天，需要定期续期：

```bash
# 手动续期
sudo certbot renew

# 自动续期（cron任务）
sudo crontab -e

# 添加以下行（每天凌晨2点检查）
0 2 * * * certbot renew --quiet --post-hook "systemctl restart relay-node"
```

---

## 🧪 测试验证

### 1. SSL证书验证

```bash
# 在线验证（如果有公网域名）
https://www.ssllabs.com/ssltest/

# 本地验证
openssl s_client -connect localhost:8888 \
  -servername relay.example.com \
  -showcerts

# 检查证书有效期
openssl x509 -in cert.pem -noout -dates
```

### 2. API功能验证

```bash
# 健康检查
curl -k -H "X-API-Key: xxx" https://localhost:8888/health

# 拉取数据
curl -k -H "X-API-Key: xxx" https://localhost:8888/api/pull?limit=10

# 统计信息
curl -k -H "X-API-Key: xxx" https://localhost:8888/api/stats
```

### 3. 性能测试

```bash
# 使用ab测试HTTPS性能
ab -n 1000 -c 10 \
   -H "X-API-Key: xxx" \
   https://localhost:8888/health
```

---

## 🐛 故障排查

### 问题1: 证书文件不存在

**错误信息**：
```
FileNotFoundError: cert.pem not found
```

**解决方法**：
```bash
# 检查证书文件
ls -l cert.pem key.pem

# 确认路径正确
pwd
```

### 问题2: 证书权限错误

**错误信息**：
```
PermissionError: Cannot read key.pem
```

**解决方法**：
```bash
# 设置正确权限
chmod 600 key.pem
chmod 644 cert.pem
chown $USER:$USER cert.pem key.pem
```

### 问题3: 浏览器提示"不安全"

**原因**：使用自签名证书

**解决方法**：
- **测试环境**：接受证书警告，继续访问
- **生产环境**：使用Let's Encrypt或商业证书

### 问题4: 平台连接失败

**错误信息**：
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**解决方法**：

方法1: 信任自签名证书（测试环境）
```python
# 禁用SSL验证
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
```

方法2: 使用正规证书（生产环境）
- 使用Let's Encrypt
- 使用商业证书

---

## 📊 性能影响

### HTTPS开销

- CPU使用：+5-15%（加密计算）
- 延迟：+20-50ms（TLS握手）
- 吞吐量：-5-10%（加密开销）

### 优化建议

1. **启用HTTP/2**（未来版本）
2. **使用Session复用**
3. **硬件加速**（支持AES-NI的CPU）

---

## 🔄 回退到HTTP

如果HTTPS出现问题，可以快速回退：

```bash
# 1. 修改配置
vim relay_node_config.json
# 设置 "use_https": false

# 2. 重启服务
pkill -f relay_data_server.py
./start_relay_node.sh

# 3. 更新平台配置
# 将URL改回 http://...
```

---

## ✅ 生产环境检查清单

部署HTTPS前请确认：

- [ ] 使用Let's Encrypt或商业证书（不是自签名）
- [ ] 证书有效期至少30天
- [ ] 配置了自动续期
- [ ] 防火墙规则正确
- [ ] 平台能正常连接
- [ ] API功能测试通过
- [ ] 日志无错误
- [ ] 监控已设置

---

## 📚 参考资料

- [Let's Encrypt官方文档](https://letsencrypt.org/docs/)
- [SSL Labs测试工具](https://www.ssllabs.com/ssltest/)
- [Mozilla SSL配置指南](https://ssl-config.mozilla.org/)
- [OWASP TLS安全指南](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)

---

**🔒 祝您升级顺利！**
