"""
一键清除接口路由
用于调用远端C2服务器的清除、查询、重置接口
"""
import logging
import requests
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
import pymysql
from pymysql.cursors import DictCursor
from config import DB_CONFIG, C2_CLEANUP_CONFIG
import urllib3
from datetime import date
import threading
import time

# 禁用SSL警告（因为使用HTTP协议）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


def get_botnet_c2_info(botnet_name: str) -> Optional[Dict]:
    """
    从数据库获取僵网的C2服务器信息
    
    Args:
        botnet_name: 僵网名称
        
    Returns:
        包含C2 IP等信息的字典，如果不存在则返回None
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 从server_management表查询C2 IP
        cursor.execute("""
            SELECT ip, location, status, Botnet_Name
            FROM server_management
            WHERE Botnet_Name = %s
        """, (botnet_name,))
        
        result = cursor.fetchone()
        return result
        
    except Exception as e:
        logger.error(f"查询C2信息失败: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def get_all_botnets_with_c2() -> List[Dict]:
    """
    获取所有僵网类型，并检查每个僵网是否有C2权限
    
    Returns:
        包含所有僵网及其C2权限状态的列表
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # 获取所有僵网类型
        cursor.execute("""
            SELECT name, display_name, description
            FROM botnet_types
            ORDER BY created_at
        """)
        botnets = cursor.fetchall()
        
        result = []
        for botnet in botnets:
            botnet_name = botnet['name']
            
            # 检查该僵网是否有C2服务器配置
            c2_info = get_botnet_c2_info(botnet_name)
            has_c2 = c2_info is not None and c2_info.get('ip')
            
            # 检查是否配置了清除接口路径
            has_paths = botnet_name in C2_CLEANUP_CONFIG['botnet_paths']
            
            result.append({
                'botnet_name': botnet_name,
                'display_name': botnet['display_name'],
                'description': botnet.get('description'),
                'has_c2_permission': has_c2 and has_paths,
                'c2_ip': c2_info.get('ip') if c2_info else None,
                'c2_status': c2_info.get('status') if c2_info else None,
                'reason': None if (has_c2 and has_paths) else (
                    '未配置C2服务器' if not has_c2 else '未配置操作接口'
                )
            })
        
        return result
        
    except Exception as e:
        logger.error(f"获取僵网列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询僵网列表失败: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def call_c2_api(c2_ip: str, botnet_name: str, action: str) -> Dict:
    """
    调用C2服务器的API接口
    
    Args:
        c2_ip: C2服务器IP地址
        botnet_name: 僵网名称
        action: 操作类型 (cleanup/status/reset)
        
    Returns:
        C2服务器的响应数据
    """
    try:
        # 检查僵网是否有配置的路径
        if botnet_name not in C2_CLEANUP_CONFIG['botnet_paths']:
            raise HTTPException(
                status_code=400, 
                detail=f"僵网 {botnet_name} 未配置操作接口"
            )
        
        # 检查操作类型是否有效
        if action not in ['cleanup', 'status', 'reset']:
            raise HTTPException(
                status_code=400, 
                detail=f"无效的操作类型: {action}，支持的操作: cleanup, status, reset"
            )
        
        # 获取操作路径
        action_path = C2_CLEANUP_CONFIG['botnet_paths'][botnet_name][action]
        
        # 根据端口选择协议（443使用HTTPS，其他使用HTTP）
        port = C2_CLEANUP_CONFIG['c2_port']
        protocol = 'https' if port == 443 else 'http'
        base_url = f"{protocol}://{c2_ip}:{port}"
        
        # 构建完整URL（如果路径前缀为空，则直接拼接action_path）
        path_prefix = C2_CLEANUP_CONFIG['c2_path_prefix']
        full_url = f"{base_url}{path_prefix}{action_path}"
        
        # 构建请求头
        headers = {
            'X-Auth-Token': C2_CLEANUP_CONFIG['auth_token'],
            'X-Safety-Code': C2_CLEANUP_CONFIG['safety_code']
        }
        
        logger.info(f"调用C2接口: {full_url}")
        
        # 发送POST请求
        response = requests.post(
            full_url,
            headers=headers,
            timeout=C2_CLEANUP_CONFIG['request_timeout'],
            verify=C2_CLEANUP_CONFIG['verify_ssl']
        )
        
        # 检查响应状态
        response.raise_for_status()
        
        # 解析JSON响应
        result = response.json()
        logger.info(f"C2响应: {result}")
        
        return result
        
    except requests.exceptions.Timeout:
        logger.error(f"C2服务器请求超时: {c2_ip}")
        raise HTTPException(status_code=504, detail="C2服务器请求超时")
    except requests.exceptions.ConnectionError:
        logger.error(f"无法连接到C2服务器: {c2_ip}")
        raise HTTPException(status_code=503, detail="无法连接到C2服务器")
    except requests.exceptions.HTTPError as e:
        logger.error(f"C2服务器返回错误: {e}")
        raise HTTPException(status_code=502, detail=f"C2服务器错误: {str(e)}")
    except ValueError as e:
        logger.error(f"C2响应解析失败: {e}")
        raise HTTPException(status_code=502, detail="C2服务器响应格式错误")
    except Exception as e:
        logger.error(f"调用C2接口失败: {e}")
        raise HTTPException(status_code=500, detail=f"调用C2接口失败: {str(e)}")


def update_timeset_after_cleanup(botnet_name: str):
    """
    清除操作后智能更新 timeset 表
    比较 timeset.updated_at 和 botnet_nodes.updated_at，只更新过期的日期
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        node_table = f"botnet_nodes_{botnet_name}"
        timeset_table = f"botnet_timeset_{botnet_name}"
        
        # 检查 nodes 表是否存在
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = %s
        """, (node_table,))
        
        if cursor.fetchone()['count'] == 0:
            logger.warning(f"{botnet_name} 的 nodes 表不存在，跳过更新")
            return False
        
        # 获取今天的日期
        cursor.execute("SELECT CURDATE() as today")
        today = cursor.fetchone()['today']
        
        # 获取一个月前的日期
        cursor.execute("SELECT DATE_SUB(CURDATE(), INTERVAL 30 DAY) as month_ago")
        month_ago = cursor.fetchone()['month_ago']
        
        # 生成一个月内所有日期（包括今天）
        cursor.execute(f"""
            SELECT DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 30 DAY), INTERVAL seq DAY) as date
            FROM (
                SELECT 0 as seq UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 
                UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10 UNION SELECT 11 
                UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15 UNION SELECT 16 UNION SELECT 17 
                UNION SELECT 18 UNION SELECT 19 UNION SELECT 20 UNION SELECT 21 UNION SELECT 22 UNION SELECT 23 
                UNION SELECT 24 UNION SELECT 25 UNION SELECT 26 UNION SELECT 27 UNION SELECT 28 UNION SELECT 29 
                UNION SELECT 30
            ) numbers
            WHERE DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 30 DAY), INTERVAL seq DAY) <= CURDATE()
        """)
        all_dates = [row['date'] for row in cursor.fetchall()]
        
        # 查询 timeset 表中已存在的日期
        cursor.execute(f"""
            SELECT date FROM {timeset_table}
            WHERE date >= %s AND date <= %s
        """, (month_ago, today))
        existing_dates = set(row['date'] for row in cursor.fetchall())
        
        updated_count = 0
        skipped_count = 0
        
        # 对每个日期进行处理
        for date_obj in all_dates:
            date_str = date_obj.strftime('%Y-%m-%d') if hasattr(date_obj, 'strftime') else str(date_obj)
            
            # 如果不是今天且已存在，跳过
            if date_obj != today and date_obj in existing_dates:
                skipped_count += 1
                logger.info(f"{botnet_name} {date_str}: 已存在历史数据，跳过更新")
                continue
            
            # 统计该日期及之前所有 updated_at 的节点状态（累加模式）
            cursor.execute(f"""
                SELECT 
                    COUNT(DISTINCT ip) as total_ips,
                    COUNT(DISTINCT CASE WHEN status = 'active' THEN ip END) as active_ips,
                    COUNT(DISTINCT CASE WHEN status = 'cleaned' THEN ip END) as cleaned_ips,
                    COUNT(DISTINCT CASE WHEN country = '中国' THEN ip END) as china_total,
                    COUNT(DISTINCT CASE WHEN country = '中国' AND status = 'active' THEN ip END) as china_active,
                    COUNT(DISTINCT CASE WHEN country = '中国' AND status = 'cleaned' THEN ip END) as china_cleaned
                FROM {node_table}
                WHERE DATE(updated_at) <= %s
            """, (date_str,))
            
            stats = cursor.fetchone()
            
            global_count = int(stats['total_ips'] or 0)
            global_active = int(stats['active_ips'] or 0)
            global_cleaned = int(stats['cleaned_ips'] or 0)
            china_count = int(stats['china_total'] or 0)
            china_active = int(stats['china_active'] or 0)
            china_cleaned = int(stats['china_cleaned'] or 0)
            
            # 插入或更新该日期的 timeset 表
            cursor.execute(f"""
                INSERT INTO {timeset_table} (date, global_count, china_count, global_active, china_active, global_cleaned, china_cleaned)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    global_count = %s,
                    china_count = %s,
                    global_active = %s,
                    china_active = %s,
                    global_cleaned = %s,
                    china_cleaned = %s,
                    updated_at = CURRENT_TIMESTAMP
            """, (date_str, global_count, china_count, global_active, china_active, global_cleaned, china_cleaned,
                  global_count, china_count, global_active, china_active, global_cleaned, china_cleaned))
            
            updated_count += 1
            logger.info(f"{botnet_name} {date_str}: 全球{global_count}(活跃{global_active},清除{global_cleaned}), 中国{china_count}(活跃{china_active},清除{china_cleaned})")
        
        conn.commit()
        logger.info(f"{botnet_name}: 共更新 {updated_count} 个日期，跳过 {skipped_count} 个已存在的历史日期")
        return True
        
    except Exception as e:
        logger.error(f"更新 timeset 失败: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@router.get("/cleanup/check-permissions")
async def check_cleanup_permissions():
    """
    检查所有僵网的C2清除权限
    
    Returns:
        所有僵网的权限状态列表
    """
    try:
        botnets = get_all_botnets_with_c2()
        
        return {
            "status": "success",
            "message": f"共查询到 {len(botnets)} 个僵网",
            "data": {
                "botnets": botnets,
                "total_count": len(botnets),
                "with_permission": len([b for b in botnets if b['has_c2_permission']]),
                "without_permission": len([b for b in botnets if not b['has_c2_permission']])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查权限失败: {e}")
        raise HTTPException(status_code=500, detail=f"检查权限失败: {str(e)}")


@router.post("/cleanup/execute/{botnet_name}/{action}")
async def execute_cleanup_action(botnet_name: str, action: str):
    """
    执行清除操作（清除/查询/重置）
    
    Args:
        botnet_name: 僵网名称
        action: 操作类型 (cleanup/status/reset)
        
    Returns:
        操作结果
    """
    try:
        # 验证操作类型
        if action not in ['cleanup', 'status', 'reset']:
            raise HTTPException(
                status_code=400,
                detail=f"无效的操作类型: {action}"
            )
        
        # 获取C2信息
        c2_info = get_botnet_c2_info(botnet_name)
        
        if not c2_info or not c2_info.get('ip'):
            raise HTTPException(
                status_code=403,
                detail=f"僵网 {botnet_name} 没有C2权限，请联系管理员配置C2服务器"
            )
        
        c2_ip = c2_info['ip']
        
        # 调用C2 API
        c2_response = call_c2_api(c2_ip, botnet_name, action)
        
        # 如果是清除操作，执行成功后在后台循环更新 timeset 表1分钟
        if action == 'cleanup' and c2_response.get('status') == 'success':
            logger.info(f"清除操作成功，启动后台循环更新 {botnet_name} 的 timeset 数据（1分钟）...")
            # 在后台线程中循环更新1分钟
            def update_loop():
                end_time = time.time() + 60  # 1分钟后停止
                update_count = 0
                while time.time() < end_time:
                    try:
                        update_timeset_after_cleanup(botnet_name)
                        update_count += 1
                        logger.info(f"[{botnet_name}] 第 {update_count} 次更新完成，剩余时间: {int(end_time - time.time())} 秒")
                    except Exception as e:
                        logger.error(f"[{botnet_name}] 循环更新失败: {e}")
                    time.sleep(5)  # 每5秒更新一次
                logger.info(f"[{botnet_name}] 循环更新结束，共执行 {update_count} 次")
            
            thread = threading.Thread(target=update_loop, daemon=True)
            thread.start()
        
        # 操作类型的中文映射
        action_names = {
            'cleanup': '清除',
            'status': '查询状态',
            'reset': '重置'
        }
        
        return {
            "status": "success",
            "message": f"成功执行 {action_names.get(action, action)} 操作",
            "data": {
                "botnet_name": botnet_name,
                "action": action,
                "c2_ip": c2_ip,
                "c2_response": c2_response
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行清除操作失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行操作失败: {str(e)}")


@router.get("/cleanup/botnet/{botnet_name}/info")
async def get_botnet_cleanup_info(botnet_name: str):
    """
    获取单个僵网的清除信息
    
    Args:
        botnet_name: 僵网名称
        
    Returns:
        僵网的C2信息和权限状态
    """
    try:
        c2_info = get_botnet_c2_info(botnet_name)
        has_c2 = c2_info is not None and c2_info.get('ip')
        has_paths = botnet_name in C2_CLEANUP_CONFIG['botnet_paths']
        
        return {
            "status": "success",
            "data": {
                "botnet_name": botnet_name,
                "has_c2_permission": has_c2 and has_paths,
                "c2_ip": c2_info.get('ip') if c2_info else None,
                "c2_status": c2_info.get('status') if c2_info else None,
                "c2_location": c2_info.get('location') if c2_info else None,
                "available_actions": ['cleanup', 'status', 'reset'] if (has_c2 and has_paths) else [],
                "reason": None if (has_c2 and has_paths) else (
                    '未配置C2服务器' if not has_c2 else '未配置操作接口'
                )
            }
        }
        
    except Exception as e:
        logger.error(f"获取僵网信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取僵网信息失败: {str(e)}")
