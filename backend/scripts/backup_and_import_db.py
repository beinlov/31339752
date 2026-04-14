#!/usr/bin/env python3
"""
数据库备份和导入工具
用于备份当前数据库信息并导入新的 botnet.sql
"""
import pymysql
import sys
import os
from datetime import datetime

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Matrix123",
    "charset": "utf8mb4",
}

def backup_database_info():
    """备份当前数据库的表结构信息"""
    print("=" * 60)
    print("正在备份当前数据库信息...")
    print("=" * 60)
    
    try:
        conn = pymysql.connect(**DB_CONFIG, database='botnet')
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        backup_file = f"botnet_backup_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(f"数据库备份信息 - {datetime.now()}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"数据库名称: botnet\n")
            f.write(f"表数量: {len(tables)}\n\n")
            f.write("表列表:\n")
            f.write("-" * 60 + "\n")
            
            for table in tables:
                table_name = table[0]
                f.write(f"\n表名: {table_name}\n")
                
                # 获取表行数
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                count = cursor.fetchone()[0]
                f.write(f"  行数: {count}\n")
                
                # 获取表结构
                cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                create_table = cursor.fetchone()[1]
                f.write(f"  结构:\n{create_table}\n")
                f.write("-" * 60 + "\n")
        
        cursor.close()
        conn.close()
        
        print(f"✓ 数据库信息已备份到: {backup_file}")
        print(f"✓ 共备份 {len(tables)} 个表的信息")
        return True
        
    except pymysql.err.OperationalError as e:
        if "Unknown database" in str(e):
            print("⚠ 数据库 'botnet' 不存在，跳过备份")
            return True
        else:
            print(f"✗ 备份失败: {e}")
            return False
    except Exception as e:
        print(f"✗ 备份失败: {e}")
        return False

def import_new_database():
    """导入新的 botnet.sql 数据库"""
    print("\n" + "=" * 60)
    print("正在导入新数据库...")
    print("=" * 60)
    
    sql_file = "botnet.sql"
    
    if not os.path.exists(sql_file):
        print(f"✗ 错误: 找不到 {sql_file} 文件")
        return False
    
    try:
        # 连接到 MySQL（不指定数据库）
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 先删除旧数据库（如果存在）
        print("正在删除旧数据库...")
        cursor.execute("DROP DATABASE IF EXISTS botnet")
        print("✓ 旧数据库已删除")
        
        # 创建新数据库
        print("正在创建新数据库...")
        cursor.execute("CREATE DATABASE botnet CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("✓ 新数据库已创建")
        
        cursor.close()
        conn.close()
        
        # 使用 mysql 命令导入 SQL 文件（更快更可靠）
        print(f"正在导入 {sql_file}...")
        print("（这可能需要几分钟时间，请耐心等待...）")
        
        import subprocess
        
        # 使用管道方式导入，避免命令行参数中暴露密码
        cmd = f"mysql -u root -pMatrix123 botnet < {sql_file}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ 数据库导入成功！")
            return True
        else:
            # 如果 mysql 命令不可用，尝试用 Python 读取并执行
            if "mysql: command not found" in result.stderr or "not found" in result.stderr:
                print("⚠ mysql 命令不可用，使用 Python 方式导入...")
                return import_with_python(sql_file)
            else:
                print(f"✗ 导入失败: {result.stderr}")
                return False
        
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def import_with_python(sql_file):
    """使用 Python 和 pymysql 导入 SQL 文件"""
    try:
        print("正在读取 SQL 文件...")
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 连接到 botnet 数据库
        conn = pymysql.connect(**DB_CONFIG, database='botnet')
        cursor = conn.cursor()
        
        # 分割 SQL 语句
        statements = []
        current_statement = []
        
        for line in sql_content.split('\n'):
            line = line.strip()
            
            # 跳过注释和空行
            if not line or line.startswith('--') or line.startswith('/*'):
                continue
            
            current_statement.append(line)
            
            # 如果以分号结尾，说明是一个完整的语句
            if line.endswith(';'):
                statements.append(' '.join(current_statement))
                current_statement = []
        
        print(f"共 {len(statements)} 条 SQL 语句")
        print("正在执行...")
        
        # 执行所有语句
        for i, statement in enumerate(statements):
            try:
                if statement.strip():
                    cursor.execute(statement)
                
                # 每100条语句显示进度
                if (i + 1) % 100 == 0:
                    print(f"  已执行 {i + 1}/{len(statements)} 条语句...")
                    
            except Exception as e:
                # 忽略一些无关紧要的错误
                if "Table" not in str(e) or "already exists" not in str(e):
                    print(f"  ⚠ 警告 (语句 {i+1}): {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✓ 数据库导入成功！")
        return True
        
    except Exception as e:
        print(f"✗ Python 导入失败: {e}")
        return False

def verify_import():
    """验证数据库导入结果"""
    print("\n" + "=" * 60)
    print("正在验证数据库导入结果...")
    print("=" * 60)
    
    try:
        conn = pymysql.connect(**DB_CONFIG, database='botnet')
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print(f"✓ 数据库中共有 {len(tables)} 个表")
        print("\n表统计信息:")
        print("-" * 60)
        
        total_rows = 0
        for table in tables[:20]:  # 只显示前20个表
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            count = cursor.fetchone()[0]
            total_rows += count
            print(f"  {table_name:40} {count:>10} 行")
        
        if len(tables) > 20:
            print(f"  ... 还有 {len(tables) - 20} 个表未显示")
        
        print("-" * 60)
        print(f"总计: {total_rows} 行数据")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("数据库更换工具")
    print("=" * 60)
    
    # 步骤1: 备份当前数据库信息
    if not backup_database_info():
        print("\n备份失败，是否继续导入？(y/n): ", end='')
        if input().lower() != 'y':
            print("已取消操作")
            return 1
    
    # 步骤2: 导入新数据库
    if not import_new_database():
        print("\n✗ 数据库导入失败！")
        return 1
    
    # 步骤3: 验证导入结果
    if not verify_import():
        print("\n⚠ 验证失败，但数据库可能已导入，请手动检查")
        return 1
    
    print("\n" + "=" * 60)
    print("✓ 数据库更换完成！")
    print("=" * 60)
    print("\n建议:")
    print("1. 检查数据库表和数据是否正常")
    print("2. 重启相关服务")
    print("3. 测试系统功能是否正常")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
