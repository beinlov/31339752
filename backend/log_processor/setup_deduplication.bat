@echo off
REM ============================================================
REM 数据去重机制部署脚本 (Windows)
REM ============================================================

echo.
echo ============================================================
echo   僵尸网络日志处理系统 - 数据去重机制部署
echo ============================================================
echo.

REM 数据库配置
set DB_HOST=localhost
set DB_USER=root
set DB_NAME=botnet

set /p DB_PASS="请输入MySQL密码: "
echo.

REM 测试数据库连接
echo 测试数据库连接...
mysql -h %DB_HOST% -u %DB_USER% -p%DB_PASS% %DB_NAME% -e "SELECT 1" >nul 2>&1

if %errorlevel% neq 0 (
    echo [错误] 数据库连接失败！请检查配置
    pause
    exit /b 1
)

echo [成功] 数据库连接成功
echo.

REM 步骤1: 备份数据库
echo 步骤 1/3: 备份数据库...
set BACKUP_FILE=botnet_backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.sql
set BACKUP_FILE=%BACKUP_FILE: =0%

mysqldump -h %DB_HOST% -u %DB_USER% -p%DB_PASS% %DB_NAME% > %BACKUP_FILE% 2>nul

if %errorlevel% equ 0 (
    echo [成功] 数据库已备份到: %BACKUP_FILE%
) else (
    echo [错误] 备份失败！
    pause
    exit /b 1
)
echo.

REM 步骤2: 清理重复数据
echo 步骤 2/3: 清理现有重复数据...
echo [警告] 这将删除重复记录，只保留最早的一条
set /p CONFIRM="是否继续？(y/n): "

if /i not "%CONFIRM%"=="y" (
    echo 操作已取消
    pause
    exit /b 0
)

mysql -h %DB_HOST% -u %DB_USER% -p%DB_PASS% %DB_NAME% < clean_duplicates.sql

if %errorlevel% equ 0 (
    echo [成功] 重复数据已清理
) else (
    echo [错误] 清理失败！
    echo 可以从备份恢复: mysql -u %DB_USER% -p %DB_NAME% ^< %BACKUP_FILE%
    pause
    exit /b 1
)
echo.

REM 步骤3: 添加唯一约束
echo 步骤 3/3: 添加唯一约束...
mysql -h %DB_HOST% -u %DB_USER% -p%DB_PASS% %DB_NAME% < add_unique_constraint.sql

if %errorlevel% equ 0 (
    echo [成功] 唯一约束已添加
) else (
    echo [错误] 添加约束失败！
    echo 可能原因: 仍有重复数据或约束已存在
    pause
    exit /b 1
)
echo.

REM 验证
echo 验证部署...
mysql -h %DB_HOST% -u %DB_USER% -p%DB_PASS% %DB_NAME% -e "SHOW INDEX FROM botnet_nodes_asruex WHERE Key_name = 'idx_unique_record'" 2>nul | find /c /v "" > temp_count.txt
set /p RESULT=<temp_count.txt
del temp_count.txt

if %RESULT% gtr 1 (
    echo [成功] 验证成功！唯一约束已生效
) else (
    echo [警告] 验证失败，请手动检查
)
echo.

REM 完成
echo ============================================================
echo   部署完成！
echo ============================================================
echo.
echo 下一步:
echo   1. 重启日志处理器: python log_processor\main.py
echo   2. 查看去重统计: 在日志中查找 "Duplicates"
echo   3. 阅读文档: type DEDUPLICATION.md
echo.
echo 备份文件: %BACKUP_FILE%
echo 如需恢复: mysql -u %DB_USER% -p %DB_NAME% ^< %BACKUP_FILE%
echo.

pause





