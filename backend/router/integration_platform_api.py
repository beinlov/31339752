"""
第三方集成平台用户管理API接口
专为外部集成平台提供用户名密码的增删改查操作

功能包括：
1. 获取用户列表（用户名）
2. 创建用户（用户名+密码）
3. 更新用户密码
4. 删除用户
5. 简化的API密钥认证
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request, Query, Header
from pydantic import BaseModel, Field, field_validator
import pymysql
from pymysql.cursors import DictCursor
from typing import Optional, List, Dict, Any
import hashlib
import logging
from datetime import datetime
from config import DB_CONFIG

# 设置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================
# 第三方集成平台配置
# ============================================================

# 集成平台API密钥配置（生产环境必须修改）
INTEGRATION_API_KEY = "THIRD_PARTY_INTEGRATION_KEY_2024"

# 是否启用IP白名单验证
ENABLE_IP_WHITELIST = False

# 集成平台IP白名单
IP_WHITELIST = [
    "127.0.0.1",
    "localhost",
    # 添加第三方集成平台的实际IP地址
    # "192.168.1.100",
    # "10.0.0.50",
]

# ============================================================
# 数据模型
# ============================================================

class UserCreateRequest(BaseModel):
    """创建用户请求"""
    username: str = Field(..., description="用户名", min_length=1, max_length=50)
    password: str = Field(..., description="密码", min_length=6)

class UserUpdateRequest(BaseModel):
    """更新用户密码请求"""
    password: str = Field(..., description="新密码", min_length=6)

class UserResponse(BaseModel):
    """用户操作响应"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")

class UserListResponse(BaseModel):
    """用户列表响应"""
    success: bool = Field(..., description="操作是否成功")
    users: List[str] = Field(..., description="用户名列表")
    total: int = Field(..., description="用户总数")

# ============================================================
# 辅助函数
# ============================================================

def get_password_hash(password: str) -> str:
    """使用MD5哈希密码"""
    return hashlib.md5(password.encode()).hexdigest()

def verify_api_key(api_key: Optional[str] = Header(None, alias="X-API-Key")) -> bool:
    """验证API密钥"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少API密钥，请在请求头中添加 X-API-Key"
        )
    
    if api_key != INTEGRATION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API密钥无效"
        )
    
    return True

def verify_ip_whitelist(request: Request) -> bool:
    """验证IP白名单"""
    if not ENABLE_IP_WHITELIST:
        return True
    
    # 获取客户端真实IP
    client_ip = request.client.host
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()
    elif request.headers.get("X-Real-IP"):
        client_ip = request.headers.get("X-Real-IP")
    
    # 支持localhost
    if client_ip in ["127.0.0.1", "::1"] and ("127.0.0.1" in IP_WHITELIST or "localhost" in IP_WHITELIST):
        return True
    
    if client_ip not in IP_WHITELIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="IP地址不在白名单中"
        )
    
    return True

# ============================================================
# 用户管理接口
# ============================================================

# ============================================================
# 用户信息查询接口
# ============================================================

@router.get("/users", response_model=UserListResponse)
async def get_users_list(
    request: Request,
    _: bool = Depends(verify_api_key)
):
    """
    获取所有用户名列表
    
    第三方集成平台调用此接口获取系统中所有用户的用户名
    """
    conn = None
    cursor = None
    
    try:
        # 验证IP白名单
        verify_ip_whitelist(request)
        
        logger.info("第三方集成平台请求用户列表")
        
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 获取所有用户名
        cursor.execute("SELECT username FROM users ORDER BY id")
        users_data = cursor.fetchall()
        
        # 提取用户名列表
        usernames = [user[0] for user in users_data]
        
        return UserListResponse(
            success=True,
            users=usernames,
            total=len(usernames)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/users/{username}")
async def check_user_exists(
    username: str,
    request: Request,
    _: bool = Depends(verify_api_key)
):
    """
    检查用户是否存在
    
    第三方集成平台调用此接口检查指定用户名是否存在
    """
    conn = None
    cursor = None
    
    try:
        # 验证IP白名单
        verify_ip_whitelist(request)
        
        logger.info(f"第三方集成平台检查用户是否存在: {username}")
        
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 查询用户是否存在
        cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        return UserResponse(
            success=True,
            message=f"用户 {username} {'存在' if user else '不存在'}",
            data={"username": username, "exists": bool(user)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查用户失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查用户失败: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_request: UserCreateRequest,
    request: Request,
    _: bool = Depends(verify_api_key)
):
    """
    创建新用户
    
    第三方集成平台调用此接口创建新用户（用户名+密码）
    默认角色为"访客"，状态为"离线"
    """
    conn = None
    cursor = None
    
    try:
        # 验证IP白名单
        verify_ip_whitelist(request)
        
        logger.info(f"第三方集成平台创建用户: {user_request.username}")
        
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查用户名是否已存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (user_request.username,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 创建新用户
        hashed_password = get_password_hash(user_request.password)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            """
            INSERT INTO users (username, password, role, last_login, status)
            VALUES (%s, %s, '访客', %s, '离线')
            """,
            (user_request.username, hashed_password, now)
        )
        
        user_id = cursor.lastrowid
        conn.commit()
        
        logger.info(f"用户创建成功: {user_request.username} (ID: {user_id})")
        
        return UserResponse(
            success=True,
            message=f"用户 {user_request.username} 创建成功",
            data={"user_id": user_id, "username": user_request.username}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建用户失败: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.put("/users/{username}", response_model=UserResponse)
async def update_user_password(
    username: str,
    user_request: UserUpdateRequest,
    request: Request,
    _: bool = Depends(verify_api_key)
):
    """
    更新用户密码
    
    第三方集成平台调用此接口更新指定用户的密码
    """
    conn = None
    cursor = None
    
    try:
        # 验证IP白名单
        verify_ip_whitelist(request)
        
        logger.info(f"第三方集成平台更新用户密码: {username}")
        
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查用户是否存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 禁止修改admin用户密码
        if username == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能修改admin用户密码"
            )
        
        # 更新密码
        hashed_password = get_password_hash(user_request.password)
        cursor.execute(
            "UPDATE users SET password = %s WHERE username = %s",
            (hashed_password, username)
        )
        conn.commit()
        
        logger.info(f"用户密码更新成功: {username}")
        
        return UserResponse(
            success=True,
            message=f"用户 {username} 密码更新成功",
            data={"username": username}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户密码失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户密码失败: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.delete("/users/{username}", response_model=UserResponse)
async def delete_user(
    username: str,
    request: Request,
    _: bool = Depends(verify_api_key)
):
    """
    删除用户
    
    第三方集成平台调用此接口删除指定用户
    """
    conn = None
    cursor = None
    
    try:
        # 验证IP白名单
        verify_ip_whitelist(request)
        
        logger.info(f"第三方集成平台删除用户: {username}")
        
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查用户是否存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 禁止删除admin用户
        if username == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除admin用户"
            )
        
        # 删除用户
        cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        conn.commit()
        
        logger.info(f"用户删除成功: {username}")
        
        return UserResponse(
            success=True,
            message=f"用户 {username} 删除成功",
            data={"username": username}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户失败: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================
# 配置和状态接口
# ============================================================

@router.get("/config")
async def get_integration_config():
    """
    获取第三方集成平台接口配置信息
    
    返回API接口的基本配置信息，便于第三方集成平台了解接口规范
    """
    return {
        "api_version": "1.0",
        "description": "第三方集成平台用户管理API - 专注于用户名密码的增删改查操作",
        "authentication": {
            "type": "API Key",
            "header": "X-API-Key",
            "required": True
        },
        "endpoints": {
            "get_users": {
                "method": "GET",
                "path": "/api/integration/users",
                "description": "获取所有用户名列表"
            },
            "check_user": {
                "method": "GET",
                "path": "/api/integration/users/{username}",
                "description": "检查用户是否存在"
            },
            "create_user": {
                "method": "POST",
                "path": "/api/integration/users",
                "description": "创建新用户（用户名+密码）"
            },
            "update_password": {
                "method": "PUT",
                "path": "/api/integration/users/{username}",
                "description": "更新用户密码"
            },
            "delete_user": {
                "method": "DELETE",
                "path": "/api/integration/users/{username}",
                "description": "删除用户"
            },
            "config": {
                "method": "GET",
                "path": "/api/integration/config",
                "description": "获取接口配置信息"
            }
        },
        "security": {
            "api_key_enabled": True,
            "ip_whitelist_enabled": ENABLE_IP_WHITELIST,
            "protected_users": ["admin"]
        },
        "user_defaults": {
            "role": "访客",
            "status": "离线"
        },
        "notes": [
            "所有接口都需要在请求头中提供 X-API-Key",
            "创建的用户默认角色为'访客'，状态为'离线'",
            "不能修改或删除admin用户",
            "密码使用MD5哈希存储"
        ]
    }
