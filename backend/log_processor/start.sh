#!/bin/bash
# 启动僵尸网络日志处理器

echo "Starting Botnet Log Processor..."
echo "================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 not found"
    exit 1
fi

# 检查依赖
echo "Checking dependencies..."
python3 -c "import pymysql, watchdog" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install pymysql watchdog awaits
fi

# 启动主程序
echo "Starting main processor..."
cd "$(dirname "$0")"
python3 main.py

echo "Processor stopped."



