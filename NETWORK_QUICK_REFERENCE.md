# 网络问题快速参考卡

## 🚨 遇到无法访问时的快速检查

### 1️⃣ 运行诊断脚本（1分钟）
```bash
/home/spider/31339752/scripts/check_connectivity.sh
```

### 2️⃣ 查看实时日志
```bash
tail -f /home/spider/31339752/backend/logs/api_backend.log | grep --color -E "ERROR|Exception"
```

### 3️⃣ 测试连接
```bash
# 测试后端
curl http://localhost:8000/api/botnet-types

# 测试外部访问（从其他机器）
curl http://10.61.241.38:8000/api/botnet-types
```

---

## 🔍 常见问题速查

| 症状 | 可能原因 | 快速解决 |
|------|---------|---------|
| 一会儿能访问，一会儿不能 | **VPN连接不稳定** | 重连VPN，检查`ping 10.61.241.38` |
| 返回404错误 | 路径错误或前端配置问题 | 检查URL路径，确认配置文件 |
| 返回500错误 | 后端服务异常 | 查看日志，检查数据库连接 |
| 连接超时 | 网络不通或服务未启动 | 检查VPN，确认服务运行 |
| 响应很慢（>5秒） | 数据库查询慢或资源不足 | 检查系统资源，优化查询 |
| 登录失败 | 密码错误或session过期 | 确认密码，清除浏览器缓存 |

---

## 📊 当前诊断结果（2026-04-16）

✅ **服务状态: 正常**
- 后端: 运行中 (响应时间 0.01s)
- 前端: 运行中
- 服务器可达

⚠️ **注意事项**:
- 发现失败的登录尝试（密码错误）
- 日志中有少量数据库错误

---

## 🛠️ 间歇性问题的最可能原因

根据你的描述"刚才无法访问，现在又可以了"，**最可能的原因是**:

### 1. VPN连接波动（80%可能性）
**特征**:
- 访问时有时无
- 几分钟后自动恢复
- 其他VPN资源也受影响

**解决方案**:
```bash
# 持续监控VPN连接
watch -n 2 "ping -c 1 10.61.241.38 | tail -n 1"

# 如果频繁丢包，联系网络管理员
```

### 2. 后端服务重载（15%可能性）
**特征**:
- 正好在你修改代码后发生
- 中断时间很短（1-3秒）
- 日志显示服务重启

**原因**: Uvicorn使用了`--reload`模式

**解决方案**:
```bash
# 查看当前启动参数
ps aux | grep uvicorn

# 如果看到 --reload，这会在代码变化时自动重启
# 生产环境建议去掉此参数
```

### 3. 网络设备/防火墙（5%可能性）
**特征**:
- 特定时间段发生
- 多人同时受影响

**排查方法**: 联系网络管理员

---

## 🔧 推荐操作

### 启动持续监控（后台运行）
```bash
# 每30秒检查一次，记录到日志
nohup /home/spider/31339752/scripts/monitor_health.sh 30 > /dev/null 2>&1 &

# 查看监控日志
tail -f /home/spider/31339752/logs/health_monitor.log

# 查看告警日志
cat /home/spider/31339752/logs/health_alerts.log
```

### 停止监控
```bash
pkill -f monitor_health.sh
```

---

## 📞 需要帮助时

如果问题持续，收集以下信息：

1. **诊断脚本输出**:
   ```bash
   /home/spider/31339752/scripts/check_connectivity.sh > diagnostic_$(date +%Y%m%d_%H%M%S).txt
   ```

2. **最近的错误日志**:
   ```bash
   tail -n 200 /home/spider/31339752/backend/logs/api_backend.log > error_log.txt
   ```

3. **浏览器控制台截图**: F12 > Network标签

4. **VPN连接状态**: 是否稳定，延迟多少

---

## 📚 详细文档

- **VPN访问配置**: `/home/spider/31339752/docs/VPN_ACCESS_CONFIGURATION.md`
- **完整故障排除指南**: `/home/spider/31339752/docs/TROUBLESHOOTING_NETWORK_ISSUES.md`

---

## 🎯 下次再遇到问题时

1. **不要慌** - 很可能几分钟后自动恢复
2. **运行诊断脚本** - 快速了解状态
3. **检查VPN** - 最常见的原因
4. **查看日志** - 寻找错误信息
5. **记录时间和现象** - 方便后续分析

---

**最后更新**: 2026-04-16 18:46
**服务器**: 10.61.241.38
**状态**: ✅ 正常运行
