========================================
Botnet Platform - Encoding Issue FIXED
========================================

PROBLEM:
- Chinese characters in .bat files caused encoding errors
- Commands were misinterpreted by Windows CMD

SOLUTION:
- All .bat files converted to pure English
- Added PowerShell alternatives (.ps1)

========================================
HOW TO START THE PLATFORM
========================================

Option 1: Batch File (Fixed, Recommended)
------------------------------------------
Double-click:  start_all.bat

Option 2: PowerShell (If .bat still has issues)
------------------------------------------------
Right-click start_all.ps1 -> Run with PowerShell

Option 3: Manual Start
----------------------
1. redis-server
2. cd backend && python worker.py
3. cd backend && uvicorn main:app --host 0.0.0.0 --port 8000

========================================
VERIFICATION
========================================

Test encoding fix:
  test_encoding.bat

Check services status:
  check_status.bat

Stop all services:
  stop_all.bat

========================================
EXPECTED OUTPUT (start_all.bat)
========================================

========================================
  Botnet Platform - Start All Services
========================================

[Step 1/4] Checking Redis status...
[OK] Redis is running

[Step 2/4] Checking Python environment...
[OK] Python environment ready

[Step 3/4] Checking dependencies...
[OK] Dependencies ready

[Step 4/4] Starting services...
========================================

[Starting] Worker process (background)...
[Starting] Web service (port: 8000)...

========================================
  All Services Started Successfully!
========================================

Services:
  1. Redis Server  - Port 6379
  2. Worker Process - Background data processing
  3. Web Service   - http://localhost:8000

Frontend Access:
  http://localhost:8000

========================================
TROUBLESHOOTING
========================================

If you still see encoding errors:
1. Use PowerShell version: start_all.ps1
2. Or start manually (see Option 3 above)

If Redis fails to start:
- Install Redis: https://github.com/tporadowski/redis/releases
- Or use Docker: docker run -d -p 6379:6379 redis

If Python not found:
- Add Python to PATH
- Or use full path: C:\Python39\python.exe

========================================
FILES FIXED
========================================

[FIXED] start_all.bat
[FIXED] stop_all.bat
[FIXED] check_status.bat
[FIXED] backend/start_worker.bat
[NEW]   start_all.ps1 (PowerShell alternative)
[NEW]   test_encoding.bat (test script)

========================================
