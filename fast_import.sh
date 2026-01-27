#!/bin/bash
# 超快速数据库导入

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo
echo "============================================================"
echo "   超快速数据库导入（批量INSERT优化）"
echo "============================================================"
echo

START_TIME=$(date +%s)

# 步骤1: 清空并重建数据库
echo -e "${BLUE}[1/3]${NC} 清空并重建数据库..."
docker exec mysql mysql -uroot -pMatrix123 -e "
DROP DATABASE IF EXISTS botnet;
CREATE DATABASE botnet CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
" 2>&1 | grep -v Warning
echo -e "${GREEN}✓${NC} 数据库已重建"
echo

# 步骤2: 创建表结构
echo -e "${BLUE}[2/3]${NC} 创建表结构..."
docker exec -i mysql mysql -uroot -pMatrix123 < schema_only.sql 2>&1 | grep -v Warning | head -5
echo -e "${GREEN}✓${NC} 表结构创建完成"

TABLES=$(docker exec mysql mysql -uroot -pMatrix123 -e "USE botnet; SHOW TABLES;" 2>/dev/null | wc -l)
TABLES=$((TABLES - 1))
echo "  创建了 $TABLES 个表"
echo

# 步骤3: 批量导入数据
echo -e "${BLUE}[3/3]${NC} 批量导入数据（优化版）..."
echo "数据量: 2,871个批次 (每批~1000行)"
echo "预计时间: 2-3分钟"
echo

# 后台导入
docker exec -i mysql mysql -uroot -pMatrix123 botnet < data_optimized.sql 2>&1 | tee fast_import.log &
IMPORT_PID=$!

echo "导入进程PID: $IMPORT_PID"
echo "正在导入..."
echo

# 监控进度
SECONDS=0
LAST_ROWS=0
while kill -0 $IMPORT_PID 2>/dev/null; do
    sleep 5
    ELAPSED=$SECONDS
    
    # 查询当前数据量
    CURRENT=$(docker exec mysql mysql -uroot -pMatrix123 -e "
        SELECT 
            COALESCE(SUM(table_rows), 0) as total,
            ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb
        FROM information_schema.tables 
        WHERE table_schema = 'botnet';
    " 2>/dev/null | tail -1)
    
    TOTAL_ROWS=$(echo $CURRENT | awk '{print $1}')
    SIZE_MB=$(echo $CURRENT | awk '{print $2}')
    
    # 计算速度
    if [ "$TOTAL_ROWS" != "NULL" ] && [ "$TOTAL_ROWS" -gt 0 ]; then
        RATE=$((($TOTAL_ROWS - $LAST_ROWS) / 5))
        LAST_ROWS=$TOTAL_ROWS
        echo "  [${ELAPSED}s] 已导入 ${TOTAL_ROWS} 行 (${SIZE_MB} MB) | 速度: ${RATE} 行/秒"
    fi
done

wait $IMPORT_PID

# 完成
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

echo
echo "============================================================"
echo -e "   ${GREEN}导入完成！${NC}"
echo "============================================================"
echo

# 最终统计
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
echo -e "${GREEN}✓${NC} 数据库导入完成！"
echo
