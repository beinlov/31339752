#!/usr/bin/env python3
"""
合并单行INSERT为批量INSERT
将 2,838,045 个单行INSERT合并为批量INSERT（每1000行一批）
"""
import sys
import re

print("开始合并INSERT语句...")
print("这将大幅提升导入速度！")
print()

output_file = open('data_optimized.sql', 'w', encoding='utf-8')

# 写入文件头
output_file.write("-- 优化后的数据插入脚本（批量INSERT）\n")
output_file.write("-- 自动从data_only.sql优化生成\n\n")
output_file.write("USE botnet;\n")
output_file.write("SET FOREIGN_KEY_CHECKS = 0;\n")
output_file.write("SET NAMES utf8mb4;\n")
output_file.write("SET autocommit = 0;\n\n")  # 禁用自动提交

current_table = None
values_buffer = []
BATCH_SIZE = 1000  # 每1000行合并一次
total_lines = 0
batches = 0

print("批量大小: 1000行/批")
print("开始处理...\n")

with open('data_only.sql', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        total_lines += 1
        
        # 进度显示
        if total_lines % 100000 == 0:
            print(f"  已处理 {total_lines:,} 行, 生成 {batches:,} 个批次")
        
        # 跳过注释和空行
        stripped = line.strip()
        if not stripped or stripped.startswith('--') or stripped.startswith('/*') or stripped.startswith('SET') or stripped.startswith('USE'):
            output_file.write(line)
            continue
        
        # 匹配 INSERT INTO `table_name` VALUES (...)
        match = re.match(r'INSERT INTO `([^`]+)` VALUES (.+);', line)
        if not match:
            # 不是INSERT语句，直接写入
            output_file.write(line)
            continue
        
        table_name = match.group(1)
        values = match.group(2)
        
        # 如果表名改变，刷新之前的buffer
        if current_table and current_table != table_name:
            if values_buffer:
                # 写入批量INSERT
                output_file.write(f"INSERT INTO `{current_table}` VALUES\n")
                output_file.write(',\n'.join(values_buffer))
                output_file.write(';\n')
                output_file.write('COMMIT;\n\n')  # 提交事务
                batches += 1
                values_buffer = []
        
        current_table = table_name
        values_buffer.append(values)
        
        # 达到批量大小，写入
        if len(values_buffer) >= BATCH_SIZE:
            output_file.write(f"INSERT INTO `{current_table}` VALUES\n")
            output_file.write(',\n'.join(values_buffer))
            output_file.write(';\n')
            output_file.write('COMMIT;\n\n')  # 提交事务
            batches += 1
            values_buffer = []

# 写入剩余的buffer
if values_buffer and current_table:
    output_file.write(f"INSERT INTO `{current_table}` VALUES\n")
    output_file.write(',\n'.join(values_buffer))
    output_file.write(';\n')
    output_file.write('COMMIT;\n\n')
    batches += 1

output_file.write("\nSET FOREIGN_KEY_CHECKS = 1;\n")
output_file.write("SET autocommit = 1;\n")
output_file.close()

print(f"\n完成！")
print(f"  原始INSERT语句: {total_lines:,}")
print(f"  优化后批次数: {batches:,}")
print(f"  压缩比: {total_lines/batches:.1f}x")
print(f"\n生成文件: data_optimized.sql")
print(f"\n预期导入速度提升: 100-200倍！")
