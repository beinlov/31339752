#!/bin/bash
# ============================================================
# 僵尸网络监控系统 - 一键启动脚本 (Linux/Mac)
# ============================================================

echo ""
echo "============================================================"
echo "  启动僵尸网络监控系统"
echo "============================================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR"
LOG_PROCESSOR_DIR="$BACKEND_DIR/log_processor"
FRONTEND_DIR="$BACKEND_DIR/../fronted"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    exit 1
fi

# 检查Node.js
if ! command -v npm &> /dev/null; then
    echo "警告: 未找到 npm，将跳过前端启动"
    SKIP_FRONTEND=1
fi

echo "[1/3] 启动日志处理器 (Log Processor)..."
cd "$LOG_PROCESSOR_DIR"
python3 main.py > log_processor.log 2>&1 &
LOG_PROCESSOR_PID=$!
echo "  ✓ 日志处理器已启动 (PID: $LOG_PROCESSOR_PID)"

# 等待3秒
sleep 3

echo "[2/3] 启动FastAPI后端 (Backend API)..."
cd "$BACKEND_DIR"
python3 main.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "  ✓ FastAPI后端已启动 (PID: $BACKEND_PID)"

# 等待3秒
sleep 3

if [ -z "$SKIP_FRONTEND" ]; then
    echo "[3/3] 启动前端界面 (Frontend)..."
    cd "$FRONTEND_DIR"
    npm start > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "  ✓ 前端界面已启动 (PID: $FRONTEND_PID)"
else
    echo "[3/3] 跳过前端启动"
fi

echo ""
echo "============================================================"
echo "  所有服务已启动！"
echo "============================================================"
echo ""
echo "  - 日志处理器 PID: $LOG_PROCESSOR_PID"
echo "  - FastAPI后端 PID: $BACKEND_PID"
if [ ! -z "$FRONTEND_PID" ]; then
    echo "  - 前端界面 PID: $FRONTEND_PID"
fi
echo ""
echo "  - FastAPI后端: http://localhost:8000"
echo "  - 前端界面: http://localhost:3000"
echo ""
echo "  停止所有服务:"
echo "    kill $LOG_PROCESSOR_PID $BACKEND_PID $FRONTEND_PID"
echo ""
echo "============================================================"

# 保存PID到文件
echo "$LOG_PROCESSOR_PID" > "$BACKEND_DIR/.log_processor.pid"
echo "$BACKEND_PID" > "$BACKEND_DIR/.backend.pid"
if [ ! -z "$FRONTEND_PID" ]; then
    echo "$FRONTEND_PID" > "$BACKEND_DIR/.frontend.pid"
fi

echo "PID已保存到 .log_processor.pid, .backend.pid, .frontend.pid"





