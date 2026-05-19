import asyncio
import json
import logging
import random


class KademliaProtocol(asyncio.DatagramProtocol):
    def __init__(self, node_id, routing_table):
        self.node_id = node_id
        self.routing_table = routing_table
        self.transport = None
        self.my_ip = None
        self.futures = {}

    def set_my_ip(self, ip):
        self.my_ip = ip

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        try:
            msg = json.loads(data.decode())
        except:
            return

        sender = msg.get('sender')
        if not sender: return

        # 更新路由表
        is_added, bucket, oldest = self.routing_table.add_contact(sender)
        if not is_added and oldest:
            asyncio.create_task(self._ping_check(bucket, oldest, sender))

        msg_type = msg.get('type')
        msg_id = msg.get('msg_id')

        if msg_type == 'PING':
            self._send_response(addr, msg_id, 'PONG', {})
        elif msg_type == 'PONG':
            self._complete_future(msg_id, msg)
        elif msg_type == 'FIND_NODE':
            nodes = self.routing_table.find_close_nodes(msg.get('target_id'))
            self._send_response(addr, msg_id, 'FIND_NODE_REPLY', {'nodes': nodes})
        elif msg_type == 'FIND_NODE_REPLY':
            self._complete_future(msg_id, msg)

    async def _ping_check(self, bucket, oldest, new_contact):
        is_alive = await self.ping(oldest)
        if not is_alive:
            try:
                bucket.remove(oldest)
                bucket.append(new_contact)
            except:
                pass

    def _send_response(self, addr, msg_id, type_str, data):
        if not self.my_ip: return
        data.update(
            {'type': type_str, 'msg_id': msg_id, 'sender': {'id': self.node_id, 'ip': self.my_ip, 'port': 8000}})
        self.transport.sendto(json.dumps(data).encode(), addr)

    def _complete_future(self, msg_id, result):
        if msg_id in self.futures and not self.futures[msg_id].done():
            self.futures[msg_id].set_result(result)

    async def _send_request(self, addr, type_str, data):
        if not self.my_ip: return None
        msg_id = random.randint(1, 999999)
        future = asyncio.get_running_loop().create_future()
        self.futures[msg_id] = future
        data.update(
            {'type': type_str, 'msg_id': msg_id, 'sender': {'id': self.node_id, 'ip': self.my_ip, 'port': 8000}})
        self.transport.sendto(json.dumps(data).encode(), addr)
        try:
            return await asyncio.wait_for(future, timeout=2.0)
        except asyncio.TimeoutError:
            del self.futures[msg_id]
            return None

    async def ping(self, target):
        return await self._send_request((target['ip'], target['port']), 'PING', {}) is not None

    async def find_node(self, target, lookup_id):
        res = await self._send_request(
            (target['ip'], target['port']),
            'FIND_NODE',
            {'target_id': lookup_id}
        )

        if not res:
            return []

        nodes = res.get('nodes')
        if not isinstance(nodes, list):
            return []

        return nodes
