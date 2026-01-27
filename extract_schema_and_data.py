#!/usr/bin/env python3
"""
从botnet.sql中分离建表语句和数据插入语句
"""
import sys

print("开始处理botnet.sql...")
print("这可能需要几分钟，请耐心等待...")

schema_file = open('schema_only.sql', 'w', encoding='utf-8')
data_file = open('data_only.sql', 'w', encoding='utf-8')

# 写入文件头
schema_file.write("-- 数据库建表脚本\n")
schema_file.write("-- 自动从botnet.sql提取\n\n")
schema_file.write("USE botnet;\n")
schema_file.write("SET FOREIGN_KEY_CHECKS = 0;\n")
schema_file.write("SET NAMES utf8mb4;\n\n")

data_file.write("-- 数据插入脚本\n")
data_file.write("-- 自动从botnet.sql提取\n\n")
data_file.write("USE botnet;\n")
data_file.write("SET FOREIGN_KEY_CHECKS = 0;\n")
data_file.write("SET NAMES utf8mb4;\n\n")

# 状态机
in_create_table = False
create_buffer = []
line_count = 0
create_count = 0
insert_count = 0

with open('botnet.sql', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        line_count += 1
        
        # 进度显示
        if line_count % 100000 == 0:
            print(f"  已处理 {line_count:,} 行 (CREATE: {create_count}, INSERT: {insert_count})")
        
        # 检测CREATE TABLE开始
        if line.strip().startswith('CREATE TABLE'):
            in_create_table = True
            create_buffer = [line]
            continue
        
        # 如果在CREATE TABLE块中
        if in_create_table:
            create_buffer.append(line)
            # 检测CREATE TABLE结束（以分号结尾）
            if ';' in line:
                in_create_table = False
                schema_file.writelines(create_buffer)
                schema_file.write('\n')
                create_count += 1
                create_buffer = []
            continue
        
        # DROP TABLE语句
        if line.strip().startswith('DROP TABLE'):
            schema_file.write(line)
            if ';' not in line:
                # 多行DROP TABLE
                next_line = next(f, '')
                schema_file.write(next_line)
            schema_file.write('\n')
            continue
        
        # INSERT语句
        if line.strip().startswith('INSERT INTO'):
            data_file.write(line)
            insert_count += 1
            continue

# 写入文件尾
schema_file.write("\nSET FOREIGN_KEY_CHECKS = 1;\n")
data_file.write("\nSET FOREIGN_KEY_CHECKS = 1;\n")

schema_file.close()
data_file.close()

print(f"\n完成！")
print(f"  总行数: {line_count:,}")
print(f"  CREATE TABLE语句: {create_count}")
print(f"  INSERT语句: {insert_count:,}")
print(f"\n生成文件:")
print(f"  schema_only.sql - 建表脚本")
print(f"  data_only.sql - 数据插入脚本")
