@echo off
chcp 65001 >nul
echo ========================================
echo   Ramnit数据导入修复验证脚本
echo ========================================
echo.

echo [步骤1] 验证配置文件...
echo ----------------------------------------
cd /d "%~dp0"
python test/test_ramnit_import.py
if errorlevel 1 (
    echo.
    echo ❌ 配置验证失败！
    echo    请检查 backend/log_processor/config.py
    echo    确保 important_events 为空列表: []
    pause
    exit /b 1
)
echo.

echo [步骤2] 测试日志格式解析...
echo ----------------------------------------
python test/test_ramnit_parser.py
if errorlevel 1 (
    echo.
    echo ❌ 格式解析测试失败！
    pause
    exit /b 1
)
echo.

echo [步骤3] 检查数据库连接...
echo ----------------------------------------
echo 请确认以下信息:
echo   数据库: botnet
echo   用户: root
echo   密码: 123456 (config.py中配置)
echo.
echo 按任意键继续...
pause >nul

echo.
echo ========================================
echo   ✅ 验证完成！
echo ========================================
echo.
echo 修复内容:
echo   1. ✅ 日志解析器支持Ramnit格式
echo   2. ✅ 系统消息自动过滤
echo   3. ✅ important_events配置修正
echo   4. ✅ 事件类型智能识别
echo.
echo 下一步操作:
echo   1. 停止正在运行的日志处理器 (Ctrl+C)
echo   2. 运行: cd backend\log_processor
echo   3. 运行: python main.py
echo   4. 上传Ramnit日志到: backend\logs\ramnit\
echo   5. 观察日志输出和数据库
echo.
echo 数据库验证SQL:
echo   SELECT COUNT(*) FROM botnet_nodes_ramnit;
echo   SELECT * FROM botnet_nodes_ramnit ORDER BY created_at DESC LIMIT 10;
echo.
pause

