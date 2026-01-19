# Botnet Platform - Start All Services (PowerShell)
# ========================================

Write-Host "========================================" -ForegroundColor Green
Write-Host "  Botnet Platform - Start All Services" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Step 1: Check Redis
Write-Host "[Step 1/4] Checking Redis status..." -ForegroundColor Cyan
$redis = redis-cli ping 2>$null
if ($redis -ne "PONG") {
    Write-Host "[Starting] Redis not running, starting..." -ForegroundColor Yellow
    Start-Process -FilePath "redis-server" -WindowStyle Normal
    Start-Sleep -Seconds 2
    $redis = redis-cli ping 2>$null
    if ($redis -ne "PONG") {
        Write-Host "[ERROR] Redis failed to start!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Solutions:"
        Write-Host "1. Install Redis: https://github.com/tporadowski/redis/releases"
        Write-Host "2. Or use Docker: docker run -d -p 6379:6379 redis"
        pause
        exit 1
    }
    Write-Host "[OK] Redis started successfully" -ForegroundColor Green
} else {
    Write-Host "[OK] Redis is running" -ForegroundColor Green
}

# Step 2: Check Python
Write-Host ""
Write-Host "[Step 2/4] Checking Python environment..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python environment ready" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found in PATH" -ForegroundColor Red
    pause
    exit 1
}

# Step 3: Check dependencies
Write-Host ""
Write-Host "[Step 3/4] Checking dependencies..." -ForegroundColor Cyan
$redisModule = python -c "import redis" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] redis library not installed, installing..." -ForegroundColor Yellow
    pip install redis
}
Write-Host "[OK] Dependencies ready" -ForegroundColor Green

# Step 4: Start services
Write-Host ""
Write-Host "[Step 4/4] Starting services..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Navigate to backend
$backendPath = Join-Path $PSScriptRoot "backend"
Set-Location $backendPath

# Start Worker
Write-Host "[Starting] Worker process (background)..." -ForegroundColor Cyan
Start-Process -FilePath "cmd" -ArgumentList "/k python worker.py" -WindowStyle Normal
Start-Sleep -Seconds 1

# Start Web Service
Write-Host "[Starting] Web service (port: 8000)..." -ForegroundColor Cyan
Start-Process -FilePath "cmd" -ArgumentList "/k uvicorn main:app --host 0.0.0.0 --port 8000 --reload" -WindowStyle Normal
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  All Services Started Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services:"
Write-Host "  1. Redis Server  - Port 6379"
Write-Host "  2. Worker Process - Background data processing"
Write-Host "  3. Web Service   - http://localhost:8000"
Write-Host ""
Write-Host "Frontend Access:" -ForegroundColor Yellow
Write-Host "  http://localhost:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "To stop services:"
Write-Host "  - Close all opened command windows"
Write-Host "  - Or run stop_all.ps1"
Write-Host ""
Write-Host "========================================" -ForegroundColor Green

pause
