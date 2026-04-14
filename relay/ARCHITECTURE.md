# 中转服务器架构说明

## 📐 设计原则

### 代码复用原则
**不重复造轮子** - 充分利用现有成熟代码

- ✅ **复用 `changeip.py`**：已有完整的AWS EIP切换逻辑，直接复用
- ✅ **复用 C2端拉取逻辑**：`data_puller.py` 与 C2端的 `remote_puller.py` 逻辑一致
- ✅ **复用平台推送逻辑**：`data_pusher.py` 使用平台的推送接收API

### 适配器模式
**桥接现有代码与新架构**

```
┌─────────────────┐
│ relay_service   │ 主服务协调器
└────────┬────────┘
         │
    ┌────┴────────────────────┐
    │                         │
┌───▼──────────┐    ┌────────▼────────┐
│ data_puller  │    │ ip_changer      │
│ data_pusher  │    │ _adapter        │ 适配器
│ data_storage │    └────────┬────────┘
└──────────────┘             │
                      ┌──────▼────────┐
                      │  changeip.py  │ 现有代码
                      └───────────────┘
```

---

## 🏗️ 模块架构

### 核心模块（8个）

#### 1. relay_service.py (主协调器)
**职责**：
- 协调所有模块工作
- 管理拉取/推送循环
- 处理暂停/恢复逻辑
- 统计信息收集

**依赖**：
```python
from data_storage import DataStorage
from data_puller import DataPuller
from data_pusher import DataPusher
from ip_changer_adapter import IPChangerAdapter
```

#### 2. data_puller.py (C2数据拉取)
**职责**：
- 从C2端拉取数据
- 支持多C2端点
- 两阶段提交确认
- 健康检查

**与C2端交互**：
```
中转服务器                    C2端
    │                          │
    ├──GET /api/pull──────────►│
    │◄─────返回数据─────────────┤
    │                          │
    ├──POST /api/confirm──────►│
    │◄─────确认成功─────────────┤
```

#### 3. data_pusher.py (平台数据推送)
**职责**：
- 向平台推送数据
- HMAC签名生成
- 失败重试机制
- 健康检查

**与平台端交互**：
```
中转服务器                    平台服务器
    │                          │
    ├──POST /api/data-push────►│
    │  (HMAC签名)              │
    │◄─────推送确认─────────────┤
```

#### 4. data_storage.py (本地缓存)
**职责**：
- SQLite数据库管理
- 数据状态跟踪
- 统计信息维护
- 过期数据清理

**数据状态流转**：
```
pending → pushed
   ↓
failed → pending (重试) → pushed
```

#### 5. changeip.py (IP切换核心) ⭐ 复用现有代码
**职责**：
- AWS EIP池管理
- EIP申请/释放/绑定
- OpenVPN配置更新
- OpenVPN重启
- AWS路由配置

**来源**：`/home/spider/31339752/changeip.py`（原始文件）

#### 6. ip_changer_adapter.py (IP切换适配器) ⭐ 新增
**职责**：
- 封装 `changeip.py` 的功能
- 提供暂停/恢复回调接口
- 独立线程运行
- 统计信息收集

**为什么需要适配器？**
- `changeip.py` 是独立的IP切换脚本，有自己的 `main()` 循环
- `relay_service.py` 需要在IP切换时暂停数据传输
- 适配器桥接两者，提供协调机制

**适配器模式优势**：
```python
# 原始代码（changeip.py）
def main():
    while True:
        change_ip()
        time.sleep(600)

# 适配后（ip_changer_adapter.py）
class IPChangerAdapter:
    def change_ip_with_callback(self):
        self.pause_callback()      # 暂停服务
        changeip.get_new_ip()      # 调用原始代码
        changeip.associate_ip()    # 调用原始代码
        self.resume_callback()     # 恢复服务
```

#### 7. config_loader.py (配置加载)
**职责**：
- 加载JSON配置文件
- 环境变量覆盖
- 配置验证
- 默认值处理

**优先级**：
```
环境变量 > 配置文件 > 默认值
```

#### 8. health_monitor.py (健康监控)
**职责**：
- C2服务器健康检查
- 平台服务器健康检查
- 数据库状态检查
- OpenVPN连接检查
- 磁盘空间检查

---

## 🔄 工作流程

### 正常运行流程

```
启动
  │
  ├─► 启动 IP切换线程 ──┐
  │                    │
  ├─► 拉取循环 ────────┼──► 每10秒
  │   └─ 从C2拉取      │
  │   └─ 保存到DB      │
  │                    │
  ├─► 推送循环 ────────┼──► 每5秒
  │   └─ 从DB读取      │
  │   └─ 推送到平台    │
  │                    │
  └─► 维护循环 ────────┼──► 定期
      └─ 清理过期      │
      └─ 重试失败      │
                       │
                  每10分钟切换IP
```

### IP切换流程（关键）

```
IP切换线程每10分钟触发
  │
  ├─► 1. 调用 pause_callback()
  │       └─► relay_service.paused = True
  │       └─► 拉取/推送循环跳过
  │
  ├─► 2. 等待AWS连通性
  │
  ├─► 3. 获取新EIP (changeip.get_new_ip)
  │
  ├─► 4. 绑定EIP (changeip.associate_ip)
  │
  ├─► 5. 更新OpenVPN配置 (changeip.update_ovpn_config)
  │
  ├─► 6. 重启OpenVPN (changeip.restart_openvpn)
  │
  ├─► 7. 等待网络恢复 (30秒)
  │
  └─► 8. 调用 resume_callback()
          └─► relay_service.paused = False
          └─► 拉取/推送循环恢复
```

---

## 🧩 为什么采用适配器模式？

### 问题场景
1. **现有代码**：`changeip.py` 是一个独立的脚本，有自己的主循环
2. **新需求**：IP切换时需要暂停数据传输，避免网络中断导致的失败
3. **设计原则**：不修改现有的 `changeip.py` 代码（保持稳定性）

### 解决方案对比

#### ❌ 方案1：直接修改 changeip.py
```python
# 需要在changeip.py中添加回调机制
def change_ip(pause_callback, resume_callback):
    pause_callback()
    # ... 切换逻辑
    resume_callback()
```
**缺点**：
- 破坏原始代码的独立性
- 增加维护复杂度
- 其他地方使用 `changeip.py` 会受影响

#### ❌ 方案2：重新实现IP切换
```python
# 创建新的ip_manager.py，重新实现所有逻辑
class IPManager:
    def get_new_ip(self): ...
    def associate_ip(self): ...
    # ... 重复200+行代码
```
**缺点**：
- 重复造轮子
- 维护两份代码
- 容易产生不一致

#### ✅ 方案3：适配器模式（当前方案）
```python
# 创建轻量级适配器
class IPChangerAdapter:
    def change_ip_with_callback(self):
        self.pause_callback()
        changeip.get_new_ip()      # 复用现有代码
        changeip.associate_ip()    # 复用现有代码
        self.resume_callback()
```
**优点**：
- 保持原始代码不变
- 仅添加协调逻辑（约150行）
- 清晰的职责分离
- 易于测试和维护

---

## 📦 代码复用统计

| 模块 | 代码来源 | 行数 | 说明 |
|------|---------|------|------|
| changeip.py | 直接复用 | 196行 | 完整的IP切换逻辑 |
| data_puller.py | 参考C2端 | 198行 | 类似 remote_puller.py |
| data_pusher.py | 参考平台 | 236行 | 使用平台推送API |
| data_storage.py | 新增 | 280行 | SQLite缓存管理 |
| ip_changer_adapter.py | 新增 | 150行 | 适配器桥接 |
| relay_service.py | 新增 | 342行 | 主协调器 |
| config_loader.py | 新增 | 173行 | 配置管理 |
| health_monitor.py | 新增 | 300行 | 健康监控 |

**复用率**：196行 / 1875行 ≈ 10.5%
**复用代码价值**：IP切换核心逻辑（最复杂的部分）

---

## 🎯 设计优势

### 1. 模块化
- 每个模块职责单一
- 低耦合高内聚
- 易于测试

### 2. 可维护性
- 清晰的代码结构
- 复用成熟代码
- 完善的文档

### 3. 可扩展性
- 支持多C2端点
- 支持多种推送目标
- 易于添加新功能

### 4. 稳定性
- 复用经过验证的代码
- 完善的错误处理
- 健康监控机制

---

## 🔧 未来优化方向

### 短期
- [ ] 添加更多监控指标
- [ ] 优化重试策略
- [ ] 性能调优

### 长期
- [ ] 支持更多云服务商（阿里云、腾讯云）
- [ ] 支持集群模式（多个中转服务器）
- [ ] 添加Web管理界面

---

## 📚 相关文档

- [README.md](README.md) - 项目概述
- [README_DEPLOYMENT.md](README_DEPLOYMENT.md) - 详细部署文档
- [QUICK_START.md](QUICK_START.md) - 快速开始指南

---

## 总结

中转服务器采用**适配器模式**，充分复用现有的 `changeip.py` 代码，通过轻量级适配器实现与主服务的协调。这种设计既保持了代码的稳定性，又满足了新的业务需求，是一个典型的**面向对象设计模式**应用案例。
