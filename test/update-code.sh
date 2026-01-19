#!/bin/bash

# =========================================
# 快速更新脚本
# 用于频繁改动时的快速部署
# =========================================

set -e

PROJECT_DIR="$HOME/botnet"

echo "========================================="
echo "  快速更新代码"
echo "========================================="

# 步骤1: 拉取最新代码
echo ""
echo "[1/4] 拉取最新代码..."
cd $PROJECT_DIR
git pull origin main

# 步骤2: 检查是否有依赖更新
echo ""
echo "[2/4] 检查依赖更新..."

# 检查 Python 依赖
cd $PROJECT_DIR/backend
if git diff HEAD@{1} requirements.txt | grep -q .; then
    echo "检测到 Python 依赖更新，重新安装..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "Python 依赖无更新"
fi

# 检查前端依赖
cd $PROJECT_DIR/fronted
if git diff HEAD@{1} package.json | grep -q .; then
    echo "检测到前端依赖更新，重新安装..."
    npm install
else
    echo "前端依赖无更新"
fi

# 步骤3: 重新构建前端
echo ""
echo "[3/4] 重新构建前端..."
cd $PROJECT_DIR/fronted
npm run build

# 步骤4: 重启服务
echo ""
echo "[4/4] 重启服务..."
bash $PROJECT_DIR/test/stop-services.sh
sleep 2
bash $PROJECT_DIR/test/start-services.sh

echo ""
echo "========================================="
echo "  更新完成！"
echo "========================================="
echo ""
echo "最新提交信息:"
cd $PROJECT_DIR
git log -1 --oneline

echo ""
echo "服务地址:"
echo "  - 前端: http://服务器IP"
echo "  - 后端API: http://服务器IP:8000"
echo "  - API文档: http://服务器IP:8000/docs"
echo ""
