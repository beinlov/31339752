@echo off
REM ============================================================
REM 一键启动Docker部署脚本（Windows）
REM ============================================================

echo ==========================================
echo   僵尸网络接管集成平台 - Docker部署
echo ==========================================
echo.

REM 检查Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未安装Docker
    echo    请访问 https://docs.docker.com/get-docker/ 安装Docker
    pause
    exit /b 1
)

REM 检查Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未安装Docker Compose
    echo    请访问 https://docs.docker.com/compose/install/ 安装Docker Compose
    pause
    exit /b 1
)

echo ✅ Docker 已安装
echo ✅ Docker Compose 已安装
echo.

REM 检查.env文件
if not exist .env (
    echo ⚠️  未找到.env文件，使用默认配置...
    echo    建议: copy .env.example .env 并修改配置
    echo.
    timeout /t 2 >nul
)

REM 构建镜像
echo 📦 构建Docker镜像...
docker-compose build
echo.

REM 启动服务
echo 🚀 启动所有服务...
docker-compose up -d
echo.

REM 等待服务启动
echo ⏳ 等待服务启动（约30秒）...
timeout /t 30 >nul
echo.

REM 检查服务状态
echo 📊 服务状态:
docker-compose ps
echo.

REM 显示访问信息
echo ==========================================
echo   🎉 部署完成！
echo ==========================================
echo.
echo 访问地址:
echo   前端: http://localhost
echo   后端: http://localhost:8000
echo   API文档: http://localhost:8000/docs
echo.
echo 默认账户:
echo   用户名: admin
echo   密码: admin
echo.
echo 常用命令:
echo   查看日志: docker-compose logs -f
echo   停止服务: docker-compose stop
echo   重启服务: docker-compose restart
echo   完全清除: docker-compose down -v
echo.
echo 详细文档: DOCKER_DEPLOYMENT.md
echo ==========================================
echo.

pause


