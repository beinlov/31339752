import os
import asyncio
import logging
from kademlia.node import Node
from kademlia.utils import get_id_from_hex

# 设置日志格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


async def main():
    node_id_hex = os.getenv('NODE_ID_HEX')
    node_id = get_id_from_hex(node_id_hex)
    port = int(os.getenv('PORT', 8000))
    bootstrap_host = os.getenv('BOOTSTRAP_HOST')

    node = Node(node_id, port)
    await node.start()

    if bootstrap_host:
        logging.info(f"Waiting for bootstrap node {bootstrap_host}...")
        await asyncio.sleep(5)
        await node.bootstrap(bootstrap_host, port)

    while True:
        await asyncio.sleep(10)
        # 获取路由表详情
        table_str = node.routing_table.get_full_info()
        total = node.routing_table.get_total_count()

        # 打印详细日志
        log_msg = (
            f"\n{'=' * 20} Routing Table (My ID: {node_id:08x}) {'=' * 20}\n"
            f"Total Peers: {total}\n"
            f"{table_str}\n"
            f"{'=' * 65}"
        )
        logging.info(log_msg)


if __name__ == '__main__':
    asyncio.run(main())