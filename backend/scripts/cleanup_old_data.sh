#!/bin/bash
# 数据清理定时任务脚本
# 建议通过crontab定时执行：0 2 * * * /home/spider/31339752/backend/scripts/cleanup_old_data.sh

# 切换到脚本目录
cd "$(dirname "$0")"

# 日志文件
LOG_FILE="/home/spider/31339752/backend/logs/data_cleanup.log"
LOG_DIR="$(dirname "$LOG_FILE")"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 记录开始时间
echo "========================================" >> "$LOG_FILE"
echo "数据清理任务开始: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 执行清理（保留180天数据）
python3 cleanup_old_data.py --days 180 >> "$LOG_FILE" 2>&1

# 记录结束时间
echo "数据清理任务完成: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 保留最近30天的日志
find "$LOG_DIR" -name "data_cleanup.log.*" -mtime +30 -delete 2>/dev/null

# 轮转日志（超过10MB则重命名）
LOG_SIZE=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
if [ "$LOG_SIZE" -gt 10485760 ]; then
    mv "$LOG_FILE" "${LOG_FILE}.$(date '+%Y%m%d_%H%M%S')"
fi
