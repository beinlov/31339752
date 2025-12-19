import logging
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import Dict, List, Optional
import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime
from config import DB_CONFIG
from fastapi.responses import JSONResponse

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 服务器数据模型
class ServerModel(BaseModel):
    id: Optional[int] = None
    location: str
    ip: str
    domain: str
    status: str
    os: str
    botnet_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# 创建服务器请求模型
class CreateServerRequest(BaseModel):
    location: str
    ip: str
    domain: str
    status: str
    os: str
    botnet_name: Optional[str] = None

# 更新服务器请求模型
class UpdateServerRequest(BaseModel):
    location: Optional[str] = None
    ip: Optional[str] = None
    domain: Optional[str] = None
    status: Optional[str] = None
    os: Optional[str] = None
    botnet_name: Optional[str] = None

# 初始化数据库表
def init_server_table():
    """确保服务器管理表存在"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], "Server_Management"))
        
        if cursor.fetchone()[0] == 0:
            # 创建表
            cursor.execute("""
                CREATE TABLE Server_Management (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    location VARCHAR(255) NOT NULL,
                    ip VARCHAR(50) NOT NULL,
                    domain VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    os VARCHAR(100) NOT NULL,
                    Botnet_Name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info("Server_Management table created successfully")
        
    except Exception as e:
        logger.error(f"Error initializing server table: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 确保表存在
init_server_table()

@router.get("/servers")
async def get_servers(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """获取所有服务器列表，支持分页"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 获取总记录数
        cursor.execute("SELECT COUNT(*) as total FROM Server_Management")
        total_count = cursor.fetchone()['total']
        
        # 获取分页数据
        cursor.execute("""
            SELECT * FROM Server_Management
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """, (page_size, (page - 1) * page_size))
        
        servers = list(cursor.fetchall())
        
        # 准备节点总数缓存，减少重复查询
        node_counts: Dict[str, Optional[int]] = {}

        # 处理datetime格式和字段名转换
        for server in servers:
            if isinstance(server['created_at'], datetime):
                server['created_at'] = server['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(server['updated_at'], datetime):
                server['updated_at'] = server['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            # 将Botnet_Name转换为botnet_name以匹配前端
            if 'Botnet_Name' in server:
                server['botnet_name'] = server.pop('Botnet_Name')
            
            botnet_name = server.get('botnet_name')
            if botnet_name:
                if botnet_name not in node_counts:
                    table_name = f"botnet_nodes_{botnet_name}"
                    try:
                        cursor.execute(f"SELECT COUNT(*) as total FROM `{table_name}`")
                        node_counts[botnet_name] = cursor.fetchone()['total']
                    except Exception as e:
                        logger.warning(f"Failed to fetch node count for {table_name}: {e}")
                        node_counts[botnet_name] = None
                server['node_count'] = node_counts.get(botnet_name)
            else:
                server['node_count'] = None
        
        response_data = {
            "status": "success",
            "message": f"Retrieved {len(servers)} servers",
            "data": {
                "servers": servers,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "total_count": total_count
                }
            }
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Error fetching servers: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.get("/servers/{server_id}")
async def get_server(server_id: int):
    """获取单个服务器详情"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        cursor.execute("SELECT * FROM Server_Management WHERE id = %s", (server_id,))
        server = cursor.fetchone()
        
        if not server:
            raise HTTPException(status_code=404, detail=f"Server with ID {server_id} not found")
        
        # 处理datetime格式和字段名转换
        if isinstance(server['created_at'], datetime):
            server['created_at'] = server['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(server['updated_at'], datetime):
            server['updated_at'] = server['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        # 将Botnet_Name转换为botnet_name以匹配前端
        if 'Botnet_Name' in server:
            server['botnet_name'] = server.pop('Botnet_Name')
        
        botnet_name = server.get('botnet_name')
        if botnet_name:
            table_name = f"botnet_nodes_{botnet_name}"
            try:
                cursor.execute(f"SELECT COUNT(*) as total FROM `{table_name}`")
                server['node_count'] = cursor.fetchone()['total']
            except Exception as e:
                logger.warning(f"Failed to fetch node count for {table_name}: {e}")
                server['node_count'] = None
        else:
            server['node_count'] = None
        
        return {
            "status": "success",
            "data": server
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching server: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.post("/servers")
async def create_server(server: CreateServerRequest):
    """创建新服务器"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO Server_Management (location, ip, domain, status, os, Botnet_Name)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (server.location, server.ip, server.domain, server.status, server.os, server.botnet_name))
        
        conn.commit()
        server_id = cursor.lastrowid
        
        return {
            "status": "success",
            "message": "Server created successfully",
            "data": {
                "id": server_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating server: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.put("/servers/{server_id}")
async def update_server(server_id: int, server_update: UpdateServerRequest):
    """更新服务器信息"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查服务器是否存在
        cursor.execute("SELECT COUNT(*) FROM Server_Management WHERE id = %s", (server_id,))
        if cursor.fetchone()[0] == 0:
            raise HTTPException(status_code=404, detail=f"Server with ID {server_id} not found")
        
        # 构建更新语句
        update_fields = []
        params = []
        
        if server_update.location is not None:
            update_fields.append("location = %s")
            params.append(server_update.location)
            
        if server_update.ip is not None:
            update_fields.append("ip = %s")
            params.append(server_update.ip)
            
        if server_update.domain is not None:
            update_fields.append("domain = %s")
            params.append(server_update.domain)
            
        if server_update.status is not None:
            update_fields.append("status = %s")
            params.append(server_update.status)
            
        if server_update.os is not None:
            update_fields.append("os = %s")
            params.append(server_update.os)
            
        if server_update.botnet_name is not None:
            update_fields.append("Botnet_Name = %s")
            params.append(server_update.botnet_name)
        
        if not update_fields:
            return {
                "status": "success",
                "message": "No fields to update"
            }
        
        # 执行更新
        params.append(server_id)
        cursor.execute(f"""
            UPDATE Server_Management
            SET {", ".join(update_fields)}
            WHERE id = %s
        """, tuple(params))
        
        conn.commit()
        
        return {
            "status": "success",
            "message": "Server updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating server: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.delete("/servers/{server_id}")
async def delete_server(server_id: int):
    """删除服务器"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查服务器是否存在
        cursor.execute("SELECT COUNT(*) FROM Server_Management WHERE id = %s", (server_id,))
        if cursor.fetchone()[0] == 0:
            raise HTTPException(status_code=404, detail=f"Server with ID {server_id} not found")
        
        # 执行删除
        cursor.execute("DELETE FROM Server_Management WHERE id = %s", (server_id,))
        conn.commit()
        
        return {
            "status": "success",
            "message": "Server deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting server: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
