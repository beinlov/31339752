#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移执行脚本
自动执行所有未执行的迁移文件
"""
import os
import sys
import pymysql
import time
from pathlib import Path
from datetime import datetime

# 添加 backend 到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from config import DB_CONFIG


class MigrationManager:
    """数据库迁移管理器"""
    
    def __init__(self):
        self.conn = pymysql.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        self.migrations_dir = Path(__file__).parent / 'versions'
        self.ensure_migration_table()
    
    def ensure_migration_table(self):
        """确保迁移记录表存在"""
        print("检查迁移记录表...")
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                version VARCHAR(50) UNIQUE NOT NULL,
                description VARCHAR(255),
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                execution_time_ms INT,
                INDEX idx_version (version)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据库迁移记录表'
        """)
        self.conn.commit()
        print("✓ 迁移记录表已就绪")
    
    def get_executed_migrations(self):
        """获取已执行的迁移列表"""
        self.cursor.execute("SELECT version FROM schema_migrations ORDER BY id")
        return {row['version'] for row in self.cursor.fetchall()}
    
    def get_pending_migrations(self):
        """获取待执行的迁移文件"""
        if not self.migrations_dir.exists():
            print(f"⚠️  迁移目录不存在: {self.migrations_dir}")
            self.migrations_dir.mkdir(parents=True, exist_ok=True)
            return []
        
        executed = self.get_executed_migrations()
        all_files = sorted(self.migrations_dir.glob('*.sql'))
        
        pending = []
        for file_path in all_files:
            version = file_path.stem
            if version not in executed:
                pending.append(file_path)
        
        return pending
    
    def extract_description(self, sql_content):
        """从 SQL 文件中提取描述信息"""
        for line in sql_content.split('\n'):
            if 'Description:' in line:
                return line.split('Description:')[1].strip().strip('-').strip()
        return "No description"
    
    def execute_migration(self, file_path):
        """执行单个迁移文件"""
        version = file_path.stem
        
        print(f"\n{'='*60}")
        print(f"执行迁移: {version}")
        print(f"文件: {file_path.name}")
        print(f"{'='*60}")
        
        # 读取 SQL 文件
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        description = self.extract_description(sql_content)
        
        try:
            start_time = time.time()
            
            # 执行 SQL（按分号分割多个语句）
            statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
            
            for statement in statements:
                if statement:
                    try:
                        self.cursor.execute(statement)
                        result = self.cursor.fetchall() if self.cursor.description else None
                        if result:
                            for row in result:
                                print(f"  → {row}")
                    except Exception as e:
                        # 某些语句（如 SELECT）可能在某些情况下失败，继续执行
                        if 'SELECT' not in statement.upper():
                            raise
            
            self.conn.commit()
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # 记录迁移
            self.cursor.execute("""
                INSERT INTO schema_migrations (version, description, execution_time_ms)
                VALUES (%s, %s, %s)
            """, (version, description, execution_time))
            self.conn.commit()
            
            print(f"✓ 迁移成功！耗时: {execution_time}ms")
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"✗ 迁移失败: {e}")
            print(f"  版本: {version}")
            print(f"  文件: {file_path}")
            return False
    
    def run_all_pending(self):
        """执行所有待执行的迁移"""
        pending = self.get_pending_migrations()
        
        if not pending:
            print("\n✓ 所有迁移都已执行，无需操作")
            return True
        
        print(f"\n发现 {len(pending)} 个待执行的迁移:")
        for file_path in pending:
            print(f"  - {file_path.name}")
        
        print(f"\n开始执行迁移...")
        
        success_count = 0
        for file_path in pending:
            if self.execute_migration(file_path):
                success_count += 1
            else:
                print(f"\n✗ 迁移在 {file_path.name} 处失败，停止执行")
                break
        
        print(f"\n{'='*60}")
        print(f"迁移执行完成")
        print(f"成功: {success_count}/{len(pending)}")
        print(f"{'='*60}\n")
        
        return success_count == len(pending)
    
    def show_status(self):
        """显示迁移状态"""
        print(f"\n{'='*60}")
        print("数据库迁移状态")
        print(f"{'='*60}\n")
        
        # 已执行的迁移
        self.cursor.execute("""
            SELECT version, description, executed_at, execution_time_ms
            FROM schema_migrations
            ORDER BY id
        """)
        executed = self.cursor.fetchall()
        
        if executed:
            print(f"已执行的迁移 ({len(executed)} 个):")
            for row in executed:
                print(f"  ✓ {row['version']}")
                print(f"    描述: {row['description']}")
                print(f"    时间: {row['executed_at']} (耗时: {row['execution_time_ms']}ms)")
        else:
            print("尚未执行任何迁移")
        
        # 待执行的迁移
        pending = self.get_pending_migrations()
        if pending:
            print(f"\n待执行的迁移 ({len(pending)} 个):")
            for file_path in pending:
                print(f"  ○ {file_path.name}")
        else:
            print("\n✓ 所有迁移都已执行")
        
        print()
    
    def close(self):
        """关闭数据库连接"""
        self.cursor.close()
        self.conn.close()


def main():
    """主函数"""
    print(f"\n{'='*60}")
    print("数据库迁移管理工具")
    print(f"{'='*60}\n")
    
    print(f"数据库: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"用户: {DB_CONFIG['user']}")
    
    manager = MigrationManager()
    
    try:
        # 显示当前状态
        manager.show_status()
        
        # 执行待执行的迁移
        pending = manager.get_pending_migrations()
        if pending:
            response = input(f"\n是否执行 {len(pending)} 个待执行的迁移? (yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                manager.run_all_pending()
            else:
                print("已取消")
        
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        manager.close()


if __name__ == '__main__':
    main()
