from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime, timedelta
import logging

from config import DB_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


class NodeCountHistory(BaseModel):
    timestamp: str
    china_count: int
    global_count: int


@router.get("/node-count-history/{botnet_type}", response_model=List[NodeCountHistory])
async def get_node_count_history(botnet_type: str, hours: int = 2):
    """
    获取指定僵尸网络的节点数量历史记录（5分钟间隔）
    
    Args:
        botnet_type: 僵尸网络类型（如 mozi, ramnit 等）
        hours: 返回最近多少小时的数据（默认2小时）
    
    Returns:
        按时间排序的节点数量历史记录列表
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 检查表是否存在
        node_table = f"botnet_nodes_{botnet_type}"
        cursor.execute(f"""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = %s
        """, (node_table,))
        
        if cursor.fetchone()['count'] == 0:
            raise HTTPException(status_code=404, detail=f"Botnet type '{botnet_type}' not found")
        
        # 生成最近N小时的5分钟时间点
        now = datetime.now()
        time_points = []
        current_time = now.replace(second=0, microsecond=0)
        # 向下取整到5分钟
        current_time = current_time.replace(minute=(current_time.minute // 5) * 5)
        
        # 生成时间点列表（最近hours小时，每5分钟一个点）
        num_points = (hours * 60) // 5
        for i in range(num_points, -1, -1):
            time_point = current_time - timedelta(minutes=i * 5)
            time_points.append(time_point)
        
        result = []
        
        for time_point in time_points:
            # 查询该时间点的中国节点总数
            china_query = f"""
                SELECT COUNT(*) as count
                FROM {node_table}
                WHERE country = '中国'
                AND updated_at <= %s
            """
            cursor.execute(china_query, (time_point,))
            china_count = cursor.fetchone()['count']
            
            # 查询该时间点的全球节点总数
            global_query = f"""
                SELECT COUNT(*) as count
                FROM {node_table}
                WHERE updated_at <= %s
            """
            cursor.execute(global_query, (time_point,))
            global_count = cursor.fetchone()['count']
            
            result.append({
                "timestamp": time_point.strftime('%H:%M'),
                "china_count": int(china_count),
                "global_count": int(global_count)
            })
        
        logger.info(f"Retrieved {len(result)} history points for {botnet_type}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching node count history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
