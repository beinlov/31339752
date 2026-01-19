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
async def get_node_count_history(
    botnet_type: str, 
    days: int = 7
):
    """
    从botnet_timeset表获取指定僵尸网络的每日节点数量历史记录
    
    Args:
        botnet_type: 僵尸网络类型（如 mozi, ramnit 等）
        days: 返回最近多少天的数据（默认7天）
    
    Returns:
        按日期排序的节点数量历史记录列表
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 检查timeset表是否存在
        timeset_table = f"botnet_timeset_{botnet_type}"
        cursor.execute(f"""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = %s
        """, (timeset_table,))
        
        if cursor.fetchone()['count'] == 0:
            raise HTTPException(status_code=404, detail=f"Botnet type '{botnet_type}' not found")
        
        # 从timeset表查询最近N天的数据
        query = f"""
            SELECT 
                DATE_FORMAT(date, '%%m-%%d') as date_str,
                global_count,
                china_count
            FROM {timeset_table}
            WHERE date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY date ASC
        """
        cursor.execute(query, (days,))
        rows = cursor.fetchall()
        
        # 构建返回数据
        result = []
        for row in rows:
            result.append({
                "timestamp": row['date_str'],
                "china_count": row['china_count'],
                "global_count": row['global_count']
            })
        
        logger.info(f"Retrieved {len(result)} daily history points for {botnet_type} (last {days} days)")
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
