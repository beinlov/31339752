"""
权限验证中间件
用于验证用户角色和权限
"""
from fastapi import HTTPException, status, Header
from typing import Optional
import jwt
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 从config导入配置
try:
    from config import SECRET_KEY, ALGORITHM
except ImportError:
    from config_docker import SECRET_KEY, ALGORITHM

def verify_token(authorization: Optional[str] = Header(None)):
    """
    验证JWT token并返回用户信息
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌"
        )
    
    try:
        # 提取token (格式: "Bearer <token>")
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌格式"
            )
        
        token = authorization.replace("Bearer ", "")
        
        # 解码token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        
        if username is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌"
            )
        
        return {"username": username, "role": role}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌已过期"
        )
    except jwt.InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌签名"
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )


def require_role(*allowed_roles):
    """
    装饰器：要求特定角色才能访问
    用法: current_user = Depends(require_role("管理员", "操作员"))
    """
    def role_checker(authorization: Optional[str] = Header(None)):
        user = verify_token(authorization)
        
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要以下角色之一: {', '.join(allowed_roles)}"
            )
        
        return user
    
    return role_checker


def require_admin(authorization: Optional[str] = Header(None)):
    """
    要求管理员权限
    """
    user = verify_token(authorization)
    
    if user["role"] != "管理员":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    return user


def require_operator_or_admin(authorization: Optional[str] = Header(None)):
    """
    要求操作员或管理员权限
    """
    user = verify_token(authorization)
    
    if user["role"] not in ["管理员", "操作员"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要操作员或管理员权限"
        )
    
    return user
