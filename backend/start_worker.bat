@echo off
echo ===============================================
echo Botnet Worker Process
echo ===============================================
echo.

echo [1/3] Checking Redis connection...
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Redis not running! Start Redis first:
    echo   - Windows: redis-server.exe
    echo   - Docker: docker run -d -p 6379:6379 redis
    pause
    exit /b 1
)
echo [OK] Redis is running

echo.
echo [2/3] Checking Python environment...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH
    pause
    exit /b 1
)

echo.
echo [3/3] Starting Worker process...
echo ===============================================
python worker.py
