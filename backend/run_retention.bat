@echo off
REM 僵尸网络平台数据保留策略执行脚本
REM 用于Windows定时任务

echo ========================================
echo 僵尸网络平台 - 数据保留策略执行
echo 时间: %date% %time%
echo ========================================

REM 切换到脚本目录
cd /d %~dp0

REM 激活虚拟环境（如果使用）
REM call venv\Scripts\activate

REM 执行数据保留任务
python scripts\retention_manager.py --mode daily

echo.
echo ========================================
echo 执行完成
echo ========================================

REM 如果需要查看日志，取消下面的注释
REM pause
