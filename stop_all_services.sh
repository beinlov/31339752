#!/bin/bash
# 停止所有服务

echo "停止僵尸网络监控系统所有服务..."

cd "$(dirname "$0")"
ROOT_DIR=$(pwd)

if [ -f "$ROOT_DIR/pids.txt" ]; then
    echo "读取进程ID..."
    while read pid; do
        if ps -p $pid > /dev/null 2>&1; then
            echo "停止进程 $pid..."
            kill $pid
        else
            echo "进程 $pid 未运行"
        fi
    done < "$ROOT_DIR/pids.txt"
    
    # 删除PID文件
    rm "$ROOT_DIR/pids.txt"
    echo "所有服务已停止"
else
    echo "未找到 pids.txt 文件"
    echo "尝试通过进程名称停止..."
    
    pkill -f "python.*main.py"
    pkill -f "python.*aggregator.py"
    
    echo "已发送停止信号"
fi



