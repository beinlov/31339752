@echo off
chcp 65001 >nul
echo ============================================================
echo   统计数据聚合器启动脚本 (Windows)
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/2] 检查 Python 环境...
python --version
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.7+
    pause
    exit /b 1
)

echo.
echo [2/2] 启动统计聚合器（每30分钟聚合一次）...
echo 日志文件: backend\stats_aggregator.log
echo 按 Ctrl+C 可以停止
echo.

python stats_aggregator\aggregator.py daemon 30

pause



