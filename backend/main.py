from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pymysql
from pymysql.cursors import DictCursor
from typing import List, Dict, Union, Optional
from pydantic import BaseModel, Field, validator
import random
from datetime import datetime, timedelta
import asyncio
from router.user import router as user_router
from router.node import router as node_router
from router.asruex import router as asruex_router
from router.botnet import router as botnet_router
from router.amount import router as amount_router

import logging
import re
from ip_location.ip_query import ip_query  # 导入IP查询模块

# 设置日志
logging.basicConfig(
    level=logging.INFO,  # 改为DEBUG级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 也设置其他常用库的日志级别
logging.getLogger('uvicorn').setLevel(logging.INFO)
logging.getLogger('fastapi').setLevel(logging.INFO)

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "user": "root",  # 替换为你的数据库用户名
    "password": "root",  # 替换为你的数据库密码
    "database": "botnet"
}


# 全局异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error occurred: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error occurred: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"}
    )


# 包含用户路由
app.include_router(user_router, prefix="/api/user", tags=["users"])

# 包含节点路由
app.include_router(node_router, prefix="/api", tags=["nodes"])

# 包含asruex路由
app.include_router(asruex_router, prefix="/api/asruex", tags=["asruex"])

# 包含botnet路由
app.include_router(botnet_router, prefix="/api", tags=["botnet"])

# 包含amount路由
app.include_router(amount_router, prefix="/api", tags=["amount"])


# 数据模型
class ProvinceAmount(BaseModel):
    province: str
    amount: int


# 添加数据模型
class UserEvent(BaseModel):
    time: str
    ip: str
    location: str
    command: str


class BotnetType(BaseModel):
    name: str
    display_name: str
    description: str
    table_name: str
    created_at: Optional[datetime] = None


@app.get("/api/province-amounts")
async def get_province_amounts(botnet_type: Optional[str] = None):
    try:
        # 获取所有注册的僵尸网络类型
        botnet_tables = await get_botnet_tables()

        # 如果指定了僵尸网络类型，只查询该类型
        if botnet_type:
            if botnet_type not in botnet_tables:
                raise HTTPException(status_code=404, detail=f"Botnet type {botnet_type} not found")
            botnet_tables = {botnet_type: botnet_tables[botnet_type]}

        # 建立数据库连接
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # 构建动态查询
        # 首先获取所有省份
        provinces_query = " UNION ".join(
            f"SELECT DISTINCT province FROM {table_name}"
            for table_name in botnet_tables.values()
        )
        cursor.execute(f"SELECT DISTINCT province FROM ({provinces_query}) as provinces WHERE province IS NOT NULL")

        provinces = [row[0] for row in cursor.fetchall()]
        print(provinces)
        # 然后为每个僵尸网络类型构建查询
        query_parts = []
        for province in provinces:
            subqueries = []
            for botnet_name, table_name in botnet_tables.items():
                # 使用china_botnet_xxx表
                china_table = f"china_botnet_{botnet_name}"
                subqueries.append(f"""
                    SELECT 
                        '{province}' as province,
                        '{botnet_name}' as botnet_type,
                        COALESCE(SUM(infected_num), 0) as total
                    FROM {china_table}
                    WHERE province = %s
                """)
            query_parts.extend(subqueries)

        # 执行查询
        query = " UNION ALL ".join(query_parts)
        params = [province for province in provinces for _ in botnet_tables]
        cursor.execute(query, params)
        results = cursor.fetchall()

        # 转换为响应格式
        province_amounts = {name: [] for name in botnet_tables.keys()}

        for province, botnet_type, total in results:
            province_amounts[botnet_type].append({
                "province": province,
                "amount": int(total)
            })

        return province_amounts

    except Exception as e:
        logger.error(f"Database error in get_province_amounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()


@app.get("/api/world-amounts")
async def get_world_amounts(botnet_type: Optional[str] = None):
    try:
        # 建立数据库连接
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # 获取所有注册的僵尸网络类型
        botnet_tables = await get_botnet_tables()

        # 如果指定了僵尸网络类型，只查询该类型
        if botnet_type:
            if botnet_type not in botnet_tables:
                raise HTTPException(status_code=404, detail=f"Botnet type {botnet_type} not found")
            botnet_types = [botnet_type]
        else:
            botnet_types = list(botnet_tables.keys())

        # 构建查询
        query_parts = []
        for bot_type in botnet_types:
            # 使用global_botnet_xxx表
            global_table = f"global_botnet_{bot_type}"
            query_parts.append(f"""
                SELECT 
                    country,
                    '{bot_type}' as botnet_type,
                    infected_num
                FROM {global_table}
            """)

        # 执行查询
        if query_parts:
            query = " UNION ALL ".join(query_parts)
            cursor.execute(query)
            results = cursor.fetchall()
        else:
            results = []

        # 转换为响应格式
        world_amounts = {bot_type: [] for bot_type in botnet_types}

        for country, bot_type, amount in results:
            world_amounts[bot_type].append({
                "country": country,
                "amount": int(amount or 0)
            })

        return world_amounts

    except Exception as e:
        logger.error(f"Database error in get_world_amounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()


@app.get("/api/industry-distribution")
async def get_industry_distribution():
    results = [
        {"name": "制造业", "value": 25},
        {"name": "金融业", "value": 20},
        {"name": "互联网行业", "value": 15},
        {"name": "医疗行业", "value": 12},
        {"name": "教育行业", "value": 10},
        {"name": "零售业", "value": 8},
        {"name": "房地产业", "value": 5},
        {"name": "信息技术服务业", "value": 5}
    ]

    return {"data": results}


@app.get("/api/user-events")
async def get_user_events():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)

        query = """
        SELECT 
            DATE_FORMAT(event_time, '%Y-%m-%d %H:%i:%s') as time,
            username,
            ip,
            location,
            botnet_type,
            command
        FROM user_events
        ORDER BY event_time DESC
        LIMIT 20
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    except Exception as e:
        logger.error(f"Error fetching user events: {e}")
        return []  # 返回空数组而不是抛出异常


# 添加异常报告模型
class AnomalyReport(BaseModel):
    id: int
    ip: str
    location: str
    time: str
    description: str
    severity: str


@app.get("/api/anomaly-reports")
async def get_anomaly_reports():
    try:
        # 查询数据库中的异常报告
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)

        # 尝试查询异常报告表
        try:
            query = """
            SELECT 
                id, ip, location, 
                DATE_FORMAT(report_time, '%Y/%m/%d %H:%i') as time,
                description, severity
            FROM anomaly_reports
            ORDER BY report_time DESC
            LIMIT 20
            """
            cursor.execute(query)
            results = cursor.fetchall()
        except Exception as e:
            # 如果表不存在，返回模拟数据
            logger.warning(f"异常报告表查询失败: {e}")
            results = []
        return results
    except Exception as e:
        logger.error(f"Error fetching anomaly reports: {e}")
        # 发生错误时返回空数组
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


class IPLocationRequest(BaseModel):
    ip: str

    @validator('ip')
    def validate_ip(cls, v):
        pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid IP address format')
        return v


@app.post("/api/ip-location")
async def get_ip_location(request: IPLocationRequest):
    try:
        client_ip = request.ip
        logger.info(f"处理IP地理位置查询请求: {client_ip}")

        # 使用ip_query模块查询IP信息
        ip_info = await ip_query(client_ip)

        if not ip_info:
            return {
                "ip": client_ip,
                "city": "未知城市",
                "country": "未知国家",
                "location": "未知城市",  # 使用城市作为位置
                "isp": "未知ISP",
                "continent": "未知大洲"
            }

        # 解析地理位置信息
        country_prov_city = ip_info.get('country_prov_city', '').split('_')
        country = country_prov_city[0] if len(country_prov_city) > 0 else '未知国家'
        province = country_prov_city[1] if len(country_prov_city) > 1 else ''
        city = country_prov_city[2] if len(country_prov_city) > 2 else ''

        # 如果城市为空但有省份信息，使用省份作为城市
        if not city and province:
            city = province

        # 优先使用城市作为位置信息
        location = city or province or country or '未知城市'

        result = {
            "ip": client_ip,
            "city": city or province or "未知城市",  # 如果没有城市，使用省份
            "country": country,
            "location": location,
            "isp": ip_info.get('isp', '未知ISP'),
            "continent": ip_info.get('continent', '未知大洲')
        }

        logger.info(f"IP地理位置查询结果: {result}")
        return result

    except Exception as e:
        logger.error(f"IP地理位置查询失败: {str(e)}")
        return {
            "ip": client_ip,
            "city": "未知城市",
            "country": "未知国家",
            "location": "未知城市",  # 使用城市作为位置
            "isp": "未知ISP",
            "continent": "未知大洲",
            "error": str(e)
        }


@app.get("/api/ip-location")
async def get_ip_location_fallback(request: Request):
    try:
        # 从请求头中获取真实的客户端IP
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()
        else:
            client_ip = (
                    request.headers.get('X-Real-IP') or
                    request.headers.get('CF-Connecting-IP') or
                    request.client.host
            )

        # 创建一个请求对象并调用POST方法
        ip_request = IPLocationRequest(ip=client_ip)
        return await get_ip_location(ip_request)

    except Exception as e:
        logger.error(f"IP地理位置查询失败(fallback): {str(e)}")
        return {
            "ip": "未知",
            "city": "未知城市",
            "country": "未知国家",
            "location": "未知城市",  # 使用城市作为位置
            "isp": "未知ISP",
            "continent": "未知大洲",
            "error": str(e)
        }


# 修改现有的获取数据的函数
async def get_botnet_tables():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        cursor.execute("SELECT name, table_name FROM botnet_types")
        return {row['name']: row['table_name'] for row in cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


# 更新全球僵尸网络数据
@app.post("/api/update-global-botnet")
async def update_global_botnet(country: str, botnet_type: str, infected_num: int):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 检查僵尸网络类型是否有效
        if botnet_type not in ['asruex', 'andromeda', 'mozi']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid botnet type. Must be one of: asruex, andromeda, mozi"
            )

        # 将botnet_type转换为数据库中的格式
        db_botnet_type = botnet_type

        # 更新或插入数据
        cursor.execute("""
            INSERT INTO global_botnets (country, botnet_type, infected_num)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                infected_num = VALUES(infected_num),
                updated_at = CURRENT_TIMESTAMP
        """, (country, db_botnet_type, infected_num))

        conn.commit()
        return {"status": "success", "message": "Global botnet data updated successfully"}

    except Exception as e:
        logger.error(f"Error updating global botnet data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


# 获取特定国家的僵尸网络数据
@app.get("/api/country-botnet/{country}")
async def get_country_botnet(country: str):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 获取所有注册的僵尸网络类型
        botnet_tables = await get_botnet_tables()
        botnet_types = list(botnet_tables.keys())

        # 获取指定国家的所有僵尸网络数据
        botnets_data = {}

        for botnet_type in botnet_types:
            # 使用global_botnet_xxx表
            global_table = f"global_botnet_{botnet_type}"

            cursor.execute(f"""
                SELECT infected_num
                FROM {global_table}
                WHERE country = %s
            """, (country,))

            result = cursor.fetchone()
            if result:
                botnets_data[botnet_type] = int(result[0] or 0)
            else:
                botnets_data[botnet_type] = 0

        data = {
            "country": country,
            "botnets": botnets_data
        }

        return {"status": "success", "data": data}

    except Exception as e:
        logger.error(f"Error getting country botnet data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
