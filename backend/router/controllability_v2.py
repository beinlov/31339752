"""
僵尸网络可控性量化评估API v2
基于特征字段的新版本，支持自动等级计算
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
import pymysql
from pymysql.cursors import DictCursor
import logging
from config import DB_CONFIG, ALLOWED_BOTNET_TYPES

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# 数据模型定义
# ============================================================

class BotnetFeatures(BaseModel):
    """僵尸网络特征模型"""
    id: int
    botnet_name: str
    has_uninstall_instruction: bool = Field(description="是否有卸载或等效指令")
    has_download_instruction: bool = Field(description="是否有下载指令")
    has_command_execution: bool = Field(description="是否可执行任意系统命令")
    has_special_cleanup: bool = Field(description="是否可通过特定方法清除")
    notes: Optional[str] = None
    levels: List[int] = Field(description="自动计算的可控性等级列表")
    levels_display: str = Field(description="等级显示文本")


class UpdateBotnetFeaturesRequest(BaseModel):
    """更新僵尸网络特征请求"""
    has_uninstall_instruction: bool
    has_download_instruction: bool
    has_command_execution: bool
    has_special_cleanup: bool
    notes: Optional[str] = None


class ControllabilityLevel(BaseModel):
    """可控性等级定义"""
    id: int
    level_name: str
    description: str
    instruction_type: str


# ============================================================
# 辅助函数
# ============================================================

def calculate_levels(features: dict) -> Tuple[List[int], str]:
    """
    根据特征自动计算可控性等级
    
    规则：
    - 有卸载或等效指令 → 类别1
    - 有下载指令 → 类别2
    - 可执行任意系统命令 → 类别3
    - 仅可通过特定方法清除（前三个都没有）→ 类别4
    - 以上都没有 → 类别5
    
    Args:
        features: 包含四个特征字段的字典
    
    Returns:
        (等级列表, 等级显示文本)
    """
    levels = []
    
    # 检查各个特征
    if features.get('has_uninstall_instruction'):
        levels.append(1)
    
    if features.get('has_download_instruction'):
        levels.append(2)
    
    if features.get('has_command_execution'):
        levels.append(3)
    
    # 类别4：只有当前三个都没有，且有特殊清除方法时
    if (not features.get('has_uninstall_instruction') and 
        not features.get('has_download_instruction') and 
        not features.get('has_command_execution') and 
        features.get('has_special_cleanup')):
        levels.append(4)
    
    # 类别5：四个特征都没有
    if not levels:
        levels.append(5)
    
    # 生成显示文本
    if levels:
        levels_display = "、".join([f"类别{level}" for level in sorted(levels)])
    else:
        levels_display = "未分类"
    
    return sorted(levels), levels_display


def get_db_connection():
    """获取数据库连接"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")


# ============================================================
# API路由
# ============================================================

@router.get("/controllability-v2/levels", response_model=List[ControllabilityLevel])
async def get_controllability_levels():
    """
    获取所有可控性等级定义
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        
        query = """
        SELECT id, level_name, description, instruction_type
        FROM controllability_levels
        ORDER BY id
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        return results
        
    except Exception as e:
        logger.error(f"Error fetching controllability levels: {e}")
        raise HTTPException(status_code=500, detail=f"获取可控性等级失败: {str(e)}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/controllability-v2/features", response_model=List[BotnetFeatures])
async def get_all_botnet_features():
    """
    获取所有僵尸网络的特征信息，并自动计算等级
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        
        query = """
        SELECT 
            id, botnet_name, 
            has_uninstall_instruction,
            has_download_instruction,
            has_command_execution,
            has_special_cleanup,
            notes
        FROM botnet_controllability_features
        ORDER BY botnet_name
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # 为每条记录计算等级
        features_list = []
        for row in results:
            levels, levels_display = calculate_levels(row)
            features_list.append({
                **row,
                'levels': levels,
                'levels_display': levels_display
            })
        
        return features_list
        
    except Exception as e:
        logger.error(f"Error fetching botnet features: {e}")
        raise HTTPException(status_code=500, detail=f"获取僵尸网络特征失败: {str(e)}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/controllability-v2/features/{botnet_name}", response_model=BotnetFeatures)
async def get_botnet_features(botnet_name: str):
    """
    获取指定僵尸网络的特征信息
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        
        query = """
        SELECT 
            id, botnet_name, 
            has_uninstall_instruction,
            has_download_instruction,
            has_command_execution,
            has_special_cleanup,
            notes
        FROM botnet_controllability_features
        WHERE botnet_name = %s
        """
        
        cursor.execute(query, (botnet_name,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"僵尸网络 {botnet_name} 不存在")
        
        # 计算等级
        levels, levels_display = calculate_levels(result)
        
        return {
            **result,
            'levels': levels,
            'levels_display': levels_display
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching features for {botnet_name}: {e}")
        raise HTTPException(status_code=500, detail=f"获取特征失败: {str(e)}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.put("/controllability-v2/features/{botnet_name}")
async def update_botnet_features(botnet_name: str, request: UpdateBotnetFeaturesRequest):
    """
    更新指定僵尸网络的特征信息
    系统会自动根据新特征计算可控性等级
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查僵尸网络是否存在
        check_query = "SELECT id FROM botnet_controllability_features WHERE botnet_name = %s"
        cursor.execute(check_query, (botnet_name,))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"僵尸网络 {botnet_name} 不存在")
        
        # 更新特征
        update_query = """
        UPDATE botnet_controllability_features
        SET 
            has_uninstall_instruction = %s,
            has_download_instruction = %s,
            has_command_execution = %s,
            has_special_cleanup = %s,
            notes = %s
        WHERE botnet_name = %s
        """
        
        cursor.execute(update_query, (
            request.has_uninstall_instruction,
            request.has_download_instruction,
            request.has_command_execution,
            request.has_special_cleanup,
            request.notes,
            botnet_name
        ))
        
        conn.commit()
        
        # 计算新的等级
        features = {
            'has_uninstall_instruction': request.has_uninstall_instruction,
            'has_download_instruction': request.has_download_instruction,
            'has_command_execution': request.has_command_execution,
            'has_special_cleanup': request.has_special_cleanup,
        }
        levels, levels_display = calculate_levels(features)
        
        logger.info(f"Updated features for {botnet_name}, new levels: {levels_display}")
        
        return {
            "status": "success",
            "message": f"已更新 {botnet_name} 的特征信息",
            "botnet_name": botnet_name,
            "levels": levels,
            "levels_display": levels_display
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating features for {botnet_name}: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.post("/controllability-v2/features/{botnet_name}")
async def create_botnet_features(botnet_name: str, request: UpdateBotnetFeaturesRequest):
    """
    为新的僵尸网络创建特征记录
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查是否已存在
        check_query = "SELECT id FROM botnet_controllability_features WHERE botnet_name = %s"
        cursor.execute(check_query, (botnet_name,))
        
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"僵尸网络 {botnet_name} 已存在")
        
        # 插入新记录
        insert_query = """
        INSERT INTO botnet_controllability_features
        (botnet_name, has_uninstall_instruction, has_download_instruction,
         has_command_execution, has_special_cleanup, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            botnet_name,
            request.has_uninstall_instruction,
            request.has_download_instruction,
            request.has_command_execution,
            request.has_special_cleanup,
            request.notes
        ))
        
        conn.commit()
        
        # 计算等级
        features = {
            'has_uninstall_instruction': request.has_uninstall_instruction,
            'has_download_instruction': request.has_download_instruction,
            'has_command_execution': request.has_command_execution,
            'has_special_cleanup': request.has_special_cleanup,
        }
        levels, levels_display = calculate_levels(features)
        
        logger.info(f"Created features for {botnet_name}, levels: {levels_display}")
        
        return {
            "status": "success",
            "message": f"已创建 {botnet_name} 的特征记录",
            "botnet_name": botnet_name,
            "levels": levels,
            "levels_display": levels_display
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating features for {botnet_name}: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/controllability-v2/stats")
async def get_controllability_stats():
    """
    获取可控性评估统计信息
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        
        # 获取所有僵尸网络特征
        query = """
        SELECT 
            has_uninstall_instruction,
            has_download_instruction,
            has_command_execution,
            has_special_cleanup
        FROM botnet_controllability_features
        """
        
        cursor.execute(query)
        all_features = cursor.fetchall()
        
        # 统计各等级数量
        level_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for features in all_features:
            levels, _ = calculate_levels(features)
            for level in levels:
                level_counts[level] += 1
        
        # 总数
        total_query = "SELECT COUNT(*) as total FROM botnet_controllability_features"
        cursor.execute(total_query)
        total = cursor.fetchone()['total']
        
        return {
            "total_botnets": total,
            "level_counts": level_counts,
            "level_stats": [
                {"level": 1, "count": level_counts[1], "name": "自卸载级"},
                {"level": 2, "count": level_counts[2], "name": "代码执行级"},
                {"level": 3, "count": level_counts[3], "name": "命令执行级"},
                {"level": 4, "count": level_counts[4], "name": "非执行级"},
                {"level": 5, "count": level_counts[5], "name": "非清除级"}
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
