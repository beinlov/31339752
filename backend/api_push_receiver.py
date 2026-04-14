"""
数据推送接收API模块
接收中转服务器推送的数据，支持HMAC签名验证和防重放攻击
"""

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional
import logging
import hmac
import hashlib
from datetime import datetime
import time
from collections import OrderedDict

from config import PUSH_MODE_CONFIG, ALLOWED_BOTNET_TYPES

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Nonce缓存（防重放攻击）
# ============================================================

class NonceCache:
    """Nonce缓存，用于防止重放攻击"""
    
    def __init__(self, max_size: int = 10000, ttl: int = 600):
        """
        Args:
            max_size: 最大缓存大小
            ttl: 缓存过期时间（秒）
        """
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl
    
    def is_used(self, nonce: str) -> bool:
        """检查nonce是否已使用"""
        # 清理过期记录
        self._cleanup()
        return nonce in self.cache
    
    def mark_used(self, nonce: str):
        """标记nonce为已使用"""
        # 如果缓存已满，删除最旧的记录
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        
        self.cache[nonce] = time.time()
    
    def _cleanup(self):
        """清理过期的nonce"""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self.cache.items()
            if current_time - timestamp > self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        self._cleanup()
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'ttl': self.ttl
        }


# 全局nonce缓存
_nonce_cache = None
if PUSH_MODE_CONFIG.get('enable_nonce_cache', True):
    _nonce_cache = NonceCache(
        max_size=PUSH_MODE_CONFIG.get('nonce_cache_size', 10000),
        ttl=PUSH_MODE_CONFIG.get('nonce_cache_ttl', 600)
    )


# ============================================================
# 数据模型
# ============================================================

class PushDataRequest(BaseModel):
    """推送数据请求模型"""
    botnet_type: str = Field(..., description="僵尸网络类型")
    data: List[Dict] = Field(..., description="推送的数据列表，格式与pull返回一致")
    timestamp: str = Field(..., description="请求时间戳（ISO格式）")
    nonce: Optional[str] = Field(None, description="随机数（防重放攻击）")
    relay_server_id: Optional[str] = Field(None, description="中转服务器ID（可选）")
    
    @field_validator('botnet_type')
    @classmethod
    def validate_botnet_type(cls, v):
        if v not in ALLOWED_BOTNET_TYPES:
            raise ValueError(f'僵尸网络类型必须是以下之一: {", ".join(ALLOWED_BOTNET_TYPES)}')
        return v
    
    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        max_batch_size = PUSH_MODE_CONFIG.get('max_batch_size', 5000)
        if not v:
            raise ValueError('数据列表不能为空')
        if len(v) > max_batch_size:
            raise ValueError(f'单次推送数据量不能超过{max_batch_size}条')
        return v


class PushResponse(BaseModel):
    """推送响应模型"""
    success: bool
    message: str
    received_count: int
    processed_count: int
    duplicate_count: Optional[int] = None
    error_count: Optional[int] = None
    timestamp: str
    processing_time_ms: Optional[float] = None


# ============================================================
# 安全验证函数
# ============================================================

def verify_hmac_signature(
    request_body: str,
    signature: str,
    timestamp: str,
    nonce: Optional[str] = None
) -> bool:
    """
    验证HMAC签名
    
    Args:
        request_body: 请求体JSON字符串
        signature: 客户端提供的签名
        timestamp: 请求时间戳
        nonce: 随机数（可选）
    
    Returns:
        签名是否有效
    """
    if not PUSH_MODE_CONFIG.get('use_signature', True):
        return True
    
    try:
        secret = PUSH_MODE_CONFIG['signature_secret']
        algorithm = PUSH_MODE_CONFIG.get('signature_algorithm', 'sha256')
        
        # 构造待签名消息：timestamp + nonce + request_body
        message_parts = [timestamp]
        if nonce:
            message_parts.append(nonce)
        message_parts.append(request_body)
        message = ''.join(message_parts)
        
        # 计算HMAC签名
        if algorithm == 'sha256':
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
        elif algorithm == 'sha512':
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
        else:
            logger.error(f"不支持的签名算法: {algorithm}")
            return False
        
        # 使用恒定时间比较防止时序攻击
        return hmac.compare_digest(signature, expected_signature)
    
    except Exception as e:
        logger.error(f"HMAC签名验证失败: {e}")
        return False


def verify_timestamp(timestamp_str: str) -> bool:
    """
    验证时间戳是否在容忍范围内
    
    Args:
        timestamp_str: ISO格式时间戳
    
    Returns:
        时间戳是否有效
    """
    try:
        tolerance = PUSH_MODE_CONFIG.get('timestamp_tolerance', 300)
        
        # 解析时间戳
        request_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        current_time = datetime.now(request_time.tzinfo)
        
        # 计算时间差
        time_diff = abs((current_time - request_time).total_seconds())
        
        if time_diff > tolerance:
            logger.warning(f"时间戳超出容忍范围: {time_diff}秒 (容忍{tolerance}秒)")
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"时间戳验证失败: {e}")
        return False


def verify_ip_whitelist(client_ip: str) -> bool:
    """
    验证客户端IP是否在白名单中
    
    Args:
        client_ip: 客户端IP
    
    Returns:
        IP是否在白名单中
    """
    allowed_ips = PUSH_MODE_CONFIG.get('allowed_ips', [])
    
    # 如果白名单为空，不限制IP
    if not allowed_ips:
        return True
    
    return client_ip in allowed_ips


# ============================================================
# API端点
# ============================================================

@router.post("/api/data-push", response_model=PushResponse)
async def receive_data_push(
    request: Request,
    push_data: PushDataRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_signature: Optional[str] = Header(None, alias="X-Signature")
):
    """
    接收中转服务器推送的数据
    
    安全特性：
    - HMAC签名验证
    - 时间戳验证（防重放攻击）
    - Nonce验证（防重放攻击）
    - API密钥验证
    - IP白名单（可选）
    
    请求头：
    - X-API-Key: API密钥
    - X-Signature: HMAC签名（可选，取决于配置）
    
    请求体示例：
    {
        "botnet_type": "ramnit",
        "data": [
            {"ip": "1.2.3.4", "timestamp": "2025-01-01T12:00:00Z", ...},
            ...
        ],
        "timestamp": "2025-01-01T12:00:05Z",
        "nonce": "random-string-12345",
        "relay_server_id": "relay-001"
    }
    
    响应示例：
    {
        "success": true,
        "message": "数据推送成功",
        "received_count": 100,
        "processed_count": 95,
        "duplicate_count": 5,
        "error_count": 0,
        "timestamp": "2025-01-01T12:00:06Z",
        "processing_time_ms": 234.5
    }
    """
    start_time = time.time()
    client_ip = request.client.host
    
    logger.info(f"[PUSH] 收到推送请求: {push_data.botnet_type}, {len(push_data.data)}条数据, 来自{client_ip}")
    
    try:
        # 1. 验证API密钥
        api_key = PUSH_MODE_CONFIG.get('api_key')
        if api_key and x_api_key != api_key:
            logger.warning(f"[PUSH] API密钥验证失败, 来自{client_ip}")
            raise HTTPException(status_code=401, detail="无效的API密钥")
        
        # 2. 验证IP白名单
        if not verify_ip_whitelist(client_ip):
            logger.warning(f"[PUSH] IP不在白名单中: {client_ip}")
            raise HTTPException(status_code=403, detail="IP未授权")
        
        # 3. 验证时间戳
        if not verify_timestamp(push_data.timestamp):
            raise HTTPException(status_code=400, detail="时间戳无效或超出容忍范围")
        
        # 4. 验证Nonce（防重放）
        if _nonce_cache and push_data.nonce:
            if _nonce_cache.is_used(push_data.nonce):
                logger.warning(f"[PUSH] 检测到重放攻击: nonce={push_data.nonce}")
                raise HTTPException(status_code=400, detail="请求已被处理（重放攻击）")
            _nonce_cache.mark_used(push_data.nonce)
        
        # 5. 验证HMAC签名
        if PUSH_MODE_CONFIG.get('use_signature', True):
            if not x_signature:
                raise HTTPException(status_code=400, detail="缺少签名")
            
            # 获取原始请求体
            request_body = await request.body()
            request_body_str = request_body.decode('utf-8')
            
            if not verify_hmac_signature(
                request_body_str,
                x_signature,
                push_data.timestamp,
                push_data.nonce
            ):
                logger.warning(f"[PUSH] HMAC签名验证失败, 来自{client_ip}")
                raise HTTPException(status_code=401, detail="签名验证失败")
        
        # 6. 处理数据
        from log_processor.main import get_processor
        processor = get_processor()
        
        if not processor:
            raise HTTPException(status_code=503, detail="日志处理器未初始化")
        
        # 调用processor处理数据（与pull模式相同的数据格式）
        try:
            await processor.process_api_data(push_data.botnet_type, push_data.data)
            
            # 获取处理统计（如果可用）
            processing_time = (time.time() - start_time) * 1000
            
            response = PushResponse(
                success=True,
                message=f"成功处理{len(push_data.data)}条数据",
                received_count=len(push_data.data),
                processed_count=len(push_data.data),  # 简化处理，实际可从processor获取
                timestamp=datetime.now().isoformat(),
                processing_time_ms=round(processing_time, 2)
            )
            
            logger.info(
                f"[PUSH] 推送处理成功: {push_data.botnet_type}, "
                f"{len(push_data.data)}条, 耗时{processing_time:.2f}ms"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"[PUSH] 数据处理失败: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"数据处理失败: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PUSH] 推送接收失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"内部错误: {str(e)}")


@router.get("/api/push-status")
async def get_push_status():
    """
    获取推送模式状态
    
    返回推送接收的配置和统计信息
    """
    try:
        nonce_stats = _nonce_cache.get_stats() if _nonce_cache else None
        
        status = {
            "mode": "push",
            "enabled": PUSH_MODE_CONFIG.get('enabled', False),
            "config": {
                "use_signature": PUSH_MODE_CONFIG.get('use_signature', True),
                "timestamp_tolerance": PUSH_MODE_CONFIG.get('timestamp_tolerance', 300),
                "enable_nonce_cache": PUSH_MODE_CONFIG.get('enable_nonce_cache', True),
                "max_batch_size": PUSH_MODE_CONFIG.get('max_batch_size', 5000),
                "ip_whitelist_enabled": bool(PUSH_MODE_CONFIG.get('allowed_ips', [])),
            },
            "nonce_cache": nonce_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        return status
    
    except Exception as e:
        logger.error(f"获取推送状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/push-health")
async def push_health_check():
    """推送模式健康检查"""
    return {
        "status": "ok",
        "service": "data-push-receiver",
        "mode": "push",
        "timestamp": datetime.now().isoformat()
    }
