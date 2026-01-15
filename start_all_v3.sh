#!/bin/bash
# ============================================================
# Botnet Platform - 一键启动脚本 v3.0 (Linux/Mac)
# 基于内置Worker架构，无需单独启动worker.py
# ============================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo
echo "============================================================"
echo "   Botnet Platform - 一键启动脚本 v3.0"
echo "============================================================"
echo
echo "本脚本将启动以下服务:"
echo "  1. Redis Server      (端口: 6379)"
echo "  2. 日志处理器         (内置Worker)"
echo "  3. 平台后端API       (端口: 8000)"
echo "  4. 统计聚合器         (守护进程，30分钟间隔)"
echo "  5. 前端界面          (端口: 9000)"
echo
echo "============================================================"
echo

# ============================================================
# 步骤 1: 检查Redis状态
# ============================================================
echo -e "${BLUE}[Step 1/6]${NC} 检查Redis状态..."

if lsof -i:6379 > /dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":6379 "; then
    echo -e "${GREEN}[OK]${NC} Redis detected on port 6379"
else
    echo -e "${YELLOW}[Starting]${NC} Redis not detected, attempting to start..."
    
    if command -v redis-server > /dev/null 2>&1; then
        redis-server --daemonize yes
        sleep 2
        
        if redis-cli ping > /dev/null 2>&1; then
            echo -e "${GREEN}[OK]${NC} Redis started successfully"
        else
            echo -e "${RED}[ERROR]${NC} Redis failed to start"
            echo
            echo "解决方案:"
            echo "  1. 安装Redis: brew install redis (Mac) 或 apt install redis (Ubuntu)"
            echo "  2. 或使用Docker: docker run -d -p 6379:6379 redis"
            echo "  3. 或手动启动: redis-server"
            exit 1
        fi
    else
        echo -e "${RED}[ERROR]${NC} redis-server not found"
        echo "请先安装Redis"
        exit 1
    fi
fi

# ============================================================
# 步骤 2: 检查Python环境
# ============================================================
echo
echo -e "${BLUE}[Step 2/6]${NC} 检查Python环境..."

if ! command -v python3 > /dev/null 2>&1; then
    echo -e "${RED}[ERROR]${NC} Python3 not found"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}[OK]${NC} Python $PYTHON_VERSION detected"

# ============================================================
# 步骤 3: 检查Python依赖
# ============================================================
echo
echo -e "${BLUE}[Step 3/6]${NC} 检查Python依赖..."

if ! python3 -c "import redis, fastapi, pymysql" > /dev/null 2>&1; then
    echo -e "${YELLOW}[WARNING]${NC} Missing dependencies, installing..."
    pip3 install redis fastapi uvicorn pymysql
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR]${NC} Failed to install dependencies"
        exit 1
    fi
fi
echo -e "${GREEN}[OK]${NC} Python dependencies ready"

# ============================================================
# 步骤 4: 检查Node.js环境（前端需要）
# ============================================================
echo
echo -e "${BLUE}[Step 4/6]${NC} 检查Node.js环境..."

SKIP_FRONTEND=0
if ! command -v node > /dev/null 2>&1; then
    echo -e "${YELLOW}[WARNING]${NC} Node.js not found"
    echo "前端将无法启动，但后端服务可以正常运行"
    echo "如需启动前端，请安装Node.js: https://nodejs.org/"
    SKIP_FRONTEND=1
else
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}[OK]${NC} Node.js $NODE_VERSION detected"
fi

# ============================================================
# 步骤 5: 检查前端依赖
# ============================================================
if [ $SKIP_FRONTEND -eq 0 ]; then
    echo
    echo -e "${BLUE}[Step 5/6]${NC} 检查前端依赖..."
    
    if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
        echo -e "${YELLOW}[Installing]${NC} 前端依赖未安装，正在安装..."
        cd "$SCRIPT_DIR/frontend"
        npm install
        
        if [ $? -ne 0 ]; then
            echo -e "${YELLOW}[WARNING]${NC} 前端依赖安装失败"
            SKIP_FRONTEND=1
        else
            echo -e "${GREEN}[OK]${NC} 前端依赖安装完成"
        fi
        cd "$SCRIPT_DIR"
    else
        echo -e "${GREEN}[OK]${NC} 前端依赖已安装"
    fi
else
    echo
    echo -e "${BLUE}[Step 5/6]${NC} 跳过前端依赖检查..."
fi

# ============================================================
# 步骤 6: 启动所有服务
# ============================================================
echo
echo -e "${BLUE}[Step 6/6]${NC} 启动服务..."
echo "============================================================"
echo

# 创建日志目录
mkdir -p "$SCRIPT_DIR/backend/logs"

# 启动日志处理器
echo -e "${YELLOW}[Starting 1/4]${NC} 日志处理器 (内置Worker)..."
cd "$SCRIPT_DIR/backend/log_processor"
nohup python3 main.py > "$SCRIPT_DIR/backend/logs/log_processor_console.log" 2>&1 &
LOG_PROCESSOR_PID=$!
echo $LOG_PROCESSOR_PID > "$SCRIPT_DIR/backend/logs/log_processor.pid"
sleep 2
echo -e "${GREEN}[OK]${NC} 日志处理器已启动 (PID: $LOG_PROCESSOR_PID)"

# 启动平台后端API
echo
echo -e "${YELLOW}[Starting 2/4]${NC} 平台后端API (FastAPI)..."
cd "$SCRIPT_DIR/backend"
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > "$SCRIPT_DIR/backend/logs/api_backend.log" 2>&1 &
API_BACKEND_PID=$!
echo $API_BACKEND_PID > "$SCRIPT_DIR/backend/logs/api_backend.pid"
sleep 3
echo -e "${GREEN}[OK]${NC} 平台后端已启动 (PID: $API_BACKEND_PID, http://localhost:8000)"

# 启动统计聚合器
echo
echo -e "${YELLOW}[Starting 3/4]${NC} 统计聚合器 (守护进程)..."
cd "$SCRIPT_DIR/backend"
nohup python3 stats_aggregator/aggregator.py daemon 30 > "$SCRIPT_DIR/backend/logs/aggregator.log" 2>&1 &
AGGREGATOR_PID=$!
echo $AGGREGATOR_PID > "$SCRIPT_DIR/backend/logs/aggregator.pid"
sleep 1
echo -e "${GREEN}[OK]${NC} 统计聚合器已启动 (PID: $AGGREGATOR_PID, 每30分钟聚合一次)"

# 启动前端界面
if [ $SKIP_FRONTEND -eq 0 ]; then
    echo
    echo -e "${YELLOW}[Starting 4/4]${NC} 前端界面 (Vite)..."
    cd "$SCRIPT_DIR/frontend"
    nohup npm run dev > "$SCRIPT_DIR/backend/logs/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$SCRIPT_DIR/backend/logs/frontend.pid"
    sleep 3
    echo -e "${GREEN}[OK]${NC} 前端界面已启动 (PID: $FRONTEND_PID)"
else
    echo
    echo -e "${YELLOW}[Skipped 4/4]${NC} 前端界面 (Node.js未安装)"
fi

# ============================================================
# 启动完成
# ============================================================
echo
echo "============================================================"
echo "   所有服务启动成功！"
echo "============================================================"
echo
echo "运行中的服务:"
echo "  [1] Redis Server         - 端口: 6379"
echo "  [2] 日志处理器 (内置Worker) - PID: $LOG_PROCESSOR_PID"
echo "  [3] 平台后端API          - http://localhost:8000 (PID: $API_BACKEND_PID)"
echo "  [4] 统计聚合器           - PID: $AGGREGATOR_PID (每30分钟)"
if [ $SKIP_FRONTEND -eq 0 ]; then
    echo "  [5] 前端界面             - http://localhost:9000 (PID: $FRONTEND_PID)"
else
    echo "  [5] 前端界面             - 未启动 (Node.js未安装)"
fi
echo
echo "============================================================"
echo
echo "访问地址:"
echo "  - API文档:   http://localhost:8000/docs"
echo "  - 前端界面:  http://localhost:9000"
echo
echo "日志文件:"
echo "  - 日志处理器: backend/logs/log_processor.log"
echo "  - 平台后端:   backend/logs/api_backend.log"
echo "  - 统计聚合器: backend/logs/aggregator.log"
if [ $SKIP_FRONTEND -eq 0 ]; then
    echo "  - 前端界面:   backend/logs/frontend.log"
fi
echo
echo "停止服务:"
echo "  - 运行: ./stop_all.sh"
echo "  - 或手动: kill $LOG_PROCESSOR_PID $API_BACKEND_PID $AGGREGATOR_PID"
if [ $SKIP_FRONTEND -eq 0 ]; then
    echo "            kill $FRONTEND_PID"
fi
echo
echo "监控服务状态:"
echo "  - 诊断队列:   python3 backend/scripts/check_queue_status.py"
echo "  - 检查数据:   python3 backend/scripts/check_test_data.py"
echo
echo "============================================================"
echo
