#!/bin/bash
# ============================================================
# 僵尸网络接管集成平台 - 服务状态检查
# ============================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo
echo "============================================================"
echo "   平台服务状态检查"
echo "============================================================"
echo

# 检查MySQL
echo -e "${BLUE}[MySQL数据库]${NC}"
if sudo docker ps | grep -q mysql; then
    echo -e "  ${GREEN}✓${NC} MySQL容器运行中"
    sudo docker ps | grep mysql | awk '{print "    容器: " $NF ", 端口: 3306"}'
else
    echo -e "  ${RED}✗${NC} MySQL容器未运行"
fi
echo

# 检查Redis
echo -e "${BLUE}[Redis服务]${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Redis运行中 (端口: 6379)"
    REDIS_INFO=$(redis-cli info server | grep redis_version)
    echo "    ${REDIS_INFO}"
else
    echo -e "  ${RED}✗${NC} Redis未运行"
fi
echo

# 检查后端API
echo -e "${BLUE}[平台后端API]${NC}"
if pgrep -f "uvicorn main:app" > /dev/null; then
    PID=$(pgrep -f "uvicorn main:app")
    echo -e "  ${GREEN}✓${NC} 后端API运行中 (PID: $PID, 端口: 8000)"
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "    ${GREEN}✓${NC} API响应正常"
    else
        echo -e "    ${YELLOW}!${NC} API无响应"
    fi
else
    echo -e "  ${RED}✗${NC} 后端API未运行"
fi
echo

# 检查日志处理器
echo -e "${BLUE}[日志处理器]${NC}"
if pgrep -f "python3.*log_processor/main.py" > /dev/null; then
    PID=$(pgrep -f "python3.*log_processor/main.py")
    echo -e "  ${GREEN}✓${NC} 日志处理器运行中 (PID: $PID)"
else
    echo -e "  ${RED}✗${NC} 日志处理器未运行"
fi
echo

# 检查统计聚合器
echo -e "${BLUE}[统计聚合器]${NC}"
if pgrep -f "python3.*aggregator.py" > /dev/null; then
    PID=$(pgrep -f "python3.*aggregator.py")
    echo -e "  ${GREEN}✓${NC} 统计聚合器运行中 (PID: $PID)"
else
    echo -e "  ${RED}✗${NC} 统计聚合器未运行"
fi
echo

# 检查Timeset数据确保器
echo -e "${BLUE}[Timeset数据确保器]${NC}"
if pgrep -f "python3.*ensure_timeset_data.py" > /dev/null; then
    PID=$(pgrep -f "python3.*ensure_timeset_data.py")
    echo -e "  ${GREEN}✓${NC} Timeset确保器运行中 (PID: $PID)"
else
    echo -e "  ${RED}✗${NC} Timeset确保器未运行"
fi
echo

# 检查前端
echo -e "${BLUE}[前端界面]${NC}"
if pgrep -f "node.*vite" > /dev/null; then
    PID=$(pgrep -f "node.*vite")
    echo -e "  ${GREEN}✓${NC} 前端运行中 (PID: $PID, 端口: 9000)"
    if curl -s http://localhost:9000/ > /dev/null 2>&1; then
        echo -e "    ${GREEN}✓${NC} 前端响应正常"
    else
        echo -e "    ${YELLOW}!${NC} 前端无响应"
    fi
else
    echo -e "  ${RED}✗${NC} 前端未运行"
fi
echo

# 端口占用情况
echo "============================================================"
echo "端口占用情况:"
echo "============================================================"
netstat -tuln | grep -E "(3306|6379|8000|9000)" | awk '{print "  " $4 " -> " $6}'
echo

# 统计
echo "============================================================"
TOTAL_SERVICES=5
RUNNING_SERVICES=0

pgrep -f "uvicorn main:app" > /dev/null && RUNNING_SERVICES=$((RUNNING_SERVICES + 1))
pgrep -f "python3.*log_processor/main.py" > /dev/null && RUNNING_SERVICES=$((RUNNING_SERVICES + 1))
pgrep -f "python3.*aggregator.py" > /dev/null && RUNNING_SERVICES=$((RUNNING_SERVICES + 1))
pgrep -f "python3.*ensure_timeset_data.py" > /dev/null && RUNNING_SERVICES=$((RUNNING_SERVICES + 1))
pgrep -f "node.*vite" > /dev/null && RUNNING_SERVICES=$((RUNNING_SERVICES + 1))

echo "运行状态: $RUNNING_SERVICES/$TOTAL_SERVICES 个服务运行中"
echo

if [ $RUNNING_SERVICES -eq $TOTAL_SERVICES ]; then
    echo -e "${GREEN}✓ 所有服务正常运行${NC}"
elif [ $RUNNING_SERVICES -eq 0 ]; then
    echo -e "${RED}✗ 所有服务都未运行${NC}"
    echo "  启动服务: ./start_all_services.sh"
else
    echo -e "${YELLOW}! 部分服务未运行${NC}"
    echo "  启动服务: ./start_all_services.sh"
fi

echo "============================================================"
echo
