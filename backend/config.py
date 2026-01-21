import os

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "botnet",
    "charset": "utf8mb4",
    # 连接超时设置（秒）- 增加超时时间以应对高并发写入
    "connect_timeout": 60,   # 建立连接超时（增加到60秒）
    "read_timeout": 300,     # 读取超时（增加到5分钟）
    "write_timeout": 300,    # 写入超时（增加到5分钟）
    # 自动重连和保持连接活跃
    "autocommit": True,      # 自动提交（对于连接池更安全）
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
    'leethozer',
    'test'
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
    "enable_api_key": False,  # 开发环境可设为False，生产环境必须True
    
    # API密钥（集成平台调用同步接口时需要提供）
    # 生产环境请修改为强密钥（至少32个字符）
    "api_key": "KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4",
    
    # 是否启用IP白名单验证
    "enable_ip_whitelist": False,  # 开发环境可设为False，生产环境建议True
    
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
    },
    'test': {
        'log_dir': os.path.join(LOGS_DIR, 'test'),
        'important_events': [],
        'enabled': True,
        'description': 'Test僵尸网络'
    }
}

# ============================================================
# IP 查询与富化配置（IP Enrichment Configuration）
# ============================================================

# IP 查询缓存配置（三层缓存架构）
IP_CACHE_SIZE = 10000  # L1内存缓存最多10000个IP信息
IP_CACHE_TTL = 86400   # L1缓存24小时

# Redis缓存配置（L2缓存，可选）
REDIS_CONFIG = {
    'enabled': os.environ.get('REDIS_ENABLED', 'false').lower() == 'true',
    'host': os.environ.get('REDIS_HOST', 'localhost'),
    'port': int(os.environ.get('REDIS_PORT', '6379')),
    'db': int(os.environ.get('REDIS_DB', '0')),
    'password': os.environ.get('REDIS_PASSWORD', None),
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'ip_cache_ttl': 604800,  # IP缓存7天
    'max_connections': 50,
}

# IP富化重试配置
IP_ENRICHMENT_RETRY_CONFIG = {
    'max_retries': 3,           # 最大重试次数
    'retry_delay': 1,           # 初始重试延迟（秒）
    'retry_backoff': 2,         # 退避系数
    'timeout': 10,              # 单次查询超时（秒）
}

# IP查询限流配置（防止投毒攻击）
IP_QUERY_RATE_LIMIT = {
    'enabled': True,
    'max_queries_per_minute': 1000,  # 每分钟最多1000次查询
    'max_queries_per_ip': 10,        # 每个IP每分钟最多10次查询
    'bogon_ip_blacklist': True,      # 是否启用Bogon IP黑名单
}

# 数据库批量写入配置
DB_BATCH_SIZE = 100  # 批量写入大小（平衡性能和锁表时间）
DB_COMMIT_INTERVAL = 10  # 提交间隔（秒）
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
CONNECTION_POOL_SIZE = 10      # 数据库连接池大小（平衡处理和Web服务）

# 性能阈值配置
SLOW_FLUSH_THRESHOLD = 2.0     # 慢flush阈值（秒）
SLOW_CONNECTION_THRESHOLD = 0.5  # 慢连接阈值（秒）
HIGH_CPU_THRESHOLD = 80        # 高CPU使用率阈值（%）
HIGH_MEMORY_THRESHOLD = 85     # 高内存使用率阈值（%）

# ============================================================
# 数据质量与验证配置（Data Quality Configuration）
# ============================================================

# 输入验证配置
DATA_VALIDATION_CONFIG = {
    'strict_mode': True,  # 严格模式：验证失败则拒绝
    'max_ip_length': 15,
    'max_timestamp_length': 30,
    'max_botnet_type_length': 50,
    'required_fields': ['ip', 'timestamp', 'botnet_type'],
}

# Dead Letter队列配置
DEAD_LETTER_CONFIG = {
    'enabled': True,
    'table_name': 'data_dead_letter',
    'retention_days': 30,  # 保留30天
    'max_size': 100000,    # 最多保留10万条
}

# ============================================================
# 监控与可观测性配置（Monitoring Configuration）
# ============================================================

# 性能指标配置
METRICS_CONFIG = {
    'enabled': True,
    'export_interval': 60,  # 导出间隔（秒）
    'retention_hours': 24,  # 保留24小时
}

# 监控指标列表
MONITORING_METRICS = [
    'data_pipeline_latency_seconds',      # 端到端延迟
    'data_pipeline_duplicates_total',     # 重复数量
    'data_pipeline_queue_size',           # 队列长度
    'enrichment_cache_hit_rate',          # 富化缓存命中率
    'enrichment_failures_total',          # 富化失败次数
    'db_write_errors_total',              # 数据库写入错误
    'c2_pull_errors_total',               # C2拉取错误
]

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

# C2端日志读取配置
C2_LOG_LOOKBACK_CONFIG = {
    'mode': 'unlimited',  # 'unlimited': 无限回溯, 'limited': 限制天数
    'max_days': 90,       # limited模式下的最大回溯天数
    'description': '无限回溯模式：C2端会读取所有未处理的历史日志文件，适合长时间停运后恢复'
}

# C2数据拉取时间配置
# 拉取间隔（分钟）- 操作者可根据实时性需求调整
# 建议值：
# - 1分钟：高实时性，但增加网络和数据库负载
# - 5分钟：平衡实时性和性能（推荐）
# - 10分钟：低负载，适合大规模部署
C2_PULL_INTERVAL_MINUTES = int(os.getenv('C2_PULL_INTERVAL_MINUTES', '1'))  # 拉取间隔（分钟）

# 时间窗口重叠配置（防止边界数据丢失）
# 重叠比例：拉取时会回溯一定时间，确保边界数据不丢失
# 例如：5分钟拉取间隔，回溯2分钟（40%重叠）
C2_PULL_WINDOW_OVERLAP_RATIO = float(os.environ.get('C2_PULL_WINDOW_OVERLAP_RATIO', '0.4'))

# 计算实际的重叠窗口（分钟）
C2_PULL_OVERLAP_MINUTES = max(1, int(C2_PULL_INTERVAL_MINUTES * C2_PULL_WINDOW_OVERLAP_RATIO))

# 日志文件读取配置
LOG_FILE_READ_CONFIG = {
    'skip_current_hour': False,  # 不跳过当前小时（支持实时读取）
    'allow_incomplete_lines': True,  # 允许读取未完成的行（下次会重读）
    'encoding_errors': 'ignore',  # 编码错误处理方式
    'use_file_locks': False,  # 是否使用文件锁（通常不需要）
}

# 背压控制配置（防止下游处理不过来导致积压）
BACKPRESSURE_CONFIG = {
    'enabled': False,  # 临时禁用背压控制，用于调试拉取问题
    'queue_high_watermark': 10000,  # 队列高水位（超过此值暂停拉取）
    'queue_low_watermark': 5000,   # 队列低水位（低于此值恢复拉取）
    'pause_duration_seconds': 300,  # 暂停时长（秒）
}

# C2端点配置（用于从远程C2服务器拉取数据）
# 注意：API密钥应该从环境变量读取，这里仅作示例
# 警告：生产环境必须使用HTTPS协议
C2_ENDPOINTS = [
    # 示例配置1 - 远程C2服务器
    {
         'name': 'C2-test-remote',
         'url': os.environ.get('C2_ENDPOINT_1', 'http://124.156.139.63:8888'),  # ⬅️ 改为你的公网IP
         'api_key': os.environ.get('C2_API_KEY_1', 'KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4'),
         'enabled': True,
         'pull_interval': C2_PULL_INTERVAL_MINUTES * 60,  # 使用统一配置（转换为秒）
         'batch_size': 5000,   # 每次拉取数量
         'timeout': 30,        # 请求超时（秒）
         'verify_ssl': False,  # HTTP不需要验证SSL（如果是HTTPS改为True）
     },
    # 示例配置2
    # {
    #     'name': 'C2-Zeus-1',
    #     'url': os.environ.get('C2_ENDPOINT_2', 'https://c2-server-2.example.com:8888'),
    #     'api_key': os.environ.get('C2_API_KEY_2', 'your-api-key-here'),
    #     'enabled': True,
    #     'pull_interval': C2_PULL_INTERVAL_MINUTES * 60,
    #     'batch_size': 1000,
    #     'timeout': 30,
    #     'verify_ssl': True,
    # },
]

# 是否启用远程拉取功能
ENABLE_REMOTE_PULLING = len(C2_ENDPOINTS) > 0 and any(c.get('enabled') for c in C2_ENDPOINTS)

# 安全配置
SECURITY_CONFIG = {
    # 是否强制HTTPS（生产环境必须True）
    'force_https': os.environ.get('FORCE_HTTPS', 'false').lower() == 'true',
    
    # 是否启用请求签名（HMAC）
    'enable_request_signing': os.environ.get('ENABLE_REQUEST_SIGNING', 'false').lower() == 'true',
    
    # 请求时间戳容忍度（秒）
    'timestamp_tolerance': 300,  # 5分钟
    
    # Nonce缓存大小（防重放）
    'nonce_cache_size': 10000,
    'nonce_cache_ttl': 600,  # 10分钟
}

# ============================================================
# 队列模式配置（Queue Mode Configuration）
# ============================================================

# 队列模式开关
# - True: 启用队列模式（推荐生产环境），数据通过Redis队列异步处理
# - False: 禁用队列模式（测试环境），数据直接同步处理
QUEUE_MODE_ENABLED = os.environ.get('QUEUE_MODE_ENABLED', 'true').lower() == 'true'

# Redis队列配置
QUEUE_REDIS_CONFIG = {
    'host': os.environ.get('QUEUE_REDIS_HOST', 'localhost'),
    'port': int(os.environ.get('QUEUE_REDIS_PORT', '6379')),
    'db': int(os.environ.get('QUEUE_REDIS_DB', '0')),
    'password': os.environ.get('QUEUE_REDIS_PASSWORD', None),  # Redis密码（可选）
    'socket_connect_timeout': 5,  # 连接超时（秒）
    'socket_timeout': 5,          # 操作超时（秒）
    'retry_on_timeout': True,     # 超时时重试
    'health_check_interval': 30,  # 健康检查间隔（秒）
    'decode_responses': True,     # 自动解码响应
}

# 队列名称配置
# 注意：为保持兼容性，默认使用 botnet:ip_upload_queue（与旧版本一致）
QUEUE_NAMES = {
    'ip_upload': os.environ.get('QUEUE_NAME_IP_UPLOAD', 'botnet:ip_upload_queue'),  # IP上传队列
    'task_queue': os.environ.get('QUEUE_NAME_TASK', 'botnet:ip_upload_queue'),      # 通用任务队列（默认使用ip_upload队列）
}

# 内置Worker配置（集成在主程序中，无需单独启动）
# 主程序会自动启动指定数量的Worker协程来处理队列任务
INTERNAL_WORKER_CONFIG = {
    # 内置Worker协程数量（建议：1-4个，根据CPU核心数和数据量调整）
    # - 单核/低负载：1个
    # - 双核/中等负载：2个
    # - 四核/高负载：4个
    'worker_count': int(os.environ.get('INTERNAL_WORKER_COUNT', '1')),
    
    # 单个Worker的IP富化并发数（每个Worker内部的并发查询数）
    'enricher_concurrent': int(os.environ.get('WORKER_ENRICHER_CONCURRENT', '20')),
    
    # Worker的IP缓存配置（注意：所有Worker共享主程序的enricher缓存）
    'enricher_cache_size': int(os.environ.get('WORKER_CACHE_SIZE', '10000')),
    'enricher_cache_ttl': int(os.environ.get('WORKER_CACHE_TTL', '86400')),  # 24小时
    
    # Worker的数据库批量写入大小
    'db_batch_size': int(os.environ.get('WORKER_DB_BATCH_SIZE', '100')),
    
    # 任务失败重试配置
    'max_retries': int(os.environ.get('WORKER_MAX_RETRIES', '3')),      # 最大重试次数
    'retry_delay': int(os.environ.get('WORKER_RETRY_DELAY', '5')),      # 重试延迟（秒）
    
    # 队列拉取超时（秒）
    'queue_timeout': int(os.environ.get('WORKER_QUEUE_TIMEOUT', '1')),  # 阻塞等待时间
    
    # 是否启用内置Worker（通常应与QUEUE_MODE_ENABLED一致）
    'enabled': os.environ.get('INTERNAL_WORKER_ENABLED', 'true').lower() == 'true',
}