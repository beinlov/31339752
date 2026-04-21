# 网络访问问题诊断指南

## 当前状态分析（2026-04-16 18:44）

### ✅ 服务正常运行
```
后端进程: uvicorn运行在 0.0.0.0:8000 (PID 17387)
前端服务: 运行在 0.0.0.0:9000
API响应: HTTP 200 - 响应时间 0.024s
服务器负载: 正常 (0.45, 0.38, 0.26)
运行时间: 6小时27分钟
```

### 📊 日志分析

从 `api_backend.log` 可以看到：
- ✅ API请求正常响应（200 OK）
- ✅ 数据查询正常
- ⚠️ 有失败的登录尝试（密码错误）
- ⚠️ 偶尔出现无效的HTTP请求

---

## 间歇性访问失败的常见原因

### 1. **VPN连接不稳定** ⭐ 最可能

**现象**:
- 一会儿能访问，一会儿不能访问
- 刷新页面有时成功有时失败
- 浏览器显示"连接超时"或"无法访问"

**原因**:
- VPN连接断开后自动重连
- VPN路由表更新延迟
- VPN隧道拥塞

**验证方法**:
```bash
# 检查VPN连接状态
ip route | grep 10.61.241
ping -c 4 10.61.241.38

# 持续监控VPN连接
watch -n 1 "ping -c 1 10.61.241.38 | tail -n 1"
```

**解决方案**:
- 保持VPN连接稳定
- 配置VPN自动重连
- 使用更稳定的VPN服务器节点

---

### 2. **防火墙/安全策略**

**现象**:
- 某些IP地址可以访问，某些不能
- 特定时间段访问正常

**可能原因**:
- 服务器防火墙规则
- 网络安全设备（IDS/IPS）
- IP白名单策略

**验证方法**:
```bash
# 检查防火墙状态
sudo iptables -L -n | grep 8000
sudo firewall-cmd --list-all

# 检查连接
ss -tunlp | grep :8000
```

**解决方案**:
```bash
# 如果需要开放端口（需要管理员权限）
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=9000/tcp
sudo firewall-cmd --reload
```

---

### 3. **后端服务自动重启**

**现象**:
- 短暂无法访问（10-30秒）
- 之后自动恢复

**原因**:
- Uvicorn的`--reload`模式检测到代码变化
- 内存不足导致进程被OOM Killer终止
- 服务崩溃后自动重启

**验证方法**:
```bash
# 查看服务重启记录
journalctl -u backend --since "1 hour ago" | grep -i restart

# 检查内存使用
free -h
ps aux --sort=-%mem | head -n 10

# 查看OOM日志
dmesg | grep -i "out of memory"
```

**当前状态**:
```
✅ 服务使用 --reload 模式运行
⚠️ 代码修改会触发自动重启（1-2秒中断）
```

**解决方案**:
- 生产环境移除`--reload`参数
- 监控内存使用情况
- 使用进程管理器（systemd/supervisor）

---

### 4. **数据库连接问题**

**现象**:
- API返回500错误
- 日志显示数据库错误

**从日志中发现**:
```
ERROR:main:Database error in get_province_amounts:
ERROR:main:Database error in get_world_amounts:
```

**可能原因**:
- MySQL连接池耗尽
- 数据库查询超时
- 数据库连接中断

**验证方法**:
```bash
# 检查MySQL状态
mysql -u botnet -p -e "SHOW PROCESSLIST;"
mysql -u botnet -p -e "SHOW STATUS LIKE 'Threads%';"

# 检查数据库连接
netstat -an | grep 3306 | wc -l
```

**解决方案**:
```python
# 增加数据库连接池大小
# 在 backend/main.py 或数据库配置中
DATABASE_CONFIG = {
    "pool_size": 20,  # 增加连接池
    "max_overflow": 10,
    "pool_timeout": 30,
    "pool_recycle": 3600  # 1小时回收连接
}
```

---

### 5. **浏览器/前端缓存问题**

**现象**:
- 清除缓存后问题消失
- 使用隐身模式正常

**解决方案**:
- 清除浏览器缓存（Ctrl+Shift+Delete）
- 硬刷新页面（Ctrl+Shift+R）
- 禁用浏览器扩展

---

## 诊断工具脚本

### 快速诊断脚本

创建文件: `/home/spider/31339752/scripts/check_connectivity.sh`

```bash
#!/bin/bash

echo "=========================================="
echo "系统诊断工具 - $(date)"
echo "=========================================="

# 1. 检查后端服务
echo -e "\n[1/6] 检查后端服务..."
if curl -s http://localhost:8000/api/botnet-types > /dev/null; then
    echo "✅ 后端服务正常 (localhost:8000)"
else
    echo "❌ 后端服务异常"
fi

# 2. 检查前端服务
echo -e "\n[2/6] 检查前端服务..."
if curl -s http://localhost:9000 > /dev/null; then
    echo "✅ 前端服务正常 (localhost:9000)"
else
    echo "❌ 前端服务异常"
fi

# 3. 检查进程
echo -e "\n[3/6] 检查运行进程..."
ps aux | grep -E "uvicorn|vite" | grep -v grep | awk '{print $2, $11}'

# 4. 检查端口监听
echo -e "\n[4/6] 检查端口监听..."
netstat -tuln | grep -E "8000|9000"

# 5. 检查最近的错误日志
echo -e "\n[5/6] 检查最近的错误..."
tail -n 20 /home/spider/31339752/backend/logs/api_backend.log | grep -i "error\|exception" || echo "无最近错误"

# 6. 系统资源
echo -e "\n[6/6] 系统资源使用..."
echo "内存使用: $(free -h | awk 'NR==2{print $3"/"$2}')"
echo "CPU负载: $(uptime | awk -F'load average:' '{print $2}')"
echo "磁盘使用: $(df -h / | awk 'NR==2{print $5}')"

echo -e "\n=========================================="
echo "诊断完成"
echo "=========================================="
```

### 使用方法:
```bash
chmod +x /home/spider/31339752/scripts/check_connectivity.sh
/home/spider/31339752/scripts/check_connectivity.sh
```

---

## 监控方案

### 1. **持续监控脚本**

创建文件: `/home/spider/31339752/scripts/monitor_health.sh`

```bash
#!/bin/bash

LOG_FILE="/home/spider/31339752/logs/health_monitor.log"
mkdir -p $(dirname "$LOG_FILE")

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 检查后端
    if curl -s --max-time 5 http://localhost:8000/api/botnet-types > /dev/null; then
        STATUS="OK"
    else
        STATUS="FAILED"
        # 发送告警（可以集成钉钉/邮件）
        echo "[$TIMESTAMP] ❌ 后端服务异常" >> "$LOG_FILE"
    fi
    
    echo "[$TIMESTAMP] Backend: $STATUS" >> "$LOG_FILE"
    
    # 每30秒检查一次
    sleep 30
done
```

### 2. **实时日志监控**

```bash
# 监控错误日志
tail -f /home/spider/31339752/backend/logs/api_backend.log | grep --color=auto -E "ERROR|Exception|WARNING"

# 监控API响应时间
while true; do
    TIME=$(curl -s -o /dev/null -w "%{time_total}" http://localhost:8000/api/botnet-types)
    echo "$(date '+%H:%M:%S') - API响应时间: ${TIME}s"
    sleep 5
done
```

---

## 建议的修复措施

### 立即执行（已完成）
- ✅ 修改前端配置指向正确的服务器IP
- ✅ 检查服务运行状态

### 短期优化
1. **创建监控脚本**（如上所示）
2. **配置日志轮转**，避免日志文件过大
3. **记录VPN连接日志**，分析断连模式

### 长期改进
1. **使用进程管理器**（systemd/supervisor）
2. **配置健康检查**和自动重启
3. **添加性能监控**（Prometheus + Grafana）
4. **配置告警通知**（钉钉/企业微信）

---

## 快速命令参考

```bash
# 检查服务状态
ps aux | grep -E "uvicorn|vite"

# 测试后端连接
curl http://localhost:8000/api/botnet-types

# 查看实时日志
tail -f /home/spider/31339752/backend/logs/api_backend.log

# 重启后端（如果需要）
pkill -f "uvicorn main:app"
cd /home/spider/31339752/backend
uvicorn main:app --host 0.0.0.0 --port 8000 &

# 检查网络连接
netstat -tuln | grep -E "8000|9000"

# 检查VPN路由
ip route | grep 10.61.241
```

---

## 联系支持

如果问题持续存在，请收集以下信息：
1. 诊断脚本输出
2. 最近的错误日志（`api_backend.log`）
3. VPN连接日志
4. 浏览器开发者工具的Network标签截图
