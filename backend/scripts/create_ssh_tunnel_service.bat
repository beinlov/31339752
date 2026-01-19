@echo off
REM ============================================================
REM SSH隧道服务安装脚本（Windows）
REM 需要安装plink（PuTTY工具包）
REM ============================================================

echo 正在创建SSH隧道服务...
echo.

REM 配置（请修改这些参数）
set REMOTE_USER=你的用户名
set REMOTE_HOST=你的远程IP
set LOCAL_PORT=8888
set REMOTE_PORT=8888

REM 使用NSSM创建服务（需要先下载nssm.exe）
REM 下载: https://nssm.cc/download

if not exist nssm.exe (
    echo [错误] 未找到nssm.exe
    echo 请从 https://nssm.cc/download 下载并放在此目录
    pause
    exit /b 1
)

REM 创建服务
nssm install SSHTunnel_C2 plink.exe -N -L %LOCAL_PORT%:localhost:%REMOTE_PORT% %REMOTE_USER%@%REMOTE_HOST%

REM 配置服务参数
nssm set SSHTunnel_C2 AppStdout tunnel.log
nssm set SSHTunnel_C2 AppStderr tunnel_error.log
nssm set SSHTunnel_C2 Start SERVICE_AUTO_START

echo.
echo 服务创建完成！
echo 启动服务: net start SSHTunnel_C2
echo 停止服务: net stop SSHTunnel_C2
echo 删除服务: nssm remove SSHTunnel_C2 confirm
pause
