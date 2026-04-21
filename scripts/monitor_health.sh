#!/bin/bash

# 健康监控脚本 - 持续监控服务状态
# 用法: ./monitor_health.sh [检查间隔秒数，默认30]

INTERVAL=${1:-30}
LOG_FILE="/home/spider/31339752/logs/health_monitor.log"
ALERT_FILE="/home/spider/31339752/logs/health_alerts.log"

mkdir -p $(dirname "$LOG_FILE")

echo "=========================================="
echo "健康监控启动 - $(date)"
echo "检查间隔: ${INTERVAL}秒"
echo "日志文件: $LOG_FILE"
echo "=========================================="

# 连续失败次数
FAIL_COUNT=0
MAX_FAILS=3

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 检查后端API
    RESPONSE=$(curl -s --max-time 10 -o /dev/null -w "%{http_code},%{time_total}" http://localhost:8000/api/botnet-types)
    HTTP_CODE=$(echo $RESPONSE | cut -d',' -f1)
    TIME_TOTAL=$(echo $RESPONSE | cut -d',' -f2)
    
    if [ "$HTTP_CODE" = "200" ]; then
        STATUS="✅ OK"
        FAIL_COUNT=0
        
        # 检查响应时间
        if (( $(echo "$TIME_TOTAL > 5" | bc -l) )); then
            STATUS="⚠️  SLOW"
            echo "[$TIMESTAMP] 后端响应缓慢: ${TIME_TOTAL}s" | tee -a "$ALERT_FILE"
        fi
    else
        STATUS="❌ FAILED"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        
        echo "[$TIMESTAMP] 后端服务异常 - HTTP $HTTP_CODE (连续失败: $FAIL_COUNT)" | tee -a "$ALERT_FILE"
        
        # 连续失败达到阈值，尝试获取更多信息
        if [ $FAIL_COUNT -ge $MAX_FAILS ]; then
            echo "[$TIMESTAMP] 触发诊断..." | tee -a "$ALERT_FILE"
            
            # 检查进程是否还在运行
            if ! pgrep -f "uvicorn main:app" > /dev/null; then
                echo "[$TIMESTAMP] ⚠️  后端进程已停止！" | tee -a "$ALERT_FILE"
            fi
            
            # 检查端口是否监听
            if ! netstat -tuln | grep -q ":8000 "; then
                echo "[$TIMESTAMP] ⚠️  端口8000未监听！" | tee -a "$ALERT_FILE"
            fi
            
            FAIL_COUNT=0  # 重置计数器，避免重复告警
        fi
    fi
    
    # 记录到日志
    echo "[$TIMESTAMP] Backend: $STATUS | HTTP $HTTP_CODE | ${TIME_TOTAL}s" >> "$LOG_FILE"
    
    # 终端显示
    echo "[$TIMESTAMP] $STATUS | ${TIME_TOTAL}s"
    
    sleep "$INTERVAL"
done
