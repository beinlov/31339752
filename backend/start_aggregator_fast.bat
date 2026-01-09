@echo off
REM Start Stats Aggregator - Fast Mode (30 seconds interval)
REM ========================================

color 0E

echo ========================================
echo   Stats Aggregator - Fast Mode
echo ========================================
echo.
echo Aggregation interval: 1 minute
echo.
echo This will update frontend data every 1 minute!
echo.

cd /d "%~dp0"

echo Starting aggregator...
python stats_aggregator/aggregator.py daemon 1

pause
