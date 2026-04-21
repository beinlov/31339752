#!/bin/bash
# 检查是否有SSH端口转发

echo "检查SSH隧道/端口转发..."
echo ""

# 检查当前SSH连接
echo "=== 当前SSH连接 ==="
who | grep -v "(:0)"

echo ""
echo "=== 活跃的SSH端口转发 ==="
# 在Linux上检查
netstat -tnlp 2>/dev/null | grep "127.0.0.1:8000\|127.0.0.1:9000" || echo "未检测到端口转发"

echo ""
echo "=== SSH进程 ==="
ps aux | grep ssh | grep -v grep | grep -v sshd

echo ""
echo "提示："
echo "如果第一台电脑使用了SSH端口转发，它会在本地监听8000和9000端口"
echo "这样 localhost:8000 和 localhost:9000 就会通过SSH隧道连接到服务器"
