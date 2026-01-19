@echo off
setlocal enabledelayedexpansion

echo Testing Node.js detection...
echo.

echo Test 1: Direct node command
node --version
echo Return code: !errorlevel!
echo.

echo Test 2: Check node in PATH
where node
echo Return code: !errorlevel!
echo.

echo Test 3: Try to get version
for /f "tokens=1" %%i in ('node --version 2^>nul') do set NODE_VERSION=%%i
echo Node version: !NODE_VERSION!
echo.

echo Test 4: Check errorlevel after node command
node --version >nul 2>&1
set NODE_CHECK=!errorlevel!
echo Errorlevel after node: !NODE_CHECK!
if !NODE_CHECK! neq 0 (
    echo FAILED - Node.js not found
) else (
    echo SUCCESS - Node.js found
)
echo.

pause
