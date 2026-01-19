@echo off
chcp 65001 >nul
echo ========================================
echo 启动每日节点统计定时任务
echo ========================================
echo.
echo 定时任务将在每天上午8:00执行
echo 按 Ctrl+C 停止任务
echo.
echo ========================================
echo.

cd /d %~dp0
python daily_node_counter.py

pause
