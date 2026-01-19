@echo off
REM Auto Fix Pull Issue - Quick Solution
REM ========================================

color 0C

echo ========================================
echo   Auto Fix: Pull Issue
echo ========================================
echo.
echo This script will automatically fix the issue:
echo   - Remote puller returns 0 records
echo   - Frontend shows no data
echo.

cd /d "%~dp0backend"

echo [1/3] Checking pull state...
python reset_pull_state.py check
echo.

echo [2/3] Resetting pull state...
echo y | python reset_pull_state.py reset
echo.

echo [3/3] Next steps...
echo.
echo The pull state has been reset.
echo.
echo To apply the fix:
echo   1. Restart "Botnet Log Processor" window
echo      Close it and run: python log_processor/main.py
echo.
echo   2. Wait for next pull cycle (60 seconds)
echo.
echo   3. Check logs for:
echo      [C2-test-local] Pulling all data (no resume)
echo      [C2-test-local] Pull successful: XXX records
echo.

pause
