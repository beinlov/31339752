import logging
from collections import deque
from .utils import ID_BITS, get_bucket_index, xor_distance

K_SIZE = 5


class RoutingTable:
    def __init__(self, local_id):
        self.local_id = local_id
        # 初始化 32 个桶
        self.buckets = [deque(maxlen=K_SIZE) for _ in range(ID_BITS)]

    def add_contact(self, contact):
        if contact['id'] == self.local_id:
            return True, None, None

        dist = xor_distance(self.local_id, contact['id'])
        idx = get_bucket_index(dist)

        if idx < 0 or idx >= ID_BITS:
            return False, None, None

        bucket = self.buckets[idx]

        # 检查是否已存在
        for i, c in enumerate(bucket):
            if c['id'] == contact['id']:
                del bucket[i]
                bucket.append(contact)
                return True, bucket, None

        if len(bucket) < K_SIZE:
            bucket.append(contact)
            return True, bucket, None
        oldest = bucket[0]
        # 桶满，返回最旧节点
        return False, bucket, oldest

    def find_close_nodes(self, target_id, count=K_SIZE, exclude_id=None):
        all_nodes = []
        for b in self.buckets:
            all_nodes.extend(b)

        if exclude_id:
            all_nodes = [n for n in all_nodes if n['id'] != exclude_id]

        all_nodes.sort(key=lambda n: xor_distance(n['id'], target_id))
        return all_nodes[:count]

    def get_total_count(self):
        return sum(len(b) for b in self.buckets)

    # --- 新增方法：获取完整的路由表详情字符串 ---
    def get_full_info(self):
        lines = []
        for i, bucket in enumerate(self.buckets):
            if len(bucket) > 0:
                # 将节点 ID 转换为 8 位十六进制字符串
                nodes_str = ", ".join([f"{n['id']:08x}" for n in bucket])
                lines.append(f"  Bucket {i:2d}: [{nodes_str}]")

        if not lines:
            return "  (Empty)"
        return "\n".join(lines)