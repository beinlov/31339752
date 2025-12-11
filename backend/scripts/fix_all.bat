@echo off
REM 一键修复节点数据不一致问题
REM 此脚本会执行：数据去重 + 重建聚合表

echo ========================================
echo   节点数据修复工具
echo ========================================
echo.
echo 此脚本将执行以下操作：
echo 1. 分析重复数据
echo 2. 去重原始表
echo 3. 重建聚合表
echo 4. 验证数据一致性
echo.
echo 警告：此操作会删除重复数据！
echo 建议先备份数据库
echo.

set /p confirm="确认继续？(y/n): "
if /i not "%confirm%"=="y" (
    echo 操作已取消
    pause
    exit /b
)

echo.
echo ========================================
echo 步骤1: 分析重复数据
echo ========================================
python deduplicate_nodes.py --analyze-only
if errorlevel 1 (
    echo 分析失败！
    pause
    exit /b 1
)

echo.
set /p continue1="查看分析结果，是否继续去重？(y/n): "
if /i not "%continue1%"=="y" (
    echo 操作已取消
    pause
    exit /b
)

echo.
echo ========================================
echo 步骤2: 执行数据去重
echo ========================================
python deduplicate_nodes.py --execute
if errorlevel 1 (
    echo 去重失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo 步骤3: 重建聚合表
echo ========================================
python rebuild_aggregation.py
if errorlevel 1 (
    echo 重建聚合表失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ 所有操作完成！
echo ========================================
echo.
echo 请验证以下三个平台的数据是否一致：
echo - 后台管理系统（节点分布界面）
echo - 清除界面
echo - 僵尸网络展示处置平台
echo.
pause
