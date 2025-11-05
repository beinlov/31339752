@echo off
chcp 65001 >nul
echo ============================================================
echo   僵尸网络监控系统 - 全服务启动脚本
echo ============================================================
echo.
echo 本脚本将启动以下服务：
echo   1. FastAPI 后端服务 (端口 8000)
echo   2. 日志处理器
echo   3. 统计数据聚合器 (每30分钟)
echo.
echo 按任意键开始启动，或按 Ctrl+C 取消...
pause >nul
echo.

REM 获取脚本所在目录
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo ============================================================
echo [1/3] 启动 FastAPI 后端服务...
echo ============================================================
start "后端服务" cmd /k "cd /d %ROOT_DIR%backend && python main.py"
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo [2/3] 启动日志处理器...
echo ============================================================
start "日志处理器" cmd /k "cd /d %ROOT_DIR%backend\log_processor && python main.py"
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo [3/3] 启动统计数据聚合器...
echo ============================================================
start "统计聚合器" cmd /k "cd /d %ROOT_DIR%backend && python stats_aggregator\aggregator.py daemon 30"
timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo 所有服务已启动！
echo ============================================================
echo.
echo 服务列表：
echo   • 后端服务:     http://localhost:8000
echo   • API文档:      http://localhost:8000/docs
echo   • 日志处理器:   实时监控 backend/logs/ 目录
echo   • 统计聚合器:   每30分钟聚合一次数据
echo.
echo 日志文件位置：
echo   • 后端:         backend/main.log
echo   • 日志处理器:   backend/log_processor.log
echo   • 统计聚合器:   backend/stats_aggregator.log
echo.
echo 如需停止服务，请关闭对应的命令行窗口
echo.
pause



