# Docker 快速部署指南

## 一键部署

```bash
# 1. 克隆项目
git clone <your-repo-url> love-and-agent
cd love-and-agent

# 2. 启动应用
docker-compose -f docker-compose.source.yml up -d

# 3. 查看日志
docker-compose -f docker-compose.source.yml logs -f yu-agent
```

## 验证部署

```bash
# 检查服务状态
docker-compose -f docker-compose.source.yml ps

# 测试 API
curl http://localhost:8000/
```

## 网络说明

本配置假设 MySQL、Redis、PgVector 已安装在宿主机上，容器通过 `host.docker.internal` 访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| yu-agent | localhost:8000 | AI Agent 主应用 |
| MySQL | host.docker.internal:3306 | 宿主机上的 MySQL |
| Redis | host.docker.internal:6379 | 宿主机上的 Redis |
| PgVector | host.docker.internal:5432 | 宿主机上的 PgVector |

## 常用命令

```bash
# 停止服务
docker-compose -f docker-compose.source.yml down

# 重启服务
docker-compose -f docker-compose.source.yml restart

# 重新构建（代码更新后）
docker-compose -f docker-compose.source.yml up -d --build

# 查看日志
docker-compose -f docker-compose.source.yml logs -f

# 进入容器
docker exec -it yu-agent /bin/bash
```

## 环境变量配置

编辑 [docker-compose.source.yml](docker-compose.source.yml) 中的环境变量：

```yaml
environment:
  - DATABASE_URL=mysql+aiomysql://yu_agent:password@host.docker.internal:3306/yu_agent
  - REDIS_URL=redis://host.docker.internal:6379/0
  - PGVECTOR_CONNECTION_STRING=postgresql+asyncpg://yu_agent:password@host.docker.internal:5432/yu_agent_vector
```

## 故障排查

```bash
# 查看容器状态
docker-compose -f docker-compose.source.yml ps

# 查看日志
docker-compose -f docker-compose.source.yml logs yu-agent

# 进入容器调试
docker exec -it yu-agent /bin/bash

# 测试容器内网络连通性
docker exec -it yu-agent curl http://host.docker.internal:3306
```

## 更多信息

详细部署指南请查看 [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)
