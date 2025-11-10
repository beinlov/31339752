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


