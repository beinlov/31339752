@echo off
REM Botnet Platform - Stop All Services
REM ========================================

echo ========================================
echo   Botnet Platform - Stop Services
echo ========================================
echo.

echo [1/3] Stopping Worker process...
taskkill /FI "WindowTitle eq Botnet Worker*" /F >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Worker process stopped
) else (
    echo [INFO] Worker process not running
)

echo.
echo [2/3] Stopping Web service...
taskkill /FI "WindowTitle eq Botnet Web*" /F >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Web service stopped
) else (
    echo [INFO] Web service not running
)

REM Fallback: Kill process by port
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo [3/3] Redis service (optional)...
echo [INFO] Redis server kept running. Stop manually if needed.
REM Uncomment to stop Redis
REM taskkill /FI "WindowTitle eq Redis Server*" /F >nul 2>&1

echo.
echo ========================================
echo   Botnet Platform Stopped
echo ========================================
echo.

pause
