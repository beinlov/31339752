# -*- coding: utf-8 -*-
"""
数据导出API接口
支持导出botnet_nodes_和botnet_communications_表数据为CSV格式
"""

import csv
import io
import pymysql
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import logging
from datetime import datetime

from config import DB_CONFIG
from database.schema import get_node_table_ddl, get_communication_table_ddl

logger = logging.getLogger(__name__)
router = APIRouter()

# 允许的僵尸网络类型
ALLOWED_BOTNET_TYPES = ['asruex', 'moobot', 'mirai', 'gafgyt', 'tsunami']

def get_table_headers(table_type: str) -> list:
    """获取表头信息"""
    if table_type == 'nodes':
        return [
            'id', 'ip', 'longitude', 'latitude', 'country', 'province', 'city',
            'continent', 'isp', 'asn', 'status', 'first_seen', 'last_seen',
            'cleaned_time', 'communication_count', 'created_time', 'updated_at', 'is_china'
        ]
    elif table_type == 'communications':
        return [
            'id', 'node_id', 'ip', 'communication_time', 'received_at',
            'longitude', 'latitude', 'country', 'province', 'city',
            'continent', 'isp', 'asn', 'event_type', 'status', 'is_china'
        ]
    else:
        raise ValueError(f"Unsupported table type: {table_type}")

def escape_csv_value(value):
    """转义CSV值，处理特殊字符"""
    if value is None:
        return ''
    # 转换为字符串
    str_value = str(value)
    # 如果包含逗号、引号或换行符，需要用引号包围并转义内部引号
    if any(char in str_value for char in [',', '"', '\n', '\r']):
        escaped_value = str_value.replace('"', '""')
        return f'"{escaped_value}"'
    return str_value

def query_table_data(cursor, table_name: str, limit: Optional[int] = None):
    """查询表数据"""
    try:
        # 检查表是否存在
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() AND table_name = %s
        """, (table_name,))
        
        if cursor.fetchone()['count'] == 0:
            logger.warning(f"Table {table_name} does not exist")
            return []
        
        # 构建查询语句
        query = f"SELECT * FROM {table_name} ORDER BY id DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        return cursor.fetchall()
        
    except Exception as e:
        logger.error(f"Error querying table {table_name}: {e}")
        raise

@router.get("/export/csv")
async def export_botnet_data(
    botnet_type: str = Query(..., description="僵尸网络类型"),
    table_type: str = Query(..., description="表类型: nodes 或 communications"),
    limit: Optional[int] = Query(None, description="导出记录数限制，不限制则不传此参数")
):
    """
    导出僵尸网络数据为CSV格式
    
    参数:
    - botnet_type: 僵尸网络类型 (asruex, moobot, mirai, gafgyt, tsunami)
    - table_type: 表类型 (nodes: botnet_nodes_表, communications: botnet_communications_表)
    - limit: 可选，导出记录数限制
    """
    
    conn = None
    cursor = None
    
    try:
        # 验证参数
        if botnet_type not in ALLOWED_BOTNET_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的僵尸网络类型: {botnet_type}. 支持的类型: {', '.join(ALLOWED_BOTNET_TYPES)}"
            )
        
        if table_type not in ['nodes', 'communications']:
            raise HTTPException(
                status_code=400,
                detail="表类型必须是 'nodes' 或 'communications'"
            )
        
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 确定表名
        if table_type == 'nodes':
            table_name = f"botnet_nodes_{botnet_type}"
        else:
            table_name = f"botnet_communications_{botnet_type}"
        
        logger.info(f"Exporting data from {table_name}")
        
        # 查询数据
        data = query_table_data(cursor, table_name, limit)
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"表 {table_name} 中没有数据"
            )
        
        # 创建CSV内容
        output = io.StringIO()
        headers = get_table_headers(table_type)
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow(headers)
        
        # 写入数据行
        for row in data:
            csv_row = []
            for header in headers:
                value = row.get(header, '')
                csv_row.append(escape_csv_value(value))
            writer.writerow(csv_row)
        
        # 准备响应
        csv_content = output.getvalue()
        output.close()
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{botnet_type}_{table_type}_{timestamp}.csv"
        
        # 设置响应头
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'text/csv; charset=utf-8',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        
        logger.info(f"Successfully exported {len(data)} records from {table_name}")
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"导出数据时发生错误: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/export/csv/combined")
async def export_combined_botnet_data(
    botnet_type: str = Query(..., description="僵尸网络类型"),
    limit: Optional[int] = Query(None, description="每个表的导出记录数限制")
):
    """
    导出僵尸网络的完整数据（节点表 + 通信表）为单个CSV文件
    
    参数:
    - botnet_type: 僵尸网络类型 (asruex, moobot, mirai, gafgyt, tsunami)
    - limit: 可选，每个表的导出记录数限制
    """
    
    conn = None
    cursor = None
    
    try:
        # 验证参数
        if botnet_type not in ALLOWED_BOTNET_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的僵尸网络类型: {botnet_type}. 支持的类型: {', '.join(ALLOWED_BOTNET_TYPES)}"
            )
        
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询节点数据
        nodes_table = f"botnet_nodes_{botnet_type}"
        nodes_data = query_table_data(cursor, nodes_table, limit)
        
        # 查询通信数据
        comm_table = f"botnet_communications_{botnet_type}"
        comm_data = query_table_data(cursor, comm_table, limit)
        
        if not nodes_data and not comm_data:
            raise HTTPException(
                status_code=404,
                detail=f"僵尸网络 {botnet_type} 没有数据"
            )
        
        # 创建CSV内容
        output = io.StringIO()
        
        # 写入节点数据
        if nodes_data:
            output.write("=== 节点数据 (botnet_nodes_{}) ===\n".format(botnet_type))
            headers = get_table_headers('nodes')
            writer = csv.writer(output)
            writer.writerow(headers)
            
            for row in nodes_data:
                csv_row = []
                for header in headers:
                    value = row.get(header, '')
                    csv_row.append(escape_csv_value(value))
                writer.writerow(csv_row)
            
            output.write("\n")
        
        # 写入通信数据
        if comm_data:
            output.write("=== 通信数据 (botnet_communications_{}) ===\n".format(botnet_type))
            headers = get_table_headers('communications')
            writer = csv.writer(output)
            writer.writerow(headers)
            
            for row in comm_data:
                csv_row = []
                for header in headers:
                    value = row.get(header, '')
                    csv_row.append(escape_csv_value(value))
                writer.writerow(csv_row)
        
        # 准备响应
        csv_content = output.getvalue()
        output.close()
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{botnet_type}_combined_{timestamp}.csv"
        
        # 设置响应头
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'text/csv; charset=utf-8',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        
        total_records = (len(nodes_data) if nodes_data else 0) + (len(comm_data) if comm_data else 0)
        logger.info(f"Successfully exported combined data: {len(nodes_data) if nodes_data else 0} nodes + {len(comm_data) if comm_data else 0} communications from {botnet_type}")
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Combined export error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"导出合并数据时发生错误: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
