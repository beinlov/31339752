# ============================================================
# Docker环境配置文件
# 此文件会在Docker容器中覆盖 config.py
# ============================================================

import os

# 数据库配置（从环境变量读取）
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "123456"),
    "database": os.getenv("DB_NAME", "botnet"),
    "charset": "utf8mb4"
}

# ============================================================
# JWT认证配置
# ============================================================

# JWT密钥（从环境变量读取，生产环境必须修改）
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production-min-32-chars")

# JWT算法
ALGORITHM = "HS256"

# Token过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 默认24小时

# ============================================================
# 日志上传接口安全配置
# ============================================================

# API密钥（从环境变量读取）
API_KEY = os.getenv("API_KEY", "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4")

# 允许上传的远端IP白名单
ALLOWED_UPLOAD_IPS = os.getenv("ALLOWED_UPLOAD_IPS", "").split(",") if os.getenv("ALLOWED_UPLOAD_IPS") else []

# 单次上传日志行数限制
MAX_LOGS_PER_UPLOAD = int(os.getenv("MAX_LOGS_PER_UPLOAD", "10000"))

# 允许的僵尸网络类型
ALLOWED_BOTNET_TYPES = [
    'asruex',
    'mozi', 
    'andromeda',
    'moobot',
    'ramnit',
    'leethozer'
]

# ============================================================
# 免登录接口（SSO）配置
# ============================================================

SSO_CONFIG = {
    # 访问令牌过期时间（分钟）
    "sso_token_expire_minutes": int(os.getenv("SSO_TOKEN_EXPIRE_MINUTES", "60")),
    
    # 是否启用IP白名单验证
    "enable_ip_whitelist": os.getenv("SSO_ENABLE_IP_WHITELIST", "false").lower() == "true",
    
    # IP白名单
    "ip_whitelist": os.getenv("SSO_IP_WHITELIST", "127.0.0.1,localhost").split(",")
}

# ============================================================
# 用户数据同步接口配置
# ============================================================

SYNC_CONFIG = {
    # 是否启用API密钥验证
    "enable_api_key": os.getenv("SYNC_ENABLE_API_KEY", "true").lower() == "true",
    
    # API密钥
    "api_key": os.getenv("SYNC_API_KEY", "your-sync-api-key-here-change-in-production"),
    
    # 是否启用IP白名单验证
    "enable_ip_whitelist": os.getenv("SYNC_ENABLE_IP_WHITELIST", "true").lower() == "true",
    
    # IP白名单
    "ip_whitelist": os.getenv("SYNC_IP_WHITELIST", "127.0.0.1,localhost").split(","),
    
    # 默认用户角色
    "default_role": "访客",
    
    # 默认用户状态
    "default_status": "离线"
}

# ============================================================
# 日志处理器配置（Log Processor Configuration）
# ============================================================

# 基础路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# 僵尸网络配置
BOTNET_CONFIG = {
    'asruex': {
        'log_dir': os.path.join(LOGS_DIR, 'asruex'),
        'important_events': ['access', 'clean1', 'qla0', 'clean0', 'cleanw1'],
        'enabled': True,
        'description': 'Asruex僵尸网络'
    },
    'mozi': {
        'log_dir': os.path.join(LOGS_DIR, 'mozi'),
        'important_events': ['infection', 'command', 'beacon', 'scan'],
        'enabled': True,
        'description': 'Mozi僵尸网络'
    },
    'andromeda': {
        'log_dir': os.path.join(LOGS_DIR, 'andromeda'),
        'important_events': ['download', 'beacon', 'c2', 'infection'],
        'enabled': True,
        'description': 'Andromeda僵尸网络'
    },
    'moobot': {
        'log_dir': os.path.join(LOGS_DIR, 'moobot'),
        'important_events': ['infection', 'scan', 'attack', 'beacon'],
        'enabled': True,
        'description': 'Moobot僵尸网络'
    },
    'ramnit': {
        'log_dir': os.path.join(LOGS_DIR, 'ramnit'),
        'important_events': [],  # 空列表 = 保存所有事件(已在解析器中过滤系统消息)
        'enabled': True,
        'description': 'Ramnit僵尸网络'
    },
    'leethozer': {
        'log_dir': os.path.join(LOGS_DIR, 'leethozer'),
        'important_events': ['scan', 'exploit', 'infection', 'beacon'],
        'enabled': True,
        'description': 'Leethozer僵尸网络'
    }
}

# IP 查询缓存配置
IP_CACHE_SIZE = int(os.getenv("IP_CACHE_SIZE", "10000"))  # 缓存最多10000个IP信息
IP_CACHE_TTL = int(os.getenv("IP_CACHE_TTL", "86400"))   # 缓存24小时

# 数据库批量写入配置
DB_BATCH_SIZE = int(os.getenv("DB_BATCH_SIZE", "500"))           # 批量写入大小
DB_COMMIT_INTERVAL = int(os.getenv("DB_COMMIT_INTERVAL", "60"))       # 提交间隔（秒）
DB_STATISTICS_INTERVAL = int(os.getenv("DB_STATISTICS_INTERVAL", "300"))  # 统计更新间隔（秒）

# 日志处理配置
LOG_FILE_PATTERN = os.getenv("LOG_FILE_PATTERN", "*.txt")  # 日志文件匹配模式
LOG_ENCODING = os.getenv("LOG_ENCODING", "utf-8")      # 日志文件编码
LOG_DATE_FORMAT = os.getenv("LOG_DATE_FORMAT", "%Y-%m-%d")  # 日期格式

# 监控配置
MONITOR_INTERVAL = float(os.getenv("MONITOR_INTERVAL", "0.5"))  # 文件监控间隔（秒）
POSITION_STATE_FILE = os.path.join(BASE_DIR, 'log_processor', '.file_positions.json')  # 文件位置记录

# 性能优化配置
PERFORMANCE_MONITORING = os.getenv("PERFORMANCE_MONITORING", "true").lower() == "true"  # 启用性能监控
CONNECTION_POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "3"))       # 数据库连接池大小

# 性能阈值配置
SLOW_FLUSH_THRESHOLD = float(os.getenv("SLOW_FLUSH_THRESHOLD", "2.0"))     # 慢flush阈值（秒）
SLOW_CONNECTION_THRESHOLD = float(os.getenv("SLOW_CONNECTION_THRESHOLD", "0.5"))  # 慢连接阈值（秒）
HIGH_CPU_THRESHOLD = int(os.getenv("HIGH_CPU_THRESHOLD", "80"))        # 高CPU使用率阈值（%）
HIGH_MEMORY_THRESHOLD = int(os.getenv("HIGH_MEMORY_THRESHOLD", "85"))     # 高内存使用率阈值（%）

# ============================================================
# 统计聚合器配置（Stats Aggregator Configuration）
# ============================================================

# 聚合间隔（分钟）
AGGREGATOR_INTERVAL_MINUTES = int(os.getenv("AGGREGATOR_INTERVAL_MINUTES", "5"))

# 启动时是否立即执行一次聚合
AGGREGATOR_RUN_ON_STARTUP = os.getenv("AGGREGATOR_RUN_ON_STARTUP", "true").lower() == "true"

# 获取启用的僵尸网络类型列表（从BOTNET_CONFIG动态获取）
def get_enabled_botnet_types():
    """返回所有启用的僵尸网络类型列表"""
    return [botnet_type for botnet_type, config in BOTNET_CONFIG.items() 
            if config.get('enabled', True)]

# 兼容性：提供BOTNET_TYPES常量（向后兼容旧代码）
BOTNET_TYPES = list(BOTNET_CONFIG.keys())

# ============================================================
# 应用日志文件配置（Application Logging Configuration）
# ============================================================

# 应用日志目录（统一存放所有日志文件）
APP_LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# 确保日志目录存在
if not os.path.exists(APP_LOGS_DIR):
    os.makedirs(APP_LOGS_DIR)

# 各模块日志文件路径
LOG_PROCESSOR_LOG_FILE = os.path.join(APP_LOGS_DIR, 'log_processor.log')
STATS_AGGREGATOR_LOG_FILE = os.path.join(APP_LOGS_DIR, 'stats_aggregator.log')
REMOTE_UPLOADER_LOG_FILE = os.path.join(APP_LOGS_DIR, 'remote_uploader.log')
MAIN_APP_LOG_FILE = os.path.join(APP_LOGS_DIR, 'main_app.log')
