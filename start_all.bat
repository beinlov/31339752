@echo off
REM Botnet Platform - Start All Services
REM ========================================

color 0A

echo ========================================
echo   Botnet Platform - Start All Services
echo ========================================
echo.

echo [Step 1/4] Checking Redis status...

REM Try redis-cli first
redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Redis is running
    goto redis_ok
)

REM If redis-cli not found, check port 6379
netstat -ano | find ":6379" | find "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Redis detected on port 6379 (redis-cli not in PATH)
    goto redis_ok
)

REM Redis not running, try to start
echo [Starting] Redis not detected, attempting to start...
start "Redis Server" redis-server 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Could not start Redis automatically
    echo.
    echo Redis may already be running or needs manual start.
    echo Check if Redis Server window is open.
    echo.
    echo If you see a Redis Server window, press any key to continue.
    echo Otherwise, start Redis manually and run this script again.
    pause
)

REM Wait and check again
timeout /t 3 /nobreak >nul
netstat -ano | find ":6379" | find "LISTENING" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Redis port 6379 not listening
    echo.
    echo Solutions:
    echo 1. Install Redis: https://github.com/tporadowski/redis/releases
    echo 2. Or use Docker: docker run -d -p 6379:6379 redis
    echo 3. Or start redis-server.exe manually
    pause
    exit /b 1
)
echo [OK] Redis started successfully

:redis_ok

echo.
echo [Step 2/4] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH
    pause
    exit /b 1
)
echo [OK] Python environment ready

echo.
echo [Step 3/4] Checking dependencies...
python -c "import redis" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] redis library not installed, installing...
    pip install redis
)
echo [OK] Dependencies ready

echo.
echo [Step 4/4] Starting services...
echo ========================================
echo.

REM Navigate to backend directory
cd /d "%~dp0backend"

echo [Starting] Worker process (background)...
start "Botnet Worker" cmd /k "python worker.py"
timeout /t 1 /nobreak >nul

echo [Starting] Web service (port: 8000)...
start "Botnet Web" cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   All Services Started Successfully!
echo ========================================
echo.
echo Services:
echo   1. Redis Server  - Port 6379
echo   2. Worker Process - Background data processing
echo   3. Web Service   - http://localhost:8000
echo.
echo Frontend Access:
echo   http://localhost:8000
echo.
echo To stop services:
echo   - Close all opened command windows
echo   - Or run stop_all.bat
echo.
echo ========================================

pause
