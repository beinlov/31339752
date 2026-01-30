#!/bin/bash
# ============================================================
# 数据库状态检查脚本
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo
echo "============================================================"
echo "   数据库状态检查"
echo "============================================================"
echo

# 检查MySQL容器
echo -e "${BLUE}[MySQL容器状态]${NC}"
if sudo docker ps | grep -q mysql; then
    echo -e "  ${GREEN}✓${NC} MySQL容器运行中"
else
    echo -e "  ${RED}✗${NC} MySQL容器未运行"
    exit 1
fi
echo

# 检查数据库连接
echo -e "${BLUE}[数据库连接]${NC}"
if sudo docker exec mysql mysql -uroot -pMatrix123 -e "SELECT 1" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} 数据库连接正常"
else
    echo -e "  ${RED}✗${NC} 数据库连接失败"
    exit 1
fi
echo

# 检查botnet数据库
echo -e "${BLUE}[Botnet数据库]${NC}"
DB_EXISTS=$(sudo docker exec mysql mysql -uroot -pMatrix123 -e "SHOW DATABASES LIKE 'botnet';" 2>/dev/null | grep botnet)
if [ ! -z "$DB_EXISTS" ]; then
    echo -e "  ${GREEN}✓${NC} botnet数据库存在"
else
    echo -e "  ${RED}✗${NC} botnet数据库不存在"
    exit 1
fi
echo

# 检查表数量
echo -e "${BLUE}[数据表统计]${NC}"
TABLE_COUNT=$(sudo docker exec mysql mysql -uroot -pMatrix123 -e "USE botnet; SHOW TABLES;" 2>/dev/null | wc -l)
TABLE_COUNT=$((TABLE_COUNT - 1))  # 减去表头
echo "  总表数: $TABLE_COUNT"
echo

# 检查关键表
echo -e "${BLUE}[关键表检查]${NC}"
TABLES=(
    "botnet_nodes_asruex"
    "botnet_nodes_mozi"
    "botnet_communications_asruex"
    "botnet_communications_mozi"
    "users"
    "user_events"
)

for table in "${TABLES[@]}"; do
    if sudo docker exec mysql mysql -uroot -pMatrix123 -e "USE botnet; SHOW TABLES LIKE '$table';" 2>/dev/null | grep -q "$table"; then
        # 获取行数
        ROW_COUNT=$(sudo docker exec mysql mysql -uroot -pMatrix123 -e "USE botnet; SELECT COUNT(*) FROM $table;" 2>/dev/null | tail -1)
        if [ "$ROW_COUNT" -gt 0 ]; then
            echo -e "  ${GREEN}✓${NC} $table (${ROW_COUNT} 行)"
        else
            echo -e "  ${YELLOW}!${NC} $table (0 行 - 空表)"
        fi
    else
        echo -e "  ${RED}✗${NC} $table (不存在)"
    fi
done
echo

# 检查数据总量
echo -e "${BLUE}[数据统计]${NC}"
echo "正在统计各表数据量..."
sudo docker exec mysql mysql -uroot -pMatrix123 -e "
USE botnet;
SELECT 
    table_name AS '表名',
    table_rows AS '行数',
    ROUND(data_length / 1024 / 1024, 2) AS '数据大小(MB)'
FROM information_schema.tables 
WHERE table_schema = 'botnet' 
    AND table_rows > 0
ORDER BY table_rows DESC
LIMIT 10;
" 2>/dev/null

echo
echo "============================================================"
echo "   检查完成"
echo "============================================================"
echo
