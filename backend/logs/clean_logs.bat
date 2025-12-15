@echo off
echo ============================================================
echo 日志文件清理脚本
echo ============================================================
echo.

echo [1/3] 清理新位置的日志文件...
cd /d "%~dp0"
if exist log_processor.log (
    type nul > log_processor.log
    echo   - log_processor.log 已清空
)
if exist stats_aggregator.log (
    type nul > stats_aggregator.log
    echo   - stats_aggregator.log 已清空
)
if exist remote_uploader.log (
    type nul > remote_uploader.log
    echo   - remote_uploader.log 已清空
)
if exist main_app.log (
    type nul > main_app.log
    echo   - main_app.log 已清空
)

echo.
echo [2/3] 删除旧位置的日志文件...
cd /d "%~dp0\.."

if exist log_processor.log (
    del log_processor.log
    echo   - backend\log_processor.log 已删除
)
if exist stats_aggregator.log (
    del stats_aggregator.log
    echo   - backend\stats_aggregator.log 已删除
)

cd /d "%~dp0\..\log_processor"
if exist log_processor.log (
    del log_processor.log
    echo   - backend\log_processor\log_processor.log 已删除
)

echo.
echo [3/3] 完成！
echo.
echo ============================================================
echo 日志清理完成
echo ============================================================
pause
