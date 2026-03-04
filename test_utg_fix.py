"""
测试utg-q-008的修复是否生效
"""
import pymysql
import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from config import DB_CONFIG, C2_CLEANUP_CONFIG

def test_name_conversion():
    """测试名称转换逻辑"""
    print("=" * 60)
    print("测试名称转换逻辑")
    print("=" * 60)
    
    # server.py中的逻辑
    def normalize_botnet_name_server(name: str) -> str:
        if name:
            return name.replace('-', '_')
        return name
    
    # cleanup.py中的逻辑
    def normalize_botnet_name_cleanup(name: str) -> str:
        if name:
            return name.replace('_', '-')
        return name
    
    test_cases = [
        ('utg-q-008', 'server.py查询表名'),
        ('utg_q_008', 'cleanup.py匹配C2配置')
    ]
    
    for name, desc in test_cases:
        if desc.startswith('server'):
            result = normalize_botnet_name_server(name)
            print(f"  {desc}: {name} -> {result}")
        else:
            result = normalize_botnet_name_cleanup(name)
            print(f"  {desc}: {name} -> {result}")

def test_cleanup_config():
    """测试C2清除配置"""
    print("\n" + "=" * 60)
    print("测试C2清除配置")
    print("=" * 60)
    
    for botnet_name in C2_CLEANUP_CONFIG['botnet_paths'].keys():
        print(f"  - {botnet_name}: {C2_CLEANUP_CONFIG['botnet_paths'][botnet_name]}")

def test_database_query():
    """测试数据库查询"""
    print("\n" + "=" * 60)
    print("测试数据库查询")
    print("=" * 60)
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 测试1: 查询utg_q_008的节点表
        table_name = "botnet_nodes_utg_q_008"
        print(f"\n1. 查询节点表 {table_name}")
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        count = cursor.fetchone()[0]
        print(f"   结果: {count} 个节点")
        
        # 测试2: 查询server_management中的utg-q-008
        print("\n2. 查询 server_management 中的 utg-q-008")
        cursor.execute("SELECT ip, location FROM server_management WHERE Botnet_Name = 'utg-q-008'")
        result = cursor.fetchone()
        if result:
            print(f"   C2 IP: {result[0]}, Location: {result[1]}")
        else:
            print("   未找到")
        
        # 测试3: 查询botnet_types中的utg_q_008
        print("\n3. 查询 botnet_types 中的 utg_q_008")
        cursor.execute("SELECT display_name FROM botnet_types WHERE name = 'utg_q_008'")
        result = cursor.fetchone()
        if result:
            print(f"   Display Name: {result[0]}")
        else:
            print("   未找到")
        
        conn.close()
        
    except Exception as e:
        print(f"   错误: {e}")

def main():
    print("\n" + "=" * 60)
    print("UTG-Q-008 修复验证测试")
    print("=" * 60)
    
    test_name_conversion()
    test_cleanup_config()
    test_database_query()
    
    print("\n" + "=" * 60)
    print("预期结果:")
    print("=" * 60)
    print("1. utg-q-008 应该能够:")
    print("   - 在C2状态监控界面显示节点数（不再是Null）")
    print("   - 在一键清除界面显示为可清除状态")
    print("2. 名称转换:")
    print("   - botnet_types表: utg_q_008")
    print("   - server_management表: utg-q-008")
    print("   - 节点表名: botnet_nodes_utg_q_008")
    print("   - C2清除配置: utg-q-008")
    print("=" * 60)

if __name__ == "__main__":
    main()
