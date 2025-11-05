#!/bin/bash
# ============================================================
# 僵尸网络监控系统 - 停止脚本 (Linux/Mac)
# ============================================================

echo ""
echo "============================================================"
echo "  停止僵尸网络监控系统"
echo "============================================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 停止日志处理器
if [ -f "$SCRIPT_DIR/.log_processor.pid" ]; then
    PID=$(cat "$SCRIPT_DIR/.log_processor.pid")
    if ps -p $PID > /dev/null 2>&1; then
        echo "停止日志处理器 (PID: $PID)..."
        kill $PID
        echo "  ✓ 日志处理器已停止"
    else
        echo "  ⊗ 日志处理器未运行"
    fi
    rm "$SCRIPT_DIR/.log_processor.pid"
fi

# 停止FastAPI后端
if [ -f "$SCRIPT_DIR/.backend.pid" ]; then
    PID=$(cat "$SCRIPT_DIR/.backend.pid")
    if ps -p $PID > /dev/null 2>&1; then
        echo "停止FastAPI后端 (PID: $PID)..."
        kill $PID
        echo "  ✓ FastAPI后端已停止"
    else
        echo "  ⊗ FastAPI后端未运行"
    fi
    rm "$SCRIPT_DIR/.backend.pid"
fi

# 停止前端
if [ -f "$SCRIPT_DIR/.frontend.pid" ]; then
    PID=$(cat "$SCRIPT_DIR/.frontend.pid")
    if ps -p $PID > /dev/null 2>&1; then
        echo "停止前端界面 (PID: $PID)..."
        kill $PID
        echo "  ✓ 前端界面已停止"
    else
        echo "  ⊗ 前端界面未运行"
    fi
    rm "$SCRIPT_DIR/.frontend.pid"
fi

echo ""
echo "============================================================"
echo "  所有服务已停止"
echo "============================================================"
echo ""





