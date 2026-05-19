import asyncio
import socket
import logging
from .routing import RoutingTable
from .protocol import KademliaProtocol
from .utils import xor_distance


class Node:
    def __init__(self, node_id, port=8000):
        self.id = node_id
        self.port = port
        self.routing_table = RoutingTable(self.id)
        self.protocol = KademliaProtocol(self.id, self.routing_table)
        self.logger = logging.getLogger(f"Node-{self.id:08x}")

    async def start(self):
        loop = asyncio.get_running_loop()
        self.ip = socket.gethostbyname(socket.gethostname())
        self.protocol.set_my_ip(self.ip)

        await loop.create_datagram_endpoint(
            lambda: self.protocol,
            local_addr=('0.0.0.0', self.port)
        )
        self.logger.info(f"Started at {self.ip}:{self.port}")

    async def bootstrap(self, seed_host, seed_port):
        try:
            seed_ip = socket.gethostbyname(seed_host)
        except Exception as e:
            self.logger.error(f"DNS Error: {e}")
            return

        await self.protocol.ping({'id': 0, 'ip': seed_ip, 'port': seed_port})
        await self.iterative_find_node(self.id)

    async def iterative_find_node(self, target_id):
        shortlist = self.routing_table.find_close_nodes(target_id, count=3)
        visited = set()

        while shortlist:
            shortlist.sort(key=lambda n: xor_distance(n['id'], target_id))
            candidate = next((n for n in shortlist if n['id'] not in visited and n['id'] != self.id), None)

            if not candidate:
                break

            visited.add(candidate['id'])

            new_nodes = await self.protocol.find_node(candidate, target_id)
            if new_nodes:
                for n in new_nodes:
                    if not any(x['id'] == n['id'] for x in shortlist):
                        shortlist.append(n)