#!/bin/bash
# 部署脚本：将打包文件发送到云服务器并构建 Docker 镜像

# ============ 配置区域 ============
# 云服务器信息
REMOTE_USER="root"
REMOTE_HOST="your-server-ip"  # 修改为你的服务器 IP
REMOTE_DIR="/opt/yu-agent"

# 本地文件
LOCAL_EXE="yu-ai-agent-python/dist/yu-agent.exe"
LOCAL_DOCKERFILE="Dockerfile"
# ==================================

echo "========================================"
echo "  Yu AI Agent 部署脚本"
echo "========================================"

# 1. 创建远程目录
echo ""
echo "[1/4] 创建远程目录..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${REMOTE_DIR}"

# 2. 上传文件
echo "[2/4] 上传打包文件..."
scp ${LOCAL_EXE} ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/yu-agent
scp ${LOCAL_DOCKERFILE} ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/
scp docker-compose.yml ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/ 2>/dev/null || true

# 3. 构建镜像
echo "[3/4] 构建 Docker 镜像..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'EOF'
cd /opt/yu-agent
docker build -t yu-agent:latest .
EOF

# 4. 启动容器
echo "[4/4] 启动容器..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'EOF'
cd /opt/yu-agent
docker stop yu-agent 2>/dev/null || true
docker rm yu-agent 2>/dev/null || true
docker run -d \
    --name yu-agent \
    --restart unless-stopped \
    -p 8000:8000 \
    -v /opt/yu-agent/config:/app/config \
    yu-agent:latest
EOF

echo ""
echo "========================================"
echo "  部署完成！"
echo "  服务地址: http://${REMOTE_HOST}:8000"
echo "========================================"
