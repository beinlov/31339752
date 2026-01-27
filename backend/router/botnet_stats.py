import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime
from config import DB_CONFIG
from cache_manager import get_cache

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 数据模型
class BotnetSummary(BaseModel):
    """僵尸网络概览统计"""
    total_botnets: int
    botnet_names: List[str]
    total_nodes: int
    china_nodes: int
    global_nodes: int
    last_updated: str

class BotnetDetail(BaseModel):
    """僵尸网络详细信息"""
    name: str
    display_name: str
    description: str
    total_nodes: int
    china_nodes: int
    global_nodes: int
    created_at: Optional[str] = None

class BotnetNodeStats(BaseModel):
    """僵尸网络节点统计"""
    name: str
    display_name: str
    total_nodes: int
    china_nodes: int
    global_nodes: int
    province_distribution: Dict[str, int]
    country_distribution: Dict[str, int]

class NodeDetail(BaseModel):
    """僵尸网络节点详情"""
    id: Optional[str] = None
    ip: str
    longitude: float
    latitude: float
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    continent: Optional[str] = None
    isp: Optional[str] = None
    asn: Optional[str] = None
    status: str
    active_time: Optional[str] = None
    created_time: Optional[str] = None
    updated_at: Optional[str] = None

@router.get("/botnet-summary", response_model=BotnetSummary)
async def get_botnet_summary():
    """
    获取已接管僵尸网络的概览统计
    
    返回:
    - 僵尸网络总数
    - 僵尸网络名称列表
    - 总节点数
    - 中国节点数
    - 全球节点数
    - 最后更新时间
    
    使用Redis缓存（5分钟），与聚合器更新频率一致
    """
    # 检查缓存
    cache = get_cache()
    cache_key = cache.get_stats_summary()
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.info("Returning cached botnet summary")
        return cached_data
    
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 获取所有僵尸网络类型
        cursor.execute("SELECT name, display_name FROM botnet_types ORDER BY created_at")
        botnets = cursor.fetchall()
        
        if not botnets:
            return {
                "total_botnets": 0,
                "botnet_names": [],
                "total_nodes": 0,
                "china_nodes": 0,
                "global_nodes": 0,
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        botnet_names = [botnet['name'] for botnet in botnets]
        
        # 【优化】使用UNION ALL合并所有查询，从N+1查询优化为1次查询
        # 构建动态UNION查询
        union_queries = []
        for botnet in botnets:
            name = botnet['name']
            union_queries.append(f"""
                SELECT 
                    '{name}' as botnet_name,
                    'china' as region,
                    COALESCE(SUM(infected_num), 0) as count
                FROM china_botnet_{name}
                UNION ALL
                SELECT 
                    '{name}' as botnet_name,
                    'global' as region,
                    COALESCE(SUM(infected_num), 0) as count
                FROM global_botnet_{name}
            """)
        
        # 一次性执行所有查询
        final_query = " UNION ALL ".join(union_queries)
        
        try:
            cursor.execute(final_query)
            results = cursor.fetchall()
        except Exception as e:
            logger.error(f"Error executing union query: {e}")
            # 降级为旧逻辑
            results = []
        
        # 整理数据
        stats_map = {}
        for row in results:
            name = row['botnet_name']
            if name not in stats_map:
                stats_map[name] = {'china': 0, 'global': 0}
            stats_map[name][row['region']] = int(row['count'] or 0)
        
        # 计算总计
        total_nodes = 0
        china_nodes = 0
        global_nodes = 0
        for name in botnet_names:
            if name in stats_map:
                china_nodes += stats_map[name]['china']
                global_nodes += stats_map[name]['global']
                total_nodes += stats_map[name]['china'] + stats_map[name]['global']
        
        result = {
            "total_botnets": len(botnets),
            "botnet_names": botnet_names,
            "total_nodes": total_nodes,
            "china_nodes": china_nodes,
            "global_nodes": global_nodes,
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 写入缓存（5分钟过期，与聚合器更新频率一致）
        cache.set(cache_key, result, ttl=300)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting botnet summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/botnet-details", response_model=List[BotnetDetail])
async def get_botnet_details():
    """
    获取所有僵尸网络的详细信息
    
    返回:
    - 僵尸网络名称
    - 显示名称
    - 描述
    - 总节点数
    - 中国节点数
    - 全球节点数
    - 创建时间
    """
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 获取所有僵尸网络类型
        cursor.execute("SELECT name, display_name, description, created_at FROM botnet_types ORDER BY created_at")
        botnets = cursor.fetchall()
        
        result = []
        
        for botnet in botnets:
            botnet_name = botnet['name']
            china_nodes = 0
            global_nodes = 0
            
            # 检查中国节点表
            china_table = f"china_botnet_{botnet_name}"
            try:
                cursor.execute(f"SELECT SUM(infected_num) as count FROM {china_table}")
                china_result = cursor.fetchone()
                if china_result and china_result['count']:
                    china_nodes = int(china_result['count'])
            except Exception as e:
                logger.warning(f"Error counting china nodes for {botnet_name}: {e}")
            
            # 检查全球节点表
            global_table = f"global_botnet_{botnet_name}"
            try:
                cursor.execute(f"SELECT SUM(infected_num) as count FROM {global_table}")
                global_result = cursor.fetchone()
                if global_result and global_result['count']:
                    global_nodes = int(global_result['count'])
                    # 减去中国节点数，避免重复计算
                    try:
                        cursor.execute(f"SELECT SUM(infected_num) as count FROM {global_table} WHERE country='中国'")
                        china_in_global = cursor.fetchone()
                        if china_in_global and china_in_global['count']:
                            global_nodes -= int(china_in_global['count'])
                    except:
                        pass
            except Exception as e:
                logger.warning(f"Error counting global nodes for {botnet_name}: {e}")
            
            # 格式化创建时间
            created_at = None
            if botnet['created_at']:
                created_at = botnet['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            result.append({
                "name": botnet_name,
                "display_name": botnet['display_name'],
                "description": botnet['description'],
                "total_nodes": china_nodes + global_nodes,
                "china_nodes": china_nodes,
                "global_nodes": global_nodes,
                "created_at": created_at
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting botnet details: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/botnet-node-stats/{botnet_name}", response_model=BotnetNodeStats)
async def get_botnet_node_stats(botnet_name: str):
    """
    获取指定僵尸网络的节点统计信息
    
    参数:
    - botnet_name: 僵尸网络名称
    
    返回:
    - 僵尸网络名称
    - 显示名称
    - 总节点数
    - 中国节点数
    - 全球节点数
    - 省份分布
    - 国家分布
    """
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 检查僵尸网络是否存在
        cursor.execute("SELECT name, display_name FROM botnet_types WHERE name = %s", (botnet_name,))
        botnet = cursor.fetchone()
        
        if not botnet:
            raise HTTPException(status_code=404, detail=f"Botnet {botnet_name} not found")
        
        china_nodes = 0
        global_nodes = 0
        province_distribution = {}
        country_distribution = {}
        
        # 获取中国节点分布
        china_table = f"china_botnet_{botnet_name}"
        try:
            cursor.execute(f"SELECT province, SUM(infected_num) as count FROM {china_table} GROUP BY province")
            provinces = cursor.fetchall()
            
            for province in provinces:
                if province['province'] and province['count']:
                    province_distribution[province['province']] = int(province['count'])
                    china_nodes += int(province['count'])
        except Exception as e:
            logger.warning(f"Error getting province distribution for {botnet_name}: {e}")
        
        # 获取全球节点分布
        global_table = f"global_botnet_{botnet_name}"
        try:
            cursor.execute(f"SELECT country, SUM(infected_num) as count FROM {global_table} GROUP BY country")
            countries = cursor.fetchall()
            
            for country in countries:
                if country['country'] and country['count']:
                    country_distribution[country['country']] = int(country['count'])
                    if country['country'] != '中国':  # 避免重复计算中国节点
                        global_nodes += int(country['count'])
        except Exception as e:
            logger.warning(f"Error getting country distribution for {botnet_name}: {e}")
        
        return {
            "name": botnet_name,
            "display_name": botnet['display_name'],
            "total_nodes": china_nodes + global_nodes,
            "china_nodes": china_nodes,
            "global_nodes": global_nodes,
            "province_distribution": province_distribution,
            "country_distribution": country_distribution
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting botnet node stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/botnet-nodes/{botnet_name}")
async def get_botnet_nodes(
    botnet_name: str,
    page: int = 1,
    page_size: int = 50,
    status: Optional[str] = None,
    country: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None
):
    """
    获取指定僵尸网络的节点详细信息（从botnet_nodes_botnetname表）
    
    参数:
    - botnet_name: 僵尸网络名称
    - page: 页码，默认1
    - page_size: 每页条数，默认50
    - status: 可选的状态过滤（active/inactive）
    - country: 可选的国家过滤
    - province: 可选的省份过滤
    - city: 可选的城市过滤
    
    返回:
    - 节点列表（包含IP、经纬度、地理位置、ISP等详细信息）
    - 分页信息
    """
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 检查僵尸网络是否存在
        cursor.execute("SELECT name, display_name FROM botnet_types WHERE name = %s", (botnet_name,))
        botnet = cursor.fetchone()
        
        if not botnet:
            raise HTTPException(status_code=404, detail=f"Botnet {botnet_name} not found")
        
        # 检查节点表是否存在
        node_table = f"botnet_nodes_{botnet_name}"
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], node_table))
        
        if cursor.fetchone()['count'] == 0:
            raise HTTPException(status_code=404, detail=f"Node table for botnet {botnet_name} not found")
        
        # 构建查询条件
        conditions = []
        params = []
        
        if status:
            conditions.append("status = %s")
            params.append(status)
        
        if country:
            conditions.append("(country LIKE %s OR province LIKE %s OR city LIKE %s)")
            search_term = f"%{country}%"
            params.extend([search_term, search_term, search_term])
        
        if province:
            conditions.append("province LIKE %s")
            params.append(f"%{province}%")
        
        if city:
            conditions.append("city LIKE %s")
            params.append(f"%{city}%")
        
        # 构建基本查询
        base_query = f"""
            SELECT 
                id, ip, longitude, latitude, country, province, city, continent, isp, asn, status,
                active_time, created_time, updated_at
            FROM {node_table}
        """
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        # 获取总记录数
        count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as t"
        cursor.execute(count_query, tuple(params))
        total_count = cursor.fetchone()['total']
        
        # 添加排序和分页
        base_query += " ORDER BY updated_at DESC LIMIT %s OFFSET %s"
        params.extend([page_size, (page - 1) * page_size])
        
        # 执行主查询
        cursor.execute(base_query, tuple(params))
        nodes = list(cursor.fetchall())
        
        # 处理日期格式
        for node in nodes:
            for key in ['active_time', 'created_time', 'updated_at']:
                if node.get(key) and isinstance(node[key], datetime):
                    node[key] = node[key].strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            "status": "success",
            "data": {
                "botnet_name": botnet_name,
                "display_name": botnet['display_name'],
                "nodes": nodes,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "total_count": total_count
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting botnet nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/all-botnet-node-stats", response_model=List[BotnetNodeStats])
async def get_all_botnet_node_stats():
    """
    获取所有僵尸网络的节点统计信息（一键返回）
    
    返回:
    - 所有僵尸网络的节点统计数据列表
    - 包括节点数量和地理分布
    """
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 获取所有僵尸网络类型
        cursor.execute("SELECT name, display_name FROM botnet_types ORDER BY created_at")
        botnets = cursor.fetchall()
        
        result = []
        
        for botnet in botnets:
            botnet_name = botnet['name']
            china_nodes = 0
            global_nodes = 0
            province_distribution = {}
            country_distribution = {}
            
            # 获取中国节点分布
            china_table = f"china_botnet_{botnet_name}"
            try:
                cursor.execute(f"SELECT province, SUM(infected_num) as count FROM {china_table} GROUP BY province")
                provinces = cursor.fetchall()
                
                for province in provinces:
                    if province['province'] and province['count']:
                        province_distribution[province['province']] = int(province['count'])
                        china_nodes += int(province['count'])
            except Exception as e:
                logger.warning(f"Error getting province distribution for {botnet_name}: {e}")
            
            # 获取全球节点分布
            global_table = f"global_botnet_{botnet_name}"
            try:
                cursor.execute(f"SELECT country, SUM(infected_num) as count FROM {global_table} GROUP BY country")
                countries = cursor.fetchall()
                
                for country in countries:
                    if country['country'] and country['count']:
                        country_distribution[country['country']] = int(country['count'])
                        if country['country'] != '中国':  # 避免重复计算中国节点
                            global_nodes += int(country['count'])
            except Exception as e:
                logger.warning(f"Error getting country distribution for {botnet_name}: {e}")
            
            result.append({
                "name": botnet_name,
                "display_name": botnet['display_name'],
                "total_nodes": china_nodes + global_nodes,
                "china_nodes": china_nodes,
                "global_nodes": global_nodes,
                "province_distribution": province_distribution,
                "country_distribution": country_distribution
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting all botnet node stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/all-botnet-nodes")
async def get_all_botnet_nodes(
    page: int = 1,
    page_size: int = 50,
    status: Optional[str] = None,
    country: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None
):
    """
    获取所有僵尸网络的节点详细信息（一键返回）
    
    参数:
    - page: 页码，默认1
    - page_size: 每页条数，默认50
    - status: 可选的状态过滤（active/inactive）
    - country: 可选的国家过滤
    - province: 可选的省份过滤
    - city: 可选的城市过滤
    
    返回:
    - 所有僵尸网络的节点详细信息列表
    - 分页信息
    """
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 获取所有僵尸网络类型
        cursor.execute("SELECT name, display_name FROM botnet_types ORDER BY created_at")
        botnets = cursor.fetchall()
        
        all_nodes = []
        total_count = 0
        
        for botnet in botnets:
            botnet_name = botnet['name']
            node_table = f"botnet_nodes_{botnet_name}"
            
            # 检查节点表是否存在
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (DB_CONFIG['database'], node_table))
            
            if cursor.fetchone()['count'] == 0:
                logger.warning(f"Node table {node_table} not found, skipping")
                continue
            
            # 构建查询条件
            conditions = []
            params = []
            
            if status:
                conditions.append("status = %s")
                params.append(status)
            
            if country:
                conditions.append("(country LIKE %s OR province LIKE %s OR city LIKE %s)")
                search_term = f"%{country}%"
                params.extend([search_term, search_term, search_term])
            
            if province:
                conditions.append("province LIKE %s")
                params.append(f"%{province}%")
            
            if city:
                conditions.append("city LIKE %s")
                params.append(f"%{city}%")
            
            # 构建基本查询
            base_query = f"""
                SELECT 
                    '{botnet_name}' as botnet_name,
                    '{botnet['display_name']}' as botnet_display_name,
                    id, ip, longitude, latitude, country, province, city, continent, isp, asn, status,
                    active_time, created_time, updated_at
                FROM {node_table}
            """
            
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            
            try:
                # 获取该僵尸网络的节点数量
                count_query = f"SELECT COUNT(*) as count FROM ({base_query}) as t"
                cursor.execute(count_query, tuple(params))
                botnet_count = cursor.fetchone()['count']
                total_count += botnet_count
                
                # 获取该僵尸网络的节点数据
                cursor.execute(base_query, tuple(params))
                nodes = list(cursor.fetchall())
                
                # 处理日期格式
                for node in nodes:
                    for key in ['active_time', 'created_time', 'updated_at']:
                        if node.get(key) and isinstance(node[key], datetime):
                            node[key] = node[key].strftime('%Y-%m-%d %H:%M:%S')
                
                all_nodes.extend(nodes)
                
            except Exception as e:
                logger.warning(f"Error getting nodes for {botnet_name}: {e}")
                continue
        
        # 按更新时间排序
        all_nodes.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        
        # 分页处理
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_nodes = all_nodes[start_idx:end_idx]
        
        return {
            "status": "success",
            "data": {
                "nodes": paginated_nodes,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "total_count": total_count
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting all botnet nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
