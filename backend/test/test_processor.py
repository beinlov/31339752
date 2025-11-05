"""
测试统一日志处理系统
"""
import sys
import os
import asyncio

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_processor.parser import LogParser
from log_processor.enricher import IPEnricher
from log_processor.config import BOTNET_CONFIG


async def test_parser():
    """测试日志解析器"""
    print("=" * 60)
    print("测试日志解析器")
    print("=" * 60)
    
    # 测试asruex日志
    parser = LogParser('asruex', BOTNET_CONFIG['asruex']['important_events'])
    
    test_lines = [
        "2025-10-29 10:29:44,192.168.91.7,access,/content/faq.php?ql=b2",
        "2025-10-29 10:32:01,192.168.91.7,clean1,6.1-x64,192.168.91.7",
        "2025-10-29 10:31:55,192.168.91.7,qla0,S-1-8-68-140046984",
        "invalid line",  # 无效行
        "2025-10-29,999.999.999.999,access",  # 无效IP
    ]
    
    for line in test_lines:
        print(f"\n输入: {line}")
        result = parser.parse_line(line)
        if result:
            print(f"  ✓ 解析成功:")
            print(f"    - IP: {result['ip']}")
            print(f"    - 事件类型: {result['event_type']}")
            print(f"    - 时间戳: {result['timestamp']}")
            print(f"    - 是否保存: {parser.should_save_to_db(result)}")
            
            # 提取命令
            command = parser.extract_command(result)
            if command:
                desc = parser.get_description(result)
                print(f"    - 命令: {command}")
                print(f"    - 描述: {desc}")
        else:
            print(f"  ✗ 解析失败")
    
    print("\n✅ 解析器测试完成\n")


async def test_enricher():
    """测试IP信息增强器"""
    print("=" * 60)
    print("测试IP信息增强器")
    print("=" * 60)
    
    enricher = IPEnricher(cache_size=100, cache_ttl=3600)
    
    test_ips = [
        "8.8.8.8",           # Google DNS
        "114.114.114.114",   # 国内DNS
        "192.168.1.1",       # 内网IP
        "171.34.246.78",     # 示例IP
    ]
    
    for ip in test_ips:
        print(f"\n查询 IP: {ip}")
        info = await enricher.enrich(ip)
        if info:
            print(f"  ✓ 查询成功:")
            print(f"    - 国家: {info['country']}")
            print(f"    - 省份: {info['province']}")
            print(f"    - 城市: {info['city']}")
            print(f"    - ISP: {info['isp']}")
            print(f"    - ASN: {info['asn']}")
            print(f"    - 经度: {info['longitude']}, 纬度: {info['latitude']}")
            print(f"    - 是否中国: {info['is_china']}")
        else:
            print(f"  ✗ 查询失败")
    
    # 测试缓存
    print(f"\n\n再次查询第一个IP (测试缓存)...")
    info = await enricher.enrich(test_ips[0])
    
    # 显示统计
    stats = enricher.get_stats()
    print(f"\n统计信息:")
    print(f"  - 总查询次数: {stats['total_queries']}")
    print(f"  - 缓存命中次数: {stats['cache_hits']}")
    print(f"  - 缓存命中率: {stats['cache_hit_rate']}")
    print(f"  - 缓存大小: {stats['cache_size']}")
    
    print("\n✅ IP增强器测试完成\n")


async def test_batch_enricher():
    """测试批量IP查询"""
    print("=" * 60)
    print("测试批量IP查询")
    print("=" * 60)
    
    enricher = IPEnricher()
    
    ips = [
        "8.8.8.8",
        "114.114.114.114",
        "223.5.5.5",
        "1.1.1.1",
        "180.76.76.76",
    ]
    
    print(f"\n批量查询 {len(ips)} 个IP...")
    results = await enricher.batch_enrich(ips)
    
    for ip, info in results.items():
        print(f"\n{ip}:")
        print(f"  {info['country']} - {info['city']} ({info['isp']})")
    
    print("\n✅ 批量查询测试完成\n")


async def test_integration():
    """集成测试：完整流程"""
    print("=" * 60)
    print("集成测试：模拟完整处理流程")
    print("=" * 60)
    
    # 创建组件
    parser = LogParser('asruex', BOTNET_CONFIG['asruex']['important_events'])
    enricher = IPEnricher()
    
    # 模拟日志行
    log_lines = [
        "2025-10-29 10:29:44,8.8.8.8,access,/content/faq.php?ql=b2",
        "2025-10-29 10:30:15,114.114.114.114,clean1,6.1-x64",
        "2025-10-29 10:31:22,223.5.5.5,qla0,S-1-8-68-140046984",
    ]
    
    print(f"\n处理 {len(log_lines)} 行日志...\n")
    
    for i, line in enumerate(log_lines, 1):
        print(f"[{i}] 处理: {line[:60]}...")
        
        # 1. 解析
        parsed = parser.parse_line(line)
        if not parsed:
            print(f"    ✗ 解析失败")
            continue
            
        # 2. 检查是否需要保存
        if not parser.should_save_to_db(parsed):
            print(f"    ⊗ 跳过 (非重要事件)")
            continue
            
        # 3. 增强IP信息
        ip_info = await enricher.enrich(parsed['ip'])
        
        # 4. 显示结果
        print(f"    ✓ 成功处理:")
        print(f"      IP: {parsed['ip']}")
        print(f"      位置: {ip_info['country']} - {ip_info['province']} - {ip_info['city']}")
        print(f"      ISP: {ip_info['isp']}")
        print(f"      事件: {parsed['event_type']}")
        
        # 这里应该写入数据库，但在测试中我们跳过
        # writer.add_node(parsed, ip_info)
    
    print("\n✅ 集成测试完成\n")


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("僵尸网络日志处理系统 - 测试套件")
    print("=" * 60 + "\n")
    
    try:
        # 运行各项测试
        await test_parser()
        await test_enricher()
        await test_batch_enricher()
        await test_integration()
        
        print("=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)





