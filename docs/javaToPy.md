# Java → Python 迁移方案

> **目标**：去除 Java 服务（Spring Boot），将所有业务逻辑合并到 Python 服务（FastAPI），实现单一后端技术栈。
> **创建日期**：2026-06-23

---

## 一、迁移背景与收益

### 当前架构（迁移前）

```
前端 (Vue 3)
    │
    ▼  /api/v1/*
Java (Spring Boot) ──── 内部HTTP ────▶ Python (FastAPI)
  - JWT 认证                              - LLM 调用
  - 用户 CRUD                             - RAG 检索
  - 会话 CRUD                             - Agent 推理
  - 消息存储                              - 工具调用
  - 知识库管理                            - 向量化
  - Agent 任务管理
  - SSE 代理转发
```

### 目标架构（迁移后）

```
前端 (Vue 3)
    │
    ▼  /api/v1/*
Python (FastAPI) ────▶ LLM / PgVector / Redis
  - JWT 认证
  - 用户 CRUD
  - 会话 CRUD
  - 消息存储
  - 知识库管理
  - Agent 任务管理
  - SSE 直连（无代理）
  - RAG 检索
  - Agent 推理
```

### 核心收益

| 维度       | 迁移前                      | 迁移后               |
| -------- | ------------------------ | ----------------- |
| 请求链路     | 前端 → Java → Python → LLM | 前端 → Python → LLM |
| SSE 流式   | Java 二次转发，增加延迟           | Python 直连，零额外延迟   |
| Agent 任务 | Python 回调 Java 更新状态      | 内部直接数据库操作         |
| 知识库向量化   | Python 回调 Java 更新状态      | 内部直接数据库操作         |
| 技术栈      | Java + Python 双栈维护       | Python 单栈         |
| 代码量      | ~15 个 Java 类 + Python 代码 | 仅 Python 代码       |
| 部署       | 2 个服务 + 2 套构建配置          | 1 个服务             |

---

## 二、需要迁移的 Java 功能清单

### 2.1 用户管理模块

**Java 源文件**：
- `UserController.java` — 注册、登录、获取用户信息
- `UserServiceImpl.java` — 用户名唯一性校验、BCrypt 密码加密、JWT 生成/解析
- `JwtAuthInterceptor.java` — JWT 认证拦截器

**需要迁移到 Python 的功能**：

| 功能        | Java 实现                                   | Python 迁移方案             |
| --------- | ----------------------------------------- | ----------------------- |
| 用户注册      | `POST /api/v1/user/register`              | FastAPI 路由 + SQLAlchemy |
| 用户登录      | `POST /api/v1/user/login`                 | FastAPI 路由 + PyJWT      |
| 获取用户信息    | `GET /api/v1/user/info`                   | FastAPI 路由              |
| JWT 生成/解析 | `JwtUtils.java` (jjwt 库)                  | PyJWT 库                 |
| 密码加密      | Spring Security Crypto BCrypt             | passlib[bcrypt]         |
| 认证拦截器     | `JwtAuthInterceptor` (HandlerInterceptor) | FastAPI Depends 中间件     |

**业务规则（必须保留）**：
- 用户名唯一性校验
- 密码 BCrypt 加密存储
- JWT Token 有效期 24 小时
- 认证失败返回 401
- `X-User-Id` 通过 JWT 解析后注入请求上下文

---

### 2.2 会话管理模块

**Java 源文件**：
- `ChatController.java` — 创建、列表、详情、删除
- `ChatServiceImpl.java` — 会话 CRUD + 级联删除

**需要迁移到 Python 的功能**：

| 功能   | 端点                              | 业务规则                                                                |
| ---- | ------------------------------- | ------------------------------------------------------------------- |
| 创建会话 | `POST /api/v1/chat/create`      | love_app 必须选 emotion_status；manus 忽略 emotion_status；生成 UUID chat_id |
| 会话列表 | `GET /api/v1/chat/list`         | 分页、按 app_type 筛选（可选）、按 last_message_time 倒序、仅当前用户                   |
| 会话详情 | `GET /api/v1/chat/{chat_id}`    | 校验会话属于当前用户                                                          |
| 删除会话 | `DELETE /api/v1/chat/{chat_id}` | 软删除 + 级联软删除 messages + 级联软删除 agent_tasks                            |

**响应格式**：
```json
// 创建会话响应
{
  "code": 200,
  "message": "success",
  "data": {
    "chat_id": "uuid",
    "app_type": "love_app",
    "emotion_status": "单身",  // 返回中文
    "title": "...",
    "create_time": "2026-06-23T10:00:00"
  }
}

// 会话列表响应（分页）
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [...],
    "page": 1,
    "page_size": 10,
    "total": 100
  }
}
```

**情感状态映射**（必须保留）：
- 存储英文：`single` / `relationship` / `married`
- 返回中文：`单身` / `恋爱` / `已婚`

---

### 2.3 消息管理模块

**Java 源文件**：
- `MessageController.java` — 消息历史查询
- `MessageServiceImpl.java` — 消息保存、跨会话记忆

**需要迁移到 Python 的功能**：

| 功能 | 说明 |
|------|------|
| 消息历史查询 | `GET /api/v1/chat/{chat_id}/messages`，分页，时间倒序 |
| 保存用户消息 | chat_id + role="user" + content + metadata |
| 保存 AI 消息 | chat_id + role="assistant" + content + metadata(JSON) |
| 跨会话记忆 | 查询同一用户所有会话最近 20 条消息，不分 app_type |
| 更新 last_message_time | 每次保存消息时更新关联 chat 的 last_message_time |

**metadata JSON 结构**：
```json
{
  "emotion_status": "单身",
  "tokens_used": 150,
  "model": "mimo-v2.5",
  "tool_calls": null,
  "rag_sources": [{"document_id": 1, "title": "...", "chunk_content": "...", "similarity": 0.85}]
}
```

---

### 2.4 对话服务模块（AI 转发 → 直连）

**Java 源文件**：
- `AiController.java` — 同步对话、SSE 流式对话
- `AiServiceImpl.java` — 校验会话 → 保存用户消息 → 获取跨会话记忆 → 调用 Python → 保存 AI 消息

**迁移变化**：

| 维度 | 迁移前（Java 转发） | 迁移后（Python 直连） |
|------|---------------------|----------------------|
| 同步对话 | Java 保存消息 → 调用 Python → Java 保存回复 | Python 内部直接保存消息 + 调用 LLM |
| SSE 流式 | Java 调用 Python SSE → 逐行读取 → 转发前端 → 流结束后保存消息 | Python 直接 SSE 输出 + 内部保存消息 |
| 跨会话记忆 | Java 查询 MySQL → 传给 Python | Python 内部直接查询 MySQL |

**SSE 事件格式**（必须保持不变，前端已对接）：
```
data: {"type": "thinking", "content": "正在思考..."}

data: {"type": "answer", "content": "这是完整的一句话。"}

data: {"type": "metadata", "content": {"tokens_used": null, "model": "mimo-v2.5", "rag_sources": [...]}}

data: [DONE]
```

**关键变化**：Python 的 `/internal/ai/love/chat/sync` 和 `/internal/ai/love/chat/sse` 端点需要升级为：
- 端点路径改为 `/api/v1/ai/love/chat/sync` 和 `/api/v1/ai/love/chat/sse`（对前端暴露）
- 增加 JWT 认证（不再依赖 Java 注入 X-User-Id）
- 内部完成消息保存（不再依赖 Java）
- 内部查询跨会话记忆（不再依赖 Java 传入 history）

---

### 2.5 智能体任务模块

**Java 源文件**：
- `AgentTaskController.java` — 提交任务、查询状态、取消任务
- `AgentTaskServiceImpl.java` — 任务生命周期管理 + 异步调用 Python + 回调处理
- `InternalAgentCallbackController.java` — 接收 Python 回调

**迁移变化**：

| 维度   | 迁移前                                            | 迁移后                           |
| ---- | ---------------------------------------------- | ----------------------------- |
| 提交任务 | Java 创建 task → 异步调用 Python → Python 完成后回调 Java | Python 内部创建 task + 直接执行 Agent |
| 查询状态 | Java 查询 MySQL                                  | Python 查询 MySQL               |
| 取消任务 | Java 更新状态 + 调用 Python 取消接口                     | Python 内部取消 asyncio.Task      |
| 回调机制 | Python → HTTP 回调 → Java                        | **完全消除**，内部函数调用               |

**业务规则（必须保留）**：
- 每用户同时只能运行 1 个任务（pending/running 状态检查）
- 若无 chatId，自动创建 manus 类型会话
- 任务状态：pending → running → completed/failed/cancelled
- 取消时清空 steps，result 设为 "用户取消任务"
- completed 时将 AI 结果存入 message 表

**端点映射**：
```
POST /api/v1/agent/run           — 提交任务（需 JWT）
GET  /api/v1/agent/status/{task_id} — 查询状态（需 JWT）
POST /api/v1/agent/cancel/{task_id} — 取消任务（需 JWT）
```

---

### 2.6 知识库管理模块

**Java 源文件**：
- `KnowledgeController.java` — 上传文档、列表、删除
- `KnowledgeDocumentServiceImpl.java` — 文件上传 + 文本提取 + 异步向量化 + 回调处理
- `InternalKnowledgeCallbackController.java` — 接收 Python 向量化回调
- `VectorCleanupScheduler.java` — 定时清理孤立向量
- `FileContentExtractor.java` — Markdown/PDF/TXT 文本提取

**迁移变化**：

| 维度 | 迁移前 | 迁移后 |
|------|--------|--------|
| 文档上传 | Java 提取文本 → 保存 MySQL → 异步调用 Python 向量化 | Python 提取文本 → 保存 MySQL → 内部异步向量化 |
| 向量化回调 | Python → HTTP 回调 → Java 更新 status | **完全消除**，内部直接更新 |
| 文档删除 | Java 软删除 → 删除 PgVector 向量 | Python 软删除 → 内部删除向量 |
| 定时清理 | Java `@Scheduled` 定时任务 | Python APScheduler 或 asyncio 定时任务 |

**文件上传接口**（必须保持不变）：
```
POST /api/v1/knowledge/document
Content-Type: multipart/form-data
参数: file (MultipartFile)
```

**支持的文件类型**：`.md` / `.pdf` / `.txt`

**文本提取方案（Python 替代）**：
- Markdown：直接读取文本
- TXT：直接读取文本
- PDF：PyPDF2 或 pdfplumber（已在 Python requirements.txt 中）

---

### 2.7 基础设施模块

**Java 源文件**：
- `JwtAuthInterceptor.java` — JWT 认证
- `CorsConfig.java` — CORS 配置
- `RequestTraceFilter.java` — 请求追踪
- `GlobalExceptionHandler.java` — 统一异常处理
- `Result.java` / `PageResponse.java` — 统一响应格式
- `HealthController.java` — 健康检查

**Python 已有对应实现**：
- CORS：`main.py` 已配置 `CORSMiddleware`
- 健康检查：`app/api/health.py` 已实现
- 统一响应：Python 端的 Pydantic 模型已有 `code` / `message` / `data` 结构

**需要新增**：
- JWT 认证中间件（FastAPI `Depends`）
- 统一异常处理器（FastAPI exception handler）
- 请求追踪（可选，日志中记录 request_id）

---

## 三、前端接口兼容性

### 3.1 接口路径不变

所有前端调用的 `/api/v1/*` 路径保持不变，只是从 Java 服务改为 Python 服务监听。

### 3.2 响应格式兼容

Java 的统一响应格式：
```json
{"code": 200, "message": "success", "data": {...}}
```

Python 端需要确保所有对外接口返回相同的格式。当前 Python 的 `/internal/*` 接口格式不完全一致，需要统一。

### 3.3 认证方式不变

前端在 `Authorization` header 中携带 `Bearer <token>`，Python 端解析 JWT 提取 `user_id`。

---

## 四、数据库访问层迁移

### 4.1 当前 Python 数据库配置

Python 已有 MySQL 连接配置（`config.py` 中的 `DatabaseSettings`），但目前仅用于 AI 相关的数据读取。

### 4.2 需要新增的 SQLAlchemy 模型

对应 Java 的 5 张 MySQL 表：

| 表名 | Java Entity | Python Model（新增） |
|------|-------------|---------------------|
| `user` | `User.java` | `app/models/db/user.py` |
| `chat` | `Chat.java` | `app/models/db/chat.py` |
| `message` | `Message.java` | `app/models/db/message.py` |
| `agent_task` | `AgentTask.java` | `app/models/db/agent_task.py` |
| `knowledge_document` | `KnowledgeDocument.java` | `app/models/db/knowledge_document.py` |

### 4.3 数据库连接管理

新增 SQLAlchemy async engine 和 session 管理：
- 文件：`app/core/database.py`
- 使用 `aiomysql` 驱动（已在 requirements.txt 中）
- 提供 `get_db()` 依赖注入函数

---

## 五、新增依赖

在 `requirements.txt` 中添加：

```
# JWT
PyJWT>=2.8.0

# 密码加密
passlib[bcrypt]>=1.7.4

# PDF 文本提取
pdfplumber>=0.10.0

# 定时任务（知识库向量清理）
apscheduler>=3.10.0

# 文件上传
python-multipart>=0.0.6
```

> 注意：`python-multipart` 是 FastAPI 处理 `multipart/form-data`（文件上传）的必需依赖。

---

## 六、新增文件结构

```
yu-ai-agent-python/
├── app/
│   ├── api/                          # API 路由（改造）
│   │   ├── chat.py                   # 改造：升级为对外接口 + 消息保存
│   │   ├── agent.py                  # 改造：升级为对外接口 + 任务管理
│   │   ├── knowledge.py              # 改造：升级为对外接口 + 文档管理
│   │   ├── health.py                 # 保留
│   │   ├── mcp.py                    # 保留
│   │   ├── user.py                   # 新增：用户注册/登录/信息
│   │   └── internal/                 # 新增：内部接口（简化后可能不需要）
│   ├── core/                         # 核心模块（改造）
│   │   ├── config.py                 # 改造：新增 JWT 配置
│   │   ├── database.py               # 新增：SQLAlchemy engine + session
│   │   ├── security.py               # 改造：JWT 认证 + 用户依赖注入
│   │   ├── exceptions.py             # 新增：统一异常处理
│   │   └── logging.py                # 保留
│   ├── models/                       # 数据模型（改造）
│   │   ├── chat.py                   # 改造：调整响应格式
│   │   ├── agent.py                  # 改造：调整响应格式
│   │   ├── knowledge.py              # 改造：调整响应格式
│   │   ├── user.py                   # 新增：用户相关 DTO
│   │   └── db/                       # 新增：SQLAlchemy ORM 模型
│   │       ├── __init__.py
│   │       ├── user.py               # 新增：user 表 ORM
│   │       ├── chat.py               # 新增：chat 表 ORM
│   │       ├── message.py            # 新增：message 表 ORM
│   │       ├── agent_task.py         # 新增：agent_task 表 ORM
│   │       └── knowledge_document.py # 新增：knowledge_document 表 ORM
│   ├── services/                     # 新增：业务服务层
│   │   ├── __init__.py
│   │   ├── user_service.py           # 新增：用户业务逻辑
│   │   ├── chat_service.py           # 新增：会话业务逻辑
│   │   ├── message_service.py        # 新增：消息业务逻辑
│   │   ├── agent_service.py          # 新增：智能体任务业务逻辑
│   │   └── knowledge_service.py      # 新增：知识库业务逻辑
│   └── ai/                           # AI 模块（基本保留）
│       └── ...                       # 保留原有结构
├── config/
│   └── config-dev.yaml               # 改造：新增 JWT 密钥等配置
├── requirements.txt                  # 改造：新增依赖
├── main.py                           # 改造：注册新路由 + 初始化 DB
└── sql/
    └── database.sql                  # 保留：数据库初始化脚本
```

---

## 七、迁移步骤（按执行顺序）

### 阶段一：基础设施搭建

#### 步骤 1：新增数据库连接层

**文件**：`app/core/database.py`（新增）

- 创建 SQLAlchemy async engine（`create_async_engine`）
- 创建 `async_sessionmaker`
- 实现 `get_db()` 依赖注入函数
- 在 `main.py` 的 lifespan 中初始化连接

#### 步骤 2：新增 SQLAlchemy ORM 模型

**文件**：`app/models/db/` 目录（新增）

按 `sql/database.sql` 创建 5 个 ORM 模型：
- `User` — 对应 `user` 表
- `Chat` — 对应 `chat` 表，含软删除
- `Message` — 对应 `message` 表，含软删除
- `AgentTask` — 对应 `agent_task` 表，含软删除
- `KnowledgeDocument` — 对应 `knowledge_document` 表，含软删除

**关键点**：
- 所有表主键使用 `BIGINT AUTO_INCREMENT`（禁止 UUID 主键）
- 软删除字段 `is_deleted` 使用 `Mapped[bool]` 映射
- `metadata` JSON 字段使用 `JSON` 类型

#### 步骤 3：新增 JWT 认证中间件

**文件**：`app/core/security.py`（改造）

- 实现 `create_access_token(user_id)` — 生成 JWT，有效期 24 小时
- 实现 `decode_access_token(token)` — 解析 JWT，提取 user_id
- 实现 `get_current_user_id(token)` — FastAPI Depends，从 Authorization header 提取 user_id
- 认证失败返回 `401 Unauthorized`

#### 步骤 4：新增统一异常处理

**文件**：`app/core/exceptions.py`（新增）

- 自定义 `BusinessException` 异常类（支持 code + message）
- 注册 FastAPI exception handler，统一返回 `{"code": ..., "message": ..., "data": null}` 格式

---

### 阶段二：用户管理模块

#### 步骤 5：实现用户 API

**文件**：`app/api/user.py`（新增）、`app/services/user_service.py`（新增）、`app/models/user.py`（新增）

接口：
- `POST /api/v1/user/register` — 用户注册
  - 参数校验：用户名、密码非空
  - 用户名唯一性校验
  - BCrypt 加密密码
  - 返回 user_id + username + nickname
- `POST /api/v1/user/login` — 用户登录
  - 校验用户名密码
  - 生成 JWT Token
  - 返回 token
- `GET /api/v1/user/info` — 获取当前用户信息（需 JWT）
  - 返回 user_id + username + nickname + avatar

---

### 阶段三：会话管理模块

#### 步骤 6：实现会话 API

**文件**：`app/api/chat.py`（改造）、`app/services/chat_service.py`（新增）

将现有 `chat.py` 的 `/internal/*` 路径升级为 `/api/v1/*`，并增加完整 CRUD：

- `POST /api/v1/chat/create` — 创建会话
- `GET /api/v1/chat/list` — 会话列表（分页）
- `GET /api/v1/chat/{chat_id}` — 会话详情
- `DELETE /api/v1/chat/{chat_id}` — 删除会话（级联软删除）

**关键改造**：
- 所有端点增加 JWT 认证（`get_current_user_id` 依赖）
- 情感状态映射逻辑从 Java 迁移
- 级联软删除逻辑从 Java 迁移

---

### 阶段四：消息管理模块

#### 步骤 7：实现消息服务

**文件**：`app/services/message_service.py`（新增）

- `save_user_message(chat_id, content, metadata)` — 保存用户消息
- `save_assistant_message(chat_id, content, metadata)` — 保存 AI 消息
- `get_recent_messages(user_id, limit=20)` — 跨会话记忆查询
- `get_messages_by_chat(chat_id, page, page_size)` — 分页查询消息历史
- 每次保存消息时更新 `chat.last_message_time`

---

### 阶段五：对话服务改造

#### 步骤 8：改造对话 API

**文件**：`app/api/chat.py`（改造）

将现有 `/internal/ai/love/chat/*` 端点改造为：

- `POST /api/v1/ai/love/chat/sync` — 同步对话
  - 增加 JWT 认证
  - 内部完成：校验会话归属 → 保存用户消息 → 查询跨会话记忆 → 调用 LLM → 保存 AI 消息 → 返回结果
  - 不再需要外部传入 `history`，内部自行查询

- `POST /api/v1/ai/love/chat/sse` — SSE 流式对话
  - 增加 JWT 认证
  - 内部完成：校验会话归属 → 保存用户消息 → 查询跨会话记忆 → SSE 流式输出 → 流结束后保存 AI 消息
  - **不再需要 Java 二次转发**，直接对前端输出 SSE

**SSE 流结束后保存消息的实现方式**：
- 使用 `sse-starlette` 的 `BackgroundTask` 或在 event_generator 内部保存
- 或者使用 FastAPI 的 `response.background` 机制

---

### 阶段六：智能体任务模块

#### 步骤 9：实现智能体任务 API

**文件**：`app/api/agent.py`（改造）、`app/services/agent_service.py`（新增）

将现有 `/internal/agent/*` 端点升级为：

- `POST /api/v1/agent/run` — 提交任务（需 JWT）
  - 检查用户是否有运行中的任务
  - 若无 chatId，自动创建 manus 会话
  - 创建 agent_task 记录（status=pending）
  - 保存用户消息到 message 表
  - 启动 asyncio.Task 执行 Agent
  - 任务完成时直接更新 agent_task 状态 + 保存 AI 消息到 message 表
  - **不再需要回调机制**

- `GET /api/v1/agent/status/{task_id}` — 查询状态（需 JWT）
- `POST /api/v1/agent/cancel/{task_id}` — 取消任务（需 JWT）
  - 直接取消 asyncio.Task
  - 更新状态为 cancelled

**删除的代码**：
- `_callback_java()` 函数 — 不再需要
- `InternalAgentCallbackController` — 不再需要

---

### 阶段七：知识库管理模块

#### 步骤 10：实现知识库 API

**文件**：`app/api/knowledge.py`（改造）、`app/services/knowledge_service.py`（新增）

将现有 `/internal/knowledge/*` 端点升级为：

- `POST /api/v1/knowledge/document` — 上传文档（需 JWT）
  - 接收 `multipart/form-data` 文件
  - 识别文件类型（.md / .pdf / .txt）
  - 提取文本内容
  - 从文件名提取标题
  - 保存到 MySQL（status=0）
  - 内部异步启动向量化（不再回调）

- `GET /api/v1/knowledge/documents` — 文档列表（需 JWT）
- `DELETE /api/v1/knowledge/document/{id}` — 删除文档（需 JWT）
  - 软删除 + 删除 PgVector 向量

- `POST /api/v1/knowledge/document/{id}/retry` — 向量化重试（需 JWT）

**文件文本提取**：
- Markdown / TXT：直接 `open().read()`
- PDF：使用 `pdfplumber` 提取文本

**删除的代码**：
- `_callback_java()` 函数 — 不再需要
- `InternalKnowledgeCallbackController` — 不再需要
- Java 的 `FileContentExtractor` — Python 端重新实现

---

### 阶段八：清理与优化

#### 步骤 11：删除内部接口

- 删除 `/internal/*` 路由（不再需要 Java 调用）
- 删除 `callback` 相关配置和代码
- 删除 `X-Internal-Token` 认证逻辑

#### 步骤 12：更新配置

**文件**：`config/config.yaml`、`config/config-dev.yaml`

- 新增 JWT 配置项（`JWT_SECRET`、`JWT_EXPIRE_HOURS`）
- 删除 callback 相关配置
- 更新端口为 8081（与前端当前对接的 Java 端口一致，避免前端修改）

#### 步骤 13：更新 Docker Compose

**文件**：`docker-compose.yml`

- 删除 Java 服务容器
- Python 服务端口改为 8081（或保持 8000 + 更新前端配置）
- 更新健康检查

#### 步骤 14：删除 Java 代码

- 删除 `yu-ai-agent-java/` 整个目录
- 更新 `docs/tasks.md` 中的架构描述

---

## 八、风险与注意事项

### 8.1 前端兼容性

- 所有 `/api/v1/*` 路径必须保持不变
- 响应格式 `{"code": 200, "message": "success", "data": {...}}` 必须保持一致
- SSE 事件格式必须保持一致
- JWT Token 格式必须保持一致（前端已存储的 token 需要兼容）

### 8.2 数据库兼容性

- 表结构不变，无需迁移数据
- 软删除逻辑需要在 Python 端正确实现
- `metadata` JSON 字段的序列化/反序列化需要与 Java 保持一致

### 8.3 SSE 流式对话的内存管理

- Java 使用 `SseEmitter` + `CompletableFuture` 转发
- Python 使用 `sse-starlette` 的 `EventSourceResponse`
- 流结束后保存消息，需确保不会因连接断开而丢失

### 8.4 异步任务管理

- Python 的 `asyncio.Task` 替代 Java 的 `CompletableFuture`
- 需要处理服务重启时正在运行的任务（持久化状态或标记为 failed）

---

## 九、任务执行顺序

```
阶段一：基础设施（无业务依赖）
  步骤 1 → 步骤 2 → 步骤 3 → 步骤 4

阶段二：用户管理
  步骤 5

阶段三：会话管理
  步骤 6

阶段四：消息服务
  步骤 7

阶段五：对话服务改造
  步骤 8（依赖步骤 6、7）

阶段六：智能体任务
  步骤 9（依赖步骤 6、7）

阶段七：知识库管理
  步骤 10

阶段八：清理
  步骤 11 → 步骤 12 → 步骤 13 → 步骤 14
```

**前端任务**：
- 无需修改（接口路径和格式保持不变）
- 如 Python 端口变更，仅需更新前端 API base URL 配置

---

**文档维护人**：开发团队
**最后更新**：2026-06-23
