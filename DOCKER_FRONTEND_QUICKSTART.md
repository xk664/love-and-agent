# 前端 Docker 快速部署指南

## 一键部署

```bash
# 1. 克隆项目
git clone <your-repo-url> love-and-agent
cd love-and-agent

# 2. 启动前端
docker-compose -f docker-compose.frontend.yml up -d

# 3. 查看日志
docker-compose -f docker-compose.frontend.yml logs -f yu-agent-frontend
```

## 验证部署

```bash
# 检查服务状态
docker-compose -f docker-compose.frontend.yml ps

# 访问前端
curl http://localhost/
```

## 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| yu-agent-frontend | 80 | Vue 前端（nginx） |

## 架构说明

```
用户浏览器
    │
    ▼
Nginx (port:80) ─── /api/* ──→ 后端服务 (106.53.178.125:8000)
    │
    ▼
Vue 静态文件
```

- **前端**: http://your-server-ip/
- **后端**: http://106.53.178.125:8000/

Nginx 会自动将 `/api/*` 请求代理到你的后端服务。

## 常用命令

```bash
# 停止服务
docker-compose -f docker-compose.frontend.yml down

# 重启服务
docker-compose -f docker-compose.frontend.yml restart

# 重新构建（代码更新后）
docker-compose -f docker-compose.frontend.yml up -d --build

# 查看日志
docker-compose -f docker-compose.frontend.yml logs -f yu-agent-frontend

# 进入容器
docker exec -it yu-agent-frontend /bin/sh
```

## 故障排查

```bash
# 查看容器状态
docker-compose -f docker-compose.frontend.yml ps

# 查看日志
docker-compose -f docker-compose.frontend.yml logs yu-agent-frontend

# 进入容器调试
docker exec -it yu-agent-frontend /bin/sh

# 测试容器内能否访问后端
docker exec -it yu-agent-frontend curl http://106.53.178.125:8000/
```

## 更多信息

详细部署指南请查看 [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)
