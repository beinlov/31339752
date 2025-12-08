# ============================================================
# 僵尸网络监控系统 - 全服务启动脚本 (PowerShell)
# ============================================================

$Host.UI.RawUI.WindowTitle = "Botnet Monitoring System - Service Launcher"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  僵尸网络监控系统 - 全服务启动脚本" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "本脚本将启动以下服务：" -ForegroundColor Yellow
Write-Host "  1. FastAPI 后端服务 (端口 8000)"
Write-Host "  2. 日志处理器"
Write-Host "  3. 统计数据聚合器 (每30分钟)"
Write-Host "  4. 前端开发服务器 (Vite)"
Write-Host ""
Write-Host "按任意键开始启动，或按 Ctrl+C 取消..." -ForegroundColor Green
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Write-Host ""

# 获取脚本所在目录
$ROOT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT_DIR

# 启动后端服务
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[1/3] 启动 FastAPI 后端服务..." -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT_DIR\backend'; python main.py" -WindowStyle Normal
Start-Sleep -Seconds 3

# 启动日志处理器
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[2/3] 启动日志处理器..." -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT_DIR\backend\log_processor'; python main.py" -WindowStyle Normal
Start-Sleep -Seconds 3

# 启动统计聚合器
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[3/4] 启动统计数据聚合器..." -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT_DIR\backend\stats_aggregator'; python aggregator.py daemon 30" -WindowStyle Normal
Start-Sleep -Seconds 2

# 启动前端开发服务器
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[4/4] 启动前端开发服务器..." -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT_DIR\fronted'; npm run dev" -WindowStyle Normal
Start-Sleep -Seconds 3

# 完成
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "所有服务已启动！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "服务列表：" -ForegroundColor Cyan
Write-Host "  • 前端界面:     http://localhost:5173 (Vite开发服务器)" -ForegroundColor White
Write-Host "  • 后端服务:     http://localhost:8000" -ForegroundColor White
Write-Host "  • API文档:      http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • 日志处理器:   实时监控 backend/logs/ 目录" -ForegroundColor White
Write-Host "  • 统计聚合器:   每30分钟聚合一次数据" -ForegroundColor White
Write-Host ""
Write-Host "日志文件位置：" -ForegroundColor Cyan
Write-Host "  • 后端:         backend/main.log" -ForegroundColor White
Write-Host "  • 日志处理器:   backend/log_processor.log" -ForegroundColor White
Write-Host "  • 统计聚合器:   backend/stats_aggregator.log" -ForegroundColor White
Write-Host ""
Write-Host "如需停止服务，请关闭对应的 PowerShell 窗口" -ForegroundColor Yellow
Write-Host ""
Write-Host "按任意键退出启动器..." -ForegroundColor Green
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
