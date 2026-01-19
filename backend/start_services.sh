#!/bin/bash
# ============================================================
# 容器内启动所有后端服务的脚本
# ============================================================

set -e

echo "=========================================="
echo "  启动僵尸网络接管集成平台 - 后端服务"
echo "=========================================="
echo ""

# 等待MySQL就绪
echo "⏳ 等待MySQL数据库就绪..."
until python -c "import pymysql; pymysql.connect(host='${DB_HOST:-localhost}', user='${DB_USER:-root}', password='${DB_PASSWORD:-123456}', database='${DB_NAME:-botnet}')" 2>/dev/null; do
    echo "   MySQL尚未就绪，等待5秒..."
    sleep 5
done
echo "✅ MySQL已就绪"
echo ""

# 启动日志处理器（后台）
echo "🚀 启动日志处理器..."
python log_processor/main.py > log_processor.log 2>&1 &
LOG_PROCESSOR_PID=$!
echo "   日志处理器 PID: $LOG_PROCESSOR_PID"
echo ""

# 启动统计聚合器（后台）
echo "🚀 启动统计聚合器..."
python stats_aggregator/aggregator.py > stats_aggregator.log 2>&1 &
AGGREGATOR_PID=$!
echo "   统计聚合器 PID: $AGGREGATOR_PID"
echo ""

# 等待服务启动
sleep 3

# 启动FastAPI（前台，保持容器运行）
echo "🚀 启动FastAPI服务..."
echo "   监听地址: 0.0.0.0:8000"
echo ""
echo "=========================================="
echo "  所有服务已启动！"
echo "=========================================="
echo ""

# 捕获信号，优雅关闭
trap "echo '收到停止信号，关闭所有服务...'; kill $LOG_PROCESSOR_PID $AGGREGATOR_PID; exit 0" SIGTERM SIGINT

# 启动uvicorn
exec uvicorn main:app --host 0.0.0.0 --port 8000


