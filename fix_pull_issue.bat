@echo off
REM Quick Fix - Reset Remote Puller State
REM ========================================

color 0E

echo ========================================
echo   Fix: Reset Remote Puller State
echo ========================================
echo.
echo This will reset the pull timestamp
echo to fetch all data from C2.
echo.
echo Current issue:
echo   - Log processor shows: "remote pull: 0, saved: 0"
echo   - C2 returns 0 records (since=old timestamp)
echo   - Worker has no tasks to process
echo.
echo Solution:
echo   Delete state file to reset timestamp
echo.

pause

echo.
echo [1/3] Checking state file...
cd /d "%~dp0backend"

if exist .remote_puller_state.json (
    echo [Found] State file exists
    echo.
    type .remote_puller_state.json
    echo.
    echo [Action] Deleting state file...
    del .remote_puller_state.json
    echo [OK] State file deleted
) else (
    echo [Info] State file not found (this is OK)
    echo [Info] State might be in memory or not created yet
)

echo.
echo [2/3] Checking C2 endpoint...
echo Testing: http://localhost:8888/api/pull
echo.

REM Test C2 connection
curl -s "http://localhost:8888/api/pull?limit=5&confirm=false" -H "X-API-Key: KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4" > nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] C2 endpoint is accessible
) else (
    echo [WARNING] Cannot connect to C2 endpoint
    echo [INFO] Make sure C2 server is running on port 8888
)

echo.
echo [3/3] Next steps...
echo.
echo To apply the fix:
echo   1. Close the "Botnet Log Processor" window
echo   2. Restart log processor: 
echo      cd backend
echo      python log_processor/main.py
echo   3. Check logs for successful pull
echo.
echo Expected logs:
echo   [C2-test-local] Pulling data...
echo   [C2-test-local] Pull successful: XXX records
echo   [test] Pushed XXX data to queue
echo.
echo Then Worker will process the data automatically.
echo.

pause
