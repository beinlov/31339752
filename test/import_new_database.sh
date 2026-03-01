#!/bin/bash
# ============================================================
# 导入新数据库脚本（优化版）
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo
echo "============================================================"
echo "   导入新数据库"
echo "============================================================"
echo

# 检查新数据库文件
if [ ! -f "botnet.sql" ]; then
    echo -e "${RED}✗${NC} 找不到 botnet.sql 文件"
    exit 1
fi

FILE_SIZE=$(ls -lh botnet.sql | awk '{print $5}')
FILE_DATE=$(ls -l botnet.sql | awk '{print $6, $7, $8}')

echo "数据库文件信息:"
echo "  文件名: botnet.sql"
echo "  大小: $FILE_SIZE"
echo "  修改时间: $FILE_DATE"
echo

# 检查INSERT格式
SAMPLE_INSERT=$(grep "^INSERT INTO" botnet.sql | head -1)
if echo "$SAMPLE_INSERT" | grep -q "),($"; then
    echo -e "${GREEN}✓${NC} 检测到批量INSERT格式（快速）"
    USE_OPTIMIZATION=false
else
    echo -e "${YELLOW}!${NC} 检测到单行INSERT格式（慢）"
    echo "  建议使用优化导入（速度提升60倍）"
    USE_OPTIMIZATION=true
fi

echo
echo "导入选项:"
echo "  1. 快速导入（推荐）- 自动优化为批量INSERT"
echo "  2. 直接导入 - 使用原始文件（如果是单行INSERT会很慢）"
echo "  3. 取消"
echo

read -p "请选择 [1-3]: " choice

case $choice in
    1)
        echo
        echo -e "${BLUE}[快速导入模式]${NC}"
        echo
        
        # 步骤1: 删除旧数据库
        echo "步骤 1/4: 删除旧数据库..."
        docker exec mysql mysql -uroot -pMatrix123 -e "
            DROP DATABASE IF EXISTS botnet;
            CREATE DATABASE botnet CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        " 2>&1 | grep -v Warning
        echo -e "${GREEN}✓${NC} 旧数据库已删除，新数据库已创建"
        echo
        
        if [ "$USE_OPTIMIZATION" = true ]; then
            # 步骤2: 优化SQL文件
            echo "步骤 2/4: 优化SQL文件（提取并合并INSERT）..."
            echo "  这可能需要2-3分钟，请耐心等待..."
            
            # 提取建表语句
            python3 << 'PYTHON_SCRIPT'
import re
import sys

print("  正在分析SQL文件...")
schema_file = open('schema_new.sql', 'w', encoding='utf-8')
data_file = open('data_new_optimized.sql', 'w', encoding='utf-8')

# 写入头部
schema_file.write("USE botnet;\n")
schema_file.write("SET FOREIGN_KEY_CHECKS = 0;\n")
schema_file.write("SET NAMES utf8mb4;\n\n")

data_file.write("USE botnet;\n")
data_file.write("SET FOREIGN_KEY_CHECKS = 0;\n")
data_file.write("SET NAMES utf8mb4;\n")
data_file.write("SET autocommit = 0;\n\n")

in_create = False
create_buffer = []
current_table = None
values_buffer = []
BATCH_SIZE = 1000
line_count = 0
create_count = 0
insert_count = 0
batches = 0

print("  正在处理...")
with open('botnet.sql', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        line_count += 1
        if line_count % 500000 == 0:
            print(f"    已处理 {line_count:,} 行")
        
        stripped = line.strip()
        
        # CREATE TABLE
        if 'CREATE TABLE' in line:
            in_create = True
            create_buffer = [line]
            continue
        
        if in_create:
            create_buffer.append(line)
            if ';' in line:
                in_create = False
                schema_file.writelines(create_buffer)
                schema_file.write('\n')
                create_count += 1
                create_buffer = []
            continue
        
        # DROP TABLE
        if stripped.startswith('DROP TABLE'):
            schema_file.write(line)
            continue
        
        # INSERT
        match = re.match(r'INSERT INTO `([^`]+)` VALUES (.+);', line)
        if match:
            table_name = match.group(1)
            values = match.group(2)
            
            if current_table and current_table != table_name:
                if values_buffer:
                    data_file.write(f"INSERT INTO `{current_table}` VALUES\n")
                    data_file.write(',\n'.join(values_buffer))
                    data_file.write(';\nCOMMIT;\n\n')
                    batches += 1
                    values_buffer = []
            
            current_table = table_name
            values_buffer.append(values)
            insert_count += 1
            
            if len(values_buffer) >= BATCH_SIZE:
                data_file.write(f"INSERT INTO `{current_table}` VALUES\n")
                data_file.write(',\n'.join(values_buffer))
                data_file.write(';\nCOMMIT;\n\n')
                batches += 1
                values_buffer = []
        else:
            # 其他语句（SET, USE等）
            if stripped and not stripped.startswith('/*') and not stripped.startswith('--'):
                if 'INSERT' not in line and 'CREATE' not in line and 'DROP' not in line:
                    schema_file.write(line)

# 写入剩余buffer
if values_buffer and current_table:
    data_file.write(f"INSERT INTO `{current_table}` VALUES\n")
    data_file.write(',\n'.join(values_buffer))
    data_file.write(';\nCOMMIT;\n\n')
    batches += 1

data_file.write("SET FOREIGN_KEY_CHECKS = 1;\n")
data_file.write("SET autocommit = 1;\n")
schema_file.write("SET FOREIGN_KEY_CHECKS = 1;\n")

schema_file.close()
data_file.close()

print(f"\n  完成！")
print(f"    CREATE TABLE: {create_count}")
print(f"    INSERT语句: {insert_count:,}")
print(f"    优化批次: {batches:,}")
print(f"    压缩比: {insert_count/batches if batches > 0 else 0:.1f}x")
PYTHON_SCRIPT
            
            if [ $? -ne 0 ]; then
                echo -e "${RED}✗${NC} 优化失败"
                exit 1
            fi
            
            echo -e "${GREEN}✓${NC} SQL文件优化完成"
            echo
            
            SCHEMA_FILE="schema_new.sql"
            DATA_FILE="data_new_optimized.sql"
        else
            SCHEMA_FILE="botnet.sql"
            DATA_FILE="botnet.sql"
        fi
        
        # 步骤3: 创建表结构
        echo "步骤 3/4: 创建表结构..."
        docker exec -i mysql mysql -uroot -pMatrix123 < "$SCHEMA_FILE" 2>&1 | grep -v Warning | head -5
        
        TABLES=$(docker exec mysql mysql -uroot -pMatrix123 -e "USE botnet; SHOW TABLES;" 2>/dev/null | wc -l)
        TABLES=$((TABLES - 1))
        echo -e "${GREEN}✓${NC} 表结构创建完成（$TABLES 个表）"
        echo
        
        # 步骤4: 导入数据
        echo "步骤 4/4: 导入数据..."
        echo "  开始时间: $(date '+%H:%M:%S')"
        echo "  预计耗时: 5-10分钟"
        echo
        
        START_TIME=$(date +%s)
        
        docker exec -i mysql mysql -uroot -pMatrix123 --force botnet < "$DATA_FILE" 2>&1 | tee import_new.log &
        IMPORT_PID=$!
        
        echo "  导入进程PID: $IMPORT_PID"
        echo "  正在导入..."
        echo
        
        # 监控进度
        SECONDS=0
        while kill -0 $IMPORT_PID 2>/dev/null; do
            sleep 10
            ELAPSED=$SECONDS
            
            STATS=$(docker exec mysql mysql -uroot -pMatrix123 -e "
                SELECT 
                    COALESCE(SUM(table_rows), 0) as total,
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb
                FROM information_schema.tables 
                WHERE table_schema = 'botnet';
            " 2>/dev/null | tail -1)
            
            ROWS=$(echo $STATS | awk '{print $1}')
            SIZE=$(echo $STATS | awk '{print $2}')
            
            if [ "$ROWS" != "NULL" ] && [ "$ROWS" -gt 0 ]; then
                echo "  [${ELAPSED}s] 已导入 ${ROWS} 行 (${SIZE} MB)"
            fi
        done
        
        wait $IMPORT_PID
        
        END_TIME=$(date +%s)
        TOTAL_TIME=$((END_TIME - START_TIME))
        
        echo
        echo -e "${GREEN}✓${NC} 数据导入完成"
        echo
        ;;
    
    2)
        echo
        echo -e "${YELLOW}[直接导入模式]${NC}"
        echo -e "${YELLOW}警告: 如果是单行INSERT格式，导入可能需要4小时以上${NC}"
        echo
        
        read -p "确认继续? [y/N]: " confirm
        if [[ ! $confirm =~ ^[Yy]$ ]]; then
            echo "取消"
            exit 0
        fi
        
        echo "删除旧数据库..."
        docker exec mysql mysql -uroot -pMatrix123 -e "DROP DATABASE IF EXISTS botnet;" 2>&1 | grep -v Warning
        
        echo "导入新数据库..."
        START_TIME=$(date +%s)
        docker exec -i mysql mysql -uroot -pMatrix123 < botnet.sql 2>&1 | tee import_direct.log
        END_TIME=$(date +%s)
        TOTAL_TIME=$((END_TIME - START_TIME))
        ;;
    
    3)
        echo "取消"
        exit 0
        ;;
    
    *)
        echo -e "${RED}✗${NC} 无效选择"
        exit 1
        ;;
esac

# 最终验证
echo
echo "============================================================"
echo -e "   ${GREEN}导入完成！${NC}"
echo "============================================================"
echo

echo "数据库统计:"
docker exec mysql mysql -uroot -pMatrix123 -e "
SELECT 
    COUNT(*) as '表数量',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS '数据大小MB',
    SUM(table_rows) AS '总记录数'
FROM information_schema.tables 
WHERE table_schema = 'botnet';
" 2>&1 | grep -v Warning

echo
echo "总耗时: ${TOTAL_TIME}秒 ($(($TOTAL_TIME / 60))分$(($TOTAL_TIME % 60))秒)"
echo
echo "下一步:"
echo "  1. 检查数据: ./check_database_status.sh"
echo "  2. 启动服务: ./start_all_services.sh"
echo
