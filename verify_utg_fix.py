"""
验证 utg-q-008 修复是否完全生效
模拟后端API的逻辑
"""
import pymysql
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from config import DB_CONFIG, C2_CLEANUP_CONFIG

def normalize_botnet_name_server(name: str) -> str:
    """server.py 中的名称转换"""
    if name:
        return name.replace('-', '_')
    return name

def normalize_botnet_name_cleanup(name: str) -> str:
    """cleanup.py 中的名称转换"""
    if name:
        return name.replace('_', '-')
    return name

print("=" * 70)
print("验证1: C2状态监控界面 - 模拟 /api/servers 接口")
print("=" * 70)

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor(pymysql.cursors.DictCursor)

cursor.execute("SELECT id, ip, location, Botnet_Name FROM server_management WHERE Botnet_Name = 'utg-q-008'")
server = cursor.fetchone()

if server:
    print(f"\n找到服务器:")
    print(f"  ID: {server['id']}")
    print(f"  IP: {server['ip']}")
    print(f"  Location: {server['location']}")
    print(f"  Botnet_Name: {server['Botnet_Name']}")
    
    botnet_name = server['Botnet_Name']
    # 标准化僵网名称（将连字符转换为下划线）
    normalized_name = normalize_botnet_name_server(botnet_name)
    table_name = f"botnet_nodes_{normalized_name}"
    
    print(f"\n查询节点表: {table_name}")
    try:
        cursor.execute(f"SELECT COUNT(*) as total FROM `{table_name}`")
        node_count = cursor.fetchone()['total']
        print(f"  节点数: {node_count}")
        print(f"  ✅ 成功！不再显示 Null")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
else:
    print("❌ 未找到 utg-q-008 的服务器")

print("\n" + "=" * 70)
print("验证2: 一键清除功能 - 模拟 /api/cleanup/check-permissions 接口")
print("=" * 70)

cursor.execute("SELECT name, display_name FROM botnet_types WHERE name = 'utg-q-008'")
botnet = cursor.fetchone()

if botnet:
    botnet_name = botnet['name']
    print(f"\n找到僵网类型:")
    print(f"  name: {botnet_name}")
    print(f"  display_name: {botnet['display_name']}")
    
    # 将下划线名称转换为连字符名称（如果需要）
    # 注意: botnet_types中已经是 utg-q-008，不需要转换
    normalized_name = botnet_name
    
    # 检查C2服务器
    cursor.execute("SELECT ip FROM server_management WHERE Botnet_Name = %s", (normalized_name,))
    c2_info = cursor.fetchone()
    has_c2 = c2_info is not None
    
    # 检查清除接口配置
    has_paths = normalized_name in C2_CLEANUP_CONFIG['botnet_paths']
    
    print(f"\nC2状态:")
    print(f"  C2 IP: {c2_info['ip'] if c2_info else 'None'}")
    print(f"  有C2配置: {'✅ 是' if has_c2 else '❌ 否'}")
    print(f"  有清除接口配置: {'✅ 是' if has_paths else '❌ 否'}")
    print(f"  有清除权限: {'✅ 是' if (has_c2 and has_paths) else '❌ 否'}")
    
    if has_c2 and has_paths:
        print(f"\n清除接口路径:")
        for action, path in C2_CLEANUP_CONFIG['botnet_paths'][normalized_name].items():
            print(f"  {action}: {path}")
else:
    # 尝试查找下划线版本
    cursor.execute("SELECT name, display_name FROM botnet_types WHERE name = 'utg_q_008'")
    botnet_underscore = cursor.fetchone()
    if botnet_underscore:
        print(f"\n找到僵网类型 (下划线版本):")
        print(f"  name: {botnet_underscore['name']}")
        
        # 转换为连字符版本
        normalized_name = normalize_botnet_name_cleanup(botnet_underscore['name'])
        print(f"  转换后: {normalized_name}")
        
        # 再次检查
        cursor.execute("SELECT ip FROM server_management WHERE Botnet_Name = %s", (normalized_name,))
        c2_info = cursor.fetchone()
        has_c2 = c2_info is not None
        has_paths = normalized_name in C2_CLEANUP_CONFIG['botnet_paths']
        
        print(f"\nC2状态:")
        print(f"  C2 IP: {c2_info['ip'] if c2_info else 'None'}")
        print(f"  有C2配置: {'✅ 是' if has_c2 else '❌ 否'}")
        print(f"  有清除接口配置: {'✅ 是' if has_paths else '❌ 否'}")
        print(f"  有清除权限: {'✅ 是' if (has_c2 and has_paths) else '❌ 否'}")
    else:
        print("❌ 未找到 utg-q-008 或 utg_q_008 的僵网类型")

conn.close()

print("\n" + "=" * 70)
print("总结:")
print("=" * 70)
print("如果上述两个验证都显示 ✅，则修复成功。")
print("重启后端服务后，应该能看到:")
print("  1. C2状态监控界面显示 utg-q-008 的节点数（而不是 Null）")
print("  2. 一键清除界面显示 utg-q-008 可以清除")
print("=" * 70)
