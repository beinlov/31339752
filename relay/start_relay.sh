#!/bin/bash
################################################################################
# 中转服务器启动脚本
# 用于启动中转服务，支持环境变量配置
################################################################################

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}=================================${NC}"
echo -e "${GREEN}中转服务器启动脚本${NC}"
echo -e "${GREEN}=================================${NC}"

# 检查Python版本
echo -e "\n${YELLOW}[1/5] 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python版本: $PYTHON_VERSION${NC}"

# 检查依赖
echo -e "\n${YELLOW}[2/5] 检查依赖包...${NC}"
REQUIRED_PACKAGES="requests boto3"
MISSING_PACKAGES=""

for pkg in $REQUIRED_PACKAGES; do
    if ! python3 -c "import $pkg" 2>/dev/null; then
        MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
    fi
done

if [ -n "$MISSING_PACKAGES" ]; then
    echo -e "${YELLOW}缺少依赖包:$MISSING_PACKAGES${NC}"
    echo -e "${YELLOW}正在安装...${NC}"
    pip3 install $MISSING_PACKAGES
fi

echo -e "${GREEN}✓ 依赖包完整${NC}"

# 检查配置文件
echo -e "\n${YELLOW}[3/5] 检查配置文件...${NC}"
if [ ! -f "relay_config.json" ]; then
    if [ -f "relay_config_example.json" ]; then
        echo -e "${YELLOW}未找到relay_config.json，是否从示例创建？ (y/n)${NC}"
        read -r response
        if [ "$response" = "y" ]; then
            cp relay_config_example.json relay_config.json
            echo -e "${GREEN}✓ 已创建relay_config.json，请编辑配置后重新运行${NC}"
            exit 0
        else
            echo -e "${RED}错误: 需要配置文件relay_config.json${NC}"
            exit 1
        fi
    else
        echo -e "${RED}错误: 未找到配置文件${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ 配置文件存在${NC}"

# 检查AWS凭证（如果启用IP切换）
echo -e "\n${YELLOW}[4/5] 检查AWS凭证...${NC}"
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo -e "${YELLOW}⚠ 未设置AWS凭证环境变量${NC}"
    echo -e "${YELLOW}  如果启用了IP切换功能，请设置:${NC}"
    echo -e "${YELLOW}  export AWS_ACCESS_KEY_ID=your-key${NC}"
    echo -e "${YELLOW}  export AWS_SECRET_ACCESS_KEY=your-secret${NC}"
else
    echo -e "${GREEN}✓ AWS凭证已设置${NC}"
fi

# 检查OpenVPN（如果启用IP切换）
if [ -f "/etc/openvpn/client.conf" ]; then
    echo -e "${GREEN}✓ OpenVPN配置文件存在${NC}"
else
    echo -e "${YELLOW}⚠ OpenVPN配置文件不存在 (/etc/openvpn/client.conf)${NC}"
    echo -e "${YELLOW}  如果启用了IP切换功能，需要配置OpenVPN${NC}"
fi

# 启动服务
echo -e "\n${YELLOW}[5/5] 启动中转服务...${NC}"
echo -e "${GREEN}=================================${NC}"

# 设置环境变量（如果未设置）
export PYTHONUNBUFFERED=1

# 启动
exec python3 relay_service.py "$@"
