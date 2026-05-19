FROM python:3.9-slim

WORKDIR /app

# 设置环境变量，确保日志即时输出
ENV PYTHONUNBUFFERED=1

# 复制当前目录下所有文件到容器 (注意：点与点之间必须有空格)
COPY . .

# 暴露 UDP 端口
EXPOSE 8000/udp

# 启动命令
CMD ["python", "main.py"]