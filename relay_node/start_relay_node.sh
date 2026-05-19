#!/bin/bash

# 中继节点启动脚本

echo "=========================================="
echo "启动中继节点服务器"
echo "=========================================="

# 检查Python版本
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ 错误: 未找到Python"
    exit 1
fi

echo "✅ 使用Python: $PYTHON_CMD"
$PYTHON_CMD --version

# 检查依赖
echo ""
echo "检查依赖..."
$PYTHON_CMD -c "import aiohttp" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 缺少依赖，正在安装..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
fi
echo "✅ 依赖检查完成"

# 检查配置文件
if [ ! -f "relay_node_config.json" ]; then
    echo "❌ 错误: 配置文件不存在 relay_node_config.json"
    echo "请复制 relay_node_config.json.example 并修改配置"
    exit 1
fi

# 加载环境变量（如果存在）
if [ -f ".env" ]; then
    echo "加载环境变量: .env"
    export $(cat .env | grep -v '^#' | xargs)
fi

# 启动服务器
echo ""
echo "=========================================="
echo "启动服务器..."
echo "=========================================="
$PYTHON_CMD relay_data_server.py

# 捕获退出信号
trap 'echo ""; echo "收到停止信号，正在关闭..."; exit 0' INT TERM
