#!/bin/bash
# ============================================================
# 僵尸网络接管集成平台 - 完整五服务启动脚本
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
echo "   僵尸网络接管集成平台 - 五服务启动"
echo "============================================================"
echo
echo "本脚本将启动以下服务:"
echo "  1. MySQL数据库      (Docker容器, 端口: 3306)"
echo "  2. Redis服务        (端口: 6379)"
echo "  3. 平台后端API      (端口: 8000)"
echo "  4. 日志处理器       (后台进程)"
echo "  5. 统计聚合器       (后台进程, 30分钟间隔)"
echo "  6. Timeset数据确保器 (后台进程, 3小时间隔)"
echo "  7. 前端界面         (端口: 9000)"
echo
echo "============================================================"
echo

# ============================================================
# 步骤 1: 检查并启动MySQL (Docker容器)
# ============================================================
echo -e "${BLUE}[Step 1/7]${NC} 检查MySQL数据库..."

if sudo docker ps | grep -q mysql; then
    echo -e "${GREEN}[OK]${NC} MySQL容器已运行"
else
    echo -e "${YELLOW}[Starting]${NC} 启动MySQL容器..."
    sudo docker start mysql
    sleep 3
    
    if sudo docker ps | grep -q mysql; then
        echo -e "${GREEN}[OK]${NC} MySQL容器已启动"
    else
        echo -e "${RED}[ERROR]${NC} MySQL容器启动失败"
        exit 1
    fi
fi

# ============================================================
# 步骤 2: 检查并启动Redis
# ============================================================
echo
echo -e "${BLUE}[Step 2/7]${NC} 检查Redis服务..."

if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC} Redis已运行"
else
    echo -e "${YELLOW}[Starting]${NC} 启动Redis服务..."
    sudo systemctl start redis-server
    sleep 2
    
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}[OK]${NC} Redis已启动"
    else
        echo -e "${RED}[ERROR]${NC} Redis启动失败"
        exit 1
    fi
fi

# ============================================================
# 步骤 3: 启动平台后端API
# ============================================================
echo
echo -e "${BLUE}[Step 3/7]${NC} 启动平台后端API..."

cd "$SCRIPT_DIR/backend"
mkdir -p logs

# 检查端口是否被占用
if lsof -i:8000 > /dev/null 2>&1; then
    echo -e "${YELLOW}[WARNING]${NC} 端口8000已被占用，尝试停止旧进程..."
    pkill -f "uvicorn main:app"
    sleep 2
fi

nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > logs/api_backend.log 2>&1 &
API_PID=$!
echo $API_PID > logs/api_backend.pid
sleep 3

# 验证后端是否启动
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC} 平台后端已启动 (PID: $API_PID, http://localhost:8000)"
else
    echo -e "${RED}[ERROR]${NC} 平台后端启动失败，请检查日志: backend/logs/api_backend.log"
    exit 1
fi

# ============================================================
# 步骤 4: 启动日志处理器
# ============================================================
echo
echo -e "${BLUE}[Step 4/7]${NC} 启动日志处理器..."

cd "$SCRIPT_DIR/backend"
nohup python3 log_processor/main.py > logs/log_processor.log 2>&1 &
LOG_PROCESSOR_PID=$!
echo $LOG_PROCESSOR_PID > logs/log_processor.pid
sleep 2

echo -e "${GREEN}[OK]${NC} 日志处理器已启动 (PID: $LOG_PROCESSOR_PID)"

# ============================================================
# 步骤 5: 启动统计聚合器
# ============================================================
echo
echo -e "${BLUE}[Step 5/7]${NC} 启动统计聚合器..."

cd "$SCRIPT_DIR/backend"
nohup python3 stats_aggregator/aggregator.py > logs/aggregator.log 2>&1 &
AGGREGATOR_PID=$!
echo $AGGREGATOR_PID > logs/aggregator.pid
sleep 1

echo -e "${GREEN}[OK]${NC} 统计聚合器已启动 (PID: $AGGREGATOR_PID, 每30分钟运行)"

# ============================================================
# 步骤 6: 启动Timeset数据确保器
# ============================================================
echo
echo -e "${BLUE}[Step 6/7]${NC} 启动Timeset数据确保器..."

cd "$SCRIPT_DIR/backend"
nohup python3 scripts/ensure_timeset_data.py > logs/timeset_ensurer.log 2>&1 &
TIMESET_PID=$!
echo $TIMESET_PID > logs/timeset_ensurer.pid
sleep 1

echo -e "${GREEN}[OK]${NC} Timeset数据确保器已启动 (PID: $TIMESET_PID, 每3小时运行)"

# ============================================================
# 步骤 7: 启动前端界面
# ============================================================
echo
echo -e "${BLUE}[Step 7/7]${NC} 启动前端界面..."

cd "$SCRIPT_DIR/fronted"

# 检查Node.js版本
NODE_VERSION=$(node --version 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1)
if [ -z "$NODE_VERSION" ] || [ "$NODE_VERSION" -lt 16 ]; then
    echo -e "${RED}[ERROR]${NC} Node.js版本不足 (需要 >= 16)"
    echo "前端无法启动，但后端服务已启动"
else
    echo -e "${YELLOW}[Starting]${NC} 前端将在前台运行..."
    echo -e "${YELLOW}[INFO]${NC} 如需后台运行，请按Ctrl+C后执行:"
    echo "    cd fronted && nohup npm run dev > ../backend/logs/frontend.log 2>&1 &"
    echo
    sleep 2
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
echo "  [1] MySQL数据库      - Docker容器 (端口: 3306)"
echo "  [2] Redis服务        - 端口: 6379"
echo "  [3] 平台后端API      - PID: $API_PID (http://localhost:8000)"
echo "  [4] 日志处理器       - PID: $LOG_PROCESSOR_PID"
echo "  [5] 统计聚合器       - PID: $AGGREGATOR_PID"
echo "  [6] Timeset数据确保器 - PID: $TIMESET_PID"
if [ ! -z "$NODE_VERSION" ] && [ "$NODE_VERSION" -ge 16 ]; then
    echo "  [7] 前端界面         - 准备启动 (http://localhost:9000)"
else
    echo "  [7] 前端界面         - 未启动 (Node.js版本不足)"
fi
echo
echo "访问地址:"
echo "  - 前端界面:  http://localhost:9000"
echo "  - API文档:   http://localhost:8000/docs"
echo "  - API根路径: http://localhost:8000"
echo
echo "日志文件:"
echo "  - 后端API:    backend/logs/api_backend.log"
echo "  - 日志处理器: backend/logs/log_processor.log"
echo "  - 统计聚合器: backend/logs/aggregator.log"
echo "  - Timeset:    backend/logs/timeset_ensurer.log"
echo
echo "停止服务:"
echo "  - 运行: ./stop_all_services.sh"
echo
echo "============================================================"
echo

# 如果Node.js可用，启动前端（前台运行）
if [ ! -z "$NODE_VERSION" ] && [ "$NODE_VERSION" -ge 16 ]; then
    echo -e "${YELLOW}[启动前端...]${NC}"
    echo "按 Ctrl+C 可停止前端（其他服务将继续运行）"
    echo
    npm run dev
fi
