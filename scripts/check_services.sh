#!/bin/bash
# 快速检查所有服务运行状态

echo "=========================================="
echo "服务运行状态检查 - $(date)"
echo "=========================================="

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

check_service() {
    SERVICE_NAME=$1
    PROCESS_PATTERN=$2
    PORT=$3
    
    echo -n "[$SERVICE_NAME] "
    
    if pgrep -f "$PROCESS_PATTERN" > /dev/null; then
        PID=$(pgrep -f "$PROCESS_PATTERN" | head -n 1)
        echo -e "${GREEN}✓ 运行中${NC} (PID: $PID)"
        
        if [ ! -z "$PORT" ]; then
            if netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
                echo "           端口 $PORT 正在监听"
            fi
        fi
        return 0
    else
        echo -e "${RED}✗ 未运行${NC}"
        return 1
    fi
}

echo ""
check_service "MySQL" "mysqld" "3306" || docker ps | grep mysql > /dev/null && echo -e "  ${GREEN}✓ MySQL容器运行中${NC}"
check_service "Redis" "redis-server" "6379"
check_service "后端API" "uvicorn main:app" "8000"
check_service "日志处理器" "log_processor/main.py"
check_service "统计聚合器" "aggregator.py"
check_service "Timeset" "ensure_timeset_data.py"
check_service "前端界面" "node.*vite" "9000"

echo ""
echo "=========================================="
echo "PID文件检查:"
echo "=========================================="

SCRIPT_DIR="/home/spider/31339752"
for pidfile in api_backend.pid log_processor.pid aggregator.pid timeset_ensurer.pid frontend.pid; do
    if [ -f "$SCRIPT_DIR/backend/logs/$pidfile" ]; then
        PID=$(cat "$SCRIPT_DIR/backend/logs/$pidfile")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} $pidfile: PID $PID (运行中)"
        else
            echo -e "${RED}✗${NC} $pidfile: PID $PID (已停止，需清理)"
        fi
    fi
done

echo ""
echo "=========================================="
