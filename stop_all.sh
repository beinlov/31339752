#!/bin/bash
# ============================================================
# Botnet Platform - 停止所有服务 (Linux/Mac)
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
echo "   Botnet Platform - 停止所有服务"
echo "============================================================"
echo
echo "正在停止以下服务:"
echo "  1. 日志处理器 (Log Processor)"
echo "  2. 平台后端API (API Backend)"
echo "  3. 统计聚合器 (Stats Aggregator)"
echo "  4. 前端界面 (Frontend)"
echo
echo "警告: 这将关闭所有相关的Python和Node进程！"
echo

read -p "按Enter继续，或Ctrl+C取消..."

echo
echo -e "${YELLOW}[Stopping]${NC} 关闭服务..."

# 读取PID文件并停止进程
PID_FILES=(
    "$SCRIPT_DIR/backend/logs/log_processor.pid"
    "$SCRIPT_DIR/backend/logs/api_backend.pid"
    "$SCRIPT_DIR/backend/logs/aggregator.pid"
    "$SCRIPT_DIR/backend/logs/frontend.pid"
)

STOPPED_COUNT=0
for PID_FILE in "${PID_FILES[@]}"; do
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        SERVICE_NAME=$(basename "$PID_FILE" .pid)
        
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "  ${YELLOW}[Stopping]${NC} $SERVICE_NAME (PID: $PID)"
            kill $PID 2>/dev/null
            
            # 等待进程结束
            for i in {1..10}; do
                if ! ps -p $PID > /dev/null 2>&1; then
                    break
                fi
                sleep 0.5
            done
            
            # 如果还在运行，强制结束
            if ps -p $PID > /dev/null 2>&1; then
                echo -e "  ${YELLOW}[Force Kill]${NC} $SERVICE_NAME"
                kill -9 $PID 2>/dev/null
            fi
            
            STOPPED_COUNT=$((STOPPED_COUNT + 1))
        fi
        
        # 删除PID文件
        rm -f "$PID_FILE"
    fi
done

sleep 1

echo -e "${GREEN}[OK]${NC} $STOPPED_COUNT 个服务已停止"

echo
echo -e "${YELLOW}[Checking]${NC} 检查残留进程..."

# 检查并清理残留的Python进程
PYTHON_PIDS=$(pgrep -f "python.*main.py|python.*aggregator.py")
if [ ! -z "$PYTHON_PIDS" ]; then
    echo -e "  ${YELLOW}[Cleaning]${NC} 发现Python进程，正在清理..."
    kill $PYTHON_PIDS 2>/dev/null
    sleep 1
fi

# 检查并清理残留的Node进程
NODE_PIDS=$(pgrep -f "node.*vite|npm.*dev")
if [ ! -z "$NODE_PIDS" ]; then
    echo -e "  ${YELLOW}[Cleaning]${NC} 发现Node.js进程，正在清理..."
    kill $NODE_PIDS 2>/dev/null
    sleep 1
fi

echo -e "${GREEN}[OK]${NC} 残留进程已清理"

echo
echo "============================================================"
echo "   所有服务已停止"
echo "============================================================"
echo
echo "Redis Server 仍在运行（如需停止请手动执行: redis-cli shutdown）"
echo
echo "如需重新启动，请运行: ./start_all_v3.sh"
echo
