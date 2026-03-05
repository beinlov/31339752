"""
实时统计API - 从Redis读取活跃节点数
用于大屏实时显示，延迟低（仅受拉取间隔影响）
"""
import logging
from fastapi import APIRouter, HTTPException
from typing import Dict
import redis
from config import REDIS_CONFIG, BOTNET_CONFIG

logger = logging.getLogger(__name__)
router = APIRouter()

# Redis连接（惰性初始化）
_redis_client = None

def get_redis_client():
    """获取Redis客户端"""
    global _redis_client
    
    if _redis_client is None:
        try:
            if not REDIS_CONFIG.get('enabled', False):
                raise Exception("Redis未启用")
            
            _redis_client = redis.StrictRedis(
                host=REDIS_CONFIG['host'],
                port=REDIS_CONFIG['port'],
                db=REDIS_CONFIG['db'],
                password=REDIS_CONFIG.get('password'),
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # 测试连接
            _redis_client.ping()
            logger.info("Redis连接成功")
            
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            _redis_client = None
            raise
    
    return _redis_client


@router.get("/stats/realtime/{botnet_type}")
async def get_realtime_stats(botnet_type: str):
    """
    获取指定僵尸网络的实时活跃节点数
    
    数据来源：Redis缓存（由db_writer实时更新）
    延迟：仅受C2拉取间隔影响（当前10秒）
    
    Args:
        botnet_type: 僵尸网络类型（如 utg_q_008）
        
    Returns:
        {
            "success": true,
            "botnet_type": "utg_q_008",
            "active_count": 1234,
            "timestamp": "2026-03-04 18:47:00",
            "data_source": "redis",
            "latency": "~10s"
        }
    """
    try:
        # 检查僵尸网络类型是否有效
        if botnet_type not in BOTNET_CONFIG:
            raise HTTPException(
                status_code=404,
                detail=f"僵尸网络类型 {botnet_type} 不存在"
            )
        
        # 获取Redis客户端
        try:
            redis_client = get_redis_client()
        except Exception as e:
            # Redis不可用时，返回提示信息
            logger.warning(f"Redis不可用，无法获取实时统计: {e}")
            raise HTTPException(
                status_code=503,
                detail="实时统计服务暂时不可用（Redis未启用或连接失败）"
            )
        
        # 从Redis获取活跃节点数
        cache_key = f"botnet:active_count:{botnet_type}"
        active_count = redis_client.get(cache_key)
        
        # 如果Redis中没有数据，返回0或提示初始化
        if active_count is None:
            logger.info(f"Redis缓存中没有 {botnet_type} 的数据，返回0")
            active_count = 0
        else:
            active_count = int(active_count)
        
        from datetime import datetime
        
        return {
            "success": True,
            "botnet_type": botnet_type,
            "active_count": active_count,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "data_source": "redis",
            "latency_description": "约10秒（受C2拉取间隔影响）"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实时统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取实时统计失败: {str(e)}"
        )


@router.get("/stats/realtime/all")
async def get_all_realtime_stats():
    """
    获取所有僵尸网络的实时统计
    
    Returns:
        {
            "success": true,
            "data": {
                "utg_q_008": 1234,
                "ramnit": 567,
                ...
            },
            "timestamp": "2026-03-04 18:47:00"
        }
    """
    try:
        # 获取Redis客户端
        try:
            redis_client = get_redis_client()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail="实时统计服务暂时不可用"
            )
        
        # 获取所有僵尸网络的统计
        result = {}
        for botnet_type in BOTNET_CONFIG.keys():
            cache_key = f"botnet:active_count:{botnet_type}"
            count = redis_client.get(cache_key)
            result[botnet_type] = int(count) if count else 0
        
        from datetime import datetime
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "data_source": "redis"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取所有实时统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取实时统计失败: {str(e)}"
        )
