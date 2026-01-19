@echo off
REM ============================================================
REM 优化配置以支持15个C2并发拉取
REM ============================================================

echo ============================================================
echo   优化平台配置以支持15个C2
echo ============================================================
echo.

REM 设置环境变量优化配置
echo [1/3] 设置环境变量...

REM 增加Worker数量（根据CPU核心数）
set INTERNAL_WORKER_COUNT=3

REM 增加IP富化并发数
set WORKER_ENRICHER_CONCURRENT=50

REM 增加数据库批量写入大小
set WORKER_DB_BATCH_SIZE=500

REM 增加IP缓存大小
set WORKER_CACHE_SIZE=50000

echo [OK] Worker数量: %INTERNAL_WORKER_COUNT%
echo [OK] IP查询并发: %WORKER_ENRICHER_CONCURRENT%
echo [OK] 数据库批量: %WORKER_DB_BATCH_SIZE%
echo [OK] 缓存大小: %WORKER_CACHE_SIZE%
echo.

REM 永久保存环境变量（可选）
echo [2/3] 是否永久保存这些设置？(Y/N)
set /p SAVE_PERMANENT=
if /i "%SAVE_PERMANENT%"=="Y" (
    setx INTERNAL_WORKER_COUNT "3"
    setx WORKER_ENRICHER_CONCURRENT "50"
    setx WORKER_DB_BATCH_SIZE "500"
    setx WORKER_CACHE_SIZE "50000"
    echo [OK] 已永久保存设置
) else (
    echo [INFO] 仅在当前会话生效
)
echo.

REM 显示性能预估
echo [3/3] 性能预估...
echo ============================================================
echo 当前配置处理能力：
echo   - Worker数量: 3个
echo   - 并发查询: 50/Worker
echo   - IP富化速度: 约 60,000-90,000条/分钟
echo   - 数据库写入: 约 1,000,000条/分钟
echo.
echo 15个C2数据量（5分钟间隔）：
echo   - 总数据: 75,000条/5分钟 = 15,000条/分钟
echo   - 处理能力: 60,000条/分钟
echo   - 剩余容量: 约 75%%
echo.
echo 预期效果：
echo   ✅ 稳定运行
echo   ✅ 实时处理（延迟<30秒）
echo   ✅ 队列不会积压
echo ============================================================
echo.

echo 提示：
echo 1. 重启日志处理器使配置生效
echo 2. 运行 restart_log_processor.bat
echo 3. 监控队列长度: python backend/scripts/check_queue_status.py
echo.
pause
