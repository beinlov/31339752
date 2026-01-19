@echo off
chcp 65001 >nul
echo ========================================
echo 数据传输测试脚本（Windows）
echo ========================================
echo.

echo [步骤1/3] 生成测试日志文件...
python mock_c2_log_generator.py --mode fast --count 5 --fast-interval 2 --log-dir ./test_logs --prefix test
if %errorlevel% neq 0 (
    echo [错误] 日志生成失败
    pause
    exit /b 1
)
echo.

echo [步骤2/3] 查看生成的文件...
dir test_logs
echo.
echo 按任意键继续查看文件内容...
pause >nul

echo.
echo [示例] 查看第一个日志文件的前10行:
echo ----------------------------------------
for /f "delims=" %%f in ('dir /b /od test_logs\*.log') do (
    set FIRST_FILE=%%f
    goto :show_content
)
:show_content
type test_logs\%FIRST_FILE% | findstr /n "^" | findstr "^[1-9]:" | findstr "^[1-9]:\|^10:"
echo ----------------------------------------
echo.

echo [步骤3/3] 测试说明:
echo.
echo 现在你可以:
echo   1. 将 test_logs 文件夹中的日志复制到C2服务器
echo   2. 启动 C2 数据服务器: python c2_data_server.py
echo   3. 启动本地日志处理器验证数据拉取
echo.
echo 或者在本地测试（如果C2服务器运行在本机）:
echo   1. 修改 config.json 的 log_dir 为 test_logs 的绝对路径
echo   2. 启动: python c2_data_server.py
echo.

echo ========================================
echo 测试日志生成完成！
echo ========================================
pause
