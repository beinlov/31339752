#!/bin/bash

# =========================================
# 启动所有服务
# =========================================

PROJECT_DIR="$HOME/botnet"

echo "========================================="
echo "  启动僵尸网络监控系统"
echo "========================================="

# 进入后端目录
cd $PROJECT_DIR/backend

# 激活虚拟环境
source venv/bin/activate

# 创建日志目录
mkdir -p logs

# 启动后端服务
echo ""
echo "[1/4] 启动后端服务..."
nohup python main.py > logs/backend.log 2>&1 &
echo $! > logs/backend.pid
echo "✅ 后端服务已启动 (PID: $(cat logs/backend.pid))"

# 等待后端启动
sleep 3

# 启动日志处理器
echo ""
echo "[2/4] 启动日志处理器..."
nohup python log_processor/main.py > log_processor/log_processor.log 2>&1 &
echo $! > logs/log_processor.pid
echo "✅ 日志处理器已启动 (PID: $(cat logs/log_processor.pid))"

# 启动聚合器
echo ""
echo "[3/4] 启动统计聚合器（5分钟间隔）..."
nohup python stats_aggregator/aggregator.py daemon 5 > stats_aggregator.log 2>&1 &
echo $! > logs/aggregator.pid
echo "✅ 聚合器已启动 (PID: $(cat logs/aggregator.pid))"

# 启动前端（使用 serve 或 nginx）
echo ""
echo "[4/4] 启动前端服务..."

# 方式1: 使用 serve (npm install -g serve)
if command -v serve &> /dev/null; then
    cd $PROJECT_DIR/fronted
    nohup serve -s dist -l 80 > ../backend/logs/frontend.log 2>&1 &
    echo $! > ../backend/logs/frontend.pid
    echo "✅ 前端服务已启动 (PID: $(cat ../backend/logs/frontend.pid))"
else
    echo "⚠️  serve 未安装，请手动配置 Nginx 或安装 serve"
    echo "   安装命令: sudo npm install -g serve"
fi

echo ""
echo "========================================="
echo "  服务启动完成！"
echo "========================================="
echo ""
echo "服务状态:"
ps aux | grep -E 'python|serve' | grep -v grep

echo ""
echo "查看日志:"
echo "  - 后端: tail -f $PROJECT_DIR/backend/logs/backend.log"
echo "  - 日志处理器: tail -f $PROJECT_DIR/backend/log_processor/log_processor.log"
echo "  - 聚合器: tail -f $PROJECT_DIR/backend/stats_aggregator.log"
echo ""
