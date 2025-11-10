#!/bin/bash
# ============================================================
# 一键启动Docker部署脚本（Linux/Mac）
# ============================================================

set -e

echo "=========================================="
echo "  僵尸网络接管集成平台 - Docker部署"
echo "=========================================="
echo ""

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未安装Docker"
    echo "   请访问 https://docs.docker.com/get-docker/ 安装Docker"
    exit 1
fi

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误: 未安装Docker Compose"
    echo "   请访问 https://docs.docker.com/compose/install/ 安装Docker Compose"
    exit 1
fi

echo "✅ Docker 版本: $(docker --version)"
echo "✅ Docker Compose 版本: $(docker-compose --version)"
echo ""

# 检查.env文件
if [ ! -f .env ]; then
    echo "⚠️  未找到.env文件，使用默认配置..."
    echo "   建议: cp .env.example .env 并修改配置"
    echo ""
    sleep 2
fi

# 构建镜像
echo "📦 构建Docker镜像..."
docker-compose build
echo ""

# 启动服务
echo "🚀 启动所有服务..."
docker-compose up -d
echo ""

# 等待服务启动
echo "⏳ 等待服务启动（约30秒）..."
sleep 30
echo ""

# 检查服务状态
echo "📊 服务状态:"
docker-compose ps
echo ""

# 健康检查
echo "🏥 健康检查:"
echo -n "   MySQL: "
if docker-compose exec -T mysql mysqladmin ping -h localhost -u root -p${MYSQL_ROOT_PASSWORD:-123456} 2>/dev/null | grep -q "alive"; then
    echo "✅ 正常"
else
    echo "❌ 异常"
fi

echo -n "   Backend: "
if curl -s http://localhost:8000/api/province-amounts > /dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 异常"
fi

echo -n "   Frontend: "
if curl -s http://localhost > /dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 异常"
fi
echo ""

# 显示访问信息
echo "=========================================="
echo "  🎉 部署完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  前端: http://localhost"
echo "  后端: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo ""
echo "默认账户:"
echo "  用户名: admin"
echo "  密码: admin"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose stop"
echo "  重启服务: docker-compose restart"
echo "  完全清除: docker-compose down -v"
echo ""
echo "详细文档: DOCKER_DEPLOYMENT.md"
echo "=========================================="


