# ============================================================
# 停止所有服务 (PowerShell)
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Red
Write-Host "  停止所有服务" -ForegroundColor Red
Write-Host "============================================================" -ForegroundColor Red
Write-Host ""

# 查找并停止所有服务进程
Write-Host "正在查找运行中的服务..." -ForegroundColor Yellow

# 查找 main.py 进程（后端服务）
$mainProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
    $_.CommandLine -like "*main.py*" 
}

# 查找 aggregator.py 进程（统计聚合器）
$aggregatorProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
    $_.CommandLine -like "*aggregator.py*" 
}

# 查找 Node 进程（前端开发服务器）
$nodeProcesses = Get-Process node -ErrorAction SilentlyContinue | Where-Object { 
    $_.CommandLine -like "*vite*" -or $_.Path -like "*fronted*"
}

$totalProcesses = @($mainProcesses) + @($aggregatorProcesses) + @($nodeProcesses)

if ($totalProcesses.Count -eq 0) {
    Write-Host ""
    Write-Host "未找到运行中的服务" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "找到 $($totalProcesses.Count) 个运行中的进程" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($process in $totalProcesses) {
        try {
            Write-Host "正在停止进程 PID: $($process.Id)..." -ForegroundColor Yellow
            Stop-Process -Id $process.Id -Force
            Write-Host "  ✓ 已停止" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ 停止失败: $_" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "操作完成" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
