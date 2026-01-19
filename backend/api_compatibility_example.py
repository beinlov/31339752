"""
API兼容层示例代码
实现零前端改动的字段映射
"""

# ============================================
# 示例1: node.py 中的字段映射
# ============================================

@router.get("/node-details")
async def get_node_details(
    botnet_type: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=10, le=100000),
    status: Optional[str] = None,
    country: Optional[str] = None
):
    """
    获取节点详细信息 - 带字段兼容性映射
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        table_name = f"botnet_nodes_{botnet_type}"
        
        # 查询数据库（使用新字段名）
        query = f"""
            SELECT 
                id,
                ip,
                longitude,
                latitude,
                country,
                province,
                city,
                status,
                first_seen,      -- 新字段名
                last_seen,       -- 新字段名
                created_time,
                is_china
            FROM {table_name}
            WHERE 1=1
        """
        
        # ... 添加筛选条件 ...
        
        cursor.execute(query)
        nodes = cursor.fetchall()
        
        # ============================================
        # 关键代码：字段映射（兼容旧前端）
        # ============================================
        for node in nodes:
            # 数据库新字段 -> API旧字段（前端期望的字段名）
            node['active_time'] = node.pop('first_seen')  # first_seen -> active_time
            node['last_active'] = node.pop('last_seen')    # last_seen -> last_active
            
            # 格式化时间（如果需要）
            if node['active_time']:
                node['active_time'] = node['active_time'].strftime('%Y-%m-%d %H:%M:%S')
            if node['last_active']:
                node['last_active'] = node['last_active'].strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "nodes": nodes,  # 现在包含 active_time 和 last_active 字段
                "pagination": {
                    # ...
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


# ============================================
# 示例2: 更优雅的实现 - 使用辅助函数
# ============================================

def map_node_fields_for_api(node: dict) -> dict:
    """
    将数据库节点字段映射为API字段（向后兼容）
    
    Args:
        node: 数据库查询结果（包含新字段名）
    
    Returns:
        映射后的节点数据（包含旧字段名）
    """
    # 创建副本，避免修改原数据
    mapped = node.copy()
    
    # 字段映射
    field_mappings = {
        'first_seen': 'active_time',   # 数据库字段 -> API字段
        'last_seen': 'last_active'
    }
    
    for db_field, api_field in field_mappings.items():
        if db_field in mapped:
            value = mapped.pop(db_field)
            # 格式化时间
            if value and hasattr(value, 'strftime'):
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            mapped[api_field] = value
    
    return mapped


@router.get("/node-details-v2")
async def get_node_details_v2(
    botnet_type: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=10, le=100000)
):
    """使用辅助函数的版本"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(DictCursor)
        
        # ... 查询数据库 ...
        
        cursor.execute(query)
        nodes = cursor.fetchall()
        
        # 使用辅助函数进行字段映射
        mapped_nodes = [map_node_fields_for_api(node) for node in nodes]
        
        return {
            "code": 200,
            "data": {
                "nodes": mapped_nodes
            }
        }
    finally:
        # ... 清理资源 ...
        pass


# ============================================
# 示例3: 双字段支持（过渡方案）
# ============================================

def map_node_fields_dual_support(node: dict) -> dict:
    """
    双字段支持：同时返回新旧字段
    适用于平滑过渡期
    """
    mapped = node.copy()
    
    # 同时保留新旧字段
    if 'first_seen' in mapped:
        value = mapped['first_seen']
        if value and hasattr(value, 'strftime'):
            value_str = value.strftime('%Y-%m-%d %H:%M:%S')
            mapped['first_seen'] = value_str      # 新字段
            mapped['active_time'] = value_str     # 旧字段（兼容）
    
    if 'last_seen' in mapped:
        value = mapped['last_seen']
        if value and hasattr(value, 'strftime'):
            value_str = value.strftime('%Y-%m-%d %H:%M:%S')
            mapped['last_seen'] = value_str       # 新字段
            mapped['last_active'] = value_str     # 旧字段（兼容）
    
    return mapped


# ============================================
# 示例4: 使用装饰器实现字段映射
# ============================================

from functools import wraps

def api_compatibility(field_mappings: dict):
    """
    装饰器：自动进行字段映射
    
    Args:
        field_mappings: {数据库字段: API字段} 的映射字典
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 如果返回结果中包含 nodes 数据，进行字段映射
            if isinstance(result, dict) and 'data' in result and 'nodes' in result['data']:
                nodes = result['data']['nodes']
                
                for node in nodes:
                    for db_field, api_field in field_mappings.items():
                        if db_field in node:
                            value = node.pop(db_field)
                            # 格式化时间
                            if value and hasattr(value, 'strftime'):
                                value = value.strftime('%Y-%m-%d %H:%M:%S')
                            node[api_field] = value
            
            return result
        return wrapper
    return decorator


# 使用装饰器
@router.get("/node-details-v3")
@api_compatibility({
    'first_seen': 'active_time',
    'last_seen': 'last_active'
})
async def get_node_details_v3(botnet_type: str, page: int = 1):
    """使用装饰器的版本 - 代码更简洁"""
    # ... 正常的查询逻辑 ...
    # 返回的数据会自动进行字段映射
    return {
        "data": {
            "nodes": nodes  # 自动映射字段
        }
    }


# ============================================
# 示例5: 配置化字段映射
# ============================================

# config.py
API_FIELD_MAPPINGS = {
    'node': {
        # 数据库字段 -> API字段
        'first_seen': 'active_time',
        'last_seen': 'last_active',
        # 未来如果有其他字段需要映射，在这里添加
    }
}

# node.py
from config import API_FIELD_MAPPINGS

def apply_field_mapping(data: list, mapping_type: str = 'node') -> list:
    """
    应用配置化的字段映射
    
    Args:
        data: 节点数据列表
        mapping_type: 映射类型（从配置中获取）
    
    Returns:
        映射后的数据
    """
    mappings = API_FIELD_MAPPINGS.get(mapping_type, {})
    
    for item in data:
        for db_field, api_field in mappings.items():
            if db_field in item:
                value = item.pop(db_field)
                if value and hasattr(value, 'strftime'):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                item[api_field] = value
    
    return data


# ============================================
# 测试代码
# ============================================

def test_field_mapping():
    """测试字段映射功能"""
    
    # 模拟数据库返回的数据（新字段名）
    from datetime import datetime
    
    db_node = {
        'id': 1,
        'ip': '1.2.3.4',
        'first_seen': datetime(2024, 1, 1, 10, 0, 0),
        'last_seen': datetime(2024, 1, 8, 12, 30, 0),
        'country': '中国'
    }
    
    # 应用映射
    api_node = map_node_fields_for_api(db_node)
    
    # 验证结果
    assert 'active_time' in api_node
    assert 'last_active' in api_node
    assert 'first_seen' not in api_node
    assert 'last_seen' not in api_node
    assert api_node['active_time'] == '2024-01-01 10:00:00'
    assert api_node['last_active'] == '2024-01-08 12:30:00'
    
    print("✓ 字段映射测试通过")
    print(f"映射前: {db_node}")
    print(f"映射后: {api_node}")


if __name__ == '__main__':
    test_field_mapping()


# ============================================
# 使用建议
# ============================================

"""
推荐使用方案：

1. 小型项目：使用示例1（直接在接口中映射）
2. 中型项目：使用示例2（辅助函数）
3. 大型项目：使用示例4或5（装饰器或配置化）

迁移步骤：

1. 执行数据库迁移脚本
2. 在 node.py 中添加字段映射代码
3. 测试 API 接口返回
4. 验证前端功能正常
5. 部署

回滚方案：

如果出现问题，只需要：
1. 回滚后端代码
2. 恢复数据库备份（如果需要）

前端无需任何改动！
"""
