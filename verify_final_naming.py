"""
验证统一命名后的完整性
确保所有地方都使用 utg_q_008（下划线）格式
"""
import pymysql
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from config import DB_CONFIG, C2_CLEANUP_CONFIG

def verify_all():
    print("=" * 70)
    print("验证统一命名：所有地方都应该使用 utg_q_008（下划线格式）")
    print("=" * 70)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    all_passed = True
    
    # 1. 检查 botnet_types 表
    print("\n1. 检查 botnet_types 表")
    cursor.execute("SELECT name, display_name, table_name FROM botnet_types WHERE name LIKE '%utg%'")
    result = cursor.fetchone()
    if result:
        if result['name'] == 'utg_q_008':
            print(f"   ✅ name: {result['name']}")
            print(f"      display_name: {result['display_name']}")
            print(f"      table_name: {result['table_name']}")
        else:
            print(f"   ❌ name 应该是 'utg_q_008'，但实际是 '{result['name']}'")
            all_passed = False
    else:
        print("   ❌ 未找到 utg 相关记录")
        all_passed = False
    
    # 2. 检查 server_management 表
    print("\n2. 检查 server_management 表")
    cursor.execute("SELECT id, ip, location, Botnet_Name FROM server_management WHERE Botnet_Name LIKE '%utg%'")
    result = cursor.fetchone()
    if result:
        if result['Botnet_Name'] == 'utg_q_008':
            print(f"   ✅ Botnet_Name: {result['Botnet_Name']}")
            print(f"      ID: {result['id']}, IP: {result['ip']}, Location: {result['location']}")
        else:
            print(f"   ❌ Botnet_Name 应该是 'utg_q_008'，但实际是 '{result['Botnet_Name']}'")
            all_passed = False
    else:
        print("   ❌ 未找到 utg 相关记录")
        all_passed = False
    
    # 3. 检查节点表
    print("\n3. 检查节点表")
    cursor.execute("SHOW TABLES LIKE 'botnet_nodes_utg_q_008'")
    if cursor.fetchone():
        cursor.execute("SELECT COUNT(*) as count FROM botnet_nodes_utg_q_008")
        count = cursor.fetchone()['count']
        print(f"   ✅ 表名: botnet_nodes_utg_q_008")
        print(f"      节点数: {count}")
    else:
        print("   ❌ 表 botnet_nodes_utg_q_008 不存在")
        all_passed = False
    
    # 4. 检查 C2_CLEANUP_CONFIG
    print("\n4. 检查 C2_CLEANUP_CONFIG")
    if 'utg_q_008' in C2_CLEANUP_CONFIG['botnet_paths']:
        print(f"   ✅ 键名: utg_q_008")
        paths = C2_CLEANUP_CONFIG['botnet_paths']['utg_q_008']
        print(f"      cleanup: {paths['cleanup']}")
        print(f"      status: {paths['status']}")
        print(f"      reset: {paths['reset']}")
    else:
        print("   ❌ C2_CLEANUP_CONFIG 中未找到 'utg_q_008'")
        if 'utg-q-008' in C2_CLEANUP_CONFIG['botnet_paths']:
            print("      ⚠️  找到了 'utg-q-008'（连字符格式），需要修改为 'utg_q_008'")
        all_passed = False
    
    # 5. 模拟完整流程
    print("\n5. 模拟完整流程")
    print("\n   5.1 C2状态监控 - /api/servers")
    cursor.execute("SELECT Botnet_Name FROM server_management WHERE id = 11")
    server_botnet = cursor.fetchone()
    if server_botnet:
        botnet_name = server_botnet['Botnet_Name']
        table_name = f"botnet_nodes_{botnet_name}"
        try:
            cursor.execute(f"SELECT COUNT(*) as total FROM `{table_name}`")
            count = cursor.fetchone()['total']
            print(f"       ✅ 查询 {table_name} 成功，节点数: {count}")
        except Exception as e:
            print(f"       ❌ 查询失败: {e}")
            all_passed = False
    
    print("\n   5.2 一键清除 - /api/cleanup/check-permissions")
    cursor.execute("SELECT name FROM botnet_types WHERE name = 'utg_q_008'")
    botnet_type = cursor.fetchone()
    if botnet_type:
        botnet_name = botnet_type['name']
        
        # 检查C2
        cursor.execute("SELECT ip FROM server_management WHERE Botnet_Name = %s", (botnet_name,))
        c2 = cursor.fetchone()
        has_c2 = c2 is not None
        
        # 检查路径
        has_paths = botnet_name in C2_CLEANUP_CONFIG['botnet_paths']
        
        if has_c2 and has_paths:
            print(f"       ✅ {botnet_name} 有C2权限和清除接口")
            print(f"          C2 IP: {c2['ip']}")
            print(f"          接口配置: {list(C2_CLEANUP_CONFIG['botnet_paths'][botnet_name].keys())}")
        else:
            print(f"       ❌ {botnet_name} 权限检查失败")
            print(f"          has_c2: {has_c2}, has_paths: {has_paths}")
            all_passed = False
    
    conn.close()
    
    # 总结
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ 所有检查通过！命名已完全统一为 utg_q_008")
        print("=" * 70)
        print("\n下一步:")
        print("1. 重启后端服务")
        print("2. 刷新前端页面")
        print("3. 验证:")
        print("   - C2状态监控界面应显示节点数（不是Null）")
        print("   - 一键清除界面应显示 utg_q_008 可以清除")
    else:
        print("❌ 部分检查未通过，请查看上面的错误信息")
        print("=" * 70)
    
    return all_passed

if __name__ == "__main__":
    success = verify_all()
    sys.exit(0 if success else 1)
