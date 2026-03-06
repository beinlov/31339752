@echo off
REM 设置接管节点统计数据聚合的Windows定时任务

echo 正在设置接管节点统计数据聚合定时任务...

REM 获取当前脚本所在目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set PYTHON_SCRIPT=%PROJECT_ROOT%\stats_aggregator\takeover_stats_aggregator.py

REM 检查Python脚本是否存在
if not exist "%PYTHON_SCRIPT%" (
    echo 错误: 找不到聚合脚本 %PYTHON_SCRIPT%
    pause
    exit /b 1
)

REM 创建定时任务
schtasks /create /tn "TakeoverStatsAggregator" /tr "python \"%PYTHON_SCRIPT%\" --once" /sc minute /mo 1 /f /ru "SYSTEM"

if %errorlevel% equ 0 (
    echo 定时任务创建成功！
    echo 任务名称: TakeoverStatsAggregator
    echo 执行频率: 每分钟一次
    echo 执行脚本: %PYTHON_SCRIPT%
    echo.
    echo 可以使用以下命令管理任务:
    echo   启动任务: schtasks /run /tn "TakeoverStatsAggregator"
    echo   停止任务: schtasks /end /tn "TakeoverStatsAggregator"
    echo   删除任务: schtasks /delete /tn "TakeoverStatsAggregator" /f
    echo   查看任务: schtasks /query /tn "TakeoverStatsAggregator"
) else (
    echo 定时任务创建失败！
    echo 请确保以管理员权限运行此脚本
)

pause
