"""
测试Ramnit日志格式解析
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_processor.parser import LogParser

def test_ramnit_parser():
    """测试Ramnit格式解析"""
    parser = LogParser('ramnit')
    
    # 测试用例
    test_cases = [
        # 应该被跳过的系统消息
        ("2025/07/03 09:31:24", False, "单独的时间戳"),
        ("--- 服务器于 2025-07-03 09:31:24 启动。 ---", False, "分隔符"),
        ("2025/07/03 09:31:24 服务器已启动，监听地址: 23.27.200.187:447", False, "服务器消息"),
        ("2025/07/03 09:31:24 已启动 1000 个 worker 来处理连接。", False, "worker消息"),
        
        # 应该被解析的日志
        ("2025/07/03 09:31:24 新IP首次连接: 180.254.163.108", True, "新IP连接"),
        ("2025/07/03 09:31:24 新IP首次连接: 149.108.184.126", True, "新IP连接2"),
        ("2025/07/03 09:32:15 节点心跳: 192.168.1.100", True, "心跳"),
        ("2025/07/03 09:33:20 命令执行: 10.0.0.50", True, "命令"),
    ]
    
    print("=" * 80)
    print("Ramnit格式解析测试")
    print("=" * 80)
    
    success_count = 0
    fail_count = 0
    
    for line, should_parse, description in test_cases:
        print(f"\n测试: {description}")
        print(f"输入: {line}")
        
        result = parser.parse_line(line)
        
        if should_parse:
            if result:
                print(f"✅ 解析成功:")
                print(f"   时间戳: {result['timestamp']}")
                print(f"   IP地址: {result['ip']}")
                print(f"   事件类型: {result['event_type']}")
                print(f"   额外信息: {result['extras']}")
                success_count += 1
            else:
                print(f"❌ 解析失败 (预期成功)")
                fail_count += 1
        else:
            if result:
                print(f"❌ 意外解析成功 (预期跳过)")
                print(f"   结果: {result}")
                fail_count += 1
            else:
                print(f"✅ 正确跳过")
                success_count += 1
    
    print("\n" + "=" * 80)
    print(f"测试结果: 成功 {success_count}/{len(test_cases)}, 失败 {fail_count}/{len(test_cases)}")
    print("=" * 80)
    
    return fail_count == 0

if __name__ == "__main__":
    success = test_ramnit_parser()
    sys.exit(0 if success else 1)

