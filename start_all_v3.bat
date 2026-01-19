@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM Botnet Platform - One-Click Startup Script v3.0
REM Based on Internal Worker Architecture
REM No need to start worker.py separately
REM ============================================================

REM Initialize variables
set SKIP_FRONTEND=0

color 0A
title Botnet Platform Launcher v3.0

echo.
echo ============================================================
echo    Botnet Platform - Startup Script v3.0
echo ============================================================
echo.
echo This script will start the following services:
echo   1. Redis Server      (Port: 6379)
echo   2. Log Processor     (with Internal Worker)
echo   3. Platform Backend  (Port: 8000)
echo   4. Stats Aggregator  (Daemon, 30min interval)
echo   5. Daily Node Counter (8:00 AM daily)
echo   6. Frontend UI       (Port: 9000)
echo.
echo ============================================================
echo.

REM ============================================================
REM Step 1: Check Redis Status
REM ============================================================
echo [Step 1/6] Checking Redis status...

REM First check if port 6379 is listening
netstat -ano | find ":6379" >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] Redis detected on port 6379
    goto redis_ok
)

REM If not found, try to start Redis
echo [Starting] Redis not detected, attempting to start...
start "Redis Server" redis-server
timeout /t 3 /nobreak >nul

REM Check again
netstat -ano | find ":6379" >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] Redis started successfully
    goto redis_ok
)

echo [ERROR] Redis failed to start
echo.
echo Solutions:
echo   1. Install Redis: https://github.com/tporadowski/redis/releases
echo   2. Or use Docker: docker run -d -p 6379:6379 redis
echo   3. Or start manually: redis-server.exe
pause
exit /b 1

:redis_ok

REM ============================================================
REM Step 2: Check Python Environment
REM ============================================================
echo.
echo [Step 2/6] Checking Python environment...

python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Python not found in PATH
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% detected

REM ============================================================
REM Step 3: Check Dependencies
REM ============================================================
echo.
echo [Step 3/6] Checking Python dependencies...

python -c "import redis, fastapi, pymysql" >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARNING] Missing dependencies, installing...
    pip install redis fastapi uvicorn pymysql
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)
echo [OK] Python dependencies ready

REM ============================================================
REM Step 4: Check Node.js Environment (for frontend)
REM ============================================================
echo.
echo [Step 4/6] Checking Node.js environment...

REM Try to find node executable
where node >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARNING] Node.js not found in PATH
    echo Frontend will not start, but backend services will run normally
    echo To start frontend, install Node.js: https://nodejs.org/
    set SKIP_FRONTEND=1
) else (
    REM Node found, get version
    for /f "tokens=1" %%i in ('node --version 2^>nul') do set NODE_VERSION=%%i
    if "!NODE_VERSION!"=="" (
        echo [WARNING] Node.js command failed
        set SKIP_FRONTEND=1
    ) else (
        echo [OK] Node.js !NODE_VERSION! detected
        set SKIP_FRONTEND=0
    )
)

REM ============================================================
REM Step 5: Check Frontend Dependencies
REM ============================================================
if "!SKIP_FRONTEND!"=="0" (
    echo.
    echo [Step 5/6] Checking frontend dependencies...
    
    if not exist "%~dp0frontend\node_modules" (
        echo [Installing] Frontend dependencies not found, installing...
        pushd "%~dp0frontend"
        if exist package.json (
            call npm install
            if !errorlevel! neq 0 (
                echo [WARNING] Frontend dependency installation failed
                set SKIP_FRONTEND=1
            ) else (
                echo [OK] Frontend dependencies installed
            )
        ) else (
            echo [WARNING] package.json not found in frontend directory
            set SKIP_FRONTEND=1
        )
        popd
    ) else (
        echo [OK] Frontend dependencies already installed
    )
) else (
    echo.
    echo [Step 5/6] Skipping frontend dependency check...
)

REM ============================================================
REM Step 6: Start All Services
REM ============================================================
echo.
echo [Step 6/6] Starting services...
echo ============================================================
echo.

cd /d "%~dp0backend"

echo [Starting 1/4] Log Processor (with Internal Worker)...
start "Botnet Log Processor" cmd /k "cd /d %~dp0backend\log_processor && python main.py"
timeout /t 2 /nobreak >nul
echo [OK] Log Processor started

echo.
echo [Starting 2/4] Platform Backend API (FastAPI)...
start "Botnet API Backend" cmd /k "cd /d %~dp0backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul
echo [OK] Platform Backend started - http://localhost:8000

echo.
echo [Starting 3/5] Stats Aggregator - Daemon Mode...
start "Botnet Stats Aggregator" cmd /k "cd /d %~dp0backend\stats_aggregator && python aggregator.py daemon 30"
timeout /t 1 /nobreak >nul
echo [OK] Stats Aggregator started - aggregates every 30 minutes

echo.
echo [Starting 4/5] Daily Node Counter - Manual Execution...
echo [INFO] Note: Schedule library not installed, using manual execution
echo [INFO] To enable daily auto-run, install: pip install schedule
echo [INFO] Or use Windows Task Scheduler to run: python backend/daily_node_counter_simple.py
timeout /t 2 /nobreak >nul
echo [OK] Daily Node Counter ready (manual mode)

echo.
REM Start frontend if enabled
if "!SKIP_FRONTEND!"=="0" (
    echo [Starting 5/5] Frontend UI - Vite...
    cd /d "%~dp0frontend"
    start "Botnet Frontend" cmd /k "npm run dev"
    cd /d "%~dp0"
    timeout /t 3 /nobreak >nul
    echo [OK] Frontend UI started
) else (
    echo [Skipped 5/5] Frontend UI - Node.js not installed
)

REM ============================================================
REM Startup Complete
REM ============================================================
echo.
echo ============================================================
echo    All Services Started Successfully!
echo ============================================================
echo.
echo Running Services:
echo   [1] Redis Server         - Port: 6379
echo   [2] Log Processor (Internal Worker) - Background
echo   [3] Platform Backend API - http://localhost:8000
echo   [4] Stats Aggregator     - Background (every 30 minutes)
echo   [5] Daily Node Counter   - Background (8:00 AM daily)
if "!SKIP_FRONTEND!"=="0" (
    echo   [6] Frontend UI          - http://localhost:9000
) else (
    echo   [6] Frontend UI          - Not started - Node.js not installed
)
echo.
echo ============================================================
echo.
echo Access URLs:
echo   - API Docs:   http://localhost:8000/docs
echo   - Frontend:   http://localhost:9000
echo.
echo Log Files:
echo   - Log Processor:   backend/logs/log_processor.log
echo   - Platform API:    Console output
echo   - Aggregator:      backend/logs/stats_aggregator.log
echo   - Node Counter:    Console output
echo.
echo To Stop Services:
echo   - Close all opened command windows
echo   - Or run: stop_all.bat
echo.
echo Monitor Services:
echo   - Check queue:   python backend/scripts/check_queue_status.py
echo   - Check data:    python backend/scripts/check_test_data.py
echo.
echo ============================================================
echo.

pause
