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
    china_amount: int 
    global_amount: int

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
                # 计算中国总量
                china_query = f"""
                    SELECT COALESCE(SUM(infected_num), 0) as china_total
                    FROM china_botnet_{botnet_name}
                """
                cursor.execute(china_query)
                china_total = cursor.fetchone()['china_total']
                
                # 计算全球总量
                global_query = f"""
                    SELECT COALESCE(SUM(infected_num), 0) as global_total
                    FROM global_botnet_{botnet_name}
                """
                cursor.execute(global_query)
                global_total = cursor.fetchone()['global_total']
                
                # 添加到响应数据
                response_data.append({
                    "name": botnet_name,
                    "china_amount": int(china_total),
                    "global_amount": int(global_total)
                })
                
                logger.info(f"Botnet {botnet_name} stats - China: {china_total}, Global: {global_total}")
            
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
        
        # 获取该省份下所有城市的感染数据，使用 GROUP BY 去重
        cursor.execute(f"""
            SELECT 
                municipality as city,
                SUM(infected_num) as total
            FROM {china_table}
            WHERE province = %s 
            AND municipality IS NOT NULL
            GROUP BY municipality
            ORDER BY municipality
        """, (province_name,))
        
        city_data = cursor.fetchall()
        result_data = {
            botnet_type: [
                {
                    "city": city,
                    "amount": int(total)
                }
                for city, total in city_data
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