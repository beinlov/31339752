@echo off
REM Quick Aggregate - Manually trigger stats aggregation
REM ========================================

color 0A

echo ========================================
echo   Quick Stats Aggregation
echo ========================================
echo.
echo This will manually aggregate data from:
echo   botnet_nodes_test
echo To:
echo   china_botnet_test (province stats)
echo   global_botnet_test (country stats)
echo.
echo Estimated time: 1-3 minutes
echo.

pause

echo.
echo [Running] Aggregating stats for 'test' botnet...
echo.

cd /d "%~dp0backend"
python stats_aggregator/aggregator.py once test

echo.
echo ========================================
echo   Aggregation Complete
echo ========================================
echo.

echo [Verify] Checking stats table...
python -c "import pymysql; from config import DB_CONFIG; conn=pymysql.connect(**DB_CONFIG); cur=conn.cursor(); cur.execute('SELECT COUNT(*) FROM china_botnet_test'); count=cur.fetchone()[0]; print(f'\nchina_botnet_test records: {count}'); if count > 0: cur.execute('SELECT province, municipality, infected_num FROM china_botnet_test ORDER BY infected_num DESC LIMIT 5'); print('\nTop 5 provinces:'); for row in cur.fetchall(): print(f'  {row[0]} - {row[1]}: {row[2]} infected'); else: print('\nWARNING: Still no data in stats table!'); conn.close()"

echo.
echo.
echo ========================================
echo   Next Steps
echo ========================================
echo.
echo 1. Open frontend: http://localhost:9000
echo 2. Refresh the page (Ctrl+F5)
echo 3. You should see data on the map!
echo.
echo If still no data:
echo   - Check backend API: http://localhost:8000/api/province-amounts
echo   - Check Worker logs for errors
echo   - Run: check_data_flow.bat for diagnosis
echo.

pause
