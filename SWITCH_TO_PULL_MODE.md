# 切换到拉取模式指南

## 📋 概述

本文档指导如何从推送模式切换回拉取模式。

---

## 🔄 两种模式对比

### 推送模式 (Push Mode)

```
C2端 ──► 中转服务器 ──► 平台服务器
        (relay)        (被动接收)
```

**特点**：
- ✅ 平台服务器无需访问C2端网络
- ✅ 中转服务器动态切换IP，安全性高
- ❌ 需要额外维护中转服务器
- ❌ 架构复杂度高

### 拉取模式 (Pull Mode)

```
C2端 ◄── 平台服务器
        (主动拉取)
```

**特点**：
- ✅ 架构简单，易于维护
- ✅ 不需要中转服务器
- ❌ 需要平台服务器能访问C2端（可能需要VPN）
- ❌ 平台IP暴露给C2端

---

## 🛠️ 切换步骤

### 步骤1: 停止中转服务器（如果正在运行）

```bash
# 查找中转服务器进程
ps aux | grep relay_service.py

# 停止服务
pkill -f relay_service.py

# 确认已停止
ps aux | grep relay_service.py
```

### 步骤2: 配置平台服务器为拉取模式

#### 方法A: 使用环境变量（推荐）

```bash
cd /home/spider/31339752/backend

# 1. 创建拉取模式环境变量文件
cat > .env.pull << 'EOF'
# 设置为拉取模式
export DATA_TRANSFER_MODE="pull"

# 启用远程拉取
export ENABLE_REMOTE_PULLING="true"
EOF

# 2. 应用环境变量
source .env.pull

# 3. 启动平台服务器
python3 main.py
```

#### 方法B: 直接修改config.py（不推荐）

```bash
cd /home/spider/31339752/backend

# 编辑config.py
vim config.py

# 找到第391行，修改为：
DATA_TRANSFER_MODE = 'pull'  # 默认就是pull，确保没被改成push
```

### 步骤3: 配置C2端点

编辑 `backend/config.py`，确保 `C2_ENDPOINTS` 配置正确：

```python
# backend/config.py

C2_ENDPOINTS = [
    {
        'id': 'c2-server-1',
        'url': 'http://10.8.0.1:8888',  # C2端URL（通过VPN访问）
        'api_key': 'KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4',  # 与C2端一致
        'botnet_type': 'utg_q_008',  # 与C2端一致
        'enabled': True,
        'description': 'C2服务器1'
    }
]
```

### 步骤4: 确保网络连通

**如果C2端在内网**，需要通过VPN连接：

```bash
# 检查OpenVPN是否运行
systemctl status openvpn@client

# 如果未运行，启动VPN
sudo systemctl start openvpn@client

# 测试连通性
ping 10.8.0.1

# 测试C2 API
curl -H "X-API-Key: KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4" \
     http://10.8.0.1:8888/health
```

### 步骤5: 启动平台服务器

```bash
cd /home/spider/31339752/backend

# 停止旧服务（如果在运行）
pkill -f "python3 main.py"

# 方式1: 使用环境变量启动
source .env.pull
python3 main.py

# 方式2: 直接启动（如果已修改config.py）
python3 main.py
```

### 步骤6: 验证拉取模式

```bash
# 检查日志
tail -f /home/spider/31339752/backend/logs/app.log

# 应该看到类似输出：
# [INFO] 数据传输模式: pull
# [INFO] 启用远程拉取: True
# [INFO] C2端点数量: 1
# [INFO] 正在从 c2-server-1 拉取数据...
# [INFO] 拉取成功: 100 条记录
```

---

## ✅ 验证清单

完成切换后，请检查以下项目：

- [ ] 中转服务器已停止（`ps aux | grep relay_service` 无结果）
- [ ] 平台服务器环境变量 `DATA_TRANSFER_MODE=pull`
- [ ] 平台服务器能访问C2端（网络连通）
- [ ] C2端点配置正确（URL、API密钥、botnet_type）
- [ ] 平台服务器成功拉取到数据
- [ ] 数据库中有新增记录

---

## 🔍 故障排查

### 问题1: 平台服务器无法连接C2端

**错误信息**：
```
ConnectionError: Failed to connect to http://10.8.0.1:8888
```

**解决方法**：
```bash
# 1. 检查VPN连接
systemctl status openvpn@client

# 2. 检查网络连通性
ping 10.8.0.1

# 3. 检查C2端服务是否运行
curl http://10.8.0.1:8888/health

# 4. 如果VPN未运行，启动它
sudo systemctl start openvpn@client
```

### 问题2: API密钥认证失败

**错误信息**：
```
401 Unauthorized
```

**解决方法**：
```bash
# 检查平台端config.py中的API密钥
cd /home/spider/31339752/backend
grep "api_key" config.py

# 检查C2端配置
cd /home/spider/31339752/pull_mode
grep "api_key" config.production.json

# 确保两边一致：KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4
```

### 问题3: botnet_type不匹配

**错误信息**：
```
无数据或数据未入库
```

**解决方法**：
```bash
# 检查C2端的botnet_type
cd /home/spider/31339752/pull_mode
grep "botnet_type" config.production.json
# 输出: "botnet_type": "utg_q_008"

# 检查平台端C2_ENDPOINTS配置
cd /home/spider/31339752/backend
grep "botnet_type" config.py
# 确保C2_ENDPOINTS中的botnet_type也是 "utg_q_008"
```

### 问题4: 数据传输模式未切换

**症状**：平台服务器仍显示push模式

**解决方法**：
```bash
# 1. 清除可能存在的push模式环境变量
unset DATA_TRANSFER_MODE

# 2. 重新设置为pull模式
export DATA_TRANSFER_MODE="pull"

# 3. 验证
python3 -c "import os; print('模式:', os.environ.get('DATA_TRANSFER_MODE', 'pull'))"

# 4. 重启平台服务器
pkill -f "python3 main.py"
python3 main.py
```

---

## 📊 配置文件对比

### 拉取模式配置文件

| 文件 | 用途 | 状态 |
|------|------|------|
| `backend/config.py` | 平台服务器配置 | ✅ 需要检查 |
| `backend/.env.pull` | 拉取模式环境变量 | ✅ 可选使用 |
| `pull_mode/config.production.json` | C2端配置 | ✅ 保持不变 |
| `relay/*` | 中转服务器相关 | ❌ 不使用 |

### 推送模式配置文件（不再使用）

| 文件 | 状态 |
|------|------|
| `backend/.env.push` | ❌ 不使用 |
| `relay/relay_config.json` | ❌ 不使用 |
| `relay/relay_service.py` | ❌ 不启动 |

---

## 🚀 快速切换脚本

创建快速切换脚本：

```bash
cat > /home/spider/31339752/switch_to_pull.sh << 'EOF'
#!/bin/bash

echo "========================================="
echo "切换到拉取模式"
echo "========================================="

# 1. 停止中转服务器
echo "1. 停止中转服务器..."
pkill -f relay_service.py
sleep 2

# 2. 停止平台服务器
echo "2. 停止平台服务器..."
pkill -f "python3 main.py"
sleep 2

# 3. 设置环境变量
echo "3. 设置拉取模式..."
export DATA_TRANSFER_MODE="pull"
export ENABLE_REMOTE_PULLING="true"

# 4. 启动平台服务器
echo "4. 启动平台服务器..."
cd /home/spider/31339752/backend
python3 main.py &

echo "========================================="
echo "✅ 切换完成！"
echo "数据传输模式: pull"
echo "查看日志: tail -f /home/spider/31339752/backend/logs/app.log"
echo "========================================="
EOF

chmod +x /home/spider/31339752/switch_to_pull.sh
```

**使用方法**：
```bash
/home/spider/31339752/switch_to_pull.sh
```

---

## 📝 注意事项

### 1. 网络要求

- ✅ 拉取模式需要平台服务器能直接访问C2端
- ✅ 通常需要VPN连接到C2端内网
- ✅ 确保防火墙允许访问C2端口（默认8888）

### 2. 数据一致性

- ✅ 切换模式不会丢失数据
- ✅ 已入库的数据保持不变
- ✅ 切换后将拉取C2端的新数据

### 3. 中转服务器

- ✅ 切换到拉取模式后可以停止中转服务器
- ✅ 中转服务器的数据库可以保留（以防回退）
- ✅ 如需回到推送模式，重新启动中转服务器即可

---

## 🔄 如何回退到推送模式

如果需要切换回推送模式：

```bash
# 1. 设置推送模式
export DATA_TRANSFER_MODE="push"
export PUSH_SIGNATURE_SECRET="你的签名密钥"
export PUSH_API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"

# 2. 重启平台服务器
cd /home/spider/31339752/backend
pkill -f "python3 main.py"
python3 main.py &

# 3. 启动中转服务器
cd /home/spider/31339752/relay
./start_relay.sh
```

---

## ✅ 总结

### 拉取模式优势

1. ✅ 架构简单，无需中转服务器
2. ✅ 维护成本低
3. ✅ 延迟低，数据实时性好

### 适用场景

- ✅ 平台服务器能访问C2端网络（通过VPN）
- ✅ 不需要频繁切换IP
- ✅ 追求架构简单和维护方便

### 下一步

1. 按照步骤完成切换
2. 验证数据正常拉取
3. 监控日志确保稳定运行
