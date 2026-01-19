@echo off
chcp 65001 >nul
echo ============================================================
echo 抑制阻断功能初始化脚本
echo ============================================================
echo.

echo [1/2] 初始化数据库表...
cd backend
python scripts\init_suppression_tables.py
if %errorlevel% neq 0 (
    echo.
    echo ? 数据库初始化失败！
    echo 请检查：
    echo   1. MySQL服务是否运行
    echo   2. backend\config.py 中的数据库配置是否正确
    echo   3. 数据库用户是否有足够权限
    pause
    exit /b 1
)

echo.
echo ============================================================
echo ? 初始化完成！
echo ============================================================
echo.
echo 下一步：
echo   1. 启动后端服务: cd backend && uvicorn main:app --reload
echo   2. 启动前端服务: cd fronted && npm run dev
echo   3. 访问 http://localhost:9000
echo   4. 在左侧菜单找到 "?? 抑制阻断策略"
echo.
echo 详细说明请查看: 抑制阻断集成说明.md
echo ============================================================
pause
