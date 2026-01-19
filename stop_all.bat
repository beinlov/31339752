@echo off
REM ============================================================
REM Botnet Platform - Stop All Services
REM ============================================================

color 0C
title Stop Botnet Platform

echo.
echo ============================================================
echo    Botnet Platform - Stop All Services
echo ============================================================
echo.
echo Stopping the following services:
echo   1. Log Processor (Botnet Log Processor)
echo   2. Platform Backend (Botnet API Backend)
echo   3. Stats Aggregator (Botnet Stats Aggregator)
echo   4. Frontend UI (Botnet Frontend)
echo   5. Redis Server
echo.
echo WARNING: This will close all related Python and Node processes!
echo.

pause

echo.
echo [Stopping] Closing service windows...

REM Close services by window title
taskkill /FI "WINDOWTITLE eq Botnet Log Processor*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Botnet API Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Botnet Stats Aggregator*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Botnet Frontend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Redis Server*" /F >nul 2>&1

timeout /t 2 /nobreak >nul

echo [OK] Service windows closed

echo.
echo [Checking] Checking for remaining processes...

REM Check and cleanup remaining Python processes
tasklist /FI "IMAGENAME eq python.exe" | find /I "python.exe" >nul
if %errorlevel% equ 0 (
    echo [Cleaning] Found Python processes, cleaning up...
    taskkill /IM python.exe /F >nul 2>&1
    timeout /t 1 /nobreak >nul
)

REM Check and cleanup remaining Node processes
tasklist /FI "IMAGENAME eq node.exe" | find /I "node.exe" >nul
if %errorlevel% equ 0 (
    echo [Cleaning] Found Node.js processes, cleaning up...
    taskkill /IM node.exe /F >nul 2>&1
    timeout /t 1 /nobreak >nul
)

echo [OK] Remaining processes cleaned up

echo.
echo ============================================================
echo    All Services Stopped
echo ============================================================
echo.
echo Redis Server is still running (close manually if needed)
echo.
echo To restart, run: start_all_v3.bat
echo.

pause
