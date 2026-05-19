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


def load_config(config_file: str = 'relay_node_config.json') -> Dict[str, Any]:
    """
    加载配置文件并应用环境变量覆盖
    
    环境变量格式：
    - C2_URL: C2服务器URL
    - C2_API_KEY: C2 API密钥
    - RELAY_API_KEY: 中继节点API密钥
    - PULL_INTERVAL: 拉取间隔（秒）
    - SERVER_HOST: 服务器监听地址
    - SERVER_PORT: 服务器监听端口
    - USE_HTTPS: 是否使用HTTPS (true/false)
    
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
            "db_file": "./relay_node_cache.db",
            "retention_days": 7
        },
        "puller": {
            "c2_servers": [],
            "batch_size": 1000,
            "timeout": 30,
            "use_two_phase_commit": True
        },
        "server": {
            "host": "0.0.0.0",
            "port": 8888,
            "api_key": "CHANGE_ME_IN_PRODUCTION",
            "use_https": False,
            "ssl_cert": "./cert.pem",
            "ssl_key": "./key.pem"
        },
        "intervals": {
            "pull": 10,
            "cleanup": 3600
        },
        "push_mode": {
            "enabled": False,
            "api_endpoint": "/api/data-push"
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
    
    # 服务器配置
    if os.getenv('SERVER_HOST'):
        config.setdefault('server', {})['host'] = os.getenv('SERVER_HOST')
        logger.info(f"环境变量覆盖: SERVER_HOST = {config['server']['host']}")
    
    if os.getenv('SERVER_PORT'):
        config.setdefault('server', {})['port'] = int(os.getenv('SERVER_PORT'))
        logger.info(f"环境变量覆盖: SERVER_PORT = {config['server']['port']}")
    
    if os.getenv('RELAY_API_KEY'):
        config.setdefault('server', {})['api_key'] = os.getenv('RELAY_API_KEY')
        logger.info("环境变量覆盖: RELAY_API_KEY")
    
    if os.getenv('USE_HTTPS'):
        use_https = os.getenv('USE_HTTPS').lower() in ('true', '1', 'yes')
        config.setdefault('server', {})['use_https'] = use_https
        logger.info(f"环境变量覆盖: USE_HTTPS = {use_https}")
    
    # 间隔配置
    if os.getenv('PULL_INTERVAL'):
        config.setdefault('intervals', {})['pull'] = int(os.getenv('PULL_INTERVAL'))
        logger.info(f"环境变量覆盖: PULL_INTERVAL = {config['intervals']['pull']}")


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
    
    # 验证服务器配置
    server = config.get('server', {})
    api_key = server.get('api_key', '')
    if api_key == 'CHANGE_ME_IN_PRODUCTION':
        logger.warning("⚠️ 警告: 使用默认API密钥，生产环境请修改！")
    
    # 验证HTTPS配置（如果启用）
    if server.get('use_https', False):
        ssl_cert = server.get('ssl_cert', '')
        ssl_key = server.get('ssl_key', '')
        if not os.path.exists(ssl_cert):
            errors.append(f"SSL证书文件不存在: {ssl_cert}")
        if not os.path.exists(ssl_key):
            errors.append(f"SSL私钥文件不存在: {ssl_key}")
    
    # 输出错误
    if errors:
        logger.error("配置验证失败:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    logger.info("✅ 配置验证通过")
    return True
