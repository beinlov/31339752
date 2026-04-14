#!/usr/bin/env python3
"""
配置加载器
支持从JSON文件和环境变量加载配置
环境变量优先级高于配置文件
"""

import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def load_config(config_file: str = 'relay_config.json') -> Dict[str, Any]:
    """
    加载配置文件并应用环境变量覆盖
    
    环境变量格式：
    - C2_URL: C2服务器URL
    - C2_API_KEY: C2 API密钥
    - PLATFORM_URL: 平台服务器URL
    - PLATFORM_API_KEY: 平台API密钥
    - SIGNATURE_SECRET: HMAC签名密钥
    - RELAY_ID: 中转服务器ID
    - AWS_REGION: AWS区域
    - AWS_INSTANCE_ID: AWS实例ID
    - IP_CHANGE_ENABLED: 是否启用IP切换 (true/false)
    - IP_CHANGE_INTERVAL: IP切换间隔（秒）
    - PULL_INTERVAL: 拉取间隔（秒）
    - PUSH_INTERVAL: 推送间隔（秒）
    
    Args:
        config_file: 配置文件路径
    
    Returns:
        配置字典
    """
    # 加载基础配置
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"加载配置文件: {config_file}")
    else:
        logger.warning(f"配置文件不存在: {config_file}，使用默认配置")
        config = get_default_config()
    
    # 应用环境变量覆盖
    apply_env_overrides(config)
    
    return config


def get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return {
        "storage": {
            "db_file": "./relay_cache.db",
            "retention_days": 7
        },
        "puller": {
            "c2_servers": [],
            "batch_size": 1000,
            "timeout": 30,
            "use_two_phase_commit": True
        },
        "pusher": {
            "platform_url": "",
            "platform_api_key": "",
            "signature_secret": "",
            "relay_id": "relay-001",
            "batch_size": 1000,
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 2
        },
        "intervals": {
            "pull": 10,
            "push": 5,
            "cleanup": 3600,
            "retry": 300
        },
        "ip_change": {
            "enabled": False,
            "change_interval": 600,
            "max_eips": 5,
            "aws_region": "us-east-2",
            "instance_id": "",
            "openvpn_config": "/etc/openvpn/client.conf",
            "resume_delay": 30
        }
    }


def apply_env_overrides(config: Dict[str, Any]):
    """应用环境变量覆盖"""
    # C2服务器配置
    if os.getenv('C2_URL'):
        c2_servers = config.setdefault('puller', {}).setdefault('c2_servers', [])
        if not c2_servers:
            c2_servers.append({})
        c2_servers[0]['url'] = os.getenv('C2_URL')
        logger.info(f"环境变量覆盖: C2_URL = {c2_servers[0]['url']}")
    
    if os.getenv('C2_API_KEY'):
        c2_servers = config.setdefault('puller', {}).setdefault('c2_servers', [])
        if not c2_servers:
            c2_servers.append({})
        c2_servers[0]['api_key'] = os.getenv('C2_API_KEY')
        logger.info("环境变量覆盖: C2_API_KEY")
    
    # 平台服务器配置
    if os.getenv('PLATFORM_URL'):
        config.setdefault('pusher', {})['platform_url'] = os.getenv('PLATFORM_URL')
        logger.info(f"环境变量覆盖: PLATFORM_URL = {config['pusher']['platform_url']}")
    
    if os.getenv('PLATFORM_API_KEY'):
        config.setdefault('pusher', {})['platform_api_key'] = os.getenv('PLATFORM_API_KEY')
        logger.info("环境变量覆盖: PLATFORM_API_KEY")
    
    if os.getenv('SIGNATURE_SECRET'):
        config.setdefault('pusher', {})['signature_secret'] = os.getenv('SIGNATURE_SECRET')
        logger.info("环境变量覆盖: SIGNATURE_SECRET")
    
    if os.getenv('RELAY_ID'):
        config.setdefault('pusher', {})['relay_id'] = os.getenv('RELAY_ID')
        logger.info(f"环境变量覆盖: RELAY_ID = {config['pusher']['relay_id']}")
    
    # AWS配置
    if os.getenv('AWS_REGION'):
        config.setdefault('ip_change', {})['aws_region'] = os.getenv('AWS_REGION')
        logger.info(f"环境变量覆盖: AWS_REGION = {config['ip_change']['aws_region']}")
    
    if os.getenv('AWS_INSTANCE_ID'):
        config.setdefault('ip_change', {})['instance_id'] = os.getenv('AWS_INSTANCE_ID')
        logger.info(f"环境变量覆盖: AWS_INSTANCE_ID = {config['ip_change']['instance_id']}")
    
    # IP切换配置
    if os.getenv('IP_CHANGE_ENABLED'):
        enabled = os.getenv('IP_CHANGE_ENABLED').lower() in ('true', '1', 'yes')
        config.setdefault('ip_change', {})['enabled'] = enabled
        logger.info(f"环境变量覆盖: IP_CHANGE_ENABLED = {enabled}")
    
    if os.getenv('IP_CHANGE_INTERVAL'):
        config.setdefault('ip_change', {})['change_interval'] = int(os.getenv('IP_CHANGE_INTERVAL'))
        logger.info(f"环境变量覆盖: IP_CHANGE_INTERVAL = {config['ip_change']['change_interval']}")
    
    # 间隔配置
    if os.getenv('PULL_INTERVAL'):
        config.setdefault('intervals', {})['pull'] = int(os.getenv('PULL_INTERVAL'))
        logger.info(f"环境变量覆盖: PULL_INTERVAL = {config['intervals']['pull']}")
    
    if os.getenv('PUSH_INTERVAL'):
        config.setdefault('intervals', {})['push'] = int(os.getenv('PUSH_INTERVAL'))
        logger.info(f"环境变量覆盖: PUSH_INTERVAL = {config['intervals']['push']}")
    
    # OpenVPN配置
    if os.getenv('OPENVPN_CONFIG'):
        config.setdefault('ip_change', {})['openvpn_config'] = os.getenv('OPENVPN_CONFIG')
        logger.info(f"环境变量覆盖: OPENVPN_CONFIG = {config['ip_change']['openvpn_config']}")


def validate_config(config: Dict[str, Any]) -> bool:
    """
    验证配置的有效性
    
    Args:
        config: 配置字典
    
    Returns:
        是否有效
    """
    errors = []
    
    # 验证C2服务器配置
    c2_servers = config.get('puller', {}).get('c2_servers', [])
    if not c2_servers:
        errors.append("未配置C2服务器")
    else:
        for i, server in enumerate(c2_servers):
            if not server.get('url'):
                errors.append(f"C2服务器{i}未配置URL")
            if not server.get('api_key'):
                errors.append(f"C2服务器{i}未配置API密钥")
    
    # 验证平台服务器配置
    pusher = config.get('pusher', {})
    if not pusher.get('platform_url'):
        errors.append("未配置平台服务器URL")
    if not pusher.get('platform_api_key'):
        errors.append("未配置平台API密钥")
    if not pusher.get('signature_secret'):
        errors.append("未配置签名密钥")
    
    # 验证IP切换配置（如果启用）
    ip_change = config.get('ip_change', {})
    if ip_change.get('enabled', False):
        if not ip_change.get('instance_id'):
            errors.append("启用IP切换但未配置AWS实例ID")
        if not os.path.exists(ip_change.get('openvpn_config', '')):
            logger.warning(f"OpenVPN配置文件不存在: {ip_change.get('openvpn_config')}")
    
    # 输出错误
    if errors:
        logger.error("配置验证失败:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    logger.info("✅ 配置验证通过")
    return True
