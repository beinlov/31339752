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


@router.get("/active-botnet-communications")
async def get_active_botnet_communications(botnet_type: str):
    """获取活跃僵尸节点通信记录 - 从指定的botnet_communications_*表查询"""
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)

        safe_botnet_type = (botnet_type or '').strip().lower()
        if not safe_botnet_type:
            raise HTTPException(status_code=400, detail="botnet_type is required")

        table_name = f"botnet_communications_{safe_botnet_type}"

        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
            """,
            (DB_CONFIG['database'], table_name),
        )

        if cursor.fetchone()['count'] == 0:
            raise HTTPException(status_code=404, detail=f"Communication table for {safe_botnet_type} not found")

        cursor.execute(
            f"""
            SELECT
                DATE_FORMAT(communication_time, '%Y-%m-%d %H:%i:%s') as time,
                ip,
                COALESCE(country, '未知') as country
            FROM {table_name}
            ORDER BY communication_time DESC
            LIMIT 200
            """
        )

        return cursor.fetchall()

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/node-details")
async def get_node_details(
    botnet_type: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=10, le=100000),
    status: Optional[str] = None,
    country: Optional[str] = None,
    keyword: Optional[str] = None,
    ip_start: Optional[str] = None,
    ip_end: Optional[str] = None,
    time_start: Optional[str] = None,
    time_end: Optional[str] = None,
    ids_only: bool = False
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
        
        # 构建基础查询：使用新字段名（first_seen, last_seen）
        # 但在SELECT中映射为旧字段名（active_time, last_active）以保持API兼容性
        base_query = f"""
            SELECT 
                COALESCE(CONCAT(n.id, ''), '') as id,
                COALESCE(n.ip, '') as ip,
                COALESCE(n.longitude, 0) as longitude,
                COALESCE(n.latitude, 0) as latitude,
                CASE 
                    WHEN n.status = 'active' THEN 'active'
                    ELSE 'inactive'
                END as status,
                COALESCE(n.last_seen, n.created_time, NOW()) as last_active,
                COALESCE(n.first_seen, n.created_time, NOW()) as active_time,
                %s as botnet_type,
                COALESCE(n.country, '') as country,
                COALESCE(n.province, '') as province,
                COALESCE(n.city, '') as city
            FROM {table_name} n
            WHERE n.longitude IS NOT NULL
            AND n.latitude IS NOT NULL
        """
        
        # 添加过滤条件
        condition_params = []
        
        # 构建WHERE条件
        where_conditions = ["n.longitude IS NOT NULL", "n.latitude IS NOT NULL"]
        
        if status:
            if status == 'active':
                where_conditions.append("n.status = 'active'")
            elif status == 'inactive':
                where_conditions.append("n.status = 'inactive'")
                
        if country:
            where_conditions.append("n.country = %s")
            condition_params.append(country)

        if keyword:
            kw = keyword.strip()
            if kw:
                where_conditions.append("(n.country LIKE %s OR n.province LIKE %s OR n.city LIKE %s)")
                like_kw = f"%{kw}%"
                condition_params.extend([like_kw, like_kw, like_kw])
        
        if ip_start and ip_end:
            where_conditions.append("INET_ATON(n.ip) BETWEEN INET_ATON(%s) AND INET_ATON(%s)")
            condition_params.append(ip_start)
            condition_params.append(ip_end)
        elif ip_start:
            where_conditions.append("INET_ATON(n.ip) >= INET_ATON(%s)")
            condition_params.append(ip_start)
        elif ip_end:
            where_conditions.append("INET_ATON(n.ip) <= INET_ATON(%s)")
            condition_params.append(ip_end)
        
        if time_start:
            where_conditions.append("n.last_seen >= %s")
            condition_params.append(time_start)
        
        if time_end:
            where_conditions.append("n.last_seen <= %s")
            condition_params.append(time_end)
        
        where_sql = " AND ".join(where_conditions)
        
        # 优化后的count查询（直接计数，不使用子查询）
        count_query = f"""
            SELECT COUNT(*) as total 
            FROM {table_name} n
            WHERE {where_sql}
        """
        cursor.execute(count_query, tuple(condition_params))
        total_count = cursor.fetchone()['total']
        
        base_query += f" AND {' AND '.join(where_conditions[2:])}" if len(where_conditions) > 2 else ""
        base_params = [botnet_type, *condition_params]
        
        if ids_only:
            ids_query = f"""
                SELECT COALESCE(CONCAT(n.id, ''), '') as id
                FROM {table_name} n
                WHERE {where_sql}
            """
            cursor.execute(ids_query, tuple(condition_params))
            node_ids = [row['id'] for row in cursor.fetchall()]
            
            response_data = {
                "status": "success",
                "data": {
                    "node_ids": node_ids,
                    "total_count": total_count
                }
            }
            
            return JSONResponse(content=response_data)
            
        # 添加分页
        base_query = f"""
            SELECT 
                COALESCE(CONCAT(n.id, ''), '') as id,
                COALESCE(n.ip, '') as ip,
                COALESCE(n.longitude, 0) as longitude,
                COALESCE(n.latitude, 0) as latitude,
                CASE 
                    WHEN n.status = 'active' THEN 'active'
                    ELSE 'inactive'
                END as status,
                COALESCE(n.last_seen, n.created_time, NOW()) as last_active,
                COALESCE(n.first_seen, n.created_time, NOW()) as active_time,
                %s as botnet_type,
                COALESCE(n.country, '') as country,
                COALESCE(n.province, '') as province,
                COALESCE(n.city, '') as city
            FROM {table_name} n
            WHERE {where_sql}
        """
        base_query += " LIMIT %s OFFSET %s"
        base_params.extend([page_size, (page - 1) * page_size])
        
        # 执行主查询
        cursor.execute(base_query, tuple(base_params))
        nodes = list(cursor.fetchall())
        
        # 处理datetime格式
        for node in nodes:
            if isinstance(node['last_active'], datetime):
                node['last_active'] = node['last_active'].strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(node.get('active_time'), datetime):
                node['active_time'] = node['active_time'].strftime('%Y-%m-%d %H:%M:%S')
        
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
            ORDER BY count DESC
        """)
        china_stats = cursor.fetchall()
        china_total = int(sum(row['count'] for row in china_stats))
        
        # 构建省份分布
        province_distribution = {}
        for row in china_stats:
            province = row['province']
            if province:
                province_distribution[province] = int(row['count'])
        
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
                "province_distribution": province_distribution,  # 添加省份分布数据
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


@router.get("/node-communications")
async def get_node_communications(
    botnet_type: str,
    ip: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=10, le=1000)
):
    """
    获取节点的通信记录详情
    
    Args:
        botnet_type: 僵尸网络类型
        ip: 过滤特定IP（可选）
        start_time: 开始时间（可选，格式：YYYY-MM-DD HH:MM:SS）
        end_time: 结束时间（可选，格式：YYYY-MM-DD HH:MM:SS）
        page: 页码
        page_size: 每页数量
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        table_name = f"botnet_communications_{botnet_type}"
        
        # 检查表是否存在
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], table_name))
        
        if cursor.fetchone()['count'] == 0:
            raise HTTPException(
                status_code=404, 
                detail=f"Communication table for {botnet_type} not found"
            )
        
        # 构建查询条件
        where_clauses = []
        params = []
        
        if ip:
            where_clauses.append("ip = %s")
            params.append(ip)
        
        if start_time:
            where_clauses.append("communication_time >= %s")
            params.append(start_time)
        
        if end_time:
            where_clauses.append("communication_time <= %s")
            params.append(end_time)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) as total FROM {table_name} WHERE {where_sql}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']
        
        # 查询数据
        offset = (page - 1) * page_size
        data_sql = f"""
            SELECT 
                id,
                node_id,
                ip,
                communication_time,
                received_at,
                country,
                province,
                city,
                longitude,
                latitude,
                isp,
                asn,
                event_type,
                status,
                is_china
            FROM {table_name}
            WHERE {where_sql}
            ORDER BY communication_time DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_sql, params + [page_size, offset])
        communications = cursor.fetchall()
        
        # 格式化时间字段
        for comm in communications:
            if comm['communication_time']:
                comm['communication_time'] = comm['communication_time'].strftime('%Y-%m-%d %H:%M:%S')
            if comm['received_at']:
                comm['received_at'] = comm['received_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        response_data = {
            "status": "success",
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "communications": communications
            }
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching communications: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@router.get("/node-communication-stats")
async def get_node_communication_stats(
    botnet_type: str,
    ip: str
):
    """
    获取单个节点的通信统计信息
    
    Returns:
        节点通信统计数据
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        table_name = f"botnet_communications_{botnet_type}"
        
        # 基本统计
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_communications,
                MIN(communication_time) as first_seen,
                MAX(communication_time) as last_seen
            FROM {table_name}
            WHERE ip = %s
        """, (ip,))
        
        stats = cursor.fetchone()
        
        if stats['total_communications'] == 0:
            raise HTTPException(status_code=404, detail=f"No communications found for IP {ip}")
        
        # 按天统计
        cursor.execute(f"""
            SELECT 
                DATE(communication_time) as date,
                COUNT(*) as count
            FROM {table_name}
            WHERE ip = %s
            GROUP BY DATE(communication_time)
            ORDER BY date
        """, (ip,))
        
        timeline = cursor.fetchall()
        
        # 格式化时间
        if stats['first_seen']:
            stats['first_seen'] = stats['first_seen'].strftime('%Y-%m-%d %H:%M:%S')
        if stats['last_seen']:
            stats['last_seen'] = stats['last_seen'].strftime('%Y-%m-%d %H:%M:%S')
        
        for item in timeline:
            if item['date']:
                item['date'] = item['date'].strftime('%Y-%m-%d')
        
        response_data = {
            "status": "success",
            "data": {
                "ip": ip,
                "total_communications": stats['total_communications'],
                "first_seen": stats['first_seen'],
                "last_seen": stats['last_seen'],
                "communication_timeline": timeline
            }
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching communication stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
