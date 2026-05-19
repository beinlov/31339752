from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import pymysql
from pymysql.cursors import DictCursor
from typing import Optional
import jwt
from datetime import datetime, timedelta
import bcrypt
import logging
import hashlib
import secrets
from config import DB_CONFIG, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from auth_middleware import require_admin

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 一次性登录token存储（生产环境建议使用Redis）
# 格式: {token: {"username": str, "password": str, "expires_at": datetime, "used": bool}}
login_tokens = {}

# 数据模型
class User(BaseModel):
    id: int
    username: str
    password: str
    role: str
    status: str
    last_login: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/login")

# 辅助函数
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_password_hash(password: str) -> str:
    # 使用简单的MD5哈希用于测试
    return hashlib.md5(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # 详细的调试日志
        logger.debug(f"Verifying password:")
        logger.debug(f"Plain password: {plain_password}")
        logger.debug(f"Plain password length: {len(plain_password)}")
        logger.debug(f"Plain password bytes: {plain_password.encode().hex()}")
        
        # 计算输入密码的哈希
        calculated_hash = get_password_hash(plain_password)
        logger.debug(f"Calculated hash: {calculated_hash}")
        logger.debug(f"Stored hash: {hashed_password}")
        
        # 比较哈希值
        result = calculated_hash == hashed_password
        logger.debug(f"Password verification result: {result}")
        return result
    except Exception as e:
        logger.exception("Password verification error:")
        return False

# 用于生成测试哈希的辅助函数
def generate_test_hash(password: str = 'admin123') -> str:
    return get_password_hash(password)

def generate_login_token(username: str, password: str, expires_minutes: int = 30) -> str:
    """
    生成一次性登录token
    
    Args:
        username: 用户名
        password: 密码（明文）
        expires_minutes: token过期时间（分钟），默认30分钟
    
    Returns:
        token字符串
    """
    # 生成随机token
    token = secrets.token_urlsafe(32)
    
    # 存储token信息
    login_tokens[token] = {
        "username": username,
        "password": password,
        "expires_at": datetime.now() + timedelta(minutes=expires_minutes),
        "used": False
    }
    
    logger.info(f"Generated login token for user: {username}, expires in {expires_minutes} minutes")
    return token

def verify_login_token(token: str) -> Optional[dict]:
    """
    验证登录token（在有效期内可重复使用）
    
    Args:
        token: token字符串
    
    Returns:
        如果token有效，返回用户信息字典 {"username": str, "password": str}
        如果token无效或过期，返回None
    """
    if token not in login_tokens:
        logger.warning(f"Invalid login token: {token[:10]}...")
        return None
    
    token_info = login_tokens[token]
    
    # 检查是否过期
    if datetime.now() > token_info["expires_at"]:
        logger.warning(f"Login token expired: {token[:10]}...")
        del login_tokens[token]  # 清理过期token
        return None
    
    # 返回用户信息（不标记为已使用，允许重复使用）
    user_info = {
        "username": token_info["username"],
        "password": token_info["password"]
    }
    
    logger.info(f"Login token verified for user: {user_info['username']}")
    
    return user_info

# 路由
@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = None
    cursor = None
    try:
        logger.info(f"Login attempt for user: {form_data.username}")
        logger.debug(f"Received password: {form_data.password}")
        logger.debug(f"Password length: {len(form_data.password)}")
        
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 查询用户
        cursor.execute(
            "SELECT id, username, password, role, status FROM users WHERE username = %s",
            (form_data.username,)
        )
        user = cursor.fetchone()
        
        if not user:
            logger.warning(f"User not found: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        logger.debug(f"Found user: {user[1]}")
        logger.debug(f"Stored password hash: {user[2]}")
        
        # 验证密码
        if not verify_password(form_data.password, user[2]):
            logger.warning(f"Invalid password for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 更新最后登录时间和状态
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "UPDATE users SET last_login = %s, status = '在线' WHERE id = %s",
            (now, user[0])
        )
        conn.commit()
        
        # 创建访问令牌
        access_token = create_access_token(
            data={"sub": user[1], "role": user[3]}
        )
        
        logger.info(f"User {form_data.username} logged in successfully")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user[3],
            "username": user[1]
        }
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.post("/generate-login-token")
async def generate_login_token_endpoint(username: str, password: str, expires_minutes: int = 30):
    """
    生成登录token接口
    
    此接口供其他平台调用，生成一个登录token。
    其他平台获取到token后，可以通过URL跳转：
    http://your-domain:9000/login?token=<生成的token>
    
    安全特性：
    - token在有效期内可重复使用
    - token有过期时间（默认30分钟）
    
    参数：
    - username: 用户名
    - password: 密码（明文，仅用于生成token）
    - expires_minutes: token过期时间（分钟），默认30分钟
    
    返回：
    - token: 登录token
    - expires_at: 过期时间
    - login_url: 完整的登录URL
    
    使用示例：
    1. 其他平台调用此接口生成token
    2. 使用返回的login_url跳转到本平台
    3. 本平台自动完成登录
    """
    conn = None
    cursor = None
    try:
        logger.info(f"Token generation request for user: {username}")
        
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 验证用户名和密码
        cursor.execute(
            "SELECT id, username, password, role FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            logger.warning(f"Token generation failed: User not found - {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 验证密码
        if not verify_password(password, user[2]):
            logger.warning(f"Token generation failed: Invalid password for user - {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 生成token
        token = generate_login_token(username, password, expires_minutes)
        expires_at = datetime.now() + timedelta(minutes=expires_minutes)
        
        # 构建登录URL（这里需要根据实际部署地址修改）
        login_url = f"/login?token={token}"
        
        logger.info(f"Token generated successfully for user: {username}")
        return {
            "token": token,
            "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S"),
            "expires_in_seconds": expires_minutes * 60,
            "login_url": login_url
        }
        
    except Exception as e:
        logger.error(f"Token generation error: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成登录token失败"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/auto-login", response_model=Token)
async def auto_login(token: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None):
    """
    URL参数免登录接口（支持token和传统方式）
    
    **推荐使用token方式（更安全）：**
    1. 先调用 /api/user/generate-login-token 生成token
    2. 使用URL跳转: http://localhost:9000/login?token=<生成的token>
    
    **传统方式（兼容性，不推荐）：**
    http://localhost:9000/login?username=op1&password=123456
    
    前端会自动检测URL参数，调用此接口验证并自动登录。
    
    参数：
    - token: 一次性登录token（推荐）
    - username: 用户名（传统方式）
    - password: 密码明文（传统方式）
    
    返回：
    - access_token: JWT令牌
    - token_type: bearer
    - role: 用户角色
    - username: 用户名
    """
    conn = None
    cursor = None
    try:
        # 优先使用token方式
        if token:
            logger.info(f"Auto-login attempt with token: {token[:10]}...")
            
            # 验证token
            user_info = verify_login_token(token)
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="登录token无效、已过期或已使用"
                )
            
            username = user_info["username"]
            password = user_info["password"]
            logger.info(f"Token verified, auto-login for user: {username}")
        
        # 传统方式（兼容性）
        elif username and password:
            logger.info(f"Auto-login attempt with username/password (legacy mode): {username}")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供token或username+password参数"
            )
        
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 查询用户
        cursor.execute(
            "SELECT id, username, password, role, status FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            logger.warning(f"Auto-login failed: User not found - {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 验证密码
        if not verify_password(password, user[2]):
            logger.warning(f"Auto-login failed: Invalid password for user - {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 更新最后登录时间和状态
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "UPDATE users SET last_login = %s, status = '在线' WHERE id = %s",
            (now, user[0])
        )
        conn.commit()
        
        # 创建访问令牌
        access_token = create_access_token(
            data={"sub": user[1], "role": user[3]}
        )
        
        logger.info(f"Auto-login successful for user: {username}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user[3],
            "username": user[1]
        }
        
    except Exception as e:
        logger.error(f"Auto-login error: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="自动登录失败"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.post("/logout/{username}")
async def logout(username: str):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET status = '离线' WHERE username = %s",
            (username,)
        )
        conn.commit()
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.get("/users")
async def get_users():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, username, password, role, last_login, status FROM users"
        )
        users = cursor.fetchall()
        
        return [
            {
                "id": user[0],
                "username": user[1],
                "password": user[2],
                "role": user[3],
                "lastLogin": user[4],
                "status": user[5]
            }
            for user in users
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.post("/users")
async def create_user(user: UserCreate, current_user: dict = Depends(require_admin)):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查用户名是否已存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (user.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 创建新用户
        hashed_password = get_password_hash(user.password)
        now = datetime.now().strftime("%Y/%m/%d %H:%M")
        
        cursor.execute(
            """
            INSERT INTO users (username, password, role, last_login, status)
            VALUES (%s, %s, %s, %s, '离线')
            """,
            (user.username, hashed_password, user.role, now)
        )
        conn.commit()
        
        return {"message": "User created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.put("/users/{user_id}")
async def update_user(user_id: int, user: UserUpdate, current_user: dict = Depends(require_admin)):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 构建更新语句
        update_fields = []
        values = []
        
        if user.username is not None:
            update_fields.append("username = %s")
            values.append(user.username)
        
        if user.password is not None:
            update_fields.append("password = %s")
            values.append(get_password_hash(user.password))
        
        if user.role is not None:
            update_fields.append("role = %s")
            values.append(user.role)
            
        if user.status is not None:
            update_fields.append("status = %s")
            values.append(user.status)
        
        if not update_fields:
            return {"message": "No fields to update"}
        
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        
        cursor.execute(query, values)
        conn.commit()
        
        return {"message": "User updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(require_admin)):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查用户是否存在
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        if user[0] == "admin":
            raise HTTPException(status_code=400, detail="Cannot delete admin user")
        
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        
        return {"message": "User deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.get("/statistics")
async def get_user_statistics():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 获取总用户数
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # 获取各角色用户数
        cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
        role_counts = dict(cursor.fetchall())
        
        return {
            "totalUsers": total_users,
            "adminUsers": role_counts.get('管理员', 0),
            "operatorUsers": role_counts.get('操作员', 0),
            "viewerUsers": role_counts.get('访客', 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.get("/activity")
async def get_user_activity():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 获取最近7天的登录统计
        cursor.execute("""
            SELECT DATE(last_login) as login_date, COUNT(*) as login_count
            FROM users
            WHERE last_login >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(last_login)
            ORDER BY login_date
        """)
        
        activity_data = cursor.fetchall()
        
        # 格式化数据
        dates = []
        counts = []
        for date, count in activity_data:
            dates.append(date.strftime("%Y/%m/%d"))
            counts.append(count)
            
        return {
            "dates": dates,
            "loginCounts": counts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.get("/user-operations")
async def get_user_operations():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 获取用户操作统计
        cursor.execute("""
            SELECT 
                username,
                COUNT(*) as operation_count,
                COUNT(DISTINCT DATE(event_time)) as active_days,
                COUNT(DISTINCT botnet_type) as botnet_types,
                MAX(event_time) as last_operation
            FROM user_events
            WHERE username IS NOT NULL
            GROUP BY username
            ORDER BY operation_count DESC
        """)
        
        user_operations = cursor.fetchall()
        
        # 获取操作类型统计
        cursor.execute("""
            SELECT 
                CASE
                    WHEN command LIKE '%clear%' THEN '清除操作'
                    WHEN command LIKE '%reuse%' THEN '再利用'
                    WHEN command LIKE '%suppress%' THEN '抑制操作'
                    ELSE '其他操作'
                END as operation_type,
                COUNT(*) as count
            FROM user_events
            GROUP BY operation_type
        """)
        
        operation_types = cursor.fetchall()
        
        # 获取最近7天的操作趋势
        cursor.execute("""
            SELECT 
                DATE(event_time) as date,
                COUNT(*) as count
            FROM user_events
            WHERE event_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(event_time)
            ORDER BY date
        """)
        
        operation_trend = cursor.fetchall()
        
        return {
            "user_operations": user_operations,
            "operation_types": operation_types,
            "operation_trend": operation_trend
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@router.get("/generate-login-link")
async def generate_login_link(
    username: str,
    password: str,
    menu: Optional[str] = None,
    frontend_url: str = "http://10.10.66.95:83",
    expires_minutes: int = 30  # 默认30分钟有效期，避免用户点击时已过期
):
    conn = None
    cursor = None
    try:
        logger.info(f"Generate login link request for user: {username}")
        
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 验证用户名和密码
        cursor.execute(
            "SELECT id, username, password, role FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            logger.warning(f"Generate link failed: User not found - {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 验证密码
        if not verify_password(password, user[2]):
            logger.warning(f"Generate link failed: Invalid password for user - {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 生成token
        token = generate_login_token(username, password, expires_minutes)
        expires_at = datetime.now() + timedelta(minutes=expires_minutes)
        
        # 构建完整的登录URL
        login_url = f"{frontend_url}/login?token={token}"
        
        # 添加menu参数
        if menu:
            login_url += f"&menu={menu}"
        
        logger.info(f"Login link generated for user: {username}")
        
        return {
            "token": token,
            "login_url": login_url,
            "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S"),
            "expires_in_seconds": expires_minutes * 60,
            "menu": menu
        }
        
    except Exception as e:
        logger.error(f"Generate login link error: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成登录链接失败"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/legacy-login-redirect")
async def legacy_login_redirect(
    username: str,
    password: str,
    menu: Optional[str] = None
):
    """
    传统登录URL重定向服务（临时方案）
    
    将传统的username/password URL自动转换为安全的token URL并重定向
    
    使用场景：
    其他平台暂时无法修改代码，可以使用此接口作为过渡方案
    
    旧方式（其他平台原来的代码）：
    跳转到: http://10.61.241.38:9000/login?username=admin&password=123456&menu=server
    
    新方式（只需修改URL路径）：
    跳转到: http://10.61.241.38:8000/api/user/legacy-login-redirect?username=admin&password=123456&menu=server
    
    工作流程：
    1. 其他平台跳转到此接口（带username/password）
    2. 此接口验证用户，生成token
    3. 返回302重定向到: /login?token=xxx&menu=xxx
    4. 浏览器自动跳转（地址栏显示安全URL）
    
    注意：
    - 虽然浏览器最终显示安全URL，但服务端仍接收明文密码
    - 建议作为临时方案，长期应使用generate-login-link接口
    
    参数:
    - username: 用户名
    - password: 密码
    - menu: 菜单参数（可选）
    """
    from fastapi.responses import RedirectResponse
    
    conn = None
    cursor = None
    try:
        logger.info(f"Legacy login redirect request for user: {username}")
        
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 验证用户名和密码
        cursor.execute(
            "SELECT id, username, password, role FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            logger.warning(f"Legacy redirect failed: User not found - {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 验证密码
        if not verify_password(password, user[2]):
            logger.warning(f"Legacy redirect failed: Invalid password for user - {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 生成token
        token = generate_login_token(username, password, expires_minutes=5)
        
        # 构建重定向URL（相对路径，会重定向到前端）
        redirect_url = f"/login?token={token}"
        
        # 添加menu参数
        if menu:
            redirect_url += f"&menu={menu}"
        
        logger.info(f"Redirecting to token-based login for user: {username}")
        logger.info(f"Redirect URL: {redirect_url}")
        
        # 返回302重定向
        return RedirectResponse(
            url=redirect_url,
            status_code=302
        )
        
    except Exception as e:
        logger.error(f"Legacy login redirect error: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重定向失败"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
