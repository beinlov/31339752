@echo off
REM ============================================================
REM Botnet Monitoring System - Start All Services
REM ============================================================

chcp 65001 >nul 2>&1

echo.
echo ============================================================
echo   Starting All Services...
echo ============================================================
echo.
echo This script will start:
echo   1. FastAPI Backend Service (Port 8000)
echo   2. Log Processor
echo   3. Statistics Aggregator (every 30min)
echo   4. Frontend Dev Server (Vite)
echo.
echo Press any key to continue, or Ctrl+C to cancel...
pause >nul
echo.

REM Get script directory
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo ============================================================
echo [1/3] Starting FastAPI Backend...
echo ============================================================
start "Backend Service" cmd /k "chcp 65001 >nul 2>&1 && cd /d %ROOT_DIR%backend && python main.py"
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo [2/3] Starting Log Processor...
echo ============================================================
start "Log Processor" cmd /k "chcp 65001 >nul 2>&1 && cd /d %ROOT_DIR%backend\log_processor && python main.py"
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo [3/4] Starting Statistics Aggregator...
echo ============================================================
start "Stats Aggregator" cmd /k "chcp 65001 >nul 2>&1 && cd /d %ROOT_DIR%backend\stats_aggregator && python aggregator.py daemon 30"
timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo [4/4] Starting Frontend Dev Server...
echo ============================================================
start "Frontend Dev Server" cmd /k "chcp 65001 >nul 2>&1 && cd /d %ROOT_DIR%fronted && npm run dev"
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo All Services Started Successfully!
echo ============================================================
echo.
echo Services:
echo   - Frontend:         http://localhost:5173  (Vite Dev Server)
echo   - Backend Service:  http://localhost:8000
echo   - API Docs:         http://localhost:8000/docs
echo   - Log Processor:    Monitoring backend/logs/ directory
echo   - Stats Aggregator: Aggregating data every 30 minutes
echo.
echo Log Files:
echo   - Backend:          backend/main.log
echo   - Log Processor:    backend/log_processor.log
echo   - Stats Aggregator: backend/stats_aggregator.log
echo.
echo To stop services, close the corresponding command windows
echo.
pause
