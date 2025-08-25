import random
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional
import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime, timedelta
import logging
from config import DB_CONFIG
from fastapi.responses import JSONResponse
from functools import lru_cache

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 添加节点详情的响应模型
class NodeDetail(BaseModel):
    id: str
    ip: str
    longitude: float
    latitude: float
    status: str
    last_active: str
    botnet_type: str

# 缓存装饰器，缓存1分钟
@lru_cache(maxsize=32)
def get_cached_node_count(botnet_type: str) -> int:
    """获取节点总数的缓存函数"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        table_name = f"botnet_nodes_{botnet_type}"
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        return count
    except Exception as e:
        logger.error(f"Error getting node count: {e}")
        return 0
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.get("/node-details")
async def get_node_details(
    botnet_type: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=100, le=100000),
    status: Optional[str] = None,
    country: Optional[str] = None
):
    """获取僵尸网络节点的详细信息，支持分页和过滤"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 检查表是否存在
        table_name = f"botnet_nodes_{botnet_type}"
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], table_name))
        
        if cursor.fetchone()['count'] == 0:
            raise HTTPException(status_code=404, detail=f"Table for botnet type {botnet_type} not found")
        
        # 构建基础查询（不使用SQL_CALC_FOUND_ROWS）
        base_query = f"""
            SELECT 
                COALESCE(CONCAT(id, ''), '') as id,
                COALESCE(ip, '') as ip,
                COALESCE(longitude, 0) as longitude,
                COALESCE(latitude, 0) as latitude,
                CASE 
                    WHEN status = 'active' THEN 'active'
                    ELSE 'inactive'
                END as status,
                COALESCE(last_active, NOW()) as last_active,
                %s as botnet_type,
                COALESCE(country, '') as country,
                COALESCE(province, '') as province,
                COALESCE(city, '') as city
            FROM {table_name}
            WHERE longitude IS NOT NULL
            AND latitude IS NOT NULL
        """
        
        # 添加过滤条件
        conditions = []
        params = [botnet_type]
        
        if status:
            if status == 'active':
                conditions.append("status = 'active'")
            elif status == 'inactive':
                conditions.append("status = 'inactive'")
                
        if country:
            conditions.append("country = %s")
            params.append(country)
            
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
            
        # 获取总记录数（使用COUNT查询）
        count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as t"
        cursor.execute(count_query, tuple(params))
        total_count = cursor.fetchone()['total']
            
        # 添加分页
        base_query += " LIMIT %s OFFSET %s"
        params.extend([page_size, (page - 1) * page_size])
        
        # 执行主查询
        cursor.execute(base_query, tuple(params))
        nodes = list(cursor.fetchall())
        
        # 处理datetime格式
        for node in nodes:
            if isinstance(node['last_active'], datetime):
                node['last_active'] = node['last_active'].strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取在线/离线节点数量
        status_query = f"""
            SELECT 
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count,
                COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_count
            FROM {table_name}
        """
        cursor.execute(status_query)
        status_counts = cursor.fetchone()
        
        # 获取国家分布（只取前10个最多的国家）
        cursor.execute(f"""
            SELECT COALESCE(country, '未知') as country, COUNT(*) as count
            FROM {table_name}
            GROUP BY country
            ORDER BY count DESC
            LIMIT 10
        """)
        country_distribution = {row['country']: row['count'] for row in cursor.fetchall()}
        
        response_data = {
            "status": "success",
            "message": f"Retrieved {len(nodes)} nodes for {botnet_type}",
            "data": {
                "nodes": nodes,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "total_count": total_count
                },
                "statistics": {
                    "active_nodes": status_counts['active_count'],
                    "inactive_nodes": status_counts['inactive_count'],
                    "country_distribution": country_distribution
                }
            }
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Error fetching node details: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.get("/node-stats/{botnet_type}")
async def get_node_stats(botnet_type: str):
    """获取节点统计信息的专用接口"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 检查表是否存在
        table_name = f"botnet_nodes_{botnet_type}"
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], table_name))
        
        if cursor.fetchone()['count'] == 0:
            raise HTTPException(status_code=404, detail=f"Table for botnet type {botnet_type} not found")
        
        # 使用缓存获取总节点数
        total_count = get_cached_node_count(botnet_type)
        
        # 获取活跃/非活跃节点数量
        cursor.execute(f"""
            SELECT 
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count,
                COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_count
            FROM {table_name}
        """)
        status_counts = cursor.fetchone()
        
        # 获取国家分布
        cursor.execute(f"""
            SELECT 
                COALESCE(country, '未知') as country,
                COUNT(*) as count,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count
            FROM {table_name}
            GROUP BY country
            ORDER BY count DESC
            LIMIT 10
        """)
        country_stats = cursor.fetchall()
        
        response_data = {
            "status": "success",
            "data": {
                "total_nodes": total_count,
                "active_nodes": status_counts['active_count'],
                "inactive_nodes": status_counts['inactive_count'],
                "country_distribution": {
                    row['country']: {
                        'total': row['count'],
                        'active': row['active_count']
                    } for row in country_stats
                }
            }
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Error fetching node stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

