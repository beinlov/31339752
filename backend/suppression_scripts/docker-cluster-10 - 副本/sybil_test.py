import asyncio
import logging
import socket
import random
import sys
import os

sys.path.append(os.getcwd())
from kademlia.node import Node

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("SybilLookupTest")

TARGET_BOOTSTRAP = "node-1"
BOOTSTRAP_PORT = 8000

async def run_lookup_test():
    # 1. 启动一个正常节点（node-2 角色）
    normal_id = random.getrandbits(32)
    normal_port = 9001

    node = Node(normal_id, normal_port)
    await node.start()

    # 2. 解析 bootstrap
    bootstrap_ip = socket.gethostbyname(TARGET_BOOTSTRAP)
    bootstrap = {
        'id': 0,
        'ip': bootstrap_ip,
        'port': BOOTSTRAP_PORT
    }

    # 3. 向 node-1 bootstrap
    logger.info("Bootstrapping to node-1 ...")
    await node.protocol.ping(bootstrap)
    node.routing_table.add_contact(bootstrap)

    # 4. 构造一个“随机 key”
    fake_key = random.getrandbits(32)
    logger.info(f"Looking up key: {fake_key:08x}")

    # 5. 发起 FIND_NODE（查询转发）
    result = await node.protocol.find_node(bootstrap, fake_key)

    if not result:
        logger.warning("No nodes returned.")
        return

    print("\nReturned nodes:")
    for n in result:
        print(f"  ID={n['id']:08x} IP={n['ip']} PORT={n['port']}")

    # 6. 简单判断是否被污染
    attacker_ips = set(n['ip'] for n in result)
    if len(attacker_ips) == 1:
        print("\n⚠️ POSSIBLE SYBIL ATTACK DETECTED")
        print("All returned nodes belong to the same IP.")
    else:
        print("\n✅ Mixed nodes returned (no full hijack detected)")

if __name__ == "__main__":
    asyncio.run(run_lookup_test())
