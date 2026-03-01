#!/usr/bin/env python3
"""
部署检查脚本 - 验证环境和配置

检查项目：
1. Python版本和依赖包
2. 配置文件完整性
3. API_KEY安全性
4. 文件路径和权限
5. 日志目录可用性
"""

import sys
import os
import json
from pathlib import Path
import importlib

def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_python_version():
    """检查Python版本"""
    print_header("检查1: Python版本")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print(f"当前版本: Python {version_str}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ 要求: Python >= 3.7")
        return False
    else:
        print("✅ 版本符合要求")
        return True

def check_dependencies():
    """检查依赖包"""
    print_header("检查2: 依赖包")
    
    required = {
        'aiohttp': 'HTTP异步客户端',
        'aiofiles': '异步文件操作',
    }
    
    all_ok = True
    
    for package, desc in required.items():
        try:
            importlib.import_module(package)
            print(f"✅ {package:15s} - {desc}")
        except ImportError:
            print(f"❌ {package:15s} - 未安装")
            all_ok = False
    
    if not all_ok:
        print("\n安装命令:")
        print("  pip3 install aiohttp aiofiles")
    
    return all_ok

def check_config_file():
    """检查配置文件"""
    print_header("检查3: 配置文件")
    
    config_file = Path(__file__).parent / "config.json"
    
    if not config_file.exists():
        print(f"❌ 配置文件不存在: {config_file}")
        print("\n创建配置文件:")
        print("  cp config.example.json config.json")
        print("  nano config.json  # 编辑配置")
        return False
    
    print(f"✅ 配置文件存在: {config_file}")
    
    # 检查配置文件权限
    try:
        stat = config_file.stat()
        mode = oct(stat.st_mode)[-3:]
        
        print(f"文件权限: {mode}")
        
        if mode != '600':
            print("⚠️  建议权限: 600（只有owner可读写）")
            print("  chmod 600 config.json")
        else:
            print("✅ 权限安全")
    except Exception as e:
        print(f"⚠️  无法检查权限: {e}")
    
    # 检查配置内容
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        required_sections = ['server', 'botnet', 'processing', 'files']
        
        for section in required_sections:
            if section in config:
                print(f"✅ 配置段 [{section}] 存在")
            else:
                print(f"❌ 配置段 [{section}] 缺失")
                return False
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ 配置文件JSON格式错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return False

def check_api_key_security():
    """检查API_KEY安全性"""
    print_header("检查4: API_KEY安全性")
    
    # 检查环境变量
    env_key = os.environ.get('BOTNET_API_KEY')
    
    if env_key:
        print("✅ 环境变量 BOTNET_API_KEY 已设置")
        
        # 检查密钥强度
        if len(env_key) < 16:
            print("⚠️  API_KEY太短，建议至少16字符")
        elif env_key == "YOUR_API_KEY_HERE":
            print("❌ 使用的是示例KEY，请更换")
            return False
        else:
            print(f"✅ API_KEY长度: {len(env_key)}字符")
        
        return True
    else:
        print("⚠️  未设置环境变量 BOTNET_API_KEY")
        print("\n设置方法:")
        print('  export BOTNET_API_KEY="your-secret-key"')
        print('  或使用: export BOTNET_API_KEY="$(openssl rand -hex 32)"')
        
        # 检查配置文件中的KEY
        config_file = Path(__file__).parent / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                api_key = config.get('server', {}).get('api_key', '')
                
                if api_key == "YOUR_API_KEY_HERE":
                    print("❌ 配置文件中使用示例KEY")
                    return False
                elif api_key:
                    print("⚠️  配置文件中有API_KEY，但建议使用环境变量")
                    return True
            except:
                pass
        
        return False

def check_file_paths():
    """检查文件路径"""
    print_header("检查5: 文件路径和权限")
    
    config_file = Path(__file__).parent / "config.json"
    
    if not config_file.exists():
        print("⚠️  配置文件不存在，跳过路径检查")
        return True
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        files = config.get('files', {})
        
        paths_to_check = [
            ('state_file', '状态文件'),
            ('offset_state_file', '偏移量文件'),
            ('log_file', '日志文件'),
        ]
        
        all_ok = True
        
        for key, desc in paths_to_check:
            path_str = files.get(key)
            if not path_str:
                continue
            
            path = Path(path_str)
            parent_dir = path.parent
            
            # 检查父目录是否存在
            if parent_dir.exists():
                # 检查是否可写
                if os.access(parent_dir, os.W_OK):
                    print(f"✅ {desc:12s}: {path_str}")
                else:
                    print(f"❌ {desc:12s}: {path_str} (目录不可写)")
                    all_ok = False
            else:
                print(f"⚠️  {desc:12s}: {path_str} (目录不存在)")
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"❌ 检查文件路径失败: {e}")
        return False

def check_log_directory():
    """检查日志目录"""
    print_header("检查6: 日志目录")
    
    config_file = Path(__file__).parent / "config.json"
    
    if not config_file.exists():
        print("⚠️  配置文件不存在，跳过检查")
        return True
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        log_dir = config.get('botnet', {}).get('log_dir')
        log_pattern = config.get('botnet', {}).get('log_file_pattern')
        
        if not log_dir:
            print("❌ 配置中未设置 botnet.log_dir")
            return False
        
        print(f"日志目录: {log_dir}")
        print(f"文件模式: {log_pattern}")
        
        log_path = Path(log_dir)
        
        # 检查目录是否存在
        if not log_path.exists():
            print(f"❌ 目录不存在: {log_dir}")
            return False
        
        print("✅ 目录存在")
        
        # 检查是否可读
        if not os.access(log_path, os.R_OK):
            print(f"❌ 目录不可读")
            return False
        
        print("✅ 目录可读")
        
        # 检查是否有日志文件
        if log_pattern:
            # 简单的glob检查
            pattern_prefix = log_pattern.split('{')[0] if '{' in log_pattern else log_pattern
            
            matching_files = list(log_path.glob(f"{pattern_prefix}*"))
            
            if matching_files:
                print(f"✅ 找到 {len(matching_files)} 个匹配的日志文件")
                
                # 显示最近的3个文件
                recent_files = sorted(matching_files, key=lambda p: p.stat().st_mtime, reverse=True)[:3]
                print("\n最近的日志文件:")
                for f in recent_files:
                    size = f.stat().st_size / 1024
                    print(f"  - {f.name} ({size:.1f} KB)")
            else:
                print(f"⚠️  未找到匹配的日志文件（模式: {pattern_prefix}*）")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查日志目录失败: {e}")
        return False

def check_network_connectivity():
    """检查网络连接"""
    print_header("检查7: 网络连接")
    
    config_file = Path(__file__).parent / "config.json"
    
    if not config_file.exists():
        print("⚠️  配置文件不存在，跳过检查")
        return True
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        api_endpoint = config.get('server', {}).get('api_endpoint')
        
        if not api_endpoint or api_endpoint == "https://your-server.example.com":
            print("⚠️  API端点未配置或使用示例值")
            return False
        
        print(f"API端点: {api_endpoint}")
        
        # 尝试简单的连接测试
        try:
            from urllib.parse import urlparse
            import socket
            
            parsed = urlparse(api_endpoint)
            host = parsed.netloc.split(':')[0]
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            
            print(f"测试连接: {host}:{port}")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"✅ 可以连接到 {host}:{port}")
                return True
            else:
                print(f"❌ 无法连接到 {host}:{port}")
                return False
                
        except Exception as e:
            print(f"⚠️  连接测试失败: {e}")
            return False
        
    except Exception as e:
        print(f"❌ 检查网络失败: {e}")
        return False

def main():
    """运行所有检查"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*18 + "部署检查报告" + " "*26 + "║")
    print("╚" + "="*58 + "╝")
    
    checks = [
        ("Python版本", check_python_version),
        ("依赖包", check_dependencies),
        ("配置文件", check_config_file),
        ("API_KEY安全", check_api_key_security),
        ("文件路径", check_file_paths),
        ("日志目录", check_log_directory),
        ("网络连接", check_network_connectivity),
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 检查异常: {e}")
            results.append((name, False))
    
    # 打印总结
    print_header("检查总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:15s}: {status}")
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有检查通过！可以开始部署。")
        return 0
    else:
        print("\n⚠️  部分检查未通过，请修复后再部署。")
        return 1

if __name__ == '__main__':
    sys.exit(main())
