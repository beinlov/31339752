import asyncio
import logging
import socket
import sys
import os
import json

sys.path.append(os.getcwd())

from kademlia.node import Node
from kademlia.utils import get_id_from_hex

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger("SybilVerifier")


async def verify_sybil_attack():
    """
    验证女巫攻击的效果：
    1. 查看 node-1 的路由表内容
    2. 测试 FIND_NODE 查询是否被污染
    """
    
    # 从环境变量读取节点配置
    node_id_hex = os.getenv('NODE_ID_HEX')
    if not node_id_hex:
        logger.error("错误：未找到环境变量 NODE_ID_HEX")
        return
    
    my_node_id = get_id_from_hex(node_id_hex)
    test_port = 8999
    
    print("\n" + "=" * 70)
    print("🔍 女巫攻击效果验证")
    print("=" * 70)
    print(f"测试节点 ID: 0x{my_node_id:08x}")
    print(f"测试端口: {test_port}")
    print("=" * 70 + "\n")
    
    # 启动测试节点
    logger.info("启动测试节点...")
    node = Node(my_node_id, test_port)
    await node.start()
    await asyncio.sleep(1)
    
    # 解析 node-1 的 IP
    try:
        target_ip = socket.gethostbyname("node-1")
        target_port = 8000
        logger.info(f"目标 node-1 IP: {target_ip}:{target_port}\n")
    except Exception as e:
        logger.error(f"无法解析 node-1: {e}")
        return
    
    # ========== 测试 1: 直接 PING（不依赖路由表）==========
    print("=" * 70)
    print("📡 测试 1: 直接 PING node-1（不依赖路由表）")
    print("=" * 70)
    
    try:
        response = await asyncio.wait_for(
            node.protocol._send_request((target_ip, target_port), 'PING', {}),
            timeout=3.0
        )
        
        if response:
            print("✅ 直接 PING 成功 - node-1 响应了")
            print(f"   响应节点 ID: 0x{response['sender']['id']:08x}")
            print("   结论: 直接通信不受女巫攻击影响\n")
        else:
            print("❌ 直接 PING 失败\n")
    except asyncio.TimeoutError:
        print("❌ 直接 PING 超时\n")
    
    # ========== 测试 2: FIND_NODE 查询（依赖路由表）==========
    print("=" * 70)
    print("📡 测试 2: FIND_NODE 查询（依赖 node-1 的路由表）")
    print("=" * 70)
    print("说明: 这个测试会要求 node-1 返回它路由表中最接近某个 ID 的节点")
    print("      如果女巫攻击成功，返回的应该都是攻击节点\n")
    
    # 查询一个随机 ID，看 node-1 返回什么节点
    target_lookup_id = 0x12345678
    
    try:
        response = await asyncio.wait_for(
            node.protocol._send_request(
                (target_ip, target_port),
                'FIND_NODE',
                {'target_id': target_lookup_id}
            ),
            timeout=3.0
        )
        
        if response and 'nodes' in response:
            nodes = response['nodes']
            print(f"✅ FIND_NODE 成功 - node-1 返回了 {len(nodes)} 个节点:")
            print("-" * 70)
            
            # 分析返回的节点
            sybil_count = 0
            legitimate_nodes = []
            
            # 已知的合法节点 ID（从 docker-compose.yml）
            known_legitimate_ids = {
                0x00623457: 'node-1',
                0x00547832: 'node-2',
                0x00275278: 'node-3',
                0x00237418: 'node-4',
                0x00957358: 'node-5',
                0x00986574: 'node-6',
                0x00fd6752: 'node-7',
                0x008578d7: 'node-8',
                0x008a5d3a: 'node-9',
                0x0097ad54: 'node-10'
            }
            
            for i, n in enumerate(nodes, 1):
                node_id = n.get('id', 0)
                node_ip = n.get('ip', '未知')
                node_port = n.get('port', 0)
                
                if node_id in known_legitimate_ids:
                    node_type = f"✅ 合法节点 ({known_legitimate_ids[node_id]})"
                    legitimate_nodes.append(node_id)
                else:
                    node_type = "⚠️  疑似女巫节点"
                    sybil_count += 1
                
                print(f"  {i}. ID: 0x{node_id:08x} | IP: {node_ip:15s} | Port: {node_port} | {node_type}")
            
            print("-" * 70)
            print(f"\n📊 统计结果:")
            print(f"   合法节点数量: {len(legitimate_nodes)}")
            print(f"   疑似女巫节点数量: {sybil_count}")
            print(f"   女巫节点占比: {sybil_count/len(nodes)*100:.1f}%")
            
            if sybil_count > len(legitimate_nodes):
                print("\n结论: 女巫攻击成功！node-1 的路由表已被大量污染")
                print("         node-1 在进行节点查找时会优先返回攻击节点")
            elif sybil_count > 0:
                print("\n结论: 女巫攻击部分成功，路由表中存在攻击节点")
            else:
                print("\n✅ 结论: 未检测到女巫攻击，路由表中都是合法节点")
            
            
        else:
            print("❌ FIND_NODE 失败 - 未收到有效响应")
    
    except asyncio.TimeoutError:
        print("❌ FIND_NODE 超时")
    except Exception as e:
        logger.error(f"发生错误: {e}")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(verify_sybil_attack())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        logger.error(f"发生错误: {e}")
