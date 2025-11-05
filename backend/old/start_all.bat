@echo off
REM ============================================================
REM 僵尸网络监控系统 - 一键启动脚本
REM ============================================================

echo.
echo ============================================================
echo   启动僵尸网络监控系统
echo ============================================================
echo.

REM 获取当前目录
set BACKEND_DIR=%~dp0
set LOG_PROCESSOR_DIR=%BACKEND_DIR%log_processor
set FRONTEND_DIR=%BACKEND_DIR%..\fronted

echo [1/3] 启动日志处理器 (Log Processor)...
start "Botnet Log Processor" cmd /k "cd /d %LOG_PROCESSOR_DIR% && python main.py"

REM 等待3秒
timeout /t 3 /nobreak >nul

echo [2/3] 启动FastAPI后端 (Backend API)...
start "Botnet FastAPI Backend" cmd /k "cd /d %BACKEND_DIR% && python main.py"

REM 等待3秒
timeout /t 3 /nobreak >nul

echo [3/3] 启动前端界面 (Frontend)...
start "Botnet Frontend" cmd /k "cd /d %FRONTEND_DIR% && npm start"

echo.
echo ============================================================
echo   所有服务已启动！
echo ============================================================
echo.
echo   - 日志处理器: 后台运行，监控日志文件
echo   - FastAPI后端: http://localhost:8000
echo   - 前端界面: http://localhost:3000 (或其他端口)
echo.
echo   按任意键关闭此窗口...
echo ============================================================
pause >nul

