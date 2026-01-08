@echo off
REM ============================================================
REM 批量执行数据库迁移脚本 (Windows版本)
REM 为所有僵尸网络类型执行迁移
REM ============================================================

setlocal enabledelayedexpansion

REM 数据库配置
set DB_HOST=localhost
set DB_PORT=3306
set DB_NAME=botnet
set DB_USER=root
set DB_PASS=root

REM 僵尸网络类型列表
set BOTNET_TYPES=asruex mozi andromeda moobot ramnit leethozer

echo ========================================
echo 僵尸网络平台数据库批量迁移工具
echo ========================================
echo.

REM 检查MySQL命令是否可用
where mysql >nul 2>nul
if errorlevel 1 (
    echo [错误] 未找到 mysql 命令
    echo 请确保已安装 MySQL 客户端并添加到 PATH
    pause
    exit /b 1
)

REM 确认操作
echo [警告] 此操作将修改数据库结构！
echo 数据库: %DB_HOST%:%DB_PORT%/%DB_NAME%
echo 将要迁移的僵尸网络类型: %BOTNET_TYPES%
echo.
set /p confirm="是否继续? (yes/no): "

if /i not "%confirm%"=="yes" (
    echo 操作已取消
    pause
    exit /b 0
)

REM 备份数据库
echo.
echo [备份] 正在备份数据库...
set BACKUP_FILE=botnet_backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.sql
set BACKUP_FILE=%BACKUP_FILE: =0%

mysqldump -h%DB_HOST% -P%DB_PORT% -u%DB_USER% -p%DB_PASS% %DB_NAME% > %BACKUP_FILE% 2>nul

if errorlevel 0 (
    echo [成功] 数据库备份完成: %BACKUP_FILE%
) else (
    echo [失败] 数据库备份失败
    set /p continue_without_backup="是否继续（不建议）? (yes/no): "
    if /i not "!continue_without_backup!"=="yes" (
        pause
        exit /b 1
    )
)

REM 创建日志文件
set LOG_FILE=migration_log_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
set LOG_FILE=%LOG_FILE: =0%
echo 迁移开始时间: %date% %time% > %LOG_FILE%

REM 为每个僵尸网络类型执行迁移
set success_count=0
set fail_count=0
set total_count=0

for %%t in (%BOTNET_TYPES%) do (
    set /a total_count+=1
    echo.
    echo ========================================
    echo 正在迁移: %%t
    echo ========================================
    
    REM 使用PowerShell替换脚本中的 {type} 占位符
    powershell -Command "(Get-Content database_migration.sql) -replace '\{type\}', '%%t' | Set-Content temp_migration_%%t.sql"
    
    REM 执行迁移
    mysql -h%DB_HOST% -P%DB_PORT% -u%DB_USER% -p%DB_PASS% %DB_NAME% < temp_migration_%%t.sql >> %LOG_FILE% 2>&1
    
    if errorlevel 0 (
        echo [成功] %%t 迁移成功
        set /a success_count+=1
        echo [SUCCESS] %%t >> %LOG_FILE%
    ) else (
        echo [失败] %%t 迁移失败，请查看日志: %LOG_FILE%
        set /a fail_count+=1
        echo [FAILED] %%t >> %LOG_FILE%
    )
    
    REM 清理临时文件
    del /f /q temp_migration_%%t.sql 2>nul
)

REM 输出总结
echo.
echo ========================================
echo 迁移完成统计
echo ========================================
echo 成功: %success_count%/%total_count%
echo 失败: %fail_count%/%total_count%
echo 详细日志: %LOG_FILE%
echo 数据库备份: %BACKUP_FILE%
echo.

if %fail_count% gtr 0 (
    echo [警告] 部分迁移失败，请检查日志
    echo [提示] 如需回滚，请使用备份文件恢复:
    echo mysql -h%DB_HOST% -P%DB_PORT% -u%DB_USER% -p%DB_PASS% %DB_NAME% ^< %BACKUP_FILE%
    pause
    exit /b 1
) else (
    echo [成功] 所有迁移都已成功完成！
    pause
    exit /b 0
)
