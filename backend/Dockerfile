# ============================================================
# 僵尸网络接管集成平台 - 后端 Dockerfile
# ============================================================

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制后端代码
COPY . .

# 在Docker环境中使用 config_docker.py 覆盖 config.py
RUN mv config_docker.py config.py

# 创建日志目录
RUN mkdir -p logs/asruex logs/mozi logs/ramnit logs/andromeda logs/moobot logs/leethozer

# 创建日志处理器状态目录
RUN mkdir -p log_processor/.state

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/province-amounts', timeout=5)" || exit 1

# 复制启动脚本
COPY start_services.sh /app/start_services.sh
RUN chmod +x /app/start_services.sh

# 启动命令
CMD ["/app/start_services.sh"]

