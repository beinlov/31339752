"""
日志处理配置文件
"""
import os

# 基础路径配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "botnet",
    "charset": "utf8mb4"
}

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
MONITOR_INTERVAL = 30          # 性能监控间隔（秒）

# 性能阈值配置
SLOW_FLUSH_THRESHOLD = 2.0     # 慢flush阈值（秒）
SLOW_CONNECTION_THRESHOLD = 0.5  # 慢连接阈值（秒）
HIGH_CPU_THRESHOLD = 80        # 高CPU使用率阈值（%）
HIGH_MEMORY_THRESHOLD = 85     # 高内存使用率阈值（%）
