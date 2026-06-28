# Love and Agent - 云服务器部署指南

## 概述

本项目支持两种部署方式：
1. **源代码构建** - git clone 后直接构建（推荐）
2. **打包部署** - 本地打包后上传到服务器

**前置条件**：MySQL、Redis、PgVector 已安装在宿主机上。

---

## 方式一：源代码构建部署（推荐）

### 前置条件

- 云服务器已安装 Docker
- 云服务器已安装 Docker Compose
- 服务器可以访问 Git 仓库
- MySQL、Redis、PgVector 已安装并运行

### 部署步骤

#### 1. 克隆项目

```bash
# SSH 登录到云服务器
ssh user@your-server-ip

# 克隆项目
git clone <your-repo-url> love-and-agent

# 进入项目目录
cd love-and-agent
```

#### 2. 配置环境变量（可选）

编辑 [docker-compose.source.yml](docker-compose.source.yml) 中的环境变量：

```yaml
environment:
  - DATABASE_URL=mysql+aiomysql://yu_agent:password@host.docker.internal:3306/yu_agent
  - REDIS_URL=redis://host.docker.internal:6379/0
  - PGVECTOR_CONNECTION_STRING=postgresql+asyncpg://yu_agent:password@host.docker.internal:5432/yu_agent_vector
```

#### 3. 启动服务

```bash
# 使用源代码构建版本
docker-compose -f docker-compose.source.yml up -d

# 查看构建进度
docker-compose -f docker-compose.source.yml build

# 查看日志
docker-compose -f docker-compose.source.yml logs -f yu-agent
```

#### 4. 验证部署

```bash
# 检查容器状态
docker-compose -f docker-compose.source.yml ps

# 测试 API
curl http://localhost:8000/

# 查看健康检查
curl http://localhost:8000/internal/health/live
```

### 网络说明

| 服务 | 地址 | 说明 |
|------|------|------|
| AI Agent API | http://server-ip:8000 | 主应用 |
| API 文档 | http://server-ip:8000/docs | Swagger 文档（仅 DEBUG 模式） |
| MySQL | host.docker.internal:3306 | 宿主机上的 MySQL |
| Redis | host.docker.internal:6379 | 宿主机上的 Redis |
| PgVector | host.docker.internal:5432 | 宿主机上的 PgVector |

---

## 方式二：打包部署

### 本地打包

```bash
# 进入项目目录
cd yu-ai-agent-python

# 运行打包脚本
package.bat

# 输出文件：dist/yu-ai-agent-python-*.tar.gz
```

### 上传到服务器

```bash
# 使用 scp 上传
scp dist/yu-ai-agent-python-*.tar.gz user@your-server:/tmp/

# 或使用 rsync
rsync -avz dist/yu-ai-agent-python-*.tar.gz user@your-server:/tmp/
```

### 服务器端构建

```bash
# SSH 登录服务器
ssh user@your-server

# 创建部署目录
mkdir -p /opt/yu-agent
cd /opt/yu-agent

# 解压包
tar -xzf /tmp/yu-ai-agent-python-*.tar.gz

# 构建 Docker 镜像
docker build -t yu-ai-agent:latest .

# 运行容器
docker run -d \
  --name yu-agent \
  -p 8000:8000 \
  --add-host=host.docker.internal:host-gateway \
  -v /opt/yu-agent/config:/app/config \
  -v /opt/yu-agent/logs:/app/logs \
  -e APP_ENV=prod \
  -e DATABASE_URL=mysql+aiomysql://yu_agent:password@host.docker.internal:3306/yu_agent \
  -e REDIS_URL=redis://host.docker.internal:6379/0 \
  -e PGVECTOR_CONNECTION_STRING=postgresql+asyncpg://yu_agent:password@host.docker.internal:5432/yu_agent_vector \
  yu-ai-agent:latest
```

---

## 常用运维命令

### 查看日志

```bash
# 查看应用日志
docker-compose -f docker-compose.source.yml logs -f yu-agent

# 查看最近 100 行日志
docker-compose -f docker-compose.source.yml logs --tail=100 yu-agent
```

### 重启服务

```bash
# 重启应用
docker-compose -f docker-compose.source.yml restart yu-agent

# 停止并重新启动
docker-compose -f docker-compose.source.yml down
docker-compose -f docker-compose.source.yml up -d
```

### 更新代码

```bash
# 拉取最新代码
git pull origin main

# 重新构建并启动
docker-compose -f docker-compose.source.yml up -d --build

# 或者只重新构建（不使用缓存）
docker-compose -f docker-compose.source.yml build --no-cache
docker-compose -f docker-compose.source.yml up -d
```

### 数据库操作

```bash
# 直接连接宿主机 MySQL
mysql -u yu_agent -p -h localhost

# 直接连接宿主机 Redis
redis-cli

# 直接连接宿主机 PgVector
psql -U yu_agent -d yu_agent_vector -h localhost
```

---

## 故障排查

### 1. 容器启动失败

```bash
# 查看容器日志
docker logs yu-agent

# 检查容器状态
docker inspect yu-agent

# 进入容器调试
docker exec -it yu-agent /bin/bash
```

### 2. 数据库连接失败

```bash
# 测试容器内能否访问宿主机
docker exec -it yu-agent curl http://host.docker.internal:3306

# 检查宿主机数据库是否运行
systemctl status mysql
# 或
systemctl status mysqld
```

### 3. 端口被占用

```bash
# 查看端口占用
netstat -tulpn | grep 8000

# 修改端口映射
# 编辑 docker-compose.source.yml，修改 ports 配置
ports:
  - "8001:8000"  # 改为 8001
```

### 4. 构建失败

```bash
# 清理构建缓存
docker system prune -a

# 重新构建
docker-compose -f docker-compose.source.yml build --no-cache
```

### 5. 内存不足

```bash
# 查看容器资源使用
docker stats

# 限制容器内存
# 编辑 docker-compose.source.yml
deploy:
  resources:
    limits:
      memory: 2G
```

---

## 回滚操作

如果新版本有问题，可以快速回滚：

```bash
# 停止当前版本
docker-compose -f docker-compose.source.yml down

# 切换到之前的版本
git checkout <previous-commit-hash>

# 重新构建并启动
docker-compose -f docker-compose.source.yml up -d --build
```

---

## 技术支持

遇到问题时，请检查：
1. Docker 和 Docker Compose 版本
2. 服务器防火墙设置
3. 环境变量配置
4. 宿主机数据库服务状态
5. 应用日志

如有疑问，请查看项目文档或提交 Issue。
