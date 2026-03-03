#!/usr/bin/env python3
import sqlite3

# 检查 reports.db 结构
conn = sqlite3.connect('reports.db')
cursor = conn.cursor()

# 获取所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Tables: {tables}\n")

# 检查每个表的结构和数据
for table in tables:
    table_name = table[0]
    print(f"=== Table: {table_name} ===")
    
    # 获取列信息
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print(f"Columns: {columns}\n")
    
    # 获取样本数据
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
    rows = cursor.fetchall()
    print(f"Sample data: {rows}\n")

conn.close()
