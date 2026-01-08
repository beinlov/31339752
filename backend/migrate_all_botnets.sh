#!/bin/bash
# ============================================================
# 批量执行数据库迁移脚本
# 为所有僵尸网络类型执行迁移
# ============================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 数据库配置
DB_HOST="localhost"
DB_PORT="3306"
DB_NAME="botnet"
DB_USER="root"
DB_PASS="root"

# 僵尸网络类型列表
BOTNET_TYPES=("asruex" "mozi" "andromeda" "moobot" "ramnit" "leethozer")

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}僵尸网络平台数据库批量迁移工具${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查MySQL命令是否可用
if ! command -v mysql &> /dev/null; then
    echo -e "${RED}错误: 未找到 mysql 命令${NC}"
    echo "请确保已安装 MySQL 客户端并添加到 PATH"
    exit 1
fi

# 确认操作
echo -e "${YELLOW}警告: 此操作将修改数据库结构！${NC}"
echo "数据库: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo "将要迁移的僵尸网络类型: ${BOTNET_TYPES[*]}"
echo ""
read -p "是否继续? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "操作已取消"
    exit 0
fi

# 备份数据库
echo ""
echo -e "${YELLOW}正在备份数据库...${NC}"
BACKUP_FILE="botnet_backup_$(date +%Y%m%d_%H%M%S).sql"
mysqldump -h${DB_HOST} -P${DB_PORT} -u${DB_USER} -p${DB_PASS} ${DB_NAME} > ${BACKUP_FILE} 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 数据库备份完成: ${BACKUP_FILE}${NC}"
else
    echo -e "${RED}✗ 数据库备份失败${NC}"
    read -p "是否继续（不建议）? (yes/no): " continue_without_backup
    if [ "$continue_without_backup" != "yes" ]; then
        exit 1
    fi
fi

# 创建日志文件
LOG_FILE="migration_log_$(date +%Y%m%d_%H%M%S).txt"
echo "迁移开始时间: $(date)" > ${LOG_FILE}

# 为每个僵尸网络类型执行迁移
success_count=0
fail_count=0

for type in "${BOTNET_TYPES[@]}"; do
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}正在迁移: ${type}${NC}"
    echo -e "${YELLOW}========================================${NC}"
    
    # 替换脚本中的 {type} 占位符
    sed "s/{type}/${type}/g" database_migration.sql > "temp_migration_${type}.sql"
    
    # 执行迁移
    mysql -h${DB_HOST} -P${DB_PORT} -u${DB_USER} -p${DB_PASS} ${DB_NAME} < "temp_migration_${type}.sql" >> ${LOG_FILE} 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ${type} 迁移成功${NC}"
        ((success_count++))
        echo "[SUCCESS] ${type}" >> ${LOG_FILE}
    else
        echo -e "${RED}✗ ${type} 迁移失败，请查看日志: ${LOG_FILE}${NC}"
        ((fail_count++))
        echo "[FAILED] ${type}" >> ${LOG_FILE}
    fi
    
    # 清理临时文件
    rm -f "temp_migration_${type}.sql"
done

# 输出总结
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}迁移完成统计${NC}"
echo -e "${GREEN}========================================${NC}"
echo "成功: ${success_count}/${#BOTNET_TYPES[@]}"
echo "失败: ${fail_count}/${#BOTNET_TYPES[@]}"
echo "详细日志: ${LOG_FILE}"
echo "数据库备份: ${BACKUP_FILE}"
echo ""

if [ ${fail_count} -gt 0 ]; then
    echo -e "${RED}注意: 部分迁移失败，请检查日志${NC}"
    echo -e "${YELLOW}如需回滚，请使用备份文件恢复:${NC}"
    echo "mysql -h${DB_HOST} -P${DB_PORT} -u${DB_USER} -p${DB_PASS} ${DB_NAME} < ${BACKUP_FILE}"
    exit 1
else
    echo -e "${GREEN}所有迁移都已成功完成！${NC}"
    exit 0
fi
