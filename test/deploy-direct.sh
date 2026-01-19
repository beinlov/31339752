#!/bin/bash

# =========================================
# 直接部署脚本 - 方案B
# 不使用Docker，直接在服务器上运行
# 适合快速迭代开发
# =========================================

set -e

PROJECT_NAME="botnet"
PROJECT_DIR="$HOME/$PROJECT_NAME"

echo "========================================="
echo "  僵尸网络监控系统 - 直接部署"
echo "========================================="

# 步骤1: 检查依赖
echo ""
echo "[1/6] 检查系统依赖..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    echo "   安装命令: sudo apt install python3 python3-pip"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    echo "   安装命令: curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash - && sudo apt install -y nodejs"
    exit 1
fi
echo "✅ Node.js: $(node --version)"

# 检查 MySQL
if ! command -v mysql &> /dev/null; then
    echo "⚠️  MySQL 客户端未安装，请确保 MySQL 服务器已运行"
fi

# 步骤2: 拉取最新代码
echo ""
echo "[2/6] 拉取最新代码..."
cd $PROJECT_DIR
git pull origin main

# 步骤3: 配置后端
echo ""
echo "[3/6] 配置后端..."
cd $PROJECT_DIR/backend

# 安装 Python 依赖
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

echo "激活虚拟环境并安装依赖..."
source venv/bin/activate
pip install -r requirements.txt

# 检查配置文件
if [ ! -f "config.py" ]; then
    echo "❌ config.py 未找到，请创建配置文件"
    exit 1
fi

# 步骤4: 构建前端
echo ""
echo "[4/6] 构建前端..."
cd $PROJECT_DIR/fronted

if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

echo "构建前端..."
npm run build

# 步骤5: 停止旧服务
echo ""
echo "[5/6] 停止旧服务..."
bash $PROJECT_DIR/test/stop-services.sh

# 步骤6: 启动新服务
echo ""
echo "[6/6] 启动新服务..."
bash $PROJECT_DIR/test/start-services.sh

echo ""
echo "========================================="
echo "  部署完成！"
echo "========================================="
echo ""
echo "服务地址:"
echo "  - 前端: http://服务器IP"
echo "  - 后端API: http://服务器IP:8000"
echo "  - API文档: http://服务器IP:8000/docs"
echo ""
echo "查看日志:"
echo "  - 后端: tail -f $PROJECT_DIR/backend/logs/backend.log"
echo "  - 日志处理器: tail -f $PROJECT_DIR/backend/log_processor/log_processor.log"
echo "  - 聚合器: tail -f $PROJECT_DIR/backend/stats_aggregator.log"
echo ""
echo "管理命令:"
echo "  - 停止服务: bash $PROJECT_DIR/test/stop-services.sh"
echo "  - 启动服务: bash $PROJECT_DIR/test/start-services.sh"
echo "  - 更新代码: bash $PROJECT_DIR/test/update-code.sh"
echo ""
