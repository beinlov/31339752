#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地日志上传测试脚本
用于测试日志上传接口是否正常工作
"""

import requests
import json
from datetime import datetime
import sys

# ============================================================
# 配置区域
# ============================================================

# 本地服务器地址
API_URL = "http://localhost:8000/api/upload-logs"
STATUS_URL = "http://localhost:8000/api/upload-status"

# API密钥（必须与backend/config.py中的API_KEY一致）
API_KEY = "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"

# ============================================================
# 测试数据
# ============================================================

# 测试用例1：Mozi僵尸网络
test_case_mozi = {
    "botnet_type": "mozi",
    "logs": [
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},8.8.8.8,infection,test_bot_v1.0",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},114.114.114.114,beacon",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},223.5.5.5,command,ddos_attack"
    ],
    "source_ip": "test-client"
}

# 测试用例2：Asruex僵尸网络
test_case_asruex = {
    "botnet_type": "asruex",
    "logs": [
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},192.168.1.1,access,/content/faq.php?ql=b2",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},192.168.1.2,clean1,6.1-x64",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},192.168.1.3,qla0,S-1-8-68-140046984"
    ],
    "source_ip": "test-client"
}

# 测试用例3：Ramnit僵尸网络
test_case_ramnit = {
    "botnet_type": "ramnit",
    "logs": [
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},45.33.12.88,infection,ramnit_v2.3",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},45.33.12.89,command,steal_credentials"
    ],
    "source_ip": "test-client"
}

# ============================================================
# 测试函数
# ============================================================

def print_separator(char='=', length=60):
    """打印分隔线"""
    print(char * length)


def test_status():
    """测试状态接口"""
    print_separator()
    print("📊 测试1: 查询上传接口状态")
    print_separator()
    
    try:
        response = requests.get(STATUS_URL, timeout=10)
        print(f"\n状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API状态: {data['api_status']}")
            print(f"时间戳: {data['timestamp']}")
            print(f"\n安全配置:")
            print(f"  - API密钥验证: {data['security']['api_key_required']}")
            print(f"  - IP白名单: {data['security']['ip_whitelist_enabled']}")
            print(f"  - 单次最大上传: {data['security']['max_logs_per_upload']} 条")
            
            print(f"\n僵尸网络统计:")
            for botnet in data['botnet_types']:
                print(f"  [{botnet['type']}]")
                print(f"    - 日志文件: {botnet['log_files']}")
                print(f"    - 总行数: {botnet['total_lines']}")
                if botnet['latest_file']:
                    print(f"    - 最新文件: {botnet['latest_file']}")
                    print(f"    - 最后修改: {botnet['last_modified']}")
            
            print("\n✅ 状态查询成功！")
            return True
        else:
            print(f"\n❌ 状态查询失败: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败！请检查:")
        print("  1. 后端服务是否正在运行？")
        print("  2. 地址是否正确？ (默认: http://localhost:8000)")
        return False
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return False


def test_upload(test_case, case_name):
    """测试上传接口"""
    print_separator()
    print(f"📤 测试: {case_name}")
    print_separator()
    
    print(f"\n目标URL: {API_URL}")
    print(f"僵尸网络类型: {test_case['botnet_type']}")
    print(f"日志行数: {len(test_case['logs'])}")
    print(f"\n发送请求...")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.post(API_URL, json=test_case, headers=headers, timeout=10)
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            print(f"\n✅ 上传成功！")
            print(f"  - 接收数量: {result['received_count']}")
            print(f"  - 保存位置: {result['saved_to']}")
            print(f"  - 时间戳: {result['timestamp']}")
            return True
            
        elif response.status_code == 401:
            print("\n❌ 认证失败！")
            print("  原因: API密钥无效")
            print("  解决: 检查 test_upload.py 中的 API_KEY 是否与 backend/config.py 一致")
            return False
            
        elif response.status_code == 403:
            print("\n❌ 权限不足！")
            print("  原因: IP未在白名单中")
            print("  解决: 在 backend/config.py 的 ALLOWED_UPLOAD_IPS 中添加你的IP")
            return False
            
        else:
            print(f"\n❌ 上传失败！")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败！请检查后端服务是否运行")
        return False
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return False


def main():
    """主函数"""
    print("\n")
    print("=" * 60)
    print("  僵尸网络日志上传接口测试工具")
    print("=" * 60)
    print()
    
    # 测试1: 查询状态
    status_ok = test_status()
    print()
    
    if not status_ok:
        print("❌ 状态检查失败，终止测试")
        print("\n请确保:")
        print("  1. 后端服务已启动: python backend/main.py")
        print("  2. 日志处理器已启动: python backend/log_processor/main.py")
        sys.exit(1)
    
    # 测试2: 上传Mozi日志
    mozi_ok = test_upload(test_case_mozi, "上传 Mozi 僵尸网络日志")
    print()
    
    # 测试3: 上传Asruex日志
    asruex_ok = test_upload(test_case_asruex, "上传 Asruex 僵尸网络日志")
    print()
    
    # 测试4: 上传Ramnit日志
    ramnit_ok = test_upload(test_case_ramnit, "上传 Ramnit 僵尸网络日志")
    print()
    
    # 测试5: 再次查询状态（验证数据已更新）
    print_separator()
    print("🔄 测试: 验证数据已更新")
    print_separator()
    test_status()
    print()
    
    # 总结
    print_separator()
    print("📊 测试总结")
    print_separator()
    
    total_tests = 3
    passed_tests = sum([mozi_ok, asruex_ok, ramnit_ok])
    
    print(f"\n总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！接口工作正常。")
        print("\n下一步:")
        print("  1. 查看日志文件: backend/logs/mozi/2025-10-30.txt")
        print("  2. 查看处理器日志: tail -f backend/log_processor.log")
        print("  3. 查询数据库: SELECT * FROM botnet_nodes_mozi LIMIT 10;")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)





