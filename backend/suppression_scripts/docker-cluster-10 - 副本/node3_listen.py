import asyncio
import json
import logging

NODE3_ID = "node-3"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [node-3] %(message)s"
)

class Node3Protocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport
        logging.info("node-3 is listening for incoming requests...")

    def datagram_received(self, data, addr):
        try:
            msg = json.loads(data.decode())
        except Exception:
            return

        msg_type = msg.get("type")
        sender = msg.get("sender", {})

        logging.info(f"📩 Received message from {addr}: {msg}")

        # 只要收到请求，就明确回复
        reply = {
            "type": "NODE3_ACK",
            "msg": "node-3 已收到请求",
            "sender": {
                "id": NODE3_ID
            }
        }
        self.transport.sendto(json.dumps(reply).encode(), addr)
        logging.info("📤 Replied ACK to sender")


async def main():
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: Node3Protocol(),
        local_addr=("0.0.0.0", 8001)  # node-3 的服务端口
    )

    try:
        await asyncio.Future()  # 永久运行
    finally:
        transport.close()

if __name__ == "__main__":
    asyncio.run(main())
