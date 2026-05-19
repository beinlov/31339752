#!/usr/bin/env python3
"""
初始化可控性量化评估数据库表
"""

import pymysql
from config import DB_CONFIG

def init_controllability_tables():
    """创建可控性评估相关表并插入初始数据"""
    
    conn = None
    cursor = None
    
    try:
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("=" * 60)
        print("开始初始化可控性量化评估数据库表...")
        print("=" * 60)
        
        # 1. 创建可控性等级定义表
        print("\n[1/4] 创建 controllability_levels 表...")
        create_levels_table = """
        CREATE TABLE IF NOT EXISTS `controllability_levels` (
          `id` INT PRIMARY KEY,
          `level_name` VARCHAR(50) NOT NULL COMMENT '等级名称',
          `description` TEXT COMMENT '等级描述',
          `instruction_type` VARCHAR(100) COMMENT '指令类型说明',
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='僵尸网络可控性等级定义表'
        """
        cursor.execute(create_levels_table)
        print("   ✓ controllability_levels 表创建成功")
        
        # 2. 插入等级定义数据
        print("\n[2/4] 插入可控性等级定义数据...")
        
        # 先检查是否已有数据
        cursor.execute("SELECT COUNT(*) FROM controllability_levels")
        count = cursor.fetchone()[0]
        
        if count == 0:
            insert_levels = """
            INSERT INTO `controllability_levels` (`id`, `level_name`, `description`, `instruction_type`) VALUES
            (1, '自卸载级', '僵尸程序有卸载指令或等效指令，直接发送卸载指令', '卸载指令或等效指令'),
            (2, '代码执行级', '僵尸程序有下载执行指令，编写专杀程序使其下载执行', '下载执行指令'),
            (3, '命令执行级', '僵尸程序可执行任意系统命令，构建命令脚本执行清除', '系统命令执行'),
            (4, '非执行级', '以上指令/功能都没有，可以通过特定方法进行清除', '特定方法清除'),
            (5, '非清除级', '以上方式均不可用，无法进行清除，只能实施抑制阻断', '抑制阻断')
            """
            cursor.execute(insert_levels)
            print("   ✓ 成功插入 5 个可控性等级定义")
        else:
            print(f"   ⚠ 表中已有 {count} 条数据，跳过插入")
        
        # 3. 创建僵尸网络可控性映射表
        print("\n[3/4] 创建 botnet_controllability_mapping 表...")
        create_mapping_table = """
        CREATE TABLE IF NOT EXISTS `botnet_controllability_mapping` (
          `id` INT PRIMARY KEY AUTO_INCREMENT,
          `botnet_name` VARCHAR(100) NOT NULL COMMENT '僵尸网络名称',
          `level_id` INT NOT NULL COMMENT '可控性等级ID(1-5)',
          `examples` TEXT COMMENT '示例说明',
          `notes` TEXT COMMENT '备注信息',
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          UNIQUE KEY `uk_botnet_level` (`botnet_name`, `level_id`),
          KEY `idx_botnet_name` (`botnet_name`),
          KEY `idx_level_id` (`level_id`),
          CONSTRAINT `fk_level` FOREIGN KEY (`level_id`) REFERENCES `controllability_levels` (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='僵尸网络可控性等级映射表'
        """
        cursor.execute(create_mapping_table)
        print("   ✓ botnet_controllability_mapping 表创建成功")
        
        # 4. 插入示例映射数据
        print("\n[4/4] 插入示例映射数据...")
        
        cursor.execute("SELECT COUNT(*) FROM botnet_controllability_mapping")
        count = cursor.fetchone()[0]
        
        if count == 0:
            insert_mappings = """
            INSERT INTO `botnet_controllability_mapping` (`botnet_name`, `level_id`, `examples`, `notes`) VALUES
            ('andromeda', 1, 'AndroMeda', '僵尸程序有卸载指令'),
            ('ramnit', 2, 'Ramnit', '有下载执行指令，可编写专杀程序'),
            ('mozi', 2, 'Mozi', '支持下载执行功能'),
            ('asruex', 2, 'Asruex', '支持代码执行'),
            ('asruex', 3, 'Asruex', '支持命令执行'),
            ('autoupdate', 3, 'AutoUpdate', '可执行系统命令'),
            ('moobot', 4, 'Moobot', '需要通过漏洞打入节点内部清除'),
            ('leethozer', 5, 'LeetHozer', '无法清除，只能抑制阻断')
            """
            cursor.execute(insert_mappings)
            print("   ✓ 成功插入 8 条示例映射数据")
        else:
            print(f"   ⚠ 表中已有 {count} 条数据，跳过插入")
        
        # 提交事务
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✅ 可控性量化评估数据库表初始化完成！")
        print("=" * 60)
        
        # 显示结果统计
        cursor.execute("SELECT COUNT(*) FROM controllability_levels")
        levels_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM botnet_controllability_mapping")
        mappings_count = cursor.fetchone()[0]
        
        print(f"\n📊 统计信息:")
        print(f"   - 可控性等级: {levels_count} 个")
        print(f"   - 僵尸网络映射: {mappings_count} 条")
        print("\n🎉 现在可以重启后端服务使用新功能了！")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    init_controllability_tables()
