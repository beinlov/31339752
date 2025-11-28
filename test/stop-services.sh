#!/bin/bash

# =========================================
# 停止所有服务
# =========================================

PROJECT_DIR="$HOME/botnet"
PID_DIR="$PROJECT_DIR/backend/logs"

echo "========================================="
echo "  停止僵尸网络监控系统"
echo "========================================="

# 停止后端服务
if [ -f "$PID_DIR/backend.pid" ]; then
    PID=$(cat $PID_DIR/backend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "停止后端服务 (PID: $PID)..."
        kill $PID
        rm $PID_DIR/backend.pid
        echo "✅ 后端服务已停止"
    else
        echo "⚠️  后端服务未运行"
        rm $PID_DIR/backend.pid
    fi
else
    echo "⚠️  未找到后端服务PID文件"
fi

# 停止日志处理器
if [ -f "$PID_DIR/log_processor.pid" ]; then
    PID=$(cat $PID_DIR/log_processor.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "停止日志处理器 (PID: $PID)..."
        kill $PID
        rm $PID_DIR/log_processor.pid
        echo "✅ 日志处理器已停止"
    else
        echo "⚠️  日志处理器未运行"
        rm $PID_DIR/log_processor.pid
    fi
else
    echo "⚠️  未找到日志处理器PID文件"
fi

# 停止聚合器
if [ -f "$PID_DIR/aggregator.pid" ]; then
    PID=$(cat $PID_DIR/aggregator.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "停止聚合器 (PID: $PID)..."
        kill $PID
        rm $PID_DIR/aggregator.pid
        echo "✅ 聚合器已停止"
    else
        echo "⚠️  聚合器未运行"
        rm $PID_DIR/aggregator.pid
    fi
else
    echo "⚠️  未找到聚合器PID文件"
fi

# 停止前端服务
if [ -f "$PID_DIR/frontend.pid" ]; then
    PID=$(cat $PID_DIR/frontend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "停止前端服务 (PID: $PID)..."
        kill $PID
        rm $PID_DIR/frontend.pid
        echo "✅ 前端服务已停止"
    else
        echo "⚠️  前端服务未运行"
        rm $PID_DIR/frontend.pid
    fi
else
    echo "⚠️  未找到前端服务PID文件"
fi

# 额外清理：杀死可能遗留的Python进程
echo ""
echo "检查遗留进程..."
pkill -f "python.*main.py" 2>/dev/null && echo "清理了遗留的后端进程"
pkill -f "python.*log_processor" 2>/dev/null && echo "清理了遗留的日志处理器进程"
pkill -f "python.*aggregator" 2>/dev/null && echo "清理了遗留的聚合器进程"
pkill -f "serve.*dist" 2>/dev/null && echo "清理了遗留的前端进程"

echo ""
echo "========================================="
echo "  所有服务已停止"
echo "========================================="
