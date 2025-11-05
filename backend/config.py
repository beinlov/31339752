# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "botnet",
    "charset": "utf8mb4"
}

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