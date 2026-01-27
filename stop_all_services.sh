#!/bin/bash
# ============================================================
# 僵尸网络接管集成平台 - 停止所有服务
# ============================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo
echo "============================================================"
echo "   停止所有平台服务"
echo "============================================================"
echo

STOPPED_COUNT=0

# 停止前端
echo -e "${YELLOW}[Stopping]${NC} 前端界面..."
pkill -f "node.*vite" && STOPPED_COUNT=$((STOPPED_COUNT + 1))

# 停止后端API
echo -e "${YELLOW}[Stopping]${NC} 平台后端API..."
if [ -f "$SCRIPT_DIR/backend/logs/api_backend.pid" ]; then
    PID=$(cat "$SCRIPT_DIR/backend/logs/api_backend.pid")
    kill $PID 2>/dev/null && STOPPED_COUNT=$((STOPPED_COUNT + 1))
    rm -f "$SCRIPT_DIR/backend/logs/api_backend.pid"
else
    pkill -f "uvicorn main:app" && STOPPED_COUNT=$((STOPPED_COUNT + 1))
fi

# 停止日志处理器
echo -e "${YELLOW}[Stopping]${NC} 日志处理器..."
if [ -f "$SCRIPT_DIR/backend/logs/log_processor.pid" ]; then
    PID=$(cat "$SCRIPT_DIR/backend/logs/log_processor.pid")
    kill $PID 2>/dev/null && STOPPED_COUNT=$((STOPPED_COUNT + 1))
    rm -f "$SCRIPT_DIR/backend/logs/log_processor.pid"
else
    pkill -f "python3.*log_processor/main.py" && STOPPED_COUNT=$((STOPPED_COUNT + 1))
fi

# 停止统计聚合器
echo -e "${YELLOW}[Stopping]${NC} 统计聚合器..."
if [ -f "$SCRIPT_DIR/backend/logs/aggregator.pid" ]; then
    PID=$(cat "$SCRIPT_DIR/backend/logs/aggregator.pid")
    kill $PID 2>/dev/null && STOPPED_COUNT=$((STOPPED_COUNT + 1))
    rm -f "$SCRIPT_DIR/backend/logs/aggregator.pid"
else
    pkill -f "python3.*aggregator.py" && STOPPED_COUNT=$((STOPPED_COUNT + 1))
fi

# 停止Timeset数据确保器
echo -e "${YELLOW}[Stopping]${NC} Timeset数据确保器..."
if [ -f "$SCRIPT_DIR/backend/logs/timeset_ensurer.pid" ]; then
    PID=$(cat "$SCRIPT_DIR/backend/logs/timeset_ensurer.pid")
    kill $PID 2>/dev/null && STOPPED_COUNT=$((STOPPED_COUNT + 1))
    rm -f "$SCRIPT_DIR/backend/logs/timeset_ensurer.pid"
else
    pkill -f "python3.*ensure_timeset_data.py" && STOPPED_COUNT=$((STOPPED_COUNT + 1))
fi

sleep 2

echo
echo -e "${GREEN}[OK]${NC} 已停止 $STOPPED_COUNT 个服务"
echo
echo "注意:"
echo "  - MySQL (Docker): 仍在运行 (如需停止: sudo docker stop mysql)"
echo "  - Redis: 仍在运行 (如需停止: sudo systemctl stop redis-server)"
echo
echo "如需重新启动，请运行: ./start_all_services.sh"
echo
echo "============================================================"
echo
