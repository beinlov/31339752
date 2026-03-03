from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime
import logging

from config import DB_CONFIG

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


class BotnetDistribution(BaseModel):
    name: str
    china_active: int
    global_active: int
    china_cleaned: int
    global_cleaned: int

@router.get("/botnet-distribution", response_model=List[BotnetDistribution])
async def get_botnet_distribution():
    try:
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 获取所有注册的僵尸网络类型
        cursor.execute("SELECT name, table_name FROM botnet_types ORDER BY created_at")
        botnet_types = cursor.fetchall()
        
        response_data = []
        
        for botnet in botnet_types:
            botnet_name = botnet['name']
            
            try:
                # 计算中国总量（只包括active、cleaned）
                china_query = f"""
                    SELECT 
                        COALESCE(SUM(active_num), 0) as china_active,
                        COALESCE(SUM(cleaned_num), 0) as china_cleaned
                    FROM china_botnet_{botnet_name}
                """
                cursor.execute(china_query)
                china_result = cursor.fetchone()
                
                # 计算全球总量（只包括active、cleaned）
                global_query = f"""
                    SELECT 
                        COALESCE(SUM(active_num), 0) as global_active,
                        COALESCE(SUM(cleaned_num), 0) as global_cleaned
                    FROM global_botnet_{botnet_name}
                """
                cursor.execute(global_query)
                global_result = cursor.fetchone()
                
                # 添加到响应数据
                response_data.append({
                    "name": botnet_name,
                    "china_active": int(china_result['china_active']),
                    "global_active": int(global_result['global_active']),
                    "china_cleaned": int(china_result['china_cleaned']),
                    "global_cleaned": int(global_result['global_cleaned'])
                })
                
                logger.info(f"Botnet {botnet_name} stats - Active: C{china_result['china_active']}/G{global_result['global_active']}, Cleaned: C{china_result['china_cleaned']}/G{global_result['global_cleaned']}")
            
            except Exception as e:
                # 如果表不存在或查询失败，跳过该僵尸网络并记录警告
                logger.warning(f"Skipping botnet {botnet_name} due to error: {str(e)}")
                continue
        
        logger.info(f"Final response data: {response_data}")
        return response_data
        
    except Exception as e:
        logger.error(f"Database error in get_botnet_distribution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.get("/city-amounts/{province_name}")
async def get_city_amounts(province_name: str, botnet_type: str = None):
    try:
        if not botnet_type:
            return {
                "status": "error",
                "message": "botnet_type is required",
                "data": {}
            }

        # 建立数据库连接
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # 使用china_botnet_xxx表
        china_table = f"china_botnet_{botnet_type}"
        
        # 获取该省份下所有城市的active和cleaned数据，使用 GROUP BY 去重
        # 只统计active和cleaned状态，不统计inactive
        # 使用组合索引 idx_province_municipality 优化查询性能
        cursor.execute(f"""
            SELECT 
                municipality as city,
                SUM(active_num) as active_total,
                SUM(cleaned_num) as cleaned_total
            FROM {china_table}
            WHERE province = %s 
            AND municipality IS NOT NULL
            AND municipality != ''
            GROUP BY municipality
            ORDER BY active_total DESC, cleaned_total DESC
            LIMIT 100
        """, (province_name,))
        
        city_data = cursor.fetchall()
        result_data = {
            botnet_type: [
                {
                    "city": city,
                    "active": int(active_total) if active_total else 0,
                    "cleaned": int(cleaned_total) if cleaned_total else 0,
                    "amount": int(active_total or 0) + int(cleaned_total or 0)  # 总数 = active + cleaned
                }
                for city, active_total, cleaned_total in city_data
            ]
        }

        return {
            "status": "success",
            "message": f"成功获取省份 {province_name} 的城市数据",
            "data": result_data
        }
        
    except Exception as e:
        logger.error(f"Database error in get_city_amounts: {str(e)}")
        return {
            "status": "error",
            "message": f"获取省份 {province_name} 数据时发生错误: {str(e)}",
            "data": {botnet_type: []} if botnet_type else {}
        }
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()