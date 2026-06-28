# Yu AI Agent - Docker 部署打包指南

## 概述

本项目提供了两种打包方式，用于将 Python 项目部署到云服务器：

1. **Docker 部署包** - 打包源代码，用于在云服务器上构建 Docker 镜像
2. **PyInstaller 可执行文件** - 打包为独立的 Windows 可执行文件

---

## 方式一：Docker 部署包（推荐）

### 打包步骤

#### Windows 批处理脚本（推荐）

```bash
# 运行打包脚本
package.bat
```

#### PowerShell 脚本

```powershell
# 运行打包脚本
.\package.ps1
```

### 打包内容

脚本会打包以下文件和目录（与 Dockerfile 保持一致）：

- `main.py` - 应用入口
- `app/` - 应用代码目录
- `config/` - 配置文件目录
- `requirements.txt` - Python 依赖

### 排除内容

以下文件和目录会被自动排除：

- `.venv/` - 虚拟环境
- `__pycache__/` - Python 缓存
- `.idea/` - IDE 配置
- `.git/` - Git 仓库
- `tests/` - 测试文件
- `logs/` - 日志文件
- `dist/` - 构建输出
- `build/` - 构建临时文件
- `*.pyc` - 编译的 Python 文件

### 输出文件

打包完成后，会在 `dist/` 目录生成：

```
dist/yu-ai-agent-python-YYYYMMDD_HHMMSS.tar.gz
```

### 部署到云服务器

#### 1. 上传包到云服务器

```bash
# 使用 scp 上传
scp dist/yu-ai-agent-python-*.tar.gz user@your-server:/path/to/deploy/

# 或使用 rsync（更稳定）
rsync -avz dist/yu-ai-agent-python-*.tar.gz user@your-server:/path/to/deploy/
```

#### 2. 在云服务器上解压

```bash
cd /path/to/deploy
tar -xzf yu-ai-agent-python-*.tar.gz
```

#### 3. 构建 Docker 镜像

```bash
cd /path/to/deploy
docker build -t yu-ai-agent-python:latest .
```

#### 4. 运行容器

```bash
# 使用 docker run
docker run -d \
  --name yu-ai-agent \
  -p 8000:8000 \
  -e APP_ENV=prod \
  -e DATABASE_URL=your_database_url \
  yu-ai-agent-python:latest

# 或使用 docker-compose
docker-compose up -d
```

---

## 方式二：PyInstaller 可执行文件

如果需要打包为独立的 Windows 可执行文件：

```bash
# 运行构建脚本
build.bat
```

输出文件：`dist/yu-agent.exe`

**注意**：这种方式只适用于 Windows 环境，不适合 Docker 部署。

---

## 环境变量配置

在云服务器上运行容器时，需要配置以下环境变量：

```bash
# 必需
DATABASE_URL=mysql+aiomysql://user:password@host:3306/dbname
REDIS_URL=redis://localhost:6379/0

# 可选
APP_ENV=prod
APP_NAME=Yu AI Agent
APP_VERSION=1.0.0
DEBUG=false

# AI 配置
OPENAI_API_KEY=your_openai_key
DASHSCOPE_API_KEY=your_dashscope_key
```

---

## 常见问题

### Q1: 打包时提示缺少文件

确保在 `yu-ai-agent-python` 目录下运行打包脚本。

### Q2: tar 命令不可用

Windows 10 及以上版本自带 tar 命令。如果不可用，可以：
- 安装 Git for Windows（自带 tar）
- 使用 PowerShell 脚本（package.ps1）

### Q3: Docker 镜像构建失败

检查 Dockerfile 中的路径是否正确，确保打包的文件结构与 Dockerfile 中的 COPY 指令匹配。

### Q4: 容器启动后立即退出

检查日志：
```bash
docker logs yu-ai-agent
```

常见原因：
- 环境变量未配置
- 数据库连接失败
- 端口被占用

---

## 文件结构说明

```
yu-ai-agent-python/
├── app/                    # 应用代码
│   ├── api/               # API 路由
│   ├── core/              # 核心功能
│   ├── ai/                # AI 相关功能
│   ├── models/            # 数据模型
│   └── services/          # 业务服务
├── config/                 # 配置文件
├── main.py                # 应用入口
├── requirements.txt       # Python 依赖
├── Dockerfile             # Docker 构建文件
├── docker-compose.yml     # Docker Compose 配置
├── package.bat            # 打包脚本 (Windows)
├── package.ps1            # 打包脚本 (PowerShell)
├── build.bat              # PyInstaller 构建脚本
└── PACKAGE_README.md      # 本文档
```

---

## 技术支持

如有问题，请检查：
1. Docker 是否正确安装
2. 云服务器是否能访问外网（拉取基础镜像）
3. 环境变量是否正确配置
4. 数据库服务是否正常运行
