#!/usr/bin/env python3
"""
可控性量化评估数据库表重构迁移脚本
从基于等级映射的旧表结构迁移到基于特征字段的新表结构
"""

import pymysql
from config import DB_CONFIG
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def migrate_controllability_tables():
    """迁移可控性评估数据库表"""
    
    conn = None
    cursor = None
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("=" * 80)
        print("开始迁移可控性量化评估数据库表结构...")
        print("=" * 80)
        
        # 1. 备份旧表
        print("\n[1/5] 备份旧表...")
        try:
            cursor.execute("DROP TABLE IF EXISTS botnet_controllability_mapping_backup")
            cursor.execute("""
                CREATE TABLE botnet_controllability_mapping_backup 
                AS SELECT * FROM botnet_controllability_mapping
            """)
            cursor.execute("SELECT COUNT(*) FROM botnet_controllability_mapping_backup")
            backup_count = cursor.fetchone()[0]
            print(f"   ✓ 已备份 {backup_count} 条记录到 botnet_controllability_mapping_backup")
        except Exception as e:
            logger.warning(f"   ⚠ 备份旧表失败（可能表不存在）: {e}")
        
        # 2. 创建新表
        print("\n[2/5] 创建新表 botnet_controllability_features...")
        cursor.execute("DROP TABLE IF EXISTS botnet_controllability_features")
        
        create_table_sql = """
        CREATE TABLE `botnet_controllability_features` (
          `id` INT PRIMARY KEY AUTO_INCREMENT,
          `botnet_name` VARCHAR(100) NOT NULL UNIQUE COMMENT '僵尸网络名称',
          `has_uninstall_instruction` BOOLEAN DEFAULT FALSE COMMENT '是否有卸载或等效指令（类别1）',
          `has_download_instruction` BOOLEAN DEFAULT FALSE COMMENT '是否有下载指令（类别2）',
          `has_command_execution` BOOLEAN DEFAULT FALSE COMMENT '是否可执行任意系统命令（类别3）',
          `has_special_cleanup` BOOLEAN DEFAULT FALSE COMMENT '是否可通过特定方法清除（类别4）',
          `notes` TEXT COMMENT '备注信息',
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          KEY `idx_botnet_name` (`botnet_name`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='僵尸网络可控性特征表'
        """
        cursor.execute(create_table_sql)
        print("   ✓ 新表创建成功")
        
        # 3. 从旧表迁移数据
        print("\n[3/5] 从旧表迁移数据...")
        
        # 定义初始数据（根据之前的配置）
        initial_data = {
            'andromeda': {
                'has_uninstall_instruction': True,  # 类别1
                'has_download_instruction': False,
                'has_command_execution': False,
                'has_special_cleanup': False,
                'notes': '僵尸程序有卸载指令'
            },
            'ramnit': {
                'has_uninstall_instruction': False,
                'has_download_instruction': True,  # 类别2
                'has_command_execution': False,
                'has_special_cleanup': False,
                'notes': '有下载执行指令，可编写专杀程序'
            },
            'mozi': {
                'has_uninstall_instruction': False,
                'has_download_instruction': True,  # 类别2
                'has_command_execution': False,
                'has_special_cleanup': False,
                'notes': '支持下载执行功能'
            },
            'asruex': {
                'has_uninstall_instruction': False,
                'has_download_instruction': True,  # 类别2
                'has_command_execution': True,     # 类别3
                'has_special_cleanup': False,
                'notes': '支持代码执行和命令执行'
            },
            'autoupdate': {
                'has_uninstall_instruction': False,
                'has_download_instruction': False,
                'has_command_execution': True,  # 类别3
                'has_special_cleanup': False,
                'notes': '可执行系统命令'
            },
            'moobot': {
                'has_uninstall_instruction': False,
                'has_download_instruction': False,
                'has_command_execution': False,
                'has_special_cleanup': True,  # 类别4
                'notes': '需要通过漏洞打入节点内部清除'
            },
            'leethozer': {
                'has_uninstall_instruction': False,
                'has_download_instruction': False,
                'has_command_execution': False,
                'has_special_cleanup': False,  # 类别5（都是False）
                'notes': '无法清除，只能抑制阻断'
            },
            'fodcha': {
                'has_uninstall_instruction': False,
                'has_download_instruction': False,
                'has_command_execution': False,
                'has_special_cleanup': False,  # 类别5
                'notes': '待评估'
            },
            'utg_q_008': {
                'has_uninstall_instruction': False,
                'has_download_instruction': False,
                'has_command_execution': False,
                'has_special_cleanup': False,  # 类别5
                'notes': '待评估'
            }
        }
        
        # 插入数据
        insert_sql = """
        INSERT INTO botnet_controllability_features 
        (botnet_name, has_uninstall_instruction, has_download_instruction, 
         has_command_execution, has_special_cleanup, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        inserted_count = 0
        for botnet_name, features in initial_data.items():
            try:
                cursor.execute(insert_sql, (
                    botnet_name,
                    features['has_uninstall_instruction'],
                    features['has_download_instruction'],
                    features['has_command_execution'],
                    features['has_special_cleanup'],
                    features['notes']
                ))
                inserted_count += 1
            except Exception as e:
                logger.error(f"   ✗ 插入 {botnet_name} 失败: {e}")
        
        print(f"   ✓ 成功迁移 {inserted_count} 个僵尸网络的特征数据")
        
        # 4. 删除旧表（可选）
        print("\n[4/5] 处理旧表...")
        try:
            cursor.execute("DROP TABLE IF EXISTS botnet_controllability_mapping")
            print("   ✓ 已删除旧表 botnet_controllability_mapping")
        except Exception as e:
            logger.warning(f"   ⚠ 删除旧表失败: {e}")
        
        # 5. 提交事务
        print("\n[5/5] 提交更改...")
        conn.commit()
        print("   ✓ 数据库更改已提交")
        
        # 显示迁移结果
        print("\n" + "=" * 80)
        print("✅ 数据库表迁移完成！")
        print("=" * 80)
        
        # 显示新表数据统计
        cursor.execute("SELECT COUNT(*) FROM botnet_controllability_features")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT 
                SUM(has_uninstall_instruction) as level1,
                SUM(has_download_instruction) as level2,
                SUM(has_command_execution) as level3,
                SUM(has_special_cleanup) as level4
            FROM botnet_controllability_features
        """)
        stats = cursor.fetchone()
        
        print(f"\n📊 迁移统计:")
        print(f"   - 总僵尸网络数: {total_count}")
        print(f"   - 具有类别1特征（卸载指令）: {stats[0]}")
        print(f"   - 具有类别2特征（下载指令）: {stats[1]}")
        print(f"   - 具有类别3特征（命令执行）: {stats[2]}")
        print(f"   - 具有类别4特征（特殊清除）: {stats[3]}")
        
        print("\n🎉 现在可以重启后端服务使用新的可控性评估功能！")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ 迁移失败: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    migrate_controllability_tables()
