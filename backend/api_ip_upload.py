"""
新的IP数据上传接口
专门用于接收远端上传器发送的结构化IP数据
"""
from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
import logging
from datetime import datetime
import asyncio
import sys
import os

# 添加父目录到路径以导入log_processor模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import API_KEY, ALLOWED_UPLOAD_IPS, ALLOWED_BOTNET_TYPES, DB_CONFIG
from log_processor.main import get_processor

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

# 数据模型
class IPDataItem(BaseModel):
    """单个IP数据项"""
    ip: str = Field(..., description="IP地址")
    date: str = Field(..., description="日期 YYYY-MM-DD")
    botnet_type: str = Field(..., description="僵尸网络类型")
    timestamp: str = Field(..., description="时间戳")
    
    @validator('ip')
    def validate_ip(cls, v):
        import re
        pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid IP address format')
        return v

class IPUploadRequest(BaseModel):
    """IP数据上传请求"""
    botnet_type: str = Field(..., description="僵尸网络类型")
    ip_data: List[IPDataItem] = Field(..., description="IP数据列表")
    source_ip: Optional[str] = Field(None, description="远端服务器IP")
    
    @validator('botnet_type')
    def validate_botnet_type(cls, v):
        if v not in ALLOWED_BOTNET_TYPES:
            raise ValueError(f'僵尸网络类型必须是以下之一: {", ".join(ALLOWED_BOTNET_TYPES)}')
        return v
    
    @validator('ip_data')
    def validate_ip_data(cls, v):
        if not v:
            raise ValueError('IP数据列表不能为空')
        if len(v) > 1000:  # 限制单次上传数量
            raise ValueError('单次上传IP数量不能超过1000个')
        return v

class IPUploadResponse(BaseModel):
    """IP数据上传响应"""
    status: str
    message: str
    received_count: int
    processed_count: int
    duplicate_count: int
    timestamp: str

# 注意：旧的全局变量和函数已移除，现在使用统一的日志处理器

@router.post("/api/upload-ip-data", response_model=IPUploadResponse)
async def upload_ip_data(
    request: IPUploadRequest,
    client_request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    接收远端上传的IP数据（已去重的结构化数据）
    
    这个接口专门用于接收远端上传器发送的结构化IP数据，
    与原有的 /api/upload-logs 接口不同，这里接收的是已经
    提取和去重的IP数据，直接进行地理位置增强和数据库写入。
    
    安全特性：
    - API密钥认证
    - IP白名单验证
    - 数据格式验证
    """
    try:
        client_ip = client_request.client.host
        
        # 安全检查1：验证API密钥
        if x_api_key != API_KEY:
            logger.warning(f"无效的API密钥尝试，来自IP: {client_ip}")
            raise HTTPException(status_code=401, detail="无效的API密钥")
        
        # 安全检查2：IP白名单验证
        if ALLOWED_UPLOAD_IPS and client_ip not in ALLOWED_UPLOAD_IPS:
            logger.warning(f"未授权的IP尝试上传: {client_ip}")
            raise HTTPException(status_code=403, detail="IP未授权")
        
        logger.info(f"[{request.botnet_type}] 收到来自 {client_ip} 的IP数据上传，数量: {len(request.ip_data)}")
        
        # 获取日志处理器
        processor = get_processor()
        
        # 转换数据格式
        ip_data_list = []
        for ip_item in request.ip_data:
            ip_data_list.append({
                'ip': ip_item.ip,
                'timestamp': ip_item.timestamp,
                'date': ip_item.date,
                'botnet_type': ip_item.botnet_type
            })
        
        # 后台异步处理数据，不阻塞API响应
        asyncio.create_task(processor.process_api_data(request.botnet_type, ip_data_list))
        
        # 立即返回响应（处理在后台进行）
        return IPUploadResponse(
            status="success",
            message=f"已接收 {len(request.ip_data)} 个IP，正在后台处理",
            received_count=len(request.ip_data),
            processed_count=len(request.ip_data),
            duplicate_count=0,  # 去重在数据库层面处理
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ IP数据上传处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"IP数据上传失败: {str(e)}")

@router.get("/api/upload-ip-status")
async def get_upload_ip_status():
    """
    查询IP上传接口状态
    """
    try:
        # 获取日志处理器
        processor = get_processor()
        
        # 获取统计信息
        writer_stats = {}
        for botnet_type in ALLOWED_BOTNET_TYPES:
            if botnet_type in processor.writers:
                writer = processor.writers[botnet_type]
                stats = writer.get_stats()
                writer_stats[botnet_type] = {
                    "total_written": stats['total_written'],
                    "duplicate_count": stats['duplicate_count'],
                    "duplicate_rate": stats['duplicate_rate'],
                    "buffer_size": stats['buffer_size']
                }
        
        # 获取IP增强器统计
        enricher_stats = {}
        if processor.enricher:
            stats = processor.enricher.get_stats()
            enricher_stats = {
                "total_queries": stats['total_queries'],
                "cache_hit_rate": stats['cache_hit_rate']
            }
        
        return {
            "api_status": "running",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "security": {
                "api_key_required": True,
                "ip_whitelist_enabled": bool(ALLOWED_UPLOAD_IPS)
            },
            "writer_stats": writer_stats,
            "enricher_stats": enricher_stats,
            "processor_stats": processor.stats
        }
        
    except Exception as e:
        logger.error(f"获取IP上传状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
