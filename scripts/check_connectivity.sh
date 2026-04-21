#!/bin/bash

echo "=========================================="
echo "系统诊断工具 - $(date)"
echo "=========================================="

# 1. 检查后端服务
echo -e "\n[1/6] 检查后端服务..."
if curl -s --max-time 5 http://localhost:8000/api/botnet-types > /dev/null; then
    echo "✅ 后端服务正常 (localhost:8000)"
    RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" http://localhost:8000/api/botnet-types)
    echo "   响应时间: ${RESPONSE_TIME}s"
else
    echo "❌ 后端服务异常"
fi

# 2. 检查前端服务
echo -e "\n[2/6] 检查前端服务..."
if curl -s --max-time 5 http://localhost:9000 > /dev/null; then
    echo "✅ 前端服务正常 (localhost:9000)"
else
    echo "❌ 前端服务异常"
fi

# 3. 检查进程
echo -e "\n[3/6] 检查运行进程..."
echo "后端进程:"
ps aux | grep "[u]vicorn" | awk '{print "  PID: "$2" | CPU: "$3"% | MEM: "$4"% | "$11" "$12" "$13}'
echo "日志处理进程:"
ps aux | grep "[l]og_processor" | awk '{print "  PID: "$2" | CPU: "$3"% | MEM: "$4"% | "$11" "$12}'

# 4. 检查端口监听
echo -e "\n[4/6] 检查端口监听..."
netstat -tuln | grep -E "8000|9000" | while read line; do
    echo "  $line"
done

# 5. 检查最近的错误日志
echo -e "\n[5/6] 检查最近的错误..."
if [ -f /home/spider/31339752/backend/logs/api_backend.log ]; then
    ERROR_COUNT=$(tail -n 100 /home/spider/31339752/backend/logs/api_backend.log | grep -c -E "ERROR|Exception")
    if [ $ERROR_COUNT -gt 0 ]; then
        echo "⚠️  发现 $ERROR_COUNT 个错误（最近100行日志）"
        tail -n 100 /home/spider/31339752/backend/logs/api_backend.log | grep -E "ERROR|Exception" | tail -n 5
    else
        echo "✅ 无最近错误"
    fi
else
    echo "⚠️  日志文件不存在"
fi

# 6. 系统资源
echo -e "\n[6/6] 系统资源使用..."
echo "  内存使用: $(free -h | awk 'NR==2{print $3"/"$2" ("int($3/$2*100)"%)"}')"
echo "  CPU负载:$(uptime | awk -F'load average:' '{print $2}')"
echo "  磁盘使用: $(df -h / | awk 'NR==2{print $3"/"$2" ("$5")"}')"

# 7. 网络连通性（如果在VPN环境）
echo -e "\n[7/7] 网络连通性..."
if ping -c 1 -W 2 10.61.241.38 > /dev/null 2>&1; then
    echo "✅ 服务器10.61.241.38可达"
else
    echo "⚠️  服务器10.61.241.38不可达（VPN可能未连接）"
fi

echo -e "\n=========================================="
echo "诊断完成"
echo "=========================================="
