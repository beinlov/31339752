#!/bin/bash

# C2数据服务器启动脚本
# 使用虚拟环境运行服务器

cd /home

# 激活虚拟环境
source c2_env/bin/activate

# 设置环境变量（可选）
export C2_API_KEY="KiypG4zWLXqnREqGPH8L2Oh9ybvi6Yh4"
export C2_HTTP_HOST="0.0.0.0"
export C2_HTTP_PORT="8888"

# 启动服务器
echo "启动C2数据服务器..."
echo "配置文件: config.production.json"
echo "监听地址: ${C2_HTTP_HOST}:${C2_HTTP_PORT}"
echo "API Key: ${C2_API_KEY:0:6}***"
echo ""

python3 c2_data_server.py
