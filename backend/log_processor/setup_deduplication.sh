#!/bin/bash
# ============================================================
# 数据去重机制部署脚本
# ============================================================

echo ""
echo "============================================================"
echo "  僵尸网络日志处理系统 - 数据去重机制部署"
echo "============================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 数据库配置
DB_HOST="localhost"
DB_USER="root"
DB_NAME="botnet"

echo -n "请输入MySQL密码: "
read -s DB_PASS
echo ""
echo ""

# 测试数据库连接
echo "测试数据库连接..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASS $DB_NAME -e "SELECT 1" > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ 数据库连接失败！请检查配置${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 数据库连接成功${NC}"
echo ""

# 步骤1: 备份数据库
echo "步骤 1/3: 备份数据库..."
BACKUP_FILE="botnet_backup_$(date +%Y%m%d_%H%M%S).sql"
mysqldump -h $DB_HOST -u $DB_USER -p$DB_PASS $DB_NAME > $BACKUP_FILE 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 数据库已备份到: $BACKUP_FILE${NC}"
else
    echo -e "${RED}✗ 备份失败！${NC}"
    exit 1
fi
echo ""

# 步骤2: 清理重复数据
echo "步骤 2/3: 清理现有重复数据..."
echo -e "${YELLOW}警告: 这将删除重复记录，只保留最早的一条${NC}"
echo -n "是否继续？(y/n): "
read CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo "操作已取消"
    exit 0
fi

mysql -h $DB_HOST -u $DB_USER -p$DB_PASS $DB_NAME < clean_duplicates.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 重复数据已清理${NC}"
else
    echo -e "${RED}✗ 清理失败！${NC}"
    echo "可以从备份恢复: mysql -u $DB_USER -p $DB_NAME < $BACKUP_FILE"
    exit 1
fi
echo ""

# 步骤3: 添加唯一约束
echo "步骤 3/3: 添加唯一约束..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASS $DB_NAME < add_unique_constraint.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 唯一约束已添加${NC}"
else
    echo -e "${RED}✗ 添加约束失败！${NC}"
    echo "可能原因: 仍有重复数据或约束已存在"
    exit 1
fi
echo ""

# 验证
echo "验证部署..."
RESULT=$(mysql -h $DB_HOST -u $DB_USER -p$DB_PASS $DB_NAME -e "SHOW INDEX FROM botnet_nodes_asruex WHERE Key_name = 'idx_unique_record'" 2>/dev/null | wc -l)

if [ $RESULT -gt 1 ]; then
    echo -e "${GREEN}✓ 验证成功！唯一约束已生效${NC}"
else
    echo -e "${YELLOW}⚠ 验证失败，请手动检查${NC}"
fi
echo ""

# 完成
echo "============================================================"
echo -e "${GREEN}  部署完成！${NC}"
echo "============================================================"
echo ""
echo "下一步:"
echo "  1. 重启日志处理器: python log_processor/main.py"
echo "  2. 查看去重统计: tail -f log_processor.log | grep Duplicates"
echo "  3. 阅读文档: cat DEDUPLICATION.md"
echo ""
echo "备份文件: $BACKUP_FILE"
echo "如需恢复: mysql -u $DB_USER -p $DB_NAME < $BACKUP_FILE"
echo ""





