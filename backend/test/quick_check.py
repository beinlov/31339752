#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速系统检查脚本
一键检查所有组件是否正常工作
"""
import sys
import os
import subprocess
import time

# 添加backend到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def check_python():
    """检查Python版本"""
    print("检查 Python 环境...")
    version = sys.version_info
    print(f"  Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("  ❌ Python 版本过低，需要 3.7+")
        return False
    
    print("  ✅ Python 版本符合要求")
    return True

def check_dependencies():
    """检查依赖包"""
    print("\n检查依赖包...")
    required = ['pymysql', 'fastapi', 'uvicorn', 'watchdog']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"  ✅ {package:15s} - 已安装")
        except ImportError:
            print(f"  ❌ {package:15s} - 未安装")
            missing.append(package)
    
    if missing:
        print(f"\n  缺少依赖包，请安装:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True

def check_database():
    """检查数据库连接"""
    print("\n检查数据库连接...")
    try:
        import pymysql
        from backend.config import DB_CONFIG
        
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        
        cursor.execute("SELECT DATABASE()")
        database = cursor.fetchone()[0]
        
        print(f"  ✅ 数据库连接成功")
        print(f"     MySQL 版本: {version}")
        print(f"     当前数据库: {database}")
        
        cursor.close()
        conn.close()
        return True
        
    except ImportError:
        print("  ❌ pymysql 未安装")
        return False
    except Exception as e:
        print(f"  ❌ 数据库连接失败: {e}")
        print(f"     请检查 backend/config.py 中的配置")
        return False

def check_tables():
    """检查数据库表"""
    print("\n检查数据库表...")
    try:
        import pymysql
        from backend.config import DB_CONFIG
        
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查节点表
        botnet_types = ['asruex', 'mozi', 'andromeda', 'moobot', 'ramnit', 'leethozer']
        node_tables_exist = 0
        stats_tables_exist = 0
        
        for botnet_type in botnet_types:
            node_table = f"botnet_nodes_{botnet_type}"
            china_table = f"china_botnet_{botnet_type}"
            global_table = f"global_botnet_{botnet_type}"
            
            # 检查节点表
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (DB_CONFIG['database'], node_table))
            
            if cursor.fetchone()[0] > 0:
                cursor.execute(f"SELECT COUNT(*) FROM {node_table}")
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"  ✅ {node_table:25s} - {count:6d} 条记录")
                    node_tables_exist += 1
            
            # 检查统计表
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (DB_CONFIG['database'], china_table))
            
            if cursor.fetchone()[0] > 0:
                stats_tables_exist += 1
        
        cursor.close()
        conn.close()
        
        if node_tables_exist > 0:
            print(f"\n  ✅ 找到 {node_tables_exist} 个有数据的节点表")
        else:
            print(f"\n  ⚠️  没有找到有数据的节点表")
            print(f"     这是正常的，需要先上传日志并处理")
        
        if stats_tables_exist > 0:
            print(f"  ✅ 找到 {stats_tables_exist} 个统计表")
        else:
            print(f"  ⚠️  没有找到统计表")
            print(f"     运行聚合器后会自动创建")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 检查表失败: {e}")
        return False

def check_files():
    """检查关键文件"""
    print("\n检查关键文件...")
    
    files = [
        ('backend/config.py', '配置文件'),
        ('backend/main.py', 'FastAPI后端'),
        ('backend/log_processor/main.py', '日志处理器'),
        ('backend/stats_aggregator/aggregator.py', '统计聚合器'),
        ('test_upload.py', '上传测试脚本'),
        ('backend/test_aggregator.py', '聚合器测试脚本'),
    ]
    
    all_exist = True
    for filepath, desc in files:
        if os.path.exists(filepath):
            print(f"  ✅ {desc:15s} - {filepath}")
        else:
            print(f"  ❌ {desc:15s} - {filepath} (不存在)")
            all_exist = False
    
    return all_exist

def check_directories():
    """检查关键目录"""
    print("\n检查关键目录...")
    
    dirs = [
        'backend',
        'backend/logs',
        'backend/log_processor',
        'backend/stats_aggregator',
        'fronted',
    ]
    
    for dirname in dirs:
        if os.path.exists(dirname):
            print(f"  ✅ {dirname}")
        else:
            print(f"  ⚠️  {dirname} (不存在，将自动创建)")
            try:
                os.makedirs(dirname, exist_ok=True)
                print(f"     已创建: {dirname}")
            except Exception as e:
                print(f"     创建失败: {e}")

def main():
    print_header("僵尸网络监控系统 - 快速检查")
    
    print("此脚本将检查系统各组件是否正常工作\n")
    
    results = []
    
    # 检查Python环境
    results.append(("Python环境", check_python()))
    
    # 检查依赖包
    results.append(("依赖包", check_dependencies()))
    
    if not all(r[1] for r in results):
        print_header("检查失败")
        print("请先解决上述问题，然后重新运行此脚本")
        return
    
    # 检查文件和目录
    results.append(("关键文件", check_files()))
    check_directories()
    
    # 检查数据库
    results.append(("数据库连接", check_database()))
    
    if results[-1][1]:
        check_tables()
    
    # 总结
    print_header("检查总结")
    
    for name, result in results:
        status = "✅ 正常" if result else "❌ 异常"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n检查结果: {passed}/{total} 通过")
    
    if passed == total:
        print_header("🎉 系统检查通过！")
        print("所有组件工作正常，可以开始使用系统。\n")
        print("下一步操作：")
        print("\n1. 测试统计聚合器:")
        print("   cd backend")
        print("   python test_aggregator.py")
        print("\n2. 启动所有服务:")
        print("   Windows: start_all_services.bat")
        print("   Linux:   ./start_all_services.sh")
        print("\n3. 测试日志上传:")
        print("   python test_upload.py")
        print("\n4. 查看文档:")
        print("   - 统计聚合器使用指南.md")
        print("   - backend/stats_aggregator/ARCHITECTURE.md")
        print()
    else:
        print_header("⚠️ 部分检查失败")
        print("请根据上述错误信息进行修复，然后重新运行此脚本。\n")
        print("常见问题：")
        print("  1. 依赖包未安装: pip install pymysql fastapi uvicorn watchdog")
        print("  2. 数据库连接失败: 检查 backend/config.py 中的配置")
        print("  3. MySQL未启动: 启动MySQL服务")
        print()

if __name__ == "__main__":
    main()



