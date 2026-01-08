"""
批量迁移所有僵尸网络类型的数据库
"""

import sys
import os

# 确保导入路径正确
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from migrate_single_botnet import migrate_botnet, DB_CONFIG
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 所有僵尸网络类型
BOTNET_TYPES = [
    'asruex',
    'mozi', 
    'andromeda',
    'moobot',
    'ramnit',
    'leethozer'
]

def main():
    print("=" * 80)
    print("批量迁移所有僵尸网络数据库")
    print("=" * 80)
    print(f"\n数据库配置:")
    print(f"  Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"  Database: {DB_CONFIG['database']}")
    print(f"\n将要迁移的僵尸网络类型:")
    for i, bot_type in enumerate(BOTNET_TYPES, 1):
        print(f"  {i}. {bot_type}")
    print()
    
    success_count = 0
    failed_count = 0
    failed_types = []
    
    for i, botnet_type in enumerate(BOTNET_TYPES, 1):
        print("\n" + "=" * 80)
        print(f"[{i}/{len(BOTNET_TYPES)}] 正在迁移: {botnet_type}")
        print("=" * 80)
        
        try:
            success = migrate_botnet(botnet_type)
            if success:
                success_count += 1
                print(f"✓ {botnet_type} 迁移成功")
            else:
                failed_count += 1
                failed_types.append(botnet_type)
                print(f"✗ {botnet_type} 迁移失败")
        except Exception as e:
            failed_count += 1
            failed_types.append(botnet_type)
            logger.error(f"✗ {botnet_type} 迁移异常: {e}")
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("迁移完成汇总")
    print("=" * 80)
    print(f"总计: {len(BOTNET_TYPES)} 个僵尸网络")
    print(f"成功: {success_count} 个")
    print(f"失败: {failed_count} 个")
    
    if failed_types:
        print(f"\n失败的类型:")
        for bot_type in failed_types:
            print(f"  - {bot_type}")
        print("\n建议: 对失败的类型单独运行迁移脚本并检查错误日志")
    else:
        print("\n✓ 所有僵尸网络迁移成功！")
    
    print("=" * 80)
    
    return failed_count == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
