@echo off
REM Botnet Platform - Pull Only Mode
REM ========================================
REM
REM Optimized for: Platform without public IP
REM Data source: Pull from C2 only (no API push)
REM
REM Services:
REM 1. Redis (Cache only, no queue)
REM 2. Frontend (React, port 9000)
REM 3. Backend API (FastAPI, port 8000)
REM 4. Log Processor (Pull from C2)
REM 5. Stats Aggregator
REM
REM REQUIRED (After optimization):
REM - Worker (MUST have! Processes queue from log processor)
REM - Redis Queue (Used by log processor for async)
REM
REM ========================================

color 0A

echo ========================================
echo   Botnet Platform - Pull Only Mode
echo   (Optimized for Local Network)
echo ========================================
echo.
echo [INFO] Platform has no public IP
echo [INFO] Only pulling data from C2
echo [INFO] Worker NOT needed
echo.

REM Check Redis
echo [Check] Redis status...
netstat -ano | find ":6379" | find "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Redis is running (for cache)
) else (
    echo [INFO] Redis not detected
)

echo.
echo [1/5] Starting Frontend...
cd /d "%~dp0fronted"
start "Botnet Frontend" cmd /k "npm run dev"
timeout /t 2 /nobreak >nul

echo.
echo [2/5] Starting Backend API...
cd /d "%~dp0backend"
start "Botnet Backend API" cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 2 /nobreak >nul

echo.
echo [3/5] Starting Log Processor (Pull Mode)...
start "Botnet Log Processor" cmd /k "python log_processor/main.py"
timeout /t 2 /nobreak >nul

echo.
echo [4/5] Starting Stats Aggregator...
start "Botnet Stats Aggregator" cmd /k "python stats_aggregator/aggregator.py daemon 5"
timeout /t 2 /nobreak >nul

echo.
echo [5/5] Starting Worker (REQUIRED)...
echo [INFO] After optimization, Worker is now REQUIRED
echo [INFO] Log processor uses queue for async processing
start "Botnet Worker" cmd /k "python worker.py"
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   All Services Started!
echo ========================================
echo.
echo Architecture: Pull Mode + Async Queue (Optimized)
echo.
echo Services:
echo   1. Frontend          - http://localhost:9000
echo   2. Backend API       - http://localhost:8000
echo   3. Log Processor     - Pull from C2 every 60s, push to queue
echo   4. Stats Aggregator  - Aggregate every 5 min
echo   5. Worker            - Process queue (REQUIRED)
echo.
echo Data Flow:
echo   C2 (Public) ^<-- Pull -- Log Processor -- Queue -- Worker -- DB -- Frontend
echo.
echo [Note] Worker IS NOW REQUIRED for async processing
echo.

pause
