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
from config import DB_CONFIG

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# JWT配置
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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
async def create_user(user: UserCreate):
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
async def update_user(user_id: int, user: UserUpdate):
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
async def delete_user(user_id: int):
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
        
        # 获取在线用户数
        cursor.execute("SELECT COUNT(*) FROM users WHERE status = '在线'")
        online_users = cursor.fetchone()[0]
        
        return {
            "totalUsers": total_users,
            "adminUsers": role_counts.get('管理员', 0),
            "operatorUsers": role_counts.get('操作员', 0),
            "viewerUsers": role_counts.get('访客', 0),
            "onlineUsers": online_users
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
                    WHEN command LIKE '%ddos%' THEN 'DDoS攻击'
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
