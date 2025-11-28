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
        
        # 构建基础查询：使用子查询确保每个IP只返回最新的一条记录
        # 注意：使用 updated_at（最新响应时间）替代已废弃的 last_active 字段
        base_query = f"""
            SELECT 
                COALESCE(CONCAT(t.id, ''), '') as id,
                COALESCE(t.ip, '') as ip,
                COALESCE(t.longitude, 0) as longitude,
                COALESCE(t.latitude, 0) as latitude,
                CASE 
                    WHEN t.status = 'active' THEN 'active'
                    ELSE 'inactive'
                END as status,
                COALESCE(t.updated_at, t.created_time, NOW()) as last_active,
                %s as botnet_type,
                COALESCE(t.country, '') as country,
                COALESCE(t.province, '') as province,
                COALESCE(t.city, '') as city
            FROM (
                SELECT *,
                    ROW_NUMBER() OVER (PARTITION BY ip ORDER BY updated_at DESC, id DESC) as rn
                FROM {table_name}
                WHERE longitude IS NOT NULL
                AND latitude IS NOT NULL
            ) t
            WHERE t.rn = 1
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
            
        # 获取总记录数（已经在子查询中去重）
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
        
        # 获取在线/离线节点数量（按 IP 去重）
        status_query = f"""
            SELECT 
                COUNT(DISTINCT CASE WHEN status = 'active' THEN ip END) as active_count,
                COUNT(DISTINCT CASE WHEN status = 'inactive' THEN ip END) as inactive_count
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
    """
    获取节点统计信息的专用接口 - 从聚合表读取数据
    
    注意：此接口现在查询聚合表（china_botnet_xxx 和 global_botnet_xxx），
    与处置平台的数据源一致，确保两个平台显示的数据完全相同。
    数据更新频率：每5分钟（由聚合器定时更新）
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 检查聚合表是否存在
        china_table = f"china_botnet_{botnet_type}"
        global_table = f"global_botnet_{botnet_type}"
        
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name IN (%s, %s)
        """, (DB_CONFIG['database'], china_table, global_table))
        
        if cursor.fetchone()['count'] < 2:
            raise HTTPException(status_code=404, detail=f"Aggregation tables for {botnet_type} not found")
        
        # 从中国表获取省份分布
        cursor.execute(f"""
            SELECT 
                province,
                SUM(infected_num) as count
            FROM {china_table}
            GROUP BY province
        """)
        china_stats = cursor.fetchall()
        china_total = int(sum(row['count'] for row in china_stats))
        
        # 从全球表获取国家分布
        cursor.execute(f"""
            SELECT 
                country,
                SUM(infected_num) as count
            FROM {global_table}
            GROUP BY country
            ORDER BY count DESC
        """)
        global_stats = cursor.fetchall()
        
        # 构建国家分布（中国 + 其他国家）
        country_distribution = {}
        
        # 添加中国数据
        if china_total > 0:
            country_distribution['中国'] = china_total
        
        # 添加其他国家数据
        for row in global_stats:
            country = row['country']
            if country and country != '中国':  # 避免重复
                country_distribution[country] = int(row['count'])  # 转换为 int
        
        # 计算总节点数
        global_total = int(sum(row['count'] for row in global_stats))
        total_nodes = china_total + sum(
            int(row['count']) for row in global_stats 
            if row['country'] != '中国'
        )
        
        # 注意：聚合表中没有状态信息（active/inactive）
        # 因为聚合时使用的是最新状态，默认都是 active
        # 如果需要状态分布，需要在聚合器中添加相关逻辑
        
        response_data = {
            "status": "success",
            "data": {
                "total_nodes": total_nodes,
                "active_nodes": total_nodes,  # 聚合表中的数据默认为活跃
                "inactive_nodes": 0,           # 聚合表中没有非活跃节点统计
                "country_distribution": country_distribution,
                "status_distribution": {
                    "active": total_nodes,
                    "inactive": 0
                },
                "data_source": "aggregated",  # 标识数据来源
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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

