#!/bin/bash
# 僵尸网络监控系统 - 全服务启动脚本 (Linux/Mac)

echo "============================================================"
echo "  僵尸网络监控系统 - 全服务启动脚本"
echo "============================================================"
echo
echo "本脚本将启动以下服务："
echo "  1. FastAPI 后端服务 (端口 8000)"
echo "  2. 日志处理器"
echo "  3. 统计数据聚合器 (每30分钟)"
echo
echo "按 Enter 开始启动，或按 Ctrl+C 取消..."
read

cd "$(dirname "$0")"
ROOT_DIR=$(pwd)

# 日志目录
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

echo
echo "============================================================"
echo "[1/3] 启动 FastAPI 后端服务..."
echo "============================================================"
cd "$ROOT_DIR/backend"
nohup python3 main.py > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "后端服务 PID: $BACKEND_PID"
sleep 3

echo
echo "============================================================"
echo "[2/3] 启动日志处理器..."
echo "============================================================"
cd "$ROOT_DIR/backend/log_processor"
nohup python3 main.py > "$LOG_DIR/log_processor.log" 2>&1 &
PROCESSOR_PID=$!
echo "日志处理器 PID: $PROCESSOR_PID"
sleep 3

echo
echo "============================================================"
echo "[3/3] 启动统计数据聚合器..."
echo "============================================================"
cd "$ROOT_DIR/backend"
nohup python3 stats_aggregator/aggregator.py daemon 30 > "$LOG_DIR/stats_aggregator.log" 2>&1 &
AGGREGATOR_PID=$!
echo "统计聚合器 PID: $AGGREGATOR_PID"
sleep 2

echo
echo "============================================================"
echo "所有服务已启动！"
echo "============================================================"
echo
echo "服务列表："
echo "  • 后端服务 (PID: $BACKEND_PID):     http://localhost:8000"
echo "  • API文档:                          http://localhost:8000/docs"
echo "  • 日志处理器 (PID: $PROCESSOR_PID): 实时监控 backend/logs/ 目录"
echo "  • 统计聚合器 (PID: $AGGREGATOR_PID): 每30分钟聚合一次数据"
echo
echo "进程ID已保存到: $ROOT_DIR/pids.txt"
echo "$BACKEND_PID" > "$ROOT_DIR/pids.txt"
echo "$PROCESSOR_PID" >> "$ROOT_DIR/pids.txt"
echo "$AGGREGATOR_PID" >> "$ROOT_DIR/pids.txt"
echo
echo "日志文件位置："
echo "  • 后端:         $LOG_DIR/backend.log"
echo "  • 日志处理器:   $LOG_DIR/log_processor.log"
echo "  • 统计聚合器:   $LOG_DIR/stats_aggregator.log"
echo
echo "停止所有服务："
echo "  kill \$(cat $ROOT_DIR/pids.txt)"
echo
echo "或使用停止脚本："
echo "  ./stop_all_services.sh"
echo



