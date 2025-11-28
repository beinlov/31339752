#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地API接口修改建议
支持远端传输的新IP数据格式
"""

from fastapi import FastAPI, HTTPException, Request, Header
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import logging
import os
import json

logger = logging.getLogger(__name__)

# ============================================================
# 新的数据模型
# ============================================================

class IPData(BaseModel):
    """单个IP数据模型"""
    ip: str = Field(..., description="IP地址")
    date: str = Field(..., description="发现日期 (YYYY-MM-DD)")
    botnet_type: str = Field(..., description="僵尸网络类型")
    timestamp: str = Field(..., description="时间戳")

class IPUploadRequest(BaseModel):
    """IP数据上传请求模型"""
    botnet_type: str = Field(..., description="僵尸网络类型")
    ip_data: List[IPData] = Field(..., description="IP数据列表")
    source_ip: Optional[str] = Field(None, description="远端服务器IP")

class IPUploadResponse(BaseModel):
    """IP数据上传响应模型"""
    status: str
    message: str
    received_count: int
    processed_count: int
    duplicate_count: int
    saved_to: str
    timestamp: str

# ============================================================
# 修改建议：在main.py中添加新的API端点
# ============================================================

def add_ip_upload_endpoint(app: FastAPI):
    """
    在main.py中添加这个新的API端点
    """
    
    @app.post("/api/upload-ip-data", response_model=IPUploadResponse)
    async def upload_ip_data(
        request: IPUploadRequest,
        client_request: Request,
        x_api_key: Optional[str] = Header(None, alias="X-API-Key")
    ):
        """
        接收远端上传的IP数据（新格式）
        
        与原有的upload-logs接口的区别：
        1. 接收的是结构化的IP数据，而不是原始日志行
        2. 远端已经完成了IP提取和去重
        3. 数据格式更加标准化
        
        安全特性：
        - API密钥认证（Header: X-API-Key）
        - IP白名单验证
        - 僵尸网络类型验证
        
        示例请求:
        curl -X POST "http://localhost:8000/api/upload-ip-data" \\
             -H "Content-Type: application/json" \\
             -H "X-API-Key: your-api-key" \\
             -d '{
               "botnet_type": "mozi",
               "ip_data": [
                 {
                   "ip": "1.2.3.4",
                   "date": "2024-11-18",
                   "botnet_type": "mozi",
                   "timestamp": "2024-11-18T10:30:00"
                 }
               ],
               "source_ip": "192.168.1.100"
             }'
        """
        try:
            from config import API_KEY, ALLOWED_UPLOAD_IPS, ALLOWED_BOTNET_TYPES
            
            client_ip = client_request.client.host
            
            # 安全检查1：验证API密钥
            if x_api_key != API_KEY:
                logger.warning(f"无效的API密钥尝试，来自IP: {client_ip}")
                raise HTTPException(status_code=401, detail="无效的API密钥")
            
            # 安全检查2：IP白名单验证（如果配置了白名单）
            if ALLOWED_UPLOAD_IPS and client_ip not in ALLOWED_UPLOAD_IPS:
                logger.warning(f"未授权的IP尝试上传: {client_ip}")
                raise HTTPException(status_code=403, detail="IP未授权")
            
            # 安全检查3：僵尸网络类型验证
            if request.botnet_type not in ALLOWED_BOTNET_TYPES:
                raise HTTPException(status_code=400, detail=f"不支持的僵尸网络类型: {request.botnet_type}")
            
            logger.info(f"收到来自 {client_ip} 的IP数据上传请求，类型: {request.botnet_type}, IP数量: {len(request.ip_data)}")
            
            # 处理IP数据
            processed_count = 0
            duplicate_count = 0
            
            # 确定保存路径
            logs_base_dir = os.path.join(os.path.dirname(__file__), 'logs')
            botnet_dir = os.path.join(logs_base_dir, request.botnet_type)
            
            # 创建目录（如果不存在）
            os.makedirs(botnet_dir, exist_ok=True)
            
            # 按日期分组保存IP数据
            daily_ips = {}
            for ip_data in request.ip_data:
                date = ip_data.date
                if date not in daily_ips:
                    daily_ips[date] = []
                daily_ips[date].append(ip_data.ip)
            
            saved_files = []
            
            # 为每个日期创建/追加日志文件
            for date, ips in daily_ips.items():
                log_file = os.path.join(botnet_dir, f'{date}.txt')
                
                # 读取现有IP（用于去重）
                existing_ips = set()
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line and ',' in line:
                                    # 假设格式：timestamp,ip,other_data
                                    parts = line.split(',')
                                    if len(parts) >= 2:
                                        existing_ips.add(parts[1])
                    except Exception as e:
                        logger.warning(f"读取现有日志文件失败 {log_file}: {e}")
                
                # 写入新IP（去重）
                new_ips = []
                for ip in ips:
                    if ip not in existing_ips:
                        new_ips.append(ip)
                        processed_count += 1
                    else:
                        duplicate_count += 1
                
                if new_ips:
                    with open(log_file, 'a', encoding='utf-8') as f:
                        for ip in new_ips:
                            # 生成日志行格式：timestamp,ip,source,type
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            log_line = f"{timestamp},{ip},remote_upload,{request.botnet_type}\\n"
                            f.write(log_line)
                    
                    saved_files.append(log_file)
                    logger.info(f"保存 {len(new_ips)} 个新IP到 {log_file}")
            
            logger.info(f"✅ IP数据处理完成: 接收 {len(request.ip_data)}, 处理 {processed_count}, 重复 {duplicate_count}")
            
            return IPUploadResponse(
                status="success",
                message=f"成功处理 {processed_count} 个新IP，跳过 {duplicate_count} 个重复IP",
                received_count=len(request.ip_data),
                processed_count=processed_count,
                duplicate_count=duplicate_count,
                saved_to=", ".join(saved_files) if saved_files else "无新数据",
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ IP数据上传处理失败: {e}")
            raise HTTPException(status_code=500, detail=f"IP数据上传失败: {str(e)}")

# ============================================================
# 配置文件修改建议
# ============================================================

def update_config_suggestions():
    """
    config.py 需要添加的配置项
    """
    return """
# 在 config.py 中添加以下配置：

# 支持的僵尸网络类型
ALLOWED_BOTNET_TYPES = [
    'asruex', 'mozi', 'andromeda', 
    'moobot', 'ramnit', 'leethozer'
]

# 每次上传的最大IP数量限制
MAX_IPS_PER_UPLOAD = 1000

# IP数据验证配置
IP_VALIDATION = {
    'enable_private_ip_filter': True,  # 是否过滤私有IP
    'enable_duplicate_check': True,    # 是否检查重复
    'max_ip_age_days': 30             # IP数据最大保留天数
}
"""

# ============================================================
# 日志处理器修改建议
# ============================================================

def log_processor_modifications():
    """
    日志处理器可能需要的修改
    """
    return """
日志处理器修改建议：

1. 兼容性考虑：
   - 现有的日志处理器应该能够处理两种格式的日志文件
   - 原有的upload-logs接口生成的日志格式
   - 新的upload-ip-data接口生成的日志格式

2. 格式识别：
   - 可以通过日志行的格式来区分数据来源
   - 原格式：可能包含更多原始日志信息
   - 新格式：timestamp,ip,remote_upload,botnet_type

3. 处理逻辑：
   - 保持现有的IP提取和去重逻辑
   - 对于remote_upload来源的数据，可以跳过某些处理步骤
   - 统计时区分本地处理和远端上传的数据

4. 性能优化：
   - 远端已经完成了去重，本地可以减少重复处理
   - 可以优先处理远端上传的数据

5. 监控和统计：
   - 分别统计本地日志和远端上传的数据量
   - 监控远端上传的频率和质量
"""

# ============================================================
# 部署建议
# ============================================================

def deployment_suggestions():
    """
    部署建议
    """
    return """
部署建议：

1. 渐进式部署：
   - 先部署新的API接口，保持向后兼容
   - 测试远端上传功能
   - 逐步切换到新的数据格式

2. 监控和日志：
   - 监控两种接口的使用情况
   - 记录数据处理的统计信息
   - 设置告警机制

3. 安全考虑：
   - 确保API密钥的安全性
   - 定期更新白名单
   - 监控异常访问

4. 性能优化：
   - 根据实际数据量调整批量大小
   - 优化文件I/O操作
   - 考虑使用数据库存储IP数据

5. 备份和恢复：
   - 定期备份日志文件
   - 建立数据恢复机制
   - 测试灾难恢复流程
"""

if __name__ == "__main__":
    print("本地API接口修改建议")
    print("=" * 50)
    print(update_config_suggestions())
    print(log_processor_modifications())
    print(deployment_suggestions())
