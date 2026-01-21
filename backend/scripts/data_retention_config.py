"""
数据保留策略配置模块
定义数据分层存储和清理策略
"""
import os
from datetime import timedelta

# ============================================================
# 数据保留策略配置
# ============================================================

# 数据保留天数
HOT_DATA_DAYS = int(os.getenv('HOT_DATA_DAYS', 30))       # 热数据：1个月
WARM_DATA_DAYS = int(os.getenv('WARM_DATA_DAYS', 180))   # 温数据：6个月
COLD_DATA_DAYS = int(os.getenv('COLD_DATA_DAYS', 365))   # 冷数据：1年后删除归档

# 数据归档配置
ENABLE_ARCHIVE = os.getenv('ENABLE_ARCHIVE', 'true').lower() == 'true'
ARCHIVE_BASE_PATH = os.getenv('ARCHIVE_PATH', '/data/archive/botnet')
ARCHIVE_FORMAT = os.getenv('ARCHIVE_FORMAT', 'parquet')  # 'json', 'parquet', 'csv'
ARCHIVE_COMPRESSION = 'snappy'  # Parquet压缩算法

# 数据清理配置
CLEANUP_ENABLED = os.getenv('CLEANUP_ENABLED', 'true').lower() == 'true'
CLEANUP_BATCH_SIZE = int(os.getenv('CLEANUP_BATCH_SIZE', 10000))  # 每批删除数量
CLEANUP_DELAY_SECONDS = int(os.getenv('CLEANUP_DELAY_SECONDS', 1))  # 批次间延迟

# 安全保护
REQUIRE_ARCHIVE_BEFORE_DELETE = True  # 删除前必须先归档
KEEP_ARCHIVE_LOG = True  # 保留归档日志
MAX_DELETE_PER_RUN = 1000000  # 单次运行最多删除100万条

# 表配置
TABLES_CONFIG = {
    # 通信记录表 - 大量数据，需要定期清理
    'communications': {
        'pattern': 'botnet_communications_*',
        'time_column': 'communication_time',
        'archive_enabled': True,
        'cleanup_enabled': True,
        'hot_days': HOT_DATA_DAYS,
        'warm_days': WARM_DATA_DAYS,
    },
    # 节点表 - 数据量小，保留所有历史，仅标记inactive
    'nodes': {
        'pattern': 'botnet_nodes_*',
        'time_column': 'last_seen',
        'archive_enabled': False,  # 不归档，直接保留
        'cleanup_enabled': False,  # 不删除，仅更新状态
        'hot_days': HOT_DATA_DAYS,
        'warm_days': WARM_DATA_DAYS,
    },
    # 统计表 - 数据量极小，永久保留
    'stats': {
        'patterns': ['china_botnet_*', 'global_botnet_*'],
        'archive_enabled': False,
        'cleanup_enabled': False,
    }
}

# 僵尸网络类型列表
BOTNET_TYPES = [
    'asruex', 'mozi', 'andromeda', 
    'moobot', 'ramnit', 'leethozer'
]

# 归档文件命名模板
ARCHIVE_FILENAME_TEMPLATE = "{botnet_type}_{table_type}_{year}{month:02d}.{format}"

# 日志配置
RETENTION_LOG_PATH = os.getenv('RETENTION_LOG_PATH', '/var/log/botnet/retention.log')
RETENTION_LOG_LEVEL = os.getenv('RETENTION_LOG_LEVEL', 'INFO')

# 性能监控
ENABLE_PERFORMANCE_MONITORING = True
MONITOR_BATCH_INTERVAL = 100  # 每处理100批记录一次性能指标

# 通知配置（可选）
ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'false').lower() == 'true'
NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL', '')
NOTIFICATION_WEBHOOK = os.getenv('NOTIFICATION_WEBHOOK', '')

# 数据验证
VALIDATE_ARCHIVE_INTEGRITY = True  # 归档后验证文件完整性
ARCHIVE_CHECKSUM_ALGORITHM = 'sha256'

# ============================================================
# 辅助函数
# ============================================================

def get_archive_path(botnet_type: str, table_type: str, year: int, month: int) -> str:
    """
    生成归档文件路径
    
    Args:
        botnet_type: 僵尸网络类型
        table_type: 表类型（communications, nodes等）
        year: 年份
        month: 月份
        
    Returns:
        归档文件完整路径
    """
    filename = ARCHIVE_FILENAME_TEMPLATE.format(
        botnet_type=botnet_type,
        table_type=table_type,
        year=year,
        month=month,
        format=ARCHIVE_FORMAT
    )
    
    # 按年月组织目录结构
    year_month_dir = os.path.join(ARCHIVE_BASE_PATH, str(year), f"{month:02d}")
    os.makedirs(year_month_dir, exist_ok=True)
    
    return os.path.join(year_month_dir, filename)


def get_retention_policy(table_type: str) -> dict:
    """
    获取指定表类型的保留策略
    
    Args:
        table_type: 表类型
        
    Returns:
        保留策略配置字典
    """
    return TABLES_CONFIG.get(table_type, {})


def is_archive_enabled(table_type: str) -> bool:
    """检查是否启用归档"""
    policy = get_retention_policy(table_type)
    return ENABLE_ARCHIVE and policy.get('archive_enabled', False)


def is_cleanup_enabled(table_type: str) -> bool:
    """检查是否启用清理"""
    policy = get_retention_policy(table_type)
    return CLEANUP_ENABLED and policy.get('cleanup_enabled', False)


# ============================================================
# 配置验证
# ============================================================

def validate_config():
    """验证配置有效性"""
    errors = []
    
    # 检查天数配置合理性
    if HOT_DATA_DAYS >= WARM_DATA_DAYS:
        errors.append("HOT_DATA_DAYS must be less than WARM_DATA_DAYS")
    
    if WARM_DATA_DAYS >= COLD_DATA_DAYS:
        errors.append("WARM_DATA_DAYS must be less than COLD_DATA_DAYS")
    
    # 检查归档路径
    if ENABLE_ARCHIVE:
        if not ARCHIVE_BASE_PATH:
            errors.append("ARCHIVE_BASE_PATH must be set when ENABLE_ARCHIVE is true")
        else:
            try:
                os.makedirs(ARCHIVE_BASE_PATH, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create archive directory: {e}")
    
    # 检查批量大小
    if CLEANUP_BATCH_SIZE <= 0:
        errors.append("CLEANUP_BATCH_SIZE must be greater than 0")
    
    if MAX_DELETE_PER_RUN < CLEANUP_BATCH_SIZE:
        errors.append("MAX_DELETE_PER_RUN should be >= CLEANUP_BATCH_SIZE")
    
    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(f"- {e}" for e in errors))
    
    return True


if __name__ == "__main__":
    # 测试配置
    print("数据保留策略配置")
    print("=" * 60)
    print(f"热数据保留天数: {HOT_DATA_DAYS}")
    print(f"温数据保留天数: {WARM_DATA_DAYS}")
    print(f"冷数据保留天数: {COLD_DATA_DAYS}")
    print(f"归档启用: {ENABLE_ARCHIVE}")
    print(f"归档路径: {ARCHIVE_BASE_PATH}")
    print(f"归档格式: {ARCHIVE_FORMAT}")
    print(f"清理启用: {CLEANUP_ENABLED}")
    print(f"批量删除大小: {CLEANUP_BATCH_SIZE}")
    print()
    
    # 验证配置
    try:
        validate_config()
        print("✅ 配置验证通过")
    except ValueError as e:
        print(f"❌ 配置验证失败:\n{e}")
