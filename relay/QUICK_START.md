# 中转服务器 - 快速部署指南

## 🚀 5分钟快速部署

### 前提条件
- ✅ Ubuntu 20.04+ 或类似系统
- ✅ Python 3.7+
- ✅ AWS账号和凭证
- ✅ OpenVPN配置文件

---

## 步骤1：安装依赖 (1分钟)

```bash
# 安装Python和依赖
sudo apt update
sudo apt install -y python3 python3-pip openvpn awscli
pip3 install -r requirements.txt
```

---

## 步骤2：配置AWS (1分钟)

```bash
# 设置AWS凭证
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_DEFAULT_REGION="us-east-2"

# 验证连接
aws ec2 describe-instances --region us-east-2
```

---

## 步骤3：配置OpenVPN (1分钟)

```bash
# 复制OpenVPN配置
sudo cp /path/to/your-vpn-config.ovpn /etc/openvpn/client.conf

# 启动OpenVPN
sudo openvpn --config /etc/openvpn/client.conf --daemon

# 验证连接
ip addr show tun0
ping 10.8.0.1  # C2端OpenVPN IP
```

---

## 步骤4：配置中转服务 (1分钟)

```bash
# 复制配置模板
cp relay_config_example.json relay_config.json

# 编辑配置（修改以下关键项）
vim relay_config.json
```

**必须修改的配置**：
```json
{
  "puller": {
    "c2_servers": [{
      "url": "http://10.8.0.1:8888",          // ← 修改为实际C2端URL
      "api_key": "你的C2端API密钥"             // ← 修改为实际密钥
    }]
  },
  "pusher": {
    "platform_url": "http://你的平台:8000",    // ← 修改为实际平台URL
    "platform_api_key": "你的平台API密钥",     // ← 修改为实际密钥
    "signature_secret": "你的签名密钥"         // ← 修改为与平台一致的密钥
  },
  "ip_change": {
    "instance_id": "i-xxxxx"                  // ← 修改为实际AWS实例ID
  }
}
```

---

## 步骤5：启动服务 (1分钟)

```bash
# 测试运行
./start_relay.sh

# 观察日志输出，确认：
# ✓ 配置加载成功
# ✓ C2服务器连接成功
# ✓ 平台服务器连接成功
# ✓ IP管理器启动

# Ctrl+C 停止测试

# 配置为系统服务（推荐）
sudo cp relay-server.service /etc/systemd/system/
# 编辑服务文件，修改路径
sudo vim /etc/systemd/system/relay-server.service
# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable relay-server
sudo systemctl start relay-server
```

---

## 验证部署 ✅

```bash
# 1. 检查服务状态
sudo systemctl status relay-server

# 2. 查看实时日志
sudo journalctl -u relay-server -f

# 3. 运行健康检查
python3 health_monitor.py

# 4. 查看数据库
sqlite3 relay_cache.db "SELECT status, COUNT(*) FROM data_records GROUP BY status;"
```

---

## 预期输出示例

### 服务启动日志
```
[INFO] relay_service - 加载配置文件: relay_config.json
[INFO] relay_service - ✅ 配置验证通过
[INFO] data_storage - 数据库初始化完成
[INFO] data_puller - 数据拉取客户端初始化: 1 个C2服务器
[INFO] data_pusher - 数据推送客户端初始化: http://your-platform:8000
[INFO] ip_manager - IP管理器初始化
[INFO] relay_service - ✅ IP切换线程已启动
[INFO] relay_service - 中转服务启动
```

### 健康检查输出
```
[INFO] 检查C2服务器...
[INFO] ✅ C2服务器: 1/1 健康
[INFO] 检查平台服务器...
[INFO] ✅ 平台服务器: 健康
[INFO] 检查本地数据库...
[INFO] ✅ 数据库: 总计0条, 待推送0条, 失败0条
[INFO] 检查OpenVPN连接...
[INFO] ✅ OpenVPN: 运行中
[INFO] 检查磁盘空间...
[INFO] ✅ 磁盘空间: 75.5% 可用 (150.0 GB)
[INFO] ✅ 总体状态: 健康
```

---

## 常用命令速查

```bash
# 启动服务
sudo systemctl start relay-server

# 停止服务
sudo systemctl stop relay-server

# 重启服务
sudo systemctl restart relay-server

# 查看状态
sudo systemctl status relay-server

# 实时日志
sudo journalctl -u relay-server -f

# 健康检查
python3 health_monitor.py

# 查看统计
tail -f relay_service.log | grep "服务统计"
```

---

## 遇到问题？

### 快速排查清单

1. **C2连接失败**
   ```bash
   # 检查OpenVPN
   pgrep -f openvpn
   ip addr show tun0
   ping 10.8.0.1
   ```

2. **平台推送失败**
   ```bash
   # 检查平台连通
   curl http://your-platform:8000/api/push-health
   # 检查签名密钥是否一致
   grep signature_secret relay_config.json
   ```

3. **IP切换失败**
   ```bash
   # 检查AWS凭证
   aws ec2 describe-addresses --region us-east-2
   ```

4. **查看详细日志**
   ```bash
   # 查看所有错误
   grep -i "error\|failed\|❌" relay_service.log
   ```

---

## 下一步

✅ **部署成功！** 现在服务应该正常运行了。

📚 **阅读完整文档**：查看 [README_DEPLOYMENT.md](README_DEPLOYMENT.md) 了解：
- 详细配置说明
- 性能优化建议
- 故障排查指南
- 安全最佳实践

📊 **监控运维**：
- 设置定期健康检查（crontab）
- 配置日志轮转
- 监控磁盘使用
- 定期备份数据库

🔐 **安全加固**：
- 修改所有默认密钥
- 配置防火墙规则
- 定期更新系统
- 审计访问日志

---

## 技术支持

需要帮助？查看：
- 📖 [完整部署文档](README_DEPLOYMENT.md)
- 📝 [主README](README.md)
- 💬 提交Issue或联系管理员
