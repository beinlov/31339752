"""
用户管理集成接口
包含SSO免登录接口和用户数据同步接口

用于集成到大型平台系统
"""
from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, Field, validator
import pymysql
from typing import Optional, List
import jwt
from datetime import datetime, timedelta
import hashlib
import logging
from config import DB_CONFIG, SSO_CONFIG, SYNC_CONFIG

# 设置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# JWT配置
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"


# ============================================================
# 辅助函数
# ============================================================

def get_password_hash(password: str) -> str:
    """使用MD5哈希密码"""
    return hashlib.md5(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        calculated_hash = get_password_hash(plain_password)
        return calculated_hash == hashed_password
    except Exception as e:
        logger.exception("Password verification error:")
        return False


def verify_client_ip(request: Request, config_key='SSO_CONFIG') -> bool:
    """验证客户端IP是否在白名单中"""
    config = SSO_CONFIG if config_key == 'SSO_CONFIG' else SYNC_CONFIG
    
    if not config.get('enable_ip_whitelist', False):
        return True
    
    # 获取客户端真实IP
    client_ip = request.client.host
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()
    elif request.headers.get("X-Real-IP"):
        client_ip = request.headers.get("X-Real-IP")
    
    ip_whitelist = config.get('ip_whitelist', [])
    
    # 支持localhost
    if client_ip in ["127.0.0.1", "::1"] and ("127.0.0.1" in ip_whitelist or "localhost" in ip_whitelist):
        return True
    
    return client_ip in ip_whitelist


def verify_sync_api_key(request: Request) -> bool:
    """验证同步接口的API密钥"""
    if not SYNC_CONFIG.get('enable_api_key', True):
        return True
    
    # 从Header获取API密钥
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        # 尝试从查询参数获取
        api_key = request.query_params.get('api_key')
    
    expected_key = SYNC_CONFIG.get('api_key')
    if not expected_key:
        logger.warning("同步接口未配置API密钥")
        return False
    
    return api_key == expected_key


# ============================================================
# 数据模型
# ============================================================

class Token(BaseModel):
    """访问令牌响应模型"""
    access_token: str
    token_type: str
    role: str
    username: str


class SSOLoginRequest(BaseModel):
    """SSO登录请求模型"""
    username: str = Field(..., description="用户名", min_length=1, max_length=50)
    password: str = Field(..., description="用户密码", min_length=1)
    role: Optional[str] = Field(default=None, description="用户角色：管理员、操作员、访客（可选）")
    
    @validator('role')
    def validate_role(cls, v):
        if v is None:
            return v
        valid_roles = ['管理员', '操作员', '访客', 'admin', 'operator', 'viewer']
        role_mapping = {
            'admin': '管理员',
            'operator': '操作员',
            'viewer': '访客'
        }
        if v in role_mapping:
            return role_mapping[v]
        if v not in valid_roles:
            raise ValueError(f'角色必须是以下之一: {", ".join(valid_roles)}')
        return v


class UserSyncRequest(BaseModel):
    """用户数据同步请求模型"""
    username: str = Field(..., description="用户名", min_length=1, max_length=50)
    password: str = Field(..., description="用户密码（明文）", min_length=1)
    role: Optional[str] = Field(default=None, description="用户角色（可选）")
    
    @validator('role')
    def validate_role(cls, v):
        if v is None:
            return v
        valid_roles = ['管理员', '操作员', '访客', 'admin', 'operator', 'viewer']
        role_mapping = {
            'admin': '管理员',
            'operator': '操作员',
            'viewer': '访客'
        }
        if v in role_mapping:
            return role_mapping[v]
        if v not in valid_roles:
            raise ValueError(f'角色必须是以下之一: {", ".join(valid_roles)}')
        return v


class UserSyncResponse(BaseModel):
    """用户数据同步响应模型"""
    success: bool = Field(..., description="同步是否成功")
    message: str = Field(..., description="响应消息")
    username: str = Field(..., description="用户名")
    action: str = Field(..., description="执行的操作：created 或 updated")
    role: str = Field(..., description="用户角色")


class BatchUserSyncRequest(BaseModel):
    """批量用户数据同步请求模型"""
    users: List[UserSyncRequest] = Field(..., description="用户列表", min_items=1, max_items=100)


class UserDeleteRequest(BaseModel):
    """删除用户请求模型"""
    username: str = Field(..., description="要删除的用户名", min_length=1, max_length=50)


class UserDeleteResponse(BaseModel):
    """删除用户响应模型"""
    success: bool = Field(..., description="删除是否成功")
    message: str = Field(..., description="响应消息")
    username: str = Field(..., description="被删除的用户名")


class BatchUserDeleteRequest(BaseModel):
    """批量删除用户请求模型"""
    usernames: List[str] = Field(..., description="要删除的用户名列表", min_items=1, max_items=100)


# ============================================================
# SSO免登录接口
# ============================================================

@router.post("/sso-login", response_model=Token)
async def sso_login(request_data: SSOLoginRequest, request: Request):
    """
    SSO免登录接口（单点登录）
    
    用于集成到其他系统中，通过传递用户名和密码实现免登录访问。
    子系统可以调用此接口验证用户密码是否正确，验证通过后返回访问令牌。
    
    安全机制：
    1. 密码验证：验证用户提供的密码是否正确
    2. IP白名单：可选启用（默认关闭）
    
    **接口文档**: `another/botnet/backend/SSO_INTEGRATION.md`
    """
    conn = None
    cursor = None
    
    try:
        # 1. IP白名单验证（如果启用）
        if not verify_client_ip(request, 'SSO_CONFIG'):
            logger.warning(f"SSO login rejected: IP not in whitelist - {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP地址不在白名单中"
            )
        
        # 2. 查询用户
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, username, password, role, status FROM users WHERE username = %s",
            (request_data.username,)
        )
        user = cursor.fetchone()
        
        if not user:
            logger.warning(f"SSO login rejected: User {request_data.username} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        user_id, username, stored_password, user_role, user_status = user
        
        # 3. 验证密码
        if not verify_password(request_data.password, stored_password):
            logger.warning(f"SSO login rejected: Invalid password for user {request_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 4. 更新用户角色（如果提供）
        final_role = user_role
        if request_data.role:
            final_role = request_data.role
            cursor.execute(
                "UPDATE users SET role = %s WHERE id = %s",
                (final_role, user_id)
            )
        
        # 5. 更新用户状态和最后登录时间
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "UPDATE users SET last_login = %s, status = '在线' WHERE id = %s",
            (now, user_id)
        )
        conn.commit()
        
        # 6. 创建访问令牌
        sso_token_expire = SSO_CONFIG.get('sso_token_expire_minutes', 60)
        to_encode = {
            "sub": username,
            "role": final_role,
            "sso": True,  # 标记为SSO登录
            "exp": datetime.utcnow() + timedelta(minutes=sso_token_expire)
        }
        access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        logger.info(f"SSO login successful: {username} with role {final_role}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": final_role,
            "username": username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SSO login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SSO登录失败: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/sso-config")
async def get_sso_config():
    """
    获取SSO配置信息（用于集成方了解配置）
    """
    return {
        "token_expire_minutes": SSO_CONFIG.get('sso_token_expire_minutes', 60),
        "ip_whitelist_enabled": SSO_CONFIG.get('enable_ip_whitelist', False),
        "authentication_method": "password",
        "description": "通过用户名和密码进行身份验证"
    }


# ============================================================
# 用户数据同步接口
# ============================================================

@router.post("/sync-user", response_model=UserSyncResponse)
async def sync_user(user: UserSyncRequest, request: Request):
    """
    用户数据同步接口
    
    集成平台调用此接口将用户数据同步到子系统：
    1. 如果用户不存在，创建新用户（使用默认角色）
    2. 如果用户已存在，更新用户密码和角色（如果提供）
    
    安全机制：
    - API密钥验证（可选）
    - IP白名单验证（可选）
    
    **接口文档**: `another/botnet/backend/USER_SYNC_DESIGN.md`
    """
    conn = None
    cursor = None
    
    try:
        # 验证API密钥
        if not verify_sync_api_key(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API密钥验证失败"
            )
        
        # 验证IP白名单
        if not verify_client_ip(request, 'SYNC_CONFIG'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP地址不在白名单中"
            )
        
        logger.info(f"收到用户同步请求: username={user.username}")
        
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查用户是否已存在
        cursor.execute("SELECT id, username, role FROM users WHERE username = %s", (user.username,))
        existing_user = cursor.fetchone()
        
        # 确定用户角色
        user_role = user.role if user.role else SYNC_CONFIG.get('default_role', '访客')
        default_status = SYNC_CONFIG.get('default_status', '离线')
        
        now = datetime.now().strftime("%Y/%m/%d %H:%M")
        hashed_password = get_password_hash(user.password)
        
        if existing_user:
            # 用户已存在，更新密码和角色
            logger.info(f"用户已存在，更新用户: {user.username}")
            
            cursor.execute(
                """
                UPDATE users 
                SET password = %s, role = %s 
                WHERE username = %s
                """,
                (hashed_password, user_role, user.username)
            )
            
            conn.commit()
            action = "updated"
            message = f"用户 {user.username} 同步成功（已更新）"
            
        else:
            # 用户不存在，创建新用户
            logger.info(f"用户不存在，创建新用户: {user.username}")
            
            cursor.execute(
                """
                INSERT INTO users (username, password, role, last_login, status)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user.username, hashed_password, user_role, now, default_status)
            )
            
            conn.commit()
            action = "created"
            message = f"用户 {user.username} 同步成功（已创建）"
        
        logger.info(f"用户同步完成: {user.username}, action={action}, role={user_role}")
        
        return UserSyncResponse(
            success=True,
            message=message,
            username=user.username,
            action=action,
            role=user_role
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户同步失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"用户同步失败: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.post("/sync-users-batch")
async def sync_users_batch(batch_request: BatchUserSyncRequest, request: Request):
    """
    批量用户数据同步接口
    
    集成平台可以一次性同步多个用户到子系统
    """
    try:
        # 验证API密钥
        if not verify_sync_api_key(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API密钥验证失败"
            )
        
        # 验证IP白名单
        if not verify_client_ip(request, 'SYNC_CONFIG'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP地址不在白名单中"
            )
        
        logger.info(f"收到批量用户同步请求: {len(batch_request.users)} 个用户")
        
        results = []
        success_count = 0
        fail_count = 0
        
        # 逐个同步用户
        for user_req in batch_request.users:
            try:
                # 复用单个用户同步逻辑
                response = await sync_user(user_req, request)
                results.append({
                    "username": response.username,
                    "success": response.success,
                    "action": response.action,
                    "message": response.message,
                    "role": response.role
                })
                success_count += 1
            except Exception as e:
                logger.error(f"批量同步中用户失败: {user_req.username}, error: {str(e)}")
                results.append({
                    "username": user_req.username,
                    "success": False,
                    "action": "failed",
                    "message": f"同步失败: {str(e)}",
                    "role": None
                })
                fail_count += 1
        
        return {
            "total": len(batch_request.users),
            "success": success_count,
            "failed": fail_count,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量用户同步失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量用户同步失败: {str(e)}"
        )


@router.delete("/sync-user", response_model=UserDeleteResponse)
async def delete_sync_user(delete_req: UserDeleteRequest, request: Request):
    """
    删除用户同步接口
    
    集成平台调用此接口删除子系统中的用户
    
    安全机制：
    - API密钥验证
    - IP白名单验证
    - 禁止删除admin用户
    
    **接口文档**: `another/botnet/backend/USER_SYNC_DESIGN.md`
    """
    conn = None
    cursor = None
    
    try:
        # 验证API密钥
        if not verify_sync_api_key(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API密钥验证失败"
            )
        
        # 验证IP白名单
        if not verify_client_ip(request, 'SYNC_CONFIG'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP地址不在白名单中"
            )
        
        logger.info(f"收到删除用户请求: username={delete_req.username}")
        
        # 禁止删除admin用户
        if delete_req.username == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除admin用户"
            )
        
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查用户是否存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (delete_req.username,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 删除用户
        cursor.execute("DELETE FROM users WHERE username = %s", (delete_req.username,))
        conn.commit()
        
        logger.info(f"用户删除成功: {delete_req.username}")
        
        return UserDeleteResponse(
            success=True,
            message=f"用户 {delete_req.username} 删除成功",
            username=delete_req.username
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户删除失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"用户删除失败: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.delete("/sync-users-batch")
async def delete_sync_users_batch(batch_delete_req: BatchUserDeleteRequest, request: Request):
    """
    批量删除用户同步接口
    
    集成平台可以一次性删除多个用户
    """
    try:
        # 验证API密钥
        if not verify_sync_api_key(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API密钥验证失败"
            )
        
        # 验证IP白名单
        if not verify_client_ip(request, 'SYNC_CONFIG'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP地址不在白名单中"
            )
        
        logger.info(f"收到批量删除用户请求: {len(batch_delete_req.usernames)} 个用户")
        
        results = []
        success_count = 0
        fail_count = 0
        
        # 逐个删除用户
        for username in batch_delete_req.usernames:
            try:
                delete_req = UserDeleteRequest(username=username)
                response = await delete_sync_user(delete_req, request)
                results.append({
                    "username": response.username,
                    "success": response.success,
                    "message": response.message
                })
                success_count += 1
            except Exception as e:
                logger.error(f"批量删除中用户失败: {username}, error: {str(e)}")
                error_msg = "删除失败: "
                if "不能删除admin用户" in str(e):
                    error_msg += "不能删除admin用户"
                elif "用户不存在" in str(e):
                    error_msg += "用户不存在"
                else:
                    error_msg += str(e)
                
                results.append({
                    "username": username,
                    "success": False,
                    "message": error_msg
                })
                fail_count += 1
        
        return {
            "total": len(batch_delete_req.usernames),
            "success": success_count,
            "failed": fail_count,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除用户失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量删除用户失败: {str(e)}"
        )


@router.get("/sync-config")
async def get_sync_config():
    """
    获取用户数据同步接口配置信息（用于集成平台了解配置）
    """
    return {
        "api_key_enabled": SYNC_CONFIG.get('enable_api_key', True),
        "ip_whitelist_enabled": SYNC_CONFIG.get('enable_ip_whitelist', True),
        "default_role": SYNC_CONFIG.get('default_role', '访客'),
        "default_status": SYNC_CONFIG.get('default_status', '离线'),
        "description": "集成平台通过此接口将用户数据同步到课题三子系统",
        "endpoints": {
            "single": "/api/user/sync-user",
            "batch": "/api/user/sync-users-batch",
            "delete": "/api/user/sync-user",
            "delete_batch": "/api/user/sync-users-batch",
            "config": "/api/user/sync-config"
        }
    }


