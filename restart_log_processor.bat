@echo off
REM ============================================================
REM 重启日志处理器脚本（清除缓存）
REM ============================================================

echo ============================================================
echo   重启日志处理器
echo ============================================================
echo.

REM 1. 关闭旧进程
echo [1/4] 关闭旧的日志处理器进程...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Botnet Log Processor*" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] 已关闭旧进程
) else (
    echo [INFO] 未发现运行中的日志处理器
)
timeout /t 1 /nobreak >nul

REM 2. 清除缓存
echo.
echo [2/4] 清除Python缓存...
cd /d "%~dp0"
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc >nul 2>&1
echo [OK] 缓存已清除

REM 3. 验证配置
echo.
echo [3/4] 验证C2配置...
python backend/scripts/check_c2_config.py
echo.

REM 4. 启动日志处理器
echo [4/4] 启动日志处理器...
echo.
cd /d "%~dp0backend\log_processor"
start "Botnet Log Processor" cmd /k "python main.py"
timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo   日志处理器已启动
echo ============================================================
echo.
echo 查看日志: type backend\logs\log_processor.log
echo 查看窗口: 切换到 "Botnet Log Processor" 窗口
echo.
pause
