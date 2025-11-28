#!/bin/bash

# =========================================
# Docker 部署脚本 - 方案A
# 适合频繁改动的开发阶段
# =========================================

set -e

PROJECT_NAME="botnet"
PROJECT_DIR="$HOME/$PROJECT_NAME"
COMPOSE_FILE="docker-compose.dev.yml"

echo "========================================="
echo "  僵尸网络监控系统 - Docker 部署"
echo "========================================="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 步骤1: 拉取最新代码
echo ""
echo "[1/5] 拉取最新代码..."
cd $PROJECT_DIR
git pull origin main

# 步骤2: 检查环境变量
if [ ! -f ".env" ]; then
    echo ""
    echo "[2/5] 创建环境变量文件..."
    cp test/.env.example .env
    echo "⚠️  请编辑 .env 文件配置数据库密码"
    echo "   使用命令: nano .env"
    read -p "按回车继续..."
else
    echo ""
    echo "[2/5] 环境变量文件已存在"
fi

# 步骤3: 构建前端（如果有更新）
echo ""
echo "[3/5] 检查前端更新..."
if [ -d "fronted/src" ]; then
    echo "构建前端..."
    cd fronted
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    npm run build
    cd ..
else
    echo "⚠️  前端代码未找到，跳过构建"
fi

# 步骤4: 停止旧容器
echo ""
echo "[4/5] 停止旧容器..."
cd $PROJECT_DIR/test
docker-compose -f $COMPOSE_FILE down

# 步骤5: 启动新容器
echo ""
echo "[5/5] 启动新容器..."
docker-compose -f $COMPOSE_FILE up -d

# 等待服务启动
echo ""
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo ""
echo "========================================="
echo "  服务状态"
echo "========================================="
docker-compose -f $COMPOSE_FILE ps

# 检查后端健康状态
echo ""
echo "检查后端服务..."
if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ 后端服务正常"
else
    echo "❌ 后端服务异常，查看日志:"
    echo "   docker logs botnet-backend"
fi

# 检查前端健康状态
echo ""
echo "检查前端服务..."
if curl -f http://localhost/ > /dev/null 2>&1; then
    echo "✅ 前端服务正常"
else
    echo "❌ 前端服务异常，查看日志:"
    echo "   docker logs botnet-frontend"
fi

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
echo "  - 后端: docker logs -f botnet-backend"
echo "  - 前端: docker logs -f botnet-frontend"
echo "  - 数据库: docker logs -f botnet-mysql"
echo ""
echo "管理命令:"
echo "  - 重启: cd $PROJECT_DIR/test && docker-compose -f $COMPOSE_FILE restart"
echo "  - 停止: cd $PROJECT_DIR/test && docker-compose -f $COMPOSE_FILE stop"
echo "  - 查看状态: cd $PROJECT_DIR/test && docker-compose -f $COMPOSE_FILE ps"
echo ""
