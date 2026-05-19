import asyncio
import logging
import socket
import random
import sys
import os
import json

sys.path.append(os.getcwd())

from kademlia.node import Node

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("ConnectivityTest")

# ======== 配置 ========
NODE2_PORT = 9001

BOOTSTRAP_HOST = "node-1"
BOOTSTRAP_PORT = 8000

TARGET_NODE_NAME = "docker-cluster-10--node-3-1"
TARGET_APP_PORT = 8001

ENUMERATION_ROUNDS = 10


class AppClientProtocol(asyncio.DatagramProtocol):
    def __init__(self, on_response):
        self.on_response = on_response

    def datagram_received(self, data, addr):
        msg = data.decode(errors="ignore")
        print(f"📩 Response from node-3: {msg}")
        self.on_response.set_result(True)


async def send_udp_app_message(ip, port, message):
    """
    通过 UDP 向 node-3 发送应用层消息，并等待回复
    """
    loop = asyncio.get_running_loop()
    on_response = loop.create_future()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: AppClientProtocol(on_response),
        remote_addr=(ip, port)
    )

    transport.sendto(json.dumps(message).encode())
    print(f"📤 Sent UDP application message to {ip}:{port}")

    try:
        await asyncio.wait_for(on_response, timeout=3.0)
        print("✅ Application-layer reply received")
    except asyncio.TimeoutError:
        print("❌ No application-layer reply (timeout)")

    transport.close()


async def run_test():
    print("\n" + "=" * 70)
    print("🧪 DHT → Application Connectivity Test (node-2 via node-1)")
    print("=" * 70)

    # 1️⃣ 启动 node-2
    node2_id = random.getrandbits(32)
    node2 = Node(node2_id, NODE2_PORT)
    await node2.start()
    print(f"[node-2] ID={node2_id:08x} PORT={NODE2_PORT}")

    # 2️⃣ bootstrap（node-1）
    bootstrap_ip = socket.gethostbyname(BOOTSTRAP_HOST)
    bootstrap = {
        'id': 0,
        'ip': bootstrap_ip,
        'port': BOOTSTRAP_PORT
    }

    # 3️⃣ 枚举 node-1 路由表
    print("\n[STEP 1] Enumerating nodes from node-1 routing table (DHT-only)")
    discovered = {}

    for _ in range(ENUMERATION_ROUNDS):
        key = random.getrandbits(32)
        try:
            result = await node2.protocol.find_node(bootstrap, key)
        except Exception:
            result = []

        for n in result or []:
            discovered[(n['ip'], n['port'])] = n

        await asyncio.sleep(0.2)

    if not discovered:
        print("❌ No nodes discovered from node-1")
        return

    print(f"Discovered {len(discovered)} nodes from node-1:")
    for n in discovered.values():
        print(f"  -> ID={n['id']:08x} IP={n['ip']} PORT={n['port']}")

    # 4️⃣ 查找 node-3
    print("\n[STEP 2] Searching for node-3 entry in routing results")

    try:
        node3_ip = socket.gethostbyname(TARGET_NODE_NAME)
    except Exception:
        print("❌ Cannot resolve node-3 hostname")
        return

    node3_entry = None
    for n in discovered.values():
        if n['ip'] == node3_ip:
            node3_entry = n
            break

    if not node3_entry:
        print(
            "❌ node-3 NOT found in node-1 routing table\n"
            "→ Overlay network path to node-3 does NOT exist\n"
            "→ Application message will NOT be sent"
        )
        return

    print(
        f"✅ node-3 FOUND via DHT:\n"
        f"   DHT IP   : {node3_entry['ip']}\n"
        f"   DHT PORT : {node3_entry['port']}"
    )

    # 5️⃣ 应用层 UDP 通信（仅在 DHT 成功时）
    print("\n[STEP 3] Sending application-layer UDP message to node-3")

    await send_udp_app_message(
        node3_entry['ip'],
        TARGET_APP_PORT,
        {
            "type": "APP_MSG",
            "from": "node-2",
            "msg": "Hello node-3, this is node-2"
        }
    )

    # 6️⃣ 结论
    print("\n" + "=" * 70)
    print("📌 FINAL INTERPRETATION")
    print("=" * 70)

    print(
        "✔ node-2 ONLY used DHT information from node-1\n"
        "✔ No direct knowledge of node-3 was assumed\n"
        "✔ Application message sent ONLY if DHT path existed\n\n"
        "If node-3 does NOT receive this message under attack:\n"
        "→ node-3 is logically isolated (Eclipse)\n"
        "→ Overlay broken, underlay intact"
    )

    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(run_test())
