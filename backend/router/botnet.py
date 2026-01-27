import httpx
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
import pymysql
from pymysql.cursors import DictCursor
from typing import List, Dict, Optional
from datetime import datetime
import logging
import re
import asyncio
import random

from config import DB_CONFIG
from database.schema import (
    get_node_table_ddl, 
    get_communication_table_ddl,
    get_china_botnet_table_ddl,
    get_global_botnet_table_ddl
)
from ip_location.ip_query import ip_query  # 导入IP查询模块
from auth_middleware import require_operator_or_admin, require_admin

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


def create_botnet_timeset_table(botnet_name: str):
    """
    为新僵尸网络创建时间序列表
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        table_name = f"botnet_timeset_{botnet_name}"
        
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL UNIQUE COMMENT '日期',
            count INT NOT NULL DEFAULT 0 COMMENT '节点数量',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX idx_date (date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='{botnet_name}僵尸网络每日节点数量统计表';
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        
        logger.info(f"Created timeset table: {table_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating timeset table for {botnet_name}: {e}")
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 数据模型
class BotnetType(BaseModel):
    name: str
    display_name: str
    description: str
    table_name: str
    clean_methods: List[str] = []  # 支持的清理方法列表
    created_at: Optional[datetime] = None

class CleanBotnetRequest(BaseModel):
    botnet_type: str
    target_machines: List[str]  # IP地址列表
    clean_method: str
    username: str
    location: str
    operator_ip: str = None

    @field_validator('target_machines')
    @classmethod
    def validate_target_machines(cls, v):
        pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
        for ip in v:
            if not re.match(pattern, ip):
                raise ValueError(f'Invalid IP address format: {ip}')
        return v

    @field_validator('botnet_type')
    @classmethod
    def validate_botnet_type(cls, v):
        valid_botnets = ["asruex", "andromeda", "mozi", "leethozer", "ramnit", "autoupdate"]
        if v not in valid_botnets:
            raise ValueError(f'Invalid botnet type: {v}')
        return v

    @field_validator('clean_method')
    @classmethod
    def validate_clean_method(cls, v):
        valid_methods = ["monitor", "clear", "suppress", "reuse", "ddos"]
        if v not in valid_methods:
            raise ValueError(f'Invalid clean method: {v}')
        return v

# Helper functions
async def ensure_botnet_table_exists(bot_name: str):
    """确保僵尸网络数据表存在，如果不存在则创建（双表设计）"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        china_table = f"china_botnet_{bot_name}"
        global_table = f"global_botnet_{bot_name}"
        node_table = f"botnet_nodes_{bot_name}"
        communication_table = f"botnet_communications_{bot_name}"  # 新增通信记录表

        # 检查表是否存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, (DB_CONFIG['database'], china_table))
        
        if cursor.fetchone()[0] == 0:
            logger.info(f"Tables for {bot_name} do not exist, creating...")
            
            # 使用统一的schema定义创建所有表
            # 1. 创建中国区域统计表
            china_ddl = get_china_botnet_table_ddl(bot_name)
            cursor.execute(china_ddl)
            
            # 2. 创建全球统计表
            global_ddl = get_global_botnet_table_ddl(bot_name)
            cursor.execute(global_ddl)
            
            # 3. 创建节点表（汇总信息）
            node_ddl = get_node_table_ddl(bot_name)
            cursor.execute(node_ddl)
            
            # 4. 创建通信记录表（详细历史）- 包含外键约束RESTRICT
            comm_ddl = get_communication_table_ddl(bot_name, node_table)
            cursor.execute(comm_ddl)
            
            conn.commit()
            logger.info(f"All tables for {bot_name} created successfully: {china_table}, {global_table}, {node_table}, {communication_table}")
            
    except Exception as e:
        logger.error(f"Error ensuring table exists: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.get("/botnet-rankings")
async def get_botnet_rankings(mode: str = "global"):
    """
    获取僵尸网络排序
    mode:
      - global: 按全球节点数量排序
      - china:  按中国节点感染数量排序（country='中国'）
    """
    if mode not in ("global", "china"):
        raise HTTPException(status_code=400, detail="mode must be 'global' or 'china'")

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)

        cursor.execute("SELECT name, display_name FROM botnet_types")
        botnets = cursor.fetchall()

        results = []
        for bot in botnets:
            name = bot["name"]
            display_name = bot.get("display_name") or name

            # 计算全球节点数量
            global_count = 0
            node_table = f"botnet_nodes_{name}"
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
            """, (DB_CONFIG['database'], node_table))
            if cursor.fetchone()["cnt"] > 0:
                cursor.execute(f"SELECT COUNT(*) AS total FROM {node_table}")
                global_count = cursor.fetchone()["total"] or 0

            # 计算中国影响程度（global表的中国 infected_num）
            china_count = 0
            global_table = f"global_botnet_{name}"
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
            """, (DB_CONFIG['database'], global_table))
            if cursor.fetchone()["cnt"] > 0:
                cursor.execute(f"""
                    SELECT infected_num FROM {global_table}
                    WHERE country = %s
                    LIMIT 1
                """, ("中国",))
                row = cursor.fetchone()
                if row:
                    china_count = row.get("infected_num") or 0

            results.append({
                "name": name,
                "display_name": display_name,
                "global_count": global_count,
                "china_count": china_count
            })

        if mode == "china":
            results.sort(key=lambda x: x["china_count"], reverse=True)
        else:
            results.sort(key=lambda x: x["global_count"], reverse=True)

        return {"status": "success", "data": results}
    except Exception as e:
        logger.error(f"Error fetching botnet rankings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

async def ensure_botnet_type_exists(botnet_name: str, table_name: str):
    """确保僵尸网络类型存在于botnet_types表中，如果不存在则创建"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查类型是否存在
        cursor.execute("SELECT id FROM botnet_types WHERE name = %s", (botnet_name,))
        if not cursor.fetchone():
            logger.info(f"Botnet type {botnet_name} does not exist, creating...")
            
            # 获取默认的显示名称和描述
            display_name = f"{botnet_name.capitalize()}僵尸网络"
            description = f"{botnet_name.capitalize()}是一个新发现的僵尸网络，具体特征和危害正在分析中。"
            
            # 插入新的僵尸网络类型
            cursor.execute("""
                INSERT INTO botnet_types (name, display_name, description, table_name)
                VALUES (%s, %s, %s, %s)
            """, (botnet_name, display_name, description, table_name))
            
            conn.commit()
            logger.info(f"Botnet type {botnet_name} registered successfully")
            
            # 创建对应的timeset表
            create_botnet_timeset_table(botnet_name)
            
    except Exception as e:
        logger.error(f"Error ensuring botnet type exists: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

async def get_botnet_tables():
    """获取所有僵尸网络表的映射"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 获取所有僵尸网络类型
        cursor.execute("SELECT name, table_name FROM botnet_types")
        tables = {row['name']: row['table_name'] for row in cursor.fetchall()}
        
        # 如果表不存在，确保创建
        for botnet_name, table_name in tables.items():
            await ensure_botnet_table_exists(botnet_name)
            
        return tables
        
    except Exception as e:
        logger.error(f"Error getting botnet tables: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Routes
@router.get("/botnet-types")
async def get_botnet_types():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        cursor.execute("SELECT * FROM botnet_types ORDER BY created_at")
        types = cursor.fetchall()
        
        return {"status": "success", "data": types}
    except Exception as e:
        logger.error(f"Error fetching botnet types: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.post("/botnet-types")
async def register_botnet_type(botnet: BotnetType, current_user: dict = Depends(require_admin)):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        if not botnet.table_name.startswith('china_botnet_'):
            raise HTTPException(
                status_code=400,
                detail="Table name must start with 'china_botnet_'"
            )
        
        # 检查僵尸网络类型是否已存在
        cursor.execute("SELECT id FROM botnet_types WHERE name = %s", (botnet.name,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f"Botnet type {botnet.name} already exists"
            )
        
        # 确保表存在
        await ensure_botnet_table_exists(botnet.name)
        
        # 准备clean_methods JSON字符串
        import json
        clean_methods_json = json.dumps(botnet.clean_methods) if botnet.clean_methods else json.dumps(["clear", "suppress"])
        
        # 添加新的僵尸网络类型
        cursor.execute("""
            INSERT INTO botnet_types (name, display_name, description, table_name, clean_methods)
            VALUES (%s, %s, %s, %s, %s)
        """, (botnet.name, botnet.display_name, botnet.description, botnet.table_name, clean_methods_json))
        
        conn.commit()
        
        # 创建对应的timeset表
        create_botnet_timeset_table(botnet.name)
        return {
            "status": "success", 
            "message": f"Botnet type {botnet.name} registered successfully",
            "data": {
                "name": botnet.name,
                "display_name": botnet.display_name,
                "table_name": botnet.table_name
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error registering botnet type: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@router.post("/update-global-botnet")
async def update_global_botnet(country: str, botnet_type: str, infected_num: int):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查僵尸网络类型是否有效
        cursor.execute("SELECT name FROM botnet_types WHERE name = %s", (botnet_type,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid botnet type: {botnet_type}"
            )
        
        # 使用global_botnet_xxx表
        global_table = f"global_botnet_{botnet_type}"
        # 更新或插入数据
        cursor.execute(f"""
            INSERT INTO {global_table} (country, infected_num)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                infected_num = VALUES(infected_num),
                updated_at = CURRENT_TIMESTAMP
        """, (country, infected_num))
        
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

async def perform_async_cleanup(botnet_type: str, botnet_info: dict, clean_method: str):
    """异步执行清理操作"""
    try:
        if clean_method == "clear":
            for round in range(5):  # 执行5轮清理
                conn = pymysql.connect(**DB_CONFIG)
                cursor = conn.cursor(DictCursor)

                try:
                    # 对中国区域表的处理
                    cursor.execute(f"""
                                SELECT province, municipality, infected_num 
                                FROM {botnet_info['table_name']}
                                WHERE infected_num > 0
                                """)
                    records = cursor.fetchall()

                    total_china_reduction = 0  # 记录中国区域总减少量
                    for record in records:
                        await asyncio.sleep(0.1)  # 每处理一批数据就让出控制权
                        decrease_factor = random.uniform(0.50, 0.80)  # 每次只减少5-15%
                        old_num = record['infected_num']
                        new_num = max(int(old_num * (1 - decrease_factor)), 1)  # 确保不会降到0
                        reduction = old_num - new_num
                        total_china_reduction += reduction

                        cursor.execute(f"""
                                    UPDATE {botnet_info['table_name']}
                                    SET infected_num = %s
                                    WHERE province = %s AND municipality = %s
                                    """, (new_num, record['province'], record['municipality']))
                        conn.commit()  # 每次更新后都提交，避免长时间占用事务

                        # 更新全球表中的中国数据
                        if reduction > 0:
                            # 首先获取中国当前的感染数量
                            cursor.execute(f"""
                                        SELECT infected_num 
                                        FROM global_botnet_{botnet_type}
                                        WHERE country = '中国'
                                        """)
                            current_china = cursor.fetchone()
                            if current_china:
                                new_china_num = max(current_china['infected_num'] - reduction, 1)
                                cursor.execute(f"""
                                            UPDATE global_botnet_{botnet_type}
                                            SET infected_num = %s
                                            WHERE country = '中国'
                                            """, (new_china_num,))
                                conn.commit()

                finally:
                    cursor.close()
                    conn.close()

                # 在每轮清理之间随机等待5-10秒
                if round < 4:  # 最后一轮不需要等待
                    await asyncio.sleep(random.uniform(5, 10))

        elif clean_method == "suppress":
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            try:
                await asyncio.sleep(0.1)
                if botnet_info['target_machines']:
                    cursor.execute(f"""
                        UPDATE {botnet_info['table_name']}
                        SET infected_num = ROUND(infected_num * 0.8)
                        WHERE ip IN %s
                    """, (tuple(botnet_info['target_machines']),))
                else:
                    # 更新中国区域表
                    cursor.execute(f"""
                        UPDATE {botnet_info['table_name']}
                        SET infected_num = ROUND(infected_num * 0.8)
                    """)

                    # 同步更新全球表中的中国数据
                    cursor.execute(f"""
                        UPDATE global_botnet_{botnet_type}
                        SET infected_num = ROUND(infected_num * 0.8)
                        WHERE country = '中国'
                    """)
                conn.commit()
            finally:
                cursor.close()
                conn.close()

        elif clean_method == "reuse":
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            try:
                await asyncio.sleep(0.1)
                if botnet_info['target_machines']:
                    cursor.execute(f"""
                        UPDATE {botnet_info['table_name']}
                        SET status = 'controlled'
                        WHERE ip IN %s
                    """, (tuple(botnet_info['target_machines']),))
                else:
                    cursor.execute(f"""
                        UPDATE {botnet_info['table_name']}
                        SET status = 'controlled'
                    """)
                conn.commit()
            finally:
                cursor.close()
                conn.close()

        elif clean_method == "ddos":
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            try:
                await asyncio.sleep(0.1)
                if botnet_info['target_machines']:
                    cursor.execute(f"""
                        UPDATE {botnet_info['table_name']}
                        SET blocked = TRUE,
                            blocked_at = NOW()
                        WHERE ip IN %s
                    """, (tuple(botnet_info['target_machines']),))
                else:
                    cursor.execute(f"""
                        UPDATE {botnet_info['table_name']}
                        SET blocked = TRUE,
                            blocked_at = NOW()
                    """)
                conn.commit()
            finally:
                cursor.close()
                conn.close()

        logger.info(f"Async cleanup completed for {botnet_type} using {clean_method} method")

    except Exception as e:
        logger.error(f"Error in async cleanup: {e}")

async def perform_botnet_cleanup(botnet_type: str, clean_method: str, target_machines: List[str]) -> dict:
    """
    执行僵尸网络清理操作的通用函数
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 检查僵尸网络类型是否存在
        cursor.execute("SELECT * FROM botnet_types WHERE name = %s", (botnet_type,))
        botnet_info = cursor.fetchone()
        if not botnet_info:
            raise HTTPException(status_code=404, detail=f"Botnet type {botnet_type} not found")
        
        # 检查清理方法是否支持
        clean_methods = botnet_info.get('clean_methods', [])
        if clean_methods and clean_method not in clean_methods:
            raise HTTPException(
                status_code=400, 
                detail=f"Clean method {clean_method} not supported for {botnet_type}"
            )
        
        # 启动异步清理任务
        asyncio.create_task(perform_async_cleanup(botnet_type, botnet_info, clean_method))
        
        return {
            "status": "success",
            "message": f"Cleanup task started for {botnet_type} using {clean_method} method",
            "task_id": f"{botnet_type}_{clean_method}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
    except Exception as e:
        logger.error(f"Error in perform_botnet_cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

async def poll_logs_and_store(username: str, location: str, botnet_type: str):
    try:
        async with httpx.AsyncClient() as client:
            for _ in range(12):  # 每5秒轮询一次，最多1分钟
                await asyncio.sleep(5)
                try:
                    resp = await client.get("http://120.224.102.130:40153/get-logs")
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("status") == "success":
                            records = data.get("records", [])
                            clean_records = [r for r in records if r.get("operate") == "clean"]

                            if clean_records:
                                conn = pymysql.connect(**DB_CONFIG)
                                cursor = conn.cursor()
                                for record in clean_records:
                                    try:
                                        ip = record.get("ip")
                                        timestamp_str = record.get("timestamp")
                                        event_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                                        # 判断是否已存在相同时间和IP的记录
                                        cursor.execute("""
                                            SELECT COUNT(*) FROM user_events 
                                            WHERE event_time = %s AND ip = %s
                                        """, (event_time, ip))
                                        if cursor.fetchone()[0] > 0:
                                            continue  # 如果已存在，跳过这条记录

                                        # 插入新记录
                                        cursor.execute("""
                                            INSERT INTO user_events 
                                            (event_time, username, ip, location, botnet_type, command, status)
                                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                                        """, (
                                            event_time,
                                            username,
                                            ip,
                                            location,
                                            botnet_type,
                                            "clear operation",
                                            "completed"
                                        ))
                                    except Exception as single_e:
                                        logger.warning(f"插入单条日志失败: {single_e}")
                                conn.commit()
                                cursor.close()
                                conn.close()
                except Exception as e:
                    logger.warning(f"轮询失败: {e}")
    except Exception as e:
        logger.error(f"poll_logs_and_store 错误: {e}")

# 替换原有的清理函数
@router.post("/clean-botnet")
async def clean_botnet(request: CleanBotnetRequest, current_user: dict = Depends(require_operator_or_admin)):
    try:
        # 获取操作者的真实IP和位置信息
        location = request.location
        botnet_type = request.botnet_type
        if request.operator_ip:
            try:
                location_info = await ip_query(request.operator_ip)
                if location_info and location_info.get('country_prov_city'):
                    location = location_info['country_prov_city'].replace('_', ' ')
            except Exception as e:
                logger.error(f"IP地理位置查询失败: {str(e)}")

        if botnet_type == 'asruex':
            async with httpx.AsyncClient() as client:
                await client.get("http://120.224.102.130:40153/start-clean-server")

            asyncio.create_task(poll_logs_and_store(
                username=request.username,
                location=location,
                botnet_type=botnet_type
            ))

        # 记录清除操作到日志
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        if request.target_machines:
            # 记录操作日志
            for machine in request.target_machines:
                cursor.execute("""
                    INSERT INTO user_events 
                    (event_time, username, ip, location, botnet_type, command)
                    VALUES (NOW(), %s, %s, %s, %s, %s)
                """, (
                    request.username,
                    machine,
                    location,
                    request.botnet_type,
                    f"{request.clean_method} operation"
                ))
        else:
            cursor.execute("""
                INSERT INTO user_events 
                (event_time, username, ip, location, botnet_type, command)
                VALUES (NOW(), %s, %s, %s, %s, %s)
            """, (
                request.username,
                request.operator_ip,
                location,
                request.botnet_type,
                f"{request.clean_method} operation"
            ))
        
        conn.commit()
        cursor.close()
        conn.close()

        # 立即启动清理任务，不等待结果
        task_id = f"{request.botnet_type}_{request.clean_method}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        asyncio.create_task(
            perform_botnet_cleanup(
                request.botnet_type,
                request.clean_method,
                request.target_machines
            )
        )
        
        # 立即返回响应
        return {
            "status": "success",
            "message": "Cleanup task started",
            "task_id": task_id
        }
        
    except Exception as e:
        logger.error(f"Error in clean-botnet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/botnet-info")
async def get_botnet_info():
    """获取所有僵尸网络的详细信息"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        cursor.execute("""
            SELECT name, display_name, description
            FROM botnet_types
            ORDER BY created_at
        """)
        
        results = cursor.fetchall()
        botnet_info = {
            row['name']: {
                'title': row['display_name'],
                'description': row['description']
            }
            for row in results
        }
        
        return {"status": "success", "data": botnet_info}
    except Exception as e:
        logger.error(f"Error fetching botnet info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()



# 添加获取支持的清理方法的接口
@router.get("/clean-methods/{botnet_type}")
async def get_clean_methods(botnet_type: str):
    """获取特定僵尸网络类型支持的清理方法"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        cursor.execute("SELECT clean_methods FROM botnet_types WHERE name = %s", (botnet_type,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Botnet type {botnet_type} not found")
            
        return {
            "status": "success",
            "data": {
                "botnet_type": botnet_type,
                "clean_methods": result['clean_methods'] or ["clear", "suppress", "reuse", "ddos"]  # 默认支持所有方法
            }
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting clean methods: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
