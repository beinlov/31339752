#!/bin/bash
# ============================================================
# 优化的数据库导入脚本
# 分两步：1. 先建表  2. 再导入数据
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo
echo "============================================================"
echo "   优化数据库导入（两步法）"
echo "============================================================"
echo

# 检查文件
if [ ! -f "schema_only.sql" ] || [ ! -f "data_only.sql" ]; then
    echo -e "${RED}✗${NC} 缺少必要文件"
    echo "请先运行: python3 extract_schema_and_data.py"
    exit 1
fi

echo "文件大小:"
ls -lh schema_only.sql data_only.sql
echo

# 询问是否继续
read -p "是否开始导入? [y/N]: " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "取消"
    exit 0
fi

# 记录开始时间
START_TIME=$(date +%s)

# ============================================================
# 第1步: 建表（快速）
# ============================================================
echo
echo -e "${BLUE}[步骤 1/2]${NC} 创建表结构..."
echo "预计时间: < 10秒"

docker exec -i mysql mysql -uroot -pMatrix123 < schema_only.sql 2>&1 | grep -v Warning | head -20

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} 表结构创建成功"
else
    echo -e "${RED}✗${NC} 表结构创建失败"
    exit 1
fi

# 显示创建的表
TABLES=$(docker exec mysql mysql -uroot -pMatrix123 -e "USE botnet; SHOW TABLES;" 2>/dev/null | wc -l)
TABLES=$((TABLES - 1))
echo "  已创建 $TABLES 个表"

# ============================================================
# 第2步: 导入数据（主要时间）
# ============================================================
echo
echo -e "${BLUE}[步骤 2/2]${NC} 导入数据..."
echo "数据量: 283万条INSERT语句"
echo "预计时间: 2-4分钟（优化后的MySQL）"
echo

# 显示导入提示
echo -e "${YELLOW}提示${NC}: 可以在另一个终端运行以下命令监控进度:"
echo "  watch -n 5 './check_database_status.sh'"
echo

# 开始导入（后台）
docker exec -i mysql mysql -uroot -pMatrix123 --force botnet < data_only.sql 2>&1 | tee import_data.log &
IMPORT_PID=$!

echo "导入进程PID: $IMPORT_PID"
echo

# 等待并显示进度
echo "正在导入..."
SECONDS=0
while kill -0 $IMPORT_PID 2>/dev/null; do
    sleep 10
    ELAPSED=$SECONDS
    
    # 查询当前数据量
    TOTAL_ROWS=$(docker exec mysql mysql -uroot -pMatrix123 -e "
        SELECT SUM(table_rows) as total 
        FROM information_schema.tables 
        WHERE table_schema = 'botnet';
    " 2>/dev/null | tail -1)
    
    SIZE_MB=$(docker exec mysql mysql -uroot -pMatrix123 -e "
        SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb 
        FROM information_schema.tables 
        WHERE table_schema = 'botnet';
    " 2>/dev/null | tail -1)
    
    echo "  [${ELAPSED}s] 已导入约 ${TOTAL_ROWS} 行, 数据大小: ${SIZE_MB} MB"
done

# 等待进程完成
wait $IMPORT_PID
EXIT_CODE=$?

# ============================================================
# 完成
# ============================================================
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

echo
echo "============================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "   ${GREEN}导入完成！${NC}"
else
    echo -e "   ${YELLOW}导入完成（有部分错误）${NC}"
fi
echo "============================================================"
echo

# 最终统计
echo "导入统计:"
docker exec mysql mysql -uroot -pMatrix123 -e "
USE botnet;
SELECT 
    COUNT(*) as '表数量',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS '数据大小MB',
    SUM(table_rows) AS '总记录数'
FROM information_schema.tables 
WHERE table_schema = 'botnet';
" 2>&1 | grep -v Warning

echo
echo "耗时: ${TOTAL_TIME}秒 ($(($TOTAL_TIME / 60))分$(($TOTAL_TIME % 60))秒)"
echo
echo "下一步:"
echo "  1. 验证数据: ./check_database_status.sh"
echo "  2. 启动服务: ./start_all_services.sh"
echo
