"""
僵尸网络可控性量化评估API
提供可控性等级管理和僵尸网络映射关系的增删改查功能
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
import pymysql
from pymysql.cursors import DictCursor
import logging
from config import DB_CONFIG, ALLOWED_BOTNET_TYPES

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# 数据模型定义
# ============================================================

class ControllabilityLevel(BaseModel):
    """可控性等级模型"""
    id: int
    level_name: str
    description: Optional[str] = None
    instruction_type: Optional[str] = None


class BotnetMapping(BaseModel):
    """僵尸网络映射模型"""
    id: int
    botnet_name: str
    level_id: int
    examples: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AddBotnetMappingRequest(BaseModel):
    """添加僵尸网络映射请求"""
    level_id: int = Field(..., ge=1, le=5, description="可控性等级ID(1-5)")
    botnet_names: List[str] = Field(..., min_items=1, description="僵尸网络名称列表")


class UpdateBotnetMappingRequest(BaseModel):
    """更新僵尸网络映射请求"""
    examples: Optional[str] = None
    notes: Optional[str] = None


# ============================================================
# 数据库连接函数
# ============================================================

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

@router.get("/controllability/levels", response_model=List[ControllabilityLevel])
async def get_controllability_levels():
    """
    获取所有可控性等级定义
    
    Returns:
        List[ControllabilityLevel]: 可控性等级列表
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


@router.get("/controllability/mappings", response_model=List[BotnetMapping])
async def get_botnet_mappings():
    """
    获取所有僵尸网络与可控性等级的映射关系
    
    Returns:
        List[BotnetMapping]: 映射关系列表
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        
        query = """
        SELECT 
            id, botnet_name, level_id, examples, notes,
            DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at,
            DATE_FORMAT(updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
        FROM botnet_controllability_mapping
        ORDER BY level_id, botnet_name
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        return results
        
    except Exception as e:
        logger.error(f"Error fetching botnet mappings: {e}")
        raise HTTPException(status_code=500, detail=f"获取映射关系失败: {str(e)}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/controllability/mappings/level/{level_id}", response_model=List[BotnetMapping])
async def get_botnet_mappings_by_level(level_id: int):
    """
    获取指定可控性等级的所有僵尸网络映射
    
    Args:
        level_id: 可控性等级ID (1-5)
    
    Returns:
        List[BotnetMapping]: 该等级的映射关系列表
    """
    if level_id < 1 or level_id > 5:
        raise HTTPException(status_code=400, detail="等级ID必须在1-5之间")
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        
        query = """
        SELECT 
            id, botnet_name, level_id, examples, notes,
            DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at,
            DATE_FORMAT(updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
        FROM botnet_controllability_mapping
        WHERE level_id = %s
        ORDER BY botnet_name
        """
        
        cursor.execute(query, (level_id,))
        results = cursor.fetchall()
        
        return results
        
    except Exception as e:
        logger.error(f"Error fetching botnet mappings for level {level_id}: {e}")
        raise HTTPException(status_code=500, detail=f"获取映射关系失败: {str(e)}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/controllability/mappings/botnet/{botnet_name}", response_model=List[BotnetMapping])
async def get_botnet_mappings_by_name(botnet_name: str):
    """
    获取指定僵尸网络的所有可控性等级映射
    
    Args:
        botnet_name: 僵尸网络名称
    
    Returns:
        List[BotnetMapping]: 该僵尸网络的映射关系列表
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        
        query = """
        SELECT 
            id, botnet_name, level_id, examples, notes,
            DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at,
            DATE_FORMAT(updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
        FROM botnet_controllability_mapping
        WHERE botnet_name = %s
        ORDER BY level_id
        """
        
        cursor.execute(query, (botnet_name,))
        results = cursor.fetchall()
        
        return results
        
    except Exception as e:
        logger.error(f"Error fetching mappings for botnet {botnet_name}: {e}")
        raise HTTPException(status_code=500, detail=f"获取映射关系失败: {str(e)}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.post("/controllability/mappings")
async def add_botnet_mappings(request: AddBotnetMappingRequest):
    """
    添加僵尸网络到指定可控性等级
    支持批量添加，如果某个僵尸网络已存在则跳过
    
    Args:
        request: 添加请求，包含等级ID和僵尸网络名称列表
    
    Returns:
        dict: 添加结果
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        added_count = 0
        skipped_count = 0
        errors = []
        
        for botnet_name in request.botnet_names:
            try:
                # 检查是否已存在
                check_query = """
                SELECT id FROM botnet_controllability_mapping
                WHERE botnet_name = %s AND level_id = %s
                """
                cursor.execute(check_query, (botnet_name, request.level_id))
                existing = cursor.fetchone()
                
                if existing:
                    skipped_count += 1
                    logger.info(f"Mapping already exists: {botnet_name} - Level {request.level_id}")
                    continue
                
                # 插入新映射
                insert_query = """
                INSERT INTO botnet_controllability_mapping 
                (botnet_name, level_id)
                VALUES (%s, %s)
                """
                cursor.execute(insert_query, (botnet_name, request.level_id))
                conn.commit()
                added_count += 1
                logger.info(f"Added mapping: {botnet_name} - Level {request.level_id}")
                
            except Exception as e:
                errors.append(f"{botnet_name}: {str(e)}")
                logger.error(f"Error adding mapping for {botnet_name}: {e}")
                continue
        
        return {
            "status": "success",
            "message": f"成功添加 {added_count} 个映射，跳过 {skipped_count} 个已存在的映射",
            "added": added_count,
            "skipped": skipped_count,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in add_botnet_mappings: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"添加映射失败: {str(e)}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.put("/controllability/mappings/{mapping_id}")
async def update_botnet_mapping(mapping_id: int, request: UpdateBotnetMappingRequest):
    """
    更新僵尸网络映射的备注信息
    
    Args:
        mapping_id: 映射记录ID
        request: 更新请求，包含示例和备注
    
    Returns:
        dict: 更新结果
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查映射是否存在
        check_query = "SELECT id FROM botnet_controllability_mapping WHERE id = %s"
        cursor.execute(check_query, (mapping_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="映射记录不存在")
        
        # 更新映射
        update_query = """
        UPDATE botnet_controllability_mapping
        SET examples = %s, notes = %s
        WHERE id = %s
        """
        cursor.execute(update_query, (request.examples, request.notes, mapping_id))
        conn.commit()
        
        logger.info(f"Updated mapping {mapping_id}")
        
        return {
            "status": "success",
            "message": "更新成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating mapping {mapping_id}: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.delete("/controllability/mappings/{mapping_id}")
async def delete_botnet_mapping(mapping_id: int):
    """
    删除僵尸网络映射关系
    
    Args:
        mapping_id: 映射记录ID
    
    Returns:
        dict: 删除结果
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查映射是否存在
        check_query = "SELECT botnet_name, level_id FROM botnet_controllability_mapping WHERE id = %s"
        cursor.execute(check_query, (mapping_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="映射记录不存在")
        
        botnet_name, level_id = result
        
        # 删除映射
        delete_query = "DELETE FROM botnet_controllability_mapping WHERE id = %s"
        cursor.execute(delete_query, (mapping_id,))
        conn.commit()
        
        logger.info(f"Deleted mapping {mapping_id}: {botnet_name} - Level {level_id}")
        
        return {
            "status": "success",
            "message": f"已删除 {botnet_name} 与等级 {level_id} 的映射关系"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting mapping {mapping_id}: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/controllability/stats")
async def get_controllability_stats():
    """
    获取可控性评估统计信息
    
    Returns:
        dict: 统计数据，包括各等级的僵尸网络数量
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        
        # 统计每个等级的僵尸网络数量（去重）
        query = """
        SELECT 
            l.id,
            l.level_name,
            COUNT(DISTINCT m.botnet_name) as botnet_count
        FROM controllability_levels l
        LEFT JOIN botnet_controllability_mapping m ON l.id = m.level_id
        GROUP BY l.id, l.level_name
        ORDER BY l.id
        """
        
        cursor.execute(query)
        level_stats = cursor.fetchall()
        
        # 统计总的僵尸网络数量（去重）
        total_query = """
        SELECT COUNT(DISTINCT botnet_name) as total
        FROM botnet_controllability_mapping
        """
        cursor.execute(total_query)
        total_result = cursor.fetchone()
        
        return {
            "level_stats": level_stats,
            "total_botnets": total_result['total'] if total_result else 0
        }
        
    except Exception as e:
        logger.error(f"Error fetching controllability stats: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/controllability/available-botnets")
async def get_available_botnets():
    """
    获取所有可用的僵尸网络类型
    从配置文件中读取，包含所有已配置的僵尸网络类型
    这样可以确保即使数据库中没有注册，也能在可控性评估中使用
    同时会合并数据库中已注册的僵尸网络类型
    
    Returns:
        dict: 包含所有可用僵尸网络类型的列表
    """
    conn = None
    cursor = None
    
    try:
        # 从配置文件获取所有僵尸网络类型
        config_botnets = set(ALLOWED_BOTNET_TYPES)
        
        # 从数据库获取已注册的僵尸网络类型
        try:
            conn = get_db_connection()
            cursor = conn.cursor(DictCursor)
            cursor.execute("SELECT name FROM botnet_types")
            db_botnets = {row['name'] for row in cursor.fetchall()}
            
            # 合并两个来源的僵尸网络类型
            all_botnets = config_botnets.union(db_botnets)
        except Exception as e:
            logger.warning(f"无法从数据库获取僵尸网络类型，仅使用配置文件: {e}")
            all_botnets = config_botnets
        
        # 转换为排序后的列表
        botnet_list = sorted(list(all_botnets))
        
        return {
            "status": "success",
            "data": botnet_list,
            "count": len(botnet_list)
        }
        
    except Exception as e:
        logger.error(f"Error fetching available botnets: {e}")
        raise HTTPException(status_code=500, detail=f"获取僵尸网络类型失败: {str(e)}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
