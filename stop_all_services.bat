@echo off
REM ============================================================
REM Stop All Services
REM ============================================================

chcp 65001 >nul 2>&1

echo.
echo ============================================================
echo   Stopping All Services...
echo ============================================================
echo.

REM 停止 Python 进程（后端和聚合器）
echo Stopping Python processes...
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Backend Service*" 2>nul
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Log Processor*" 2>nul
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Stats Aggregator*" 2>nul

REM 停止 Node 进程（前端）
echo Stopping Node.js processes...
taskkill /F /FI "IMAGENAME eq node.exe" /FI "WINDOWTITLE eq Frontend Dev Server*" 2>nul

echo.
echo ============================================================
echo Services stopped!
echo ============================================================
echo.
echo Note: If some processes were not stopped, you can:
echo   1. Close the corresponding command windows manually
echo   2. Or use Task Manager to end the processes
echo.
pause
