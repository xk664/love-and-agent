# Dockerfile - 用于部署打包后的可执行文件
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装必要的系统依赖
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制打包后的可执行文件
COPY yu-ai-agent-python/dist/yu-agent /app/yu-agent

# 赋予执行权限
RUN chmod +x /app/yu-agent

# 创建配置目录
RUN mkdir -p /app/config

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# 启动命令
ENTRYPOINT ["/app/yu-agent"]
