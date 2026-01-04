import os

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "botnet",
    "charset": "utf8mb4",
    # 连接超时设置（秒）
    "connect_timeout": 30,  # 建立连接超时
    "read_timeout": 60,     # 读取超时
    "write_timeout": 60,    # 写入超时
    # 自动重连和保持连接活跃
    "autocommit": True,     # 自动提交（对于连接池更安全）
}

# ============================================================
# JWT认证配置
# ============================================================

# JWT密钥（用于生成和验证token）
# 生产环境必须修改为强密钥（建议至少32个字符）
SECRET_KEY = "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"

# JWT算法
ALGORITHM = "HS256"

# Token过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ============================================================
# 日志上传接口安全配置
# ============================================================

# API密钥（用于远端上传认证）
# 建议使用强密码，如：openssl rand -hex 32
API_KEY = "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"

# 允许上传的远端IP白名单
# 空列表表示允许所有IP（仅开发环境使用）
# 生产环境必须配置具体IP
ALLOWED_UPLOAD_IPS = [
    # "192.168.1.100",  # 远端服务器1
    # "10.0.0.50",      # 远端服务器2
    # "远端蜜罐IP",
]

# 单次上传日志行数限制
MAX_LOGS_PER_UPLOAD = 10000

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
    "sso_token_expire_minutes": 60,  # 1小时
    
    # 是否启用IP白名单验证
    "enable_ip_whitelist": False,  # 开发环境可设为False，生产环境建议True
    
    # IP白名单（仅在enable_ip_whitelist为True时生效）
    "ip_whitelist": [
        "127.0.0.1",
        "localhost",
        # 添加集成系统的IP地址，例如：
        # "192.168.1.100",
        # "10.0.0.50",
    ]
}

# ============================================================
# 用户数据同步接口配置（集成平台同步用户到子系统）
# ============================================================

SYNC_CONFIG = {
    # 是否启用API密钥验证
    "enable_api_key": True,  # 开发环境可设为False，生产环境必须True
    
    # API密钥（集成平台调用同步接口时需要提供）
    # 生产环境请修改为强密钥（至少32个字符）
    "api_key": "your-sync-api-key-here-change-in-production",
    
    # 是否启用IP白名单验证
    "enable_ip_whitelist": True,  # 开发环境可设为False，生产环境建议True
    
    # IP白名单（集成平台的IP地址）
    "ip_whitelist": [
        "127.0.0.1",
        "localhost",
        # 添加集成平台的IP地址，例如：
        # "192.168.1.100",
        # "10.0.0.50",
    ],
    
    # 默认用户角色（同步时如果未指定角色，使用此默认值）
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
IP_CACHE_SIZE = 10000  # 缓存最多10000个IP信息
IP_CACHE_TTL = 86400   # 缓存24小时

# 数据库批量写入配置
DB_BATCH_SIZE = 500           # 批量写入大小（增加到500以提高性能）
DB_COMMIT_INTERVAL = 60       # 提交间隔（秒）
DB_STATISTICS_INTERVAL = 300  # 统计更新间隔（秒）

# 日志处理配置
LOG_FILE_PATTERN = "*.txt"  # 日志文件匹配模式
LOG_ENCODING = "utf-8"      # 日志文件编码
LOG_DATE_FORMAT = "%Y-%m-%d"  # 日期格式

# 监控配置
MONITOR_INTERVAL = 0.5  # 文件监控间隔（秒）
POSITION_STATE_FILE = os.path.join(BASE_DIR, 'log_processor', '.file_positions.json')  # 文件位置记录

# 性能优化配置
PERFORMANCE_MONITORING = True  # 启用性能监控
CONNECTION_POOL_SIZE = 3       # 数据库连接池大小

# 性能阈值配置
SLOW_FLUSH_THRESHOLD = 2.0     # 慢flush阈值（秒）
SLOW_CONNECTION_THRESHOLD = 0.5  # 慢连接阈值（秒）
HIGH_CPU_THRESHOLD = 80        # 高CPU使用率阈值（%）
HIGH_MEMORY_THRESHOLD = 85     # 高内存使用率阈值（%）

# ============================================================
# 统计聚合器配置（Stats Aggregator Configuration）
# ============================================================

# 聚合间隔（分钟）
AGGREGATOR_INTERVAL_MINUTES = 5

# 启动时是否立即执行一次聚合
AGGREGATOR_RUN_ON_STARTUP = True

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

# ============================================================
# 远程数据拉取配置（Remote Data Pulling Configuration）
# ============================================================

# C2端点配置（用于从远程C2服务器拉取数据）
# 注意：API密钥应该从环境变量读取，这里仅作示例
C2_ENDPOINTS = [
    # 示例配置1
    {
         'name': 'C2-Ramnit-1',
         'url': os.environ.get('C2_ENDPOINT_1', 'http://101.32.11.139:8888'),
         'api_key': os.environ.get('C2_API_KEY_1', 'KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4'),
         'enabled': True,
         'pull_interval': 60,  # 拉取间隔（秒）
         'batch_size': 1000,   # 每次拉取数量
         'timeout': 30,        # 请求超时（秒）
     },
    # 示例配置2
    # {
    #     'name': 'C2-Zeus-1',
    #     'url': os.environ.get('C2_ENDPOINT_2', 'http://c2-server-2.example.com:8888'),
    #     'api_key': os.environ.get('C2_API_KEY_2', 'your-api-key-here'),
    #     'enabled': True,
    #     'pull_interval': 60,
    #     'batch_size': 1000,
    #     'timeout': 30,
    # },
]

# 是否启用远程拉取功能
ENABLE_REMOTE_PULLING = len(C2_ENDPOINTS) > 0 and any(c.get('enabled') for c in C2_ENDPOINTS)