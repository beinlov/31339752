## 🛠️ 首次配置（仅需执行一次）

> ⚠️ **重要提示**：以下步骤仅在首次部署时需要执行，配置完成后每次演示只需要执行「快速演示流程」部分即可。

### 1. 系统要求

**硬件要求**:
```
CPU: 4核心以上
内存: 8GB以上
磁盘: 20GB可用空间
网络: 稳定的本地网络
```

**软件要求**:
```bash
# 操作系统
Linux (Ubuntu 20.04+, CentOS 7+) 或 Windows with WSL2

# Docker 环境
Docker: 20.10+
Docker Compose: 1.29+
Python: 3.8+
```

### 2. 安装Docker

#### Ubuntu/Debian
```bash
# 更新包索引
sudo apt-get update

# 安装依赖
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加Docker仓库
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加当前用户到docker组
sudo usermod -aG docker $USER
newgrp docker

# 验证安装
docker --version
docker-compose --version
```

#### CentOS/RHEL
```bash
# 安装依赖
sudo yum install -y yum-utils

# 添加Docker仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
docker-compose --version
```

### 3. 准备测试目录

```bash
# 进入项目目录
cd /home/spider/31339752/backend/suppression_scripts/docker-cluster-10\ -\ 副本

# 检查必要文件
ls -la

# 应该看到以下文件:
# - Dockerfile
# - docker-compose.yml
# - kademlia_node.py
# - sybil.py
# - verify_sybil_attack.py
```

### 4. 配置 docker-compose.yml（重要！）

由于目录名包含中文和空格，需要修改配置文件：

```bash
cd /home/spider/31339752/backend/suppression_scripts/docker-cluster-10\ -\ 副本

# 备份原始文件
cp docker-compose.yml docker-compose.yml.bak
```

#### 4.1 修改版本和镜像配置

在 `docker-compose.yml` 开头添加版本声明，并修改所有服务配置：

```yaml
version: '3.3'

networks:
  dht_net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16

services:
  node-1:
    image: dht-node:latest  # 改为使用镜像而不是 build
    container_name: node-1
    hostname: node-1
    networks:
      - dht_net  # 改为列表格式
    entrypoint: ["python3", "main.py"]  # 添加 entrypoint
    environment:
      - PORT=8000
      - NODE_ID_HEX=00623457

  attacker:
    image: dht-node:latest
    container_name: attacker
    networks:
      - dht_net
    entrypoint: ["sleep", "infinity"]  # attacker 使用 sleep
    depends_on: [node-1]

  # 其他节点类似配置...
```

**关键修改点**：
1. ✅ 添加 `version: '3.3'`
2. ✅ 所有 `build: .` 改为 `image: dht-node:latest`
3. ✅ 所有 `networks: dht_net:` 改为 `networks: - dht_net`
4. ✅ 所有节点添加 `entrypoint: ["python3", "main.py"]`
5. ✅ attacker 使用 `entrypoint: ["sleep", "infinity"]`

### 5. 构建 Docker 镜像

#### 5.1 创建 Dockerfile.grafana（使用本地镜像避免网络问题）

```bash
cat > Dockerfile.grafana << 'EOF'
FROM grafana/grafana:10.0.6-ubuntu

USER root
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8000/udp
CMD ["python3", "main.py"]
EOF
```

#### 5.2 构建镜像

```bash
# 使用 Dockerfile.grafana 构建（避免网络拉取失败）
docker build -f Dockerfile.grafana -t dht-node:latest .

# 验证镜像
docker images | grep dht-node

# 预期输出:
# dht-node    latest    xxxxxxxxxxxx    Just now    770MB
```

### 6. 网络问题排查（如遇到问题）

#### 6.1 清理旧网络
```bash
# 查看现有网络
docker network ls | grep dht

# 如果存在旧网络，删除它
docker network rm docker-cluster-10-_dht_net
docker network rm dht_test_dht_net
```

#### 6.2 确保没有旧容器
```bash
# 停止并删除所有相关容器
docker-compose -p dht_test down
docker ps -a | grep dht | awk '{print $1}' | xargs docker rm -f 2>/dev/null
```

---

## 🎬 每次大屏演示快速流程

> 💡 **演示前准备**：确保已完成上述「首次配置」，每次演示只需执行以下步骤。

```
总用时：约 3-5 分钟
├─ 步骤1: 启动DHT网络 (30秒)
├─ 步骤2: 验证网络状态 (30秒)
├─ 步骤3: 启动女巫攻击 (1分钟)
├─ 步骤4: 查看污染效果 (30秒)
├─ 步骤5: 验证攻击成功 (1分钟)
└─ 步骤6: 清理环境 (30秒)
```

---

## 🚀 演示步骤详解

### 📍 步骤1: 启动 DHT 网络（30秒）

#### 1.1 进入项目目录
```bash
cd /home/spider/31339752/backend/suppression_scripts/docker-cluster-10\ -\ 副本
```

#### 1.2 启动所有容器
```bash
# 使用项目名称启动（重要！）
docker-compose -p dht_test up -d

# 等待容器启动
sleep 5
```

#### 1.3 验证容器状态
```bash
# 查看所有容器
docker-compose -p dht_test ps

# 预期输出（11个容器全部 Up）:
# NAME                  COMMAND              STATUS
# node-1                python3 main.py      Up
# attacker              sleep infinity       Up
# dht_test_node-2_1     python3 main.py      Up
# dht_test_node-3_1     python3 main.py      Up
# ...
# dht_test_node-10_1    python3 main.py      Up
```

#### 1.4 查看初始路由表（展示给观众）
```bash
# 查看 node-1 的路由表（攻击前状态）
docker logs node-1 2>&1 | tail -15

# 预期看到类似输出:
# ==================== Routing Table (My ID: 00623457) ====================
# Total Peers: 8
#   Bucket 21: [00547832]
#   Bucket 22: [00275278, 00237418]
#   Bucket 23: [00986574, 00fd6752, 0097ad54, 008a5d3a, 008578d7]
# =================================================================
```

**💬 讲解要点**：
- ✅ DHT 网络包含 10 个正常节点 + 1 个攻击者容器
- ✅ node-1 是种子节点，其他节点通过它加入网络
- ✅ 初始状态：node-1 的路由表只有 **8 个真实节点**
- ✅ 只有 **3 个 K-bucket** 被填充

---

### 📍 步骤2: 验证网络连通性（30秒）

#### 2.1 测试网络连通（可选，时间紧张可跳过）
```bash
# 快速验证：查看 node-1 是否接收到其他节点的连接
docker logs node-1 2>&1 | grep -i "Total Peers" | tail -1

# 预期输出：Total Peers: 8 或更多
```

#### 2.2 快速检查所有节点状态
```bash
# 统计运行中的容器数量
docker ps --filter name=node --format "{{.Names}}" | wc -l

# 预期输出: 11 (10个节点 + 1个attacker)
```

**💬 讲解要点**：
- ✅ 所有节点已成功启动并相互发现
- ✅ DHT 网络处于正常运行状态
- ✅ 现在可以开始攻击演示

---

### 📍 步骤3: 启动女巫攻击（1分钟）

#### 3.1 方法1: 使用前端界面（推荐）

```bash
# 1. 确保后端服务运行
cd /home/spider/31339752/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8080

# 2. 启动前端
cd /home/spider/31339752/fronted
npm start

# 3. 打开浏览器
# http://localhost:3000

# 4. 进入界面操作
抑制阻断策略 → 女巫攻击 → Docker女巫攻击测试
目标节点: node-1
每个Bucket攻击节点数: 8
测试描述: Docker环境测试
点击: 🚀 启动Docker测试
```

#### 3.2 方法2: 使用API直接调用

```bash
# 发送启动请求
curl -X POST "http://localhost:8080/api/sybil-attack/test/docker/start" \
  -H "Content-Type: application/json" \
  -d '{
    "target_node": "node-1",
    "attack_nodes_per_bucket": 8,
    "description": "Docker环境测试"
  }'

# 预期响应:
{
  "status": "success",
  "message": "Docker女巫攻击测试已启动",
  "task_id": "sybil-test-1715420123"
}
```

#### 3.3 方法3: 直接执行攻击脚本（推荐用于演示）

```bash
# 在后台启动攻击脚本
docker exec attacker bash -c "cd /app && python3 sybil.py 2>&1" &

# 记录进程ID（可选）
ATTACK_PID=$!

# 立即查看攻击日志（展示给观众）
sleep 2
docker exec attacker bash -c "cd /app && tail -f /proc/\$(pgrep -f sybil.py)/fd/1" 2>/dev/null || echo "攻击正在进行中..."
```

#### 3.4 实时观察攻击进度（演示重点）

```bash
# 方式1: 查看攻击节点输出（推荐）
watch -n 2 'docker logs node-1 2>&1 | grep "Total Peers" | tail -1'

# 方式2: 手动刷新查看
for i in {1..30}; do
  echo "=== 第 $i 次检查 ==="
  docker logs node-1 2>&1 | grep "Total Peers" | tail -1
  sleep 2
done

# 预期看到节点数量快速增长:
# Total Peers: 8    -> 攻击前
# Total Peers: 45   -> 10秒后
# Total Peers: 89   -> 20秒后
# Total Peers: 151  -> 30秒后（攻击完成）
```

**💬 讲解要点**：
- 🎯 攻击脚本会生成 **256 个 Sybil 节点**
- 🎯 这些节点的 NodeID 是**精心计算**的，分布在所有 K-bucket 中
- 🎯 每个 bucket 生成 8 个节点，覆盖 32 个 bucket（Bucket #0-31）
- 🎯 攻击节点使用**相同的 IP**（attacker 容器）但**不同的端口**
- ⏱️ 整个过程约需 **30-60 秒**

---

### 📍 步骤4: 查看路由表污染效果（30秒）

#### 4.1 等待攻击完成
```bash
# 等待 60 秒确保攻击完成
echo "等待女巫攻击完成..."
sleep 60
```

#### 4.2 查看污染后的路由表（关键演示点）
```bash
# 查看 node-1 的完整路由表
docker logs node-1 2>&1 | tail -40

# 预期输出（路由表被完全污染）:
# ==================== Routing Table (My ID: 00623457) ====================
# Total Peers: 151  ← 从 8 增加到 151！
#   Bucket  0: [00623456]  ← 所有 bucket 都被填充
#   Bucket  1: [00623454, 00623455]
#   Bucket  2: [00623453, 00623452, 00623451]
#   ...
#   Bucket 31: [9f2d178e, e41ea5f9, adc374c5, a09ae7b6, ce075b25]
# =================================================================
```

#### 4.3 对比分析（向观众展示）

**攻击前后对比表**：

| 指标 | 攻击前 | 攻击后 | 变化 |
|------|--------|--------|------|
| **总节点数** | 8 | 151 | 📈 **+1787%** |
| **活跃 Bucket** | 3 | 32 | 📈 **所有 bucket 被污染** |
| **真实节点比例** | 100% | 5.3% | ⚠️ **94.7% 是 Sybil 节点** |

**💬 讲解要点**：
- ✅ 路由表节点数从 8 增加到 151（**18 倍**）
- ✅ 所有 32 个 K-bucket 都被 Sybil 节点填充
- ✅ 真实节点被 Sybil 节点"淹没"
- ⚠️ 此时 node-1 已无法有效区分真实节点和攻击节点

---

### 📍 步骤5: 验证攻击成功（1分钟）

#### 5.1 运行验证脚本（关键验证）

```bash
# 使用验证脚本测试攻击效果
docker exec attacker bash -c "cd /app && NODE_ID_HEX=ffffffff python3 verify_sybil_attack.py 2>&1 | head -100"

# 预期输出（重点展示）:
# ======================================================================
# 🔍 女巫攻击效果验证
# ======================================================================
# 
# 📡 测试 1: 直接 PING node-1（不依赖路由表）
# ✅ 直接 PING 成功 - node-1 响应了
#    响应节点 ID: 0x00623457
#    结论: 直接通信不受女巫攻击影响
# 
# 📡 测试 2: FIND_NODE 查询（依赖 node-1 的路由表）
# ✅ FIND_NODE 成功 - node-1 返回了 5 个节点:
# ----------------------------------------------------------------------
#   1. ID: 0x121ed3f1 | IP: 172.25.0.11 | ⚠️  疑似女巫节点
#   2. ID: 0x13be6d1a | IP: 172.25.0.11 | ⚠️  疑似女巫节点
#   3. ID: 0x15e5e971 | IP: 172.25.0.11 | ⚠️  疑似女巫节点
#   4. ID: 0x184ddecd | IP: 172.25.0.11 | ⚠️  疑似女巫节点
#   5. ID: 0x1d106fca | IP: 172.25.0.11 | ⚠️  疑似女巫节点
# ----------------------------------------------------------------------
# 
# 📊 统计结果:
#    合法节点数量: 0
#    疑似女巫节点数量: 5
#    女巫节点占比: 100.0%
# 
# 结论: 女巫攻击成功！node-1 的路由表已被大量污染
#       node-1 在进行节点查找时会优先返回攻击节点
# ======================================================================
```

#### 5.2 验证结果说明（向观众展示）

**🎯 测试 1: 直接 PING**
- ✅ node-1 能正常响应 PING 请求
- ✅ 节点本身的功能未受影响
- 💡 说明：Sybil 攻击不影响直接通信

**⚠️ 测试 2: FIND_NODE 查询（关键测试）**
- ❌ 返回的 5 个节点 **100% 都是女巫节点**
- ❌ 所有节点都来自同一个 IP: `172.25.0.11`（attacker 容器）
- ❌ 没有返回任何真实节点
- 💡 说明：路由查询已被完全劫持

**💥 攻击影响**：
1. **路由劫持**：当其他节点通过 node-1 查找节点时，只会得到攻击者控制的节点
2. **节点隔离**：真实节点被"隐藏"，无法被新节点发现
3. **网络分割**：DHT 网络的完整性被破坏，可能导致数据丢失

---

#### 5.2 方法2: 通过API查询结果

```bash
# 获取测试任务ID
TASK_ID="sybil-test-1715420123"

# 查询测试分析结果
curl "http://localhost:8080/api/sybil-attack/test/analysis/${TASK_ID}"

# 预期响应:
{
  "status": "success",
  "data": {
    "task_id": "sybil-test-1715420123",
    "target_node": "node-1",
    "attack_result": {
      "attack_success": true,
      "pollution_rate": 0.90,
      "sybil_nodes_in_routing_table": 18,
      "total_nodes_in_routing_table": 20,
      "verify_output": "攻击成功，路由表污染率90%"
    }
  }
}
```

#### 5.3 方法3: 手动测试

```bash
# 启动一个测试节点
docker run -it --rm --network dht-network \
  -e PORT=9000 \
  -e NODE_ID_HEX=$(python3 -c "import hashlib; print(hashlib.sha256(b'test-node').hexdigest())") \
  -e BOOTSTRAP_HOST=node-1 \
  -e BOOTSTRAP_PORT=8000 \
  dht-node:latest bash

# 在容器内执行测试
python3 << 'EOF'
import requests
import json

# 请求邻居节点
response = requests.post('http://node-1:8000/find_node', json={
    'node_id': 'test',
    'target_id': 'a' * 64,
    'sender_ip': '172.18.0.100',
    'sender_port': 9000
})

data = response.json()
nodes = data.get('nodes', [])

print(f"\n收到 {len(nodes)} 个节点:")
for i, node in enumerate(nodes):
    ip = node.get('ip')
    port = node.get('port')
    # 检查是否是攻击者IP
    if ip.startswith('172.18.0.11'):  # attacker容器的IP
        print(f"{i+1}. {ip}:{port} [攻击节点]")
    else:
        print(f"{i+1}. {ip}:{port} [真实节点]")

# 统计污染率
sybil_count = sum(1 for n in nodes if n.get('ip', '').startswith('172.18.0.11'))
pollution_rate = sybil_count / len(nodes) * 100 if nodes else 0
print(f"\n污染率: {pollution_rate:.1f}% ({sybil_count}/{len(nodes)})")
EOF

# 退出容器
exit
```

### 阶段6: 收集数据和日志

#### 6.1 导出所有容器日志
```bash
# 创建日志目录
mkdir -p test-results/logs

# 导出所有节点日志
for i in {1..10}; do
  docker-compose logs node-$i > test-results/logs/node-$i.log
done

# 导出攻击者日志
docker-compose logs attacker > test-results/logs/attacker.log

echo "日志已导出到 test-results/logs/"
```

#### 6.2 导出测试报告
```bash
# 通过API获取完整报告
curl "http://localhost:8080/api/sybil-attack/test/analysis/${TASK_ID}" \
  | jq '.' > test-results/attack-report.json

echo "测试报告已保存到 test-results/attack-report.json"
```

#### 6.3 生成性能统计
```bash
# 统计容器资源使用
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
  > test-results/resource-usage.txt

echo "资源使用统计已保存到 test-results/resource-usage.txt"
```

### 📍 步骤6: 清理环境（30秒）

#### 6.1 停止所有容器
```bash
# 停止并删除所有容器
docker-compose -p dht_test down

# 预期输出:
# Stopping dht_test_node-10_1 ... done
# Stopping dht_test_node-9_1  ... done
# ...
# Stopping node-1             ... done
# Removing containers...
# Removing network dht_test_dht_net
```

#### 6.2 验证清理完成
```bash
# 确认容器已全部停止
docker ps | grep dht

# 应该没有输出，说明清理成功
```

#### 6.3 保留镜像以便下次演示
```bash
# 验证镜像仍然存在
docker images | grep dht-node

# 预期输出:
# dht-node    latest    xxxxxxxxxxxx    X minutes ago    770MB

# ✅ 镜像保留，下次演示直接启动即可
```

**💬 总结要点**：
- ✅ 演示完成，所有容器已清理
- ✅ Docker 镜像已保留，下次演示无需重新构建
- ✅ 整个演示过程用时约 **3-5 分钟**

---

## 🎭 演示脚本（一键执行）

### 完整演示脚本

创建一个自动化演示脚本，适合快速展示：

```bash
cat > demo_attack.sh << 'DEMO_SCRIPT'
#!/bin/bash

set -e

PROJECT_DIR="/home/spider/31339752/backend/suppression_scripts/docker-cluster-10 - 副本"
cd "$PROJECT_DIR"

echo "========================================="
echo "   DHT 女巫攻击 - 自动演示脚本"
echo "========================================="
echo ""

# 步骤1: 启动网络
echo "📍 步骤1/6: 启动 DHT 网络..."
docker-compose -p dht_test up -d
sleep 10
echo "✅ 网络启动完成"
echo ""

# 查看初始状态
echo "📊 攻击前状态:"
docker logs node-1 2>&1 | grep "Total Peers" | tail -1
echo ""

read -p "按回车继续启动攻击..."

# 步骤2: 启动攻击
echo "📍 步骤2/6: 启动女巫攻击（256个节点）..."
docker exec -d attacker bash -c "cd /app && python3 sybil.py 2>&1"
echo "⚡ 攻击已启动"
echo ""

# 步骤3: 监控进度
echo "📍 步骤3/6: 监控攻击进度（60秒）..."
for i in {1..12}; do
  sleep 5
  PEERS=$(docker logs node-1 2>&1 | grep "Total Peers" | tail -1)
  echo "[+$((i*5))s] $PEERS"
done
echo ""

read -p "按回车查看攻击结果..."

# 步骤4: 查看结果
echo "📍 步骤4/6: 查看路由表污染情况..."
docker logs node-1 2>&1 | tail -40
echo ""

read -p "按回车执行验证测试..."

# 步骤5: 验证攻击
echo "📍 步骤5/6: 验证攻击效果..."
docker exec attacker bash -c "cd /app && NODE_ID_HEX=ffffffff python3 verify_sybil_attack.py 2>&1" | head -60
echo ""

read -p "按回车清理环境..."

# 步骤6: 清理
echo "📍 步骤6/6: 清理环境..."
docker-compose -p dht_test down
echo "✅ 清理完成"
echo ""

echo "========================================="
echo "   演示完成！"
echo "========================================="
DEMO_SCRIPT

chmod +x demo_attack.sh
```

### 运行演示脚本

```bash
# 执行自动化演示
./demo_attack.sh

# 脚本会在关键步骤暂停，等待按回车继续
# 适合在演讲时使用，可以边讲解边演示
```

---

## 📊 演示数据展示方案

### 方案1: 终端实时展示（推荐）

```bash
# 使用 watch 命令实时刷新路由表
watch -n 2 'docker logs node-1 2>&1 | tail -40'

# 优点：简单直观，实时更新
# 适合：技术演讲、小型展示
```

### 方案2: 分屏展示（专业演示）

使用 `tmux` 或 `screen` 创建多窗口展示：

```bash
# 安装 tmux
sudo apt-get install tmux

# 启动多窗口会话
tmux new-session -s dht_demo

# 窗口1: 显示 node-1 日志
tmux split-window -h
docker logs -f node-1

# 窗口2: 显示攻击进度
tmux split-window -v
watch -n 1 'docker logs node-1 2>&1 | grep "Total Peers" | tail -1'

# 窗口3: 显示容器状态
tmux split-window -v
watch -n 2 'docker-compose -p dht_test ps'

# 在不同窗口间切换: Ctrl+b 然后按方向键
```

### 方案3: 大屏展示（会议/答辩）

准备静态截图和数据：

```bash
# 1. 生成攻击前截图
docker logs node-1 2>&1 | tail -20 > screenshots/before_attack.txt

# 2. 启动攻击并等待
docker exec -d attacker bash -c "cd /app && python3 sybil.py 2>&1"
sleep 60

# 3. 生成攻击后截图
docker logs node-1 2>&1 | tail -40 > screenshots/after_attack.txt

# 4. 生成验证结果
docker exec attacker bash -c "cd /app && NODE_ID_HEX=ffffffff python3 verify_sybil_attack.py 2>&1" \
  > screenshots/verification.txt

# 5. 创建对比报告
cat > screenshots/comparison.md << 'EOF'
# DHT 女巫攻击效果对比

## 攻击前
- 总节点数: 8
- 活跃 Bucket: 3
- 真实节点占比: 100%

## 攻击后
- 总节点数: 151 (+1787%)
- 活跃 Bucket: 32 (全部)
- 真实节点占比: 5.3%
- Sybil 节点占比: 94.7%

## FIND_NODE 测试
- 返回节点数: 5
- 女巫节点数: 5 (100%)
- 真实节点数: 0 (0%)

## 结论
✅ 攻击成功！路由表已被完全污染
EOF

echo "演示截图已保存到 screenshots/ 目录"
```

---

## 🎬 演示技巧和注意事项

### 演示前准备清单

- [ ] 确认 Docker 已启动：`sudo systemctl status docker`
- [ ] 确认镜像存在：`docker images | grep dht-node`
- [ ] 确认没有旧容器：`docker ps -a | grep dht`
- [ ] 进入项目目录
- [ ] 准备演示脚本或命令历史

### 常见演示问题

#### 问题1: 容器启动失败
```bash
# 检查日志
docker-compose -p dht_test logs

# 强制重建
docker-compose -p dht_test down
docker-compose -p dht_test up -d --force-recreate
```

#### 问题2: 攻击效果不明显
```bash
# 等待更长时间（至少60秒）
sleep 60

# 检查 attacker 容器是否在运行
docker ps | grep attacker

# 查看攻击日志
docker logs attacker 2>&1 | tail -50
```

#### 问题3: 演示时间过长
```bash
# 使用预先录制的演示视频
# 或使用静态截图配合讲解
# 重点展示：攻击前后对比 + 验证结果
```

### 时间控制建议

**完整演示（5分钟）**：
- 启动网络：30秒
- 查看初始状态：30秒
- 启动攻击：30秒
- 等待+监控：1.5分钟
- 查看结果：1分钟
- 验证效果：1分钟
- 清理：30秒

**快速演示（2分钟）**：
- 预先启动网络和攻击
- 直接展示污染后的路由表

echo "========================================="
echo "  DHT女巫攻击 - Docker环境实战演示"
echo "========================================="
echo ""

# 步骤1
echo "📌 步骤1: 启动DHT网络（10个正常节点）"
docker-compose up -d
sleep 5
docker-compose ps
echo "✓ 网络启动成功"
echo ""
read -p "按回车继续..."

# 步骤2
echo "📌 步骤2: 验证网络连通性"
docker exec node-2 python3 -c "import requests; print(requests.post('http://node-1:8000/ping', json={'node_id':'test','sender_ip':'172.18.0.3','sender_port':8001}).json())"
echo "✓ 网络连通正常"
echo ""
read -p "按回车继续..."

# 步骤3
echo "📌 步骤3: 启动女巫攻击（256个恶意节点）"
docker exec -d attacker python3 /app/sybil.py
echo "✓ 攻击已启动，请观察日志..."
docker-compose logs -f attacker &
sleep 60
echo ""
read -p "按回车继续..."

# 步骤4
echo "📌 步骤4: 验证攻击效果"
docker run --rm --network dht-network -v $(pwd):/app dht-node:latest python3 /app/verify_sybil_attack.py
echo ""
read -p "按回车继续..."

# 步骤5
echo "📌 步骤5: 清理环境"
docker-compose down
echo "✓ 演示完成！"
EOF

chmod +x demo.sh
```

#### 演示脚本
```bash
# 运行演示
./demo.sh

# 演示过程会在每个步骤暂停，
# 讲解员可以在此时进行详细说明
```

---

## 🔍 故障排查

### 常见问题

#### 问题1: Docker容器无法启动
```bash
# 检查端口占用
netstat -tunlp | grep 800[0-9]

# 解决方案: 修改docker-compose.yml中的端口映射
# 或停止占用端口的进程
```

#### 问题2: 攻击节点注册失败
```bash
# 检查攻击者容器日志
docker-compose logs attacker | grep ERROR

# 常见原因:
# 1. 网络不通 - 检查docker network
# 2. 目标节点未响应 - 检查node-1日志
# 3. 脚本错误 - 检查Python版本和依赖
```

#### 问题3: 污染率低于预期
```bash
# 可能原因:
# 1. 攻击时间太短 - 增加等待时间到60-90秒
# 2. 目标节点路由表过大 - 检查K值配置
# 3. 其他节点持续刷新路由表 - 暂停其他节点
```

---

## 📈 测试数据记录表

### 测试记录模板

| 测试ID | 日期 | 目标节点 | 攻击节点数 | 污染率 | 用时 | 状态 | 备注 |
|--------|------|---------|-----------|--------|------|------|------|
| T001 | 2026-05-11 | node-1 | 256 | 90% | 135s | ✓ | 首次测试 |
| T002 | 2026-05-11 | node-2 | 256 | 85% | 142s | ✓ | 对比测试 |
| T003 | 2026-05-11 | node-1 | 512 | 95% | 268s | ✓ | 加倍测试 |

### 性能数据记录

```csv
时间戳,CPU使用率,内存使用,网络流入,网络流出,已注册节点数
16:00:00,5%,120MB,100KB/s,80KB/s,0
16:00:30,15%,180MB,500KB/s,300KB/s,64
16:01:00,20%,220MB,800KB/s,600KB/s,128
16:01:30,18%,240MB,600KB/s,400KB/s,256
16:02:00,10%,250MB,200KB/s,150KB/s,256
```

---

## 🌐 平台后台管理界面使用指南

### 访问Web管理界面

平台已集成女巫攻击测试功能，无需手动执行命令，可通过Web界面一键操作。

#### 登录平台

```
URL: http://your-server-ip:9000
默认账户:
  - 用户名: test / 密码: test123
  - 用户名: op1 / 密码: 123456
```

#### 导航到女巫攻击模块

```
主菜单 → 抑制阻断 → 女巫攻击 标签页
```

---

### Docker测试环境（界面展示）

#### 配置区域

**参数设置**：
- 🎯 **目标节点**：下拉选择框（默认：node-1）
- 🔢 **每bucket攻击节点数**：滑块控制 1-20（默认：8）
  - 实时显示总节点数计算：`8 × 32 = 256`
- 📝 **测试描述**：可选文本框

**操作按钮**：
- `🚀 启动Docker测试` - 一键启动完整测试流程
- `🔄 刷新状态` - 更新容器和任务状态

#### Docker容器状态

**运行状态显示**：
```
✅ Docker环境运行中 (11 个容器)
```

**容器列表表格**：

| 容器名称 | 状态 | 操作 |
|---------|------|------|
| node-1 | 🟢 Up | [查看日志] |
| node-2 | 🟢 Up | [查看日志] |
| ... | ... | ... |
| attacker | 🟢 Up | [查看日志] |

#### 测试任务列表

**任务历史表格**：

| 任务ID | 目标节点 | 攻击节点数 | 状态 | 启动时间 | 操作 |
|-------|---------|-----------|------|---------|------|
| sybil-docker_... | node-1 | 256 | 🟢 已完成 | 2026-05-12 10:30 | [查看结果] |
| sybil-docker_... | node-1 | 256 | 🟡 攻击中 | 2026-05-12 10:45 | [停止] |

**状态徽章说明**：
- 🔵 **准备中** - 初始化环境
- 🟡 **启动Docker** - Docker容器启动中
- 🟠 **攻击中** - 正在执行女巫攻击
- 🟣 **验证中** - 验证攻击效果
- 🟢 **已完成** - 测试成功完成
- 🔴 **失败** - 测试失败
- ⚫ **已停止** - 手动停止

#### 查看测试结果

点击"查看结果"按钮后显示弹窗：

```
女巫攻击测试结果

攻击成功: 是
验证输出:
======================================================================
🔍 女巫攻击效果验证
======================================================================

📡 测试 1: 直接 PING node-1（不依赖路由表）
✅ 直接 PING 成功 - node-1 响应了
   结论: 直接通信不受女巫攻击影响

📡 测试 2: FIND_NODE 查询（依赖 node-1 的路由表）
✅ FIND_NODE 成功 - node-1 返回了 5 个节点:
----------------------------------------------------------------------
  1. ID: 0x121ed3f1 | IP: 172.25.0.11 | ⚠️  疑似女巫节点
  2. ID: 0x13be6d1a | IP: 172.25.0.11 | ⚠️  疑似女巫节点
  3. ID: 0x15e5e971 | IP: 172.25.0.11 | ⚠️  疑似女巫节点
  4. ID: 0x184ddecd | IP: 172.25.0.11 | ⚠️  疑似女巫节点
  5. ID: 0x1d106fca | IP: 172.25.0.11 | ⚠️  疑似女巫节点
----------------------------------------------------------------------

📊 统计结果:
   合法节点数量: 0
   疑似女巫节点数量: 5
   女巫节点占比: 100.0%

结论: 女巫攻击成功！node-1 的路由表已被大量污染
======================================================================
```

---

### 真实网络环境（高级功能）

#### VPS服务器管理

**添加VPS服务器**：

点击 `➕ 添加VPS服务器` 按钮，填写表单：
- VPS名称（如：VPS-1）
- IP地址
- SSH端口（默认：22）
- 用户名（默认：root）
- 密码
- 地理位置（可选）
- 备注说明（可选）

**VPS列表表格**：

| 名称 | IP:端口 | 地理位置 | 状态 | 最后检查 | 操作 |
|------|---------|---------|------|---------|------|
| VPS-1 | 45.76.123.10:22 | 美国东海岸 | 🟢 在线 | 2分钟前 | [测试连接] [删除] |
| VPS-2 | 139.180.x.x:22 | 日本东京 | 🔴 离线 | 1小时前 | [测试连接] [删除] |

#### 分布式攻击部署

**配置表单**：
- 攻击任务名称
- 目标IP地址
- 目标端口（默认：8000）
- 总攻击节点数（默认：256）
- VPS服务器选择（复选框）
  - 自动显示：已选择 X 台VPS，每台约 Y 个节点
- 备注说明

**分布式任务表格**：

| 任务名称 | 目标 | VPS数量 | 总节点数 | 状态 | 启动时间 | 操作 |
|---------|------|---------|---------|------|---------|------|
| Attack-Test | 192.168.1.100:8000 | 3 | 256 | 🟢 运行中 | 2026-05-12 11:00 | [停止] |

---

### 使用流程

#### 快速测试（Docker环境）

1. **启动测试**
   ```
   点击 "🚀 启动Docker测试" 按钮
   ```

2. **自动执行**
   - ✅ 系统自动启动Docker容器
   - ✅ 执行女巫攻击脚本
   - ✅ 等待污染完成
   - ✅ 验证攻击效果
   - ✅ 记录测试结果

3. **查看结果**
   ```
   等待状态变为 "🟢 已完成"
   点击 "查看结果" 按钮
   ```

4. **清理环境**
   ```
   点击任务的 "停止" 按钮
   或使用命令: docker-compose -p dht_test down
   ```
