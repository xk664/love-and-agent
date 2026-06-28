# Yu AI Agent - 智能陪伴系统

一个基于大语言模型的智能陪伴系统，支持情感陪伴、超级智能体任务执行、知识库问答，以及创新的"数字朋友"人格蒸馏功能。

## 核心功能

### 恋爱大师
- 情感陪伴与恋爱咨询
- 基于用户情感状态（单身/恋爱/已婚）提供个性化建议
- SSE 流式对话，实时响应

### 超级智能体
- 自主规划与任务执行
- 支持复杂任务分解
- 任务状态实时追踪

### 数字朋友（亮点功能）
- **人格蒸馏技术**：用户上传聊天记录等素材，LLM 自动分析生成校准问题
- 用户补充回答后，系统融合素材与校准信息生成个性化系统提示词
- 实现 AI 对特定人物性格、说话风格的精准模拟

### 知识库
- 文档上传与管理（支持 PDF、TXT、Markdown）
- 向量化存储与混合检索（关键词匹配 + 向量相似度 + RRF 排序）
- 基于知识库的增强问答

## 技术栈

### 后端
- **框架**: FastAPI + Uvicorn
- **数据库**: MySQL（主数据）+ PostgreSQL/PgVector（向量存储）
- **缓存**: Redis
- **LLM**: 通义千问（DashScope）/ OpenAI 兼容接口
- **认证**: JWT

### 前端
- **框架**: Vue 3 + Vite
- **UI**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router

## 项目结构

```
love-and-agent/
├── yu-ai-agent-python/          # 后端
│   ├── app/
│   │   ├── api/                 # API 路由
│   │   ├── ai/                  # AI 能力（LLM、RAG、记忆）
│   │   ├── models/              # 数据模型
│   │   ├── services/            # 业务逻辑
│   │   └── core/                # 核心配置
│   ├── config/                  # 配置文件
│   └── requirements.txt
│
└── yu-ai-agent-frontend/        # 前端
    ├── src/
    │   ├── views/               # 页面组件
    │   ├── components/          # 通用组件
    │   ├── api/                 # API 调用
    │   ├── stores/              # Pinia 状态
    │   └── router/              # 路由配置
    └── package.json
```

## 快速启动

### 环境要求

- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- PostgreSQL 14+（需安装 pgvector 扩展）
- Redis 6+

### 1. 启动后端

```bash
# 进入后端目录
cd yu-ai-agent-python

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制 .env.example 并修改）
cp .env.example .env
# 编辑 .env 文件，配置数据库、Redis、API Key 等

# 启动服务
python main.py
```

后端服务默认运行在 http://localhost:8000

### 2. 启动前端

```bash
# 进入前端目录
cd yu-ai-agent-frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务默认运行在 http://localhost:5173

### 3. 数据库初始化

```bash
# 后端启动时会自动创建表结构
# 如需手动初始化，请执行 SQL 脚本
```

## 环境变量配置

在 `yu-ai-agent-python/.env` 中配置：

```env
# 数据库
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/yu_agent
DATABASE_URL_SYNC=mysql+pymysql://user:password@localhost:3306/yu_agent

# PgVector
PGVECTOR_CONNECTION_STRING=postgresql+asyncpg://user:password@localhost:5432/yu_agent_vector

# Redis
REDIS_URL=redis://localhost:6379/0

# DashScope (通义千问)
DASHSCOPE_API_KEY=your_api_key

# JWT
JWT_SECRET_KEY=your_secret_key
```

## API 文档

启动后端后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT
