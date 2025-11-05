@echo off
REM 启动僵尸网络日志处理器 (Windows)

echo Starting Botnet Log Processor...
echo ================================

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    pause
    exit /b 1
)

REM 检查依赖
echo Checking dependencies...
python -c "import pymysql, watchdog" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install pymysql watchdog awaits
)

REM 启动主程序
echo Starting main processor...
cd /d "%~dp0"
python main.py

echo Processor stopped.
pause





