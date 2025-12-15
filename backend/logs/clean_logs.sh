#!/bin/bash
echo "============================================================"
echo "日志文件清理脚本"
echo "============================================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

echo "[1/3] 清理新位置的日志文件..."
cd "$SCRIPT_DIR"

# 清空新位置的日志文件
for log_file in log_processor.log stats_aggregator.log remote_uploader.log main_app.log; do
    if [ -f "$log_file" ]; then
        > "$log_file"
        echo "  - $log_file 已清空"
    fi
done

echo ""
echo "[2/3] 删除旧位置的日志文件..."

# 删除backend根目录的旧日志文件
cd "$BACKEND_DIR"
for log_file in log_processor.log stats_aggregator.log; do
    if [ -f "$log_file" ]; then
        rm -f "$log_file"
        echo "  - backend/$log_file 已删除"
    fi
done

# 删除log_processor子目录的旧日志文件
if [ -f "log_processor/log_processor.log" ]; then
    rm -f "log_processor/log_processor.log"
    echo "  - backend/log_processor/log_processor.log 已删除"
fi

echo ""
echo "[3/3] 完成！"
echo ""
echo "============================================================"
echo "日志清理完成"
echo "============================================================"
