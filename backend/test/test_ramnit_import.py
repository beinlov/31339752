"""
测试Ramnit数据是否能成功导入数据库
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_processor.parser import LogParser
from log_processor.config import BOTNET_CONFIG

def test_important_events():
    """测试Ramnit的事件过滤配置"""
    
    print("=" * 80)
    print("Ramnit事件过滤测试")
    print("=" * 80)
    
    # 获取配置
    ramnit_config = BOTNET_CONFIG.get('ramnit', {})
    important_events = ramnit_config.get('important_events', [])
    
    print(f"\n配置的 important_events: {important_events}")
    print(f"说明: {'保存所有事件' if not important_events else '只保存特定事件'}\n")
    
    # 创建解析器
    parser = LogParser('ramnit', important_events)
    
    # 测试用例
    test_lines = [
        "2025/07/03 09:31:24 新IP首次连接: 180.254.163.108",
        "2025/07/03 09:31:24 新IP首次连接: 149.108.184.126",
        "2025/07/03 09:32:15 节点心跳: 192.168.1.100",
        "2025/07/03 09:33:20 命令执行: 10.0.0.50",
    ]
    
    print("测试日志行:")
    print("-" * 80)
    
    saved_count = 0
    filtered_count = 0
    
    for line in test_lines:
        parsed = parser.parse_line(line)
        
        if parsed:
            should_save = parser.should_save_to_db(parsed)
            status = "✅ 保存" if should_save else "❌ 过滤"
            
            if should_save:
                saved_count += 1
            else:
                filtered_count += 1
            
            print(f"{status} | 事件类型: {parsed['event_type']:20s} | IP: {parsed['ip']:15s} | {line[:50]}")
        else:
            print(f"⏭️  跳过 | {line[:50]}")
    
    print("\n" + "=" * 80)
    print("测试结果:")
    print(f"  保存到数据库: {saved_count} 条")
    print(f"  被过滤: {filtered_count} 条")
    
    if important_events and filtered_count > 0:
        print(f"\n⚠️  警告: 有 {filtered_count} 条记录被过滤!")
        print(f"  原因: 事件类型不在 important_events 列表中")
        print(f"  建议: 将 important_events 设为空列表 [] 以保存所有事件")
    elif not important_events:
        print(f"\n✅ 配置正确: important_events 为空,所有事件都会保存")
    
    print("=" * 80)
    
    return filtered_count == 0

if __name__ == "__main__":
    success = test_important_events()
    sys.exit(0 if success else 1)

