#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
接管节点统计数据API接口
为其他业务方提供数据查询服务
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
import pymysql
from pymysql.cursors import DictCursor
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/takeover-stats", tags=["接管节点统计"])

def get_db_connection():
    """获取数据库连接"""
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")

@router.get("/latest", summary="获取最新的接管节点统计数据")
async def get_latest_stats():
    """
    获取最新的接管节点统计数据
    
    返回数据包括：
    - 已接管节点总数
    - 已接管国内节点总数  
    - 已接管国外节点总数
    - 近一个月接管节点总数
    - 近一个月接管国内节点数
    - 近一个月接管国外节点数
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        
        # 获取最新的统计数据
        cursor.execute("""
            SELECT 
                total_nodes,
                total_domestic_nodes,
                total_foreign_nodes,
                monthly_total_nodes,
                monthly_domestic_nodes,
                monthly_foreign_nodes,
                cleaned_total_nodes,
                cleaned_domestic_nodes,
                cleaned_foreign_nodes,
                monthly_cleaned_total_nodes,
                monthly_cleaned_domestic_nodes,
                monthly_cleaned_foreign_nodes,
                suppression_total_count,
                monthly_suppression_count,
                created_at,
                updated_at
            FROM takeover_stats 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="暂无统计数据")
        
        return {
            "status": "success",
            "data": {
                "total_stats": {
                    "total_nodes": result["total_nodes"],
                    "total_domestic_nodes": result["total_domestic_nodes"],
                    "total_foreign_nodes": result["total_foreign_nodes"]
                },
                "monthly_stats": {
                    "monthly_total_nodes": result["monthly_total_nodes"],
                    "monthly_domestic_nodes": result["monthly_domestic_nodes"],
                    "monthly_foreign_nodes": result["monthly_foreign_nodes"]
                },
                "cleaned_stats": {
                    "cleaned_total_nodes": result["cleaned_total_nodes"],
                    "cleaned_domestic_nodes": result["cleaned_domestic_nodes"],
                    "cleaned_foreign_nodes": result["cleaned_foreign_nodes"]
                },
                "monthly_cleaned_stats": {
                    "monthly_cleaned_total_nodes": result["monthly_cleaned_total_nodes"],
                    "monthly_cleaned_domestic_nodes": result["monthly_cleaned_domestic_nodes"],
                    "monthly_cleaned_foreign_nodes": result["monthly_cleaned_foreign_nodes"]
                },
                "suppression_stats": {
                    "suppression_total_count": result["suppression_total_count"],
                    "monthly_suppression_count": result["monthly_suppression_count"]
                },
                "timestamp": result["created_at"].isoformat(),
                "updated_at": result["updated_at"].isoformat()
            },
            "message": "获取最新统计数据成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取最新统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/detail", summary="获取按僵尸网络类型分类的详细统计数据")
async def get_detail_stats(
    botnet_type: Optional[str] = Query(None, description="指定僵尸网络类型，不指定则返回所有类型")
):
    """
    获取按僵尸网络类型分类的详细统计数据
    
    参数:
    - botnet_type: 可选，指定僵尸网络类型
    
    返回每个僵尸网络类型的详细统计数据
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        
        # 构建查询SQL
        base_sql = """
            SELECT 
                botnet_type,
                total_nodes,
                total_domestic_nodes,
                total_foreign_nodes,
                monthly_total_nodes,
                monthly_domestic_nodes,
                monthly_foreign_nodes,
                cleaned_total_nodes,
                cleaned_domestic_nodes,
                cleaned_foreign_nodes,
                monthly_cleaned_total_nodes,
                monthly_cleaned_domestic_nodes,
                monthly_cleaned_foreign_nodes,
                suppression_total_count,
                monthly_suppression_count,
                created_at,
                updated_at
            FROM takeover_stats_detail 
            WHERE created_at = (
                SELECT MAX(created_at) FROM takeover_stats_detail
            )
        """
        
        params = []
        if botnet_type:
            base_sql += " AND botnet_type = %s"
            params.append(botnet_type)
        
        base_sql += " ORDER BY total_nodes DESC"
        
        cursor.execute(base_sql, params)
        results = cursor.fetchall()
        
        if not results:
            raise HTTPException(status_code=404, detail="暂无详细统计数据")
        
        # 格式化返回数据
        detail_data = []
        for row in results:
            detail_data.append({
                "botnet_type": row["botnet_type"],
                "total_stats": {
                    "total_nodes": row["total_nodes"],
                    "total_domestic_nodes": row["total_domestic_nodes"],
                    "total_foreign_nodes": row["total_foreign_nodes"]
                },
                "monthly_stats": {
                    "monthly_total_nodes": row["monthly_total_nodes"],
                    "monthly_domestic_nodes": row["monthly_domestic_nodes"],
                    "monthly_foreign_nodes": row["monthly_foreign_nodes"]
                },
                "cleaned_stats": {
                    "cleaned_total_nodes": row["cleaned_total_nodes"],
                    "cleaned_domestic_nodes": row["cleaned_domestic_nodes"],
                    "cleaned_foreign_nodes": row["cleaned_foreign_nodes"]
                },
                "monthly_cleaned_stats": {
                    "monthly_cleaned_total_nodes": row["monthly_cleaned_total_nodes"],
                    "monthly_cleaned_domestic_nodes": row["monthly_cleaned_domestic_nodes"],
                    "monthly_cleaned_foreign_nodes": row["monthly_cleaned_foreign_nodes"]
                },
                "suppression_stats": {
                    "suppression_total_count": row["suppression_total_count"],
                    "monthly_suppression_count": row["monthly_suppression_count"]
                },
                "timestamp": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat()
            })
        
        return {
            "status": "success",
            "data": detail_data,
            "count": len(detail_data),
            "message": "获取详细统计数据成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取详细统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/history", summary="获取历史统计数据")
async def get_history_stats(
    hours: int = Query(24, ge=1, le=168, description="获取最近N小时的数据，最大168小时(7天)"),
    botnet_type: Optional[str] = Query(None, description="指定僵尸网络类型，不指定则返回总体数据")
):
    """
    获取历史统计数据
    
    参数:
    - hours: 获取最近N小时的数据，默认24小时，最大168小时(7天)
    - botnet_type: 可选，指定僵尸网络类型
    
    返回历史趋势数据，用于图表展示
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        
        # 计算时间范围
        start_time = datetime.now() - timedelta(hours=hours)
        
        if botnet_type:
            # 查询指定僵尸网络类型的历史数据
            cursor.execute("""
                SELECT 
                    botnet_type,
                    total_nodes,
                    total_domestic_nodes,
                    total_foreign_nodes,
                    monthly_total_nodes,
                    monthly_domestic_nodes,
                    monthly_foreign_nodes,
                    cleaned_total_nodes,
                    cleaned_domestic_nodes,
                    cleaned_foreign_nodes,
                    monthly_cleaned_total_nodes,
                    monthly_cleaned_domestic_nodes,
                    monthly_cleaned_foreign_nodes,
                    suppression_total_count,
                    monthly_suppression_count,
                    created_at
                FROM takeover_stats_detail 
                WHERE created_at >= %s AND botnet_type = %s
                ORDER BY created_at ASC
            """, (start_time, botnet_type))
        else:
            # 查询总体历史数据
            cursor.execute("""
                SELECT 
                    total_nodes,
                    total_domestic_nodes,
                    total_foreign_nodes,
                    monthly_total_nodes,
                    monthly_domestic_nodes,
                    monthly_foreign_nodes,
                    cleaned_total_nodes,
                    cleaned_domestic_nodes,
                    cleaned_foreign_nodes,
                    monthly_cleaned_total_nodes,
                    monthly_cleaned_domestic_nodes,
                    monthly_cleaned_foreign_nodes,
                    suppression_total_count,
                    monthly_suppression_count,
                    created_at
                FROM takeover_stats 
                WHERE created_at >= %s
                ORDER BY created_at ASC
            """, (start_time,))
        
        results = cursor.fetchall()
        
        if not results:
            raise HTTPException(status_code=404, detail="指定时间范围内暂无数据")
        
        # 格式化返回数据
        history_data = []
        for row in results:
            data_point = {
                "total_stats": {
                    "total_nodes": row["total_nodes"],
                    "total_domestic_nodes": row["total_domestic_nodes"],
                    "total_foreign_nodes": row["total_foreign_nodes"]
                },
                "monthly_stats": {
                    "monthly_total_nodes": row["monthly_total_nodes"],
                    "monthly_domestic_nodes": row["monthly_domestic_nodes"],
                    "monthly_foreign_nodes": row["monthly_foreign_nodes"]
                },
                "cleaned_stats": {
                    "cleaned_total_nodes": row["cleaned_total_nodes"],
                    "cleaned_domestic_nodes": row["cleaned_domestic_nodes"],
                    "cleaned_foreign_nodes": row["cleaned_foreign_nodes"]
                },
                "monthly_cleaned_stats": {
                    "monthly_cleaned_total_nodes": row["monthly_cleaned_total_nodes"],
                    "monthly_cleaned_domestic_nodes": row["monthly_cleaned_domestic_nodes"],
                    "monthly_cleaned_foreign_nodes": row["monthly_cleaned_foreign_nodes"]
                },
                "suppression_stats": {
                    "suppression_total_count": row["suppression_total_count"],
                    "monthly_suppression_count": row["monthly_suppression_count"]
                },
                "timestamp": row["created_at"].isoformat()
            }
            
            if botnet_type:
                data_point["botnet_type"] = row["botnet_type"]
            
            history_data.append(data_point)
        
        return {
            "status": "success",
            "data": history_data,
            "count": len(history_data),
            "time_range": {
                "start": start_time.isoformat(),
                "end": datetime.now().isoformat(),
                "hours": hours
            },
            "botnet_type": botnet_type,
            "message": "获取历史数据成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/summary", summary="获取统计数据摘要")
async def get_stats_summary():
    """
    获取统计数据摘要
    
    返回各类型僵尸网络的排名和占比信息
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        
        # 获取最新的总体数据
        cursor.execute("""
            SELECT 
                total_nodes,
                total_domestic_nodes,
                total_foreign_nodes,
                monthly_total_nodes,
                monthly_domestic_nodes,
                monthly_foreign_nodes,
                cleaned_total_nodes,
                cleaned_domestic_nodes,
                cleaned_foreign_nodes,
                monthly_cleaned_total_nodes,
                monthly_cleaned_domestic_nodes,
                monthly_cleaned_foreign_nodes,
                suppression_total_count,
                monthly_suppression_count
            FROM takeover_stats 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        total_result = cursor.fetchone()
        
        if not total_result:
            raise HTTPException(status_code=404, detail="暂无统计数据")
        
        # 获取各类型详细数据
        cursor.execute("""
            SELECT 
                botnet_type,
                total_nodes,
                total_domestic_nodes,
                total_foreign_nodes,
                monthly_total_nodes,
                monthly_domestic_nodes,
                monthly_foreign_nodes,
                cleaned_total_nodes,
                cleaned_domestic_nodes,
                cleaned_foreign_nodes,
                monthly_cleaned_total_nodes,
                monthly_cleaned_domestic_nodes,
                monthly_cleaned_foreign_nodes,
                suppression_total_count,
                monthly_suppression_count
            FROM takeover_stats_detail 
            WHERE created_at = (
                SELECT MAX(created_at) FROM takeover_stats_detail
            )
            ORDER BY total_nodes DESC
        """)
        
        detail_results = cursor.fetchall()
        
        # 计算占比和排名
        total_all_nodes = total_result["total_nodes"]
        rankings = []
        
        for i, row in enumerate(detail_results, 1):
            percentage = (row["total_nodes"] / total_all_nodes * 100) if total_all_nodes > 0 else 0
            rankings.append({
                "rank": i,
                "botnet_type": row["botnet_type"],
                "total_nodes": row["total_nodes"],
                "percentage": round(percentage, 2),
                "domestic_nodes": row["total_domestic_nodes"],
                "foreign_nodes": row["total_foreign_nodes"],
                "monthly_nodes": row["monthly_total_nodes"],
                "cleaned_nodes": row["cleaned_total_nodes"],
                "monthly_cleaned_nodes": row["monthly_cleaned_total_nodes"],
                "suppression_count": row["suppression_total_count"],
                "monthly_suppression_count": row["monthly_suppression_count"]
            })
        
        return {
            "status": "success",
            "data": {
                "overview": {
                    "total_nodes": total_result["total_nodes"],
                    "total_domestic_nodes": total_result["total_domestic_nodes"],
                    "total_foreign_nodes": total_result["total_foreign_nodes"],
                    "monthly_total_nodes": total_result["monthly_total_nodes"],
                    "monthly_domestic_nodes": total_result["monthly_domestic_nodes"],
                    "monthly_foreign_nodes": total_result["monthly_foreign_nodes"],
                    "cleaned_total_nodes": total_result["cleaned_total_nodes"],
                    "cleaned_domestic_nodes": total_result["cleaned_domestic_nodes"],
                    "cleaned_foreign_nodes": total_result["cleaned_foreign_nodes"],
                    "monthly_cleaned_total_nodes": total_result["monthly_cleaned_total_nodes"],
                    "monthly_cleaned_domestic_nodes": total_result["monthly_cleaned_domestic_nodes"],
                    "monthly_cleaned_foreign_nodes": total_result["monthly_cleaned_foreign_nodes"],
                    "suppression_total_count": total_result["suppression_total_count"],
                    "monthly_suppression_count": total_result["monthly_suppression_count"]
                },
                "rankings": rankings,
                "statistics": {
                    "total_botnet_types": len(rankings),
                    "domestic_ratio": round((total_result["total_domestic_nodes"] / total_result["total_nodes"] * 100) if total_result["total_nodes"] > 0 else 0, 2),
                    "foreign_ratio": round((total_result["total_foreign_nodes"] / total_result["total_nodes"] * 100) if total_result["total_nodes"] > 0 else 0, 2)
                }
            },
            "message": "获取统计摘要成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取统计摘要失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/health", summary="健康检查接口")
async def health_check():
    """
    健康检查接口
    
    检查数据库连接和数据更新状态
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        
        # 检查最新数据的时间
        cursor.execute("""
            SELECT 
                MAX(created_at) as latest_update,
                COUNT(*) as record_count
            FROM takeover_stats
        """)
        
        result = cursor.fetchone()
        
        if not result or not result["latest_update"]:
            return {
                "status": "warning",
                "message": "暂无统计数据",
                "database_connection": "ok",
                "latest_update": None,
                "record_count": 0
            }
        
        # 检查数据是否过期（超过5分钟未更新）
        latest_update = result["latest_update"]
        time_diff = datetime.now() - latest_update
        is_data_fresh = time_diff.total_seconds() < 300  # 5分钟
        
        return {
            "status": "ok" if is_data_fresh else "warning",
            "message": "服务正常" if is_data_fresh else "数据可能过期",
            "database_connection": "ok",
            "latest_update": latest_update.isoformat(),
            "record_count": result["record_count"],
            "data_age_seconds": int(time_diff.total_seconds()),
            "is_data_fresh": is_data_fresh
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "error",
            "message": f"服务异常: {str(e)}",
            "database_connection": "error"
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
