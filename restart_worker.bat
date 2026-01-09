@echo off
REM Restart Worker - Apply Performance Fix
REM ========================================

color 0E

echo ========================================
echo   Restart Worker (Performance Fix Applied)
echo ========================================
echo.
echo Performance improvements:
echo   - Fixed executemany (was 1000x slower)
echo   - Using true batch INSERT
echo   - Expected: 1000 records in ^<1 second
echo.
echo Previous performance:
echo   - 1000 records in 188 seconds (5 records/sec)
echo.
echo Expected performance:
echo   - 1000 records in ^<1 second (1000+ records/sec)
echo   - 80x faster overall
echo.

pause

echo.
echo [1/2] Finding old Worker process...
tasklist | find "python.exe" | find "worker.py" >nul 2>&1
if %errorlevel% equ 0 (
    echo [Found] Worker is running
    echo [Action] Please close the "Botnet Worker" window manually
    echo.
    pause
) else (
    echo [Info] Worker not running
)

echo.
echo [2/2] Starting new Worker...
cd /d "%~dp0backend"
start "Botnet Worker" cmd /k "python worker.py"

echo.
echo ========================================
echo   Worker Restarted
echo ========================================
echo.
echo Watch for new logs showing:
echo   [test] Inserting new nodes: 1000 records, time: 0.X sec (1000+ rec/sec)
echo   [test] Communication records inserted: 1000 records, time: 0.X sec
echo   [Worker] Task completed: 1000 records, time: ~3 sec
echo.
echo If you see these improvements, the fix worked! 
echo.

pause
