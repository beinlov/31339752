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
    获取所有僵网及其C2权限状态
    
    Returns:
        僵网列表，每个包含名称、显示名、C2状态等信息
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
            
            # 查询是否有C2 IP
            c2_info = get_botnet_c2_info(botnet_name)
            has_c2 = c2_info is not None and c2_info.get('ip')
            
            # 检查是否在配置中定义了操作路径
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
        
        # 构建完整URL
        base_url = f"http://{c2_ip}:{C2_CLEANUP_CONFIG['c2_port']}"
        full_url = f"{base_url}{C2_CLEANUP_CONFIG['c2_path_prefix']}{action_path}"
        
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
