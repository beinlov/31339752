#!/bin/bash
# 快速切换到拉取模式脚本

set -e

echo "========================================="
echo "切换到拉取模式 (Pull Mode)"
echo "========================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 停止中转服务器
echo -e "\n${YELLOW}步骤1: 停止中转服务器...${NC}"
if pgrep -f relay_service.py > /dev/null; then
    pkill -f relay_service.py
    sleep 2
    echo -e "${GREEN}✅ 中转服务器已停止${NC}"
else
    echo -e "${GREEN}✅ 中转服务器未运行${NC}"
fi

# 2. 停止平台服务器
echo -e "\n${YELLOW}步骤2: 停止平台服务器...${NC}"
if pgrep -f "python3 main.py" > /dev/null; then
    pkill -f "python3 main.py"
    sleep 2
    echo -e "${GREEN}✅ 平台服务器已停止${NC}"
else
    echo -e "${GREEN}✅ 平台服务器未运行${NC}"
fi

# 3. 清除推送模式环境变量
echo -e "\n${YELLOW}步骤3: 清除推送模式配置...${NC}"
unset DATA_TRANSFER_MODE
unset PUSH_SIGNATURE_SECRET
unset PUSH_API_KEY
echo -e "${GREEN}✅ 环境变量已清除${NC}"

# 4. 创建拉取模式配置
echo -e "\n${YELLOW}步骤4: 配置拉取模式...${NC}"
cd /home/spider/31339752/backend

cat > .env.pull << 'EOF'
# 拉取模式配置
export DATA_TRANSFER_MODE="pull"
export ENABLE_REMOTE_PULLING="true"
EOF

echo -e "${GREEN}✅ 拉取模式配置已创建: backend/.env.pull${NC}"

# 5. 检查VPN连接（可选）
echo -e "\n${YELLOW}步骤5: 检查网络连通性...${NC}"
if ping -c 1 -W 2 10.8.0.1 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ C2端网络连通 (10.8.0.1)${NC}"
else
    echo -e "${RED}⚠️  警告: 无法连接到C2端 (10.8.0.1)${NC}"
    echo -e "${YELLOW}   请确保VPN已连接: systemctl status openvpn@client${NC}"
fi

# 6. 启动平台服务器
echo -e "\n${YELLOW}步骤6: 启动平台服务器...${NC}"
source .env.pull

# 后台启动
nohup python3 main.py > /dev/null 2>&1 &
PLATFORM_PID=$!

sleep 3

# 检查是否成功启动
if ps -p $PLATFORM_PID > /dev/null; then
    echo -e "${GREEN}✅ 平台服务器已启动 (PID: $PLATFORM_PID)${NC}"
else
    echo -e "${RED}❌ 平台服务器启动失败${NC}"
    echo -e "${YELLOW}   请查看日志: tail -f backend/logs/app.log${NC}"
    exit 1
fi

# 7. 显示状态
echo -e "\n========================================="
echo -e "${GREEN}✅ 切换完成！${NC}"
echo "========================================="
echo -e "数据传输模式: ${GREEN}pull${NC}"
echo -e "平台服务器PID: ${GREEN}$PLATFORM_PID${NC}"
echo ""
echo "查看日志:"
echo "  tail -f /home/spider/31339752/backend/logs/app.log"
echo ""
echo "检查进程:"
echo "  ps aux | grep 'python3 main.py'"
echo ""
echo "停止服务:"
echo "  pkill -f 'python3 main.py'"
echo "========================================="
