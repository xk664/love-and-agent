# AI 超级智能体系统 - 产品需求文档 (PRD)

> **项目名称**：AI 超级智能体系统
> **版本**：v1.4
> **创建日期**：2026-06-18
> **最后更新**：2026-06-18
> **技术架构**：Java + Python 完全分离微服务架构（Java 转发调用 Python）

---

## 1. 项目概述

### 1.1 项目背景

从零开始构建一个采用 **Java + Python 完全分离微服务架构** 的 AI 智能体系统。Java 和 Python 作为独立微服务，通过 HTTP REST API 进行通信。**所有客户端请求统一由 Java 端接收，Java 负责业务逻辑处理（用户管理、对话管理、会话管理等），当需要 AI 能力时由 Java 转发调用 Python 服务，再将结果返回客户端。** Python 不直接对外暴露接口，仅作为内部 AI 引擎服务。Gateway 验证 JWT 后将用户 ID 传递给下游 Java/Python 服务。

### 1.2 项目目标

- 从零构建高性能、可扩展的 AI 智能体平台
- 支持多种 AI 应用场景（恋爱咨询、超级智能体等）
- 提供完善的工具调用和 MCP 服务集成能力
- 实现 RAG 知识库检索增强生成功能
- 支持多轮对话、对话记忆、流式输出等特性
- Java 和 Python 服务完全独立，通过 HTTP REST 通信

### 1.3 核心价值

- **Java 转发架构**：所有客户端请求由 Java 统一接收和转发，Python 作为内部 AI 引擎，不直接对外暴露
- **完全分离**：Java 和 Python 作为独立微服务，通过 HTTP REST 通信，职责清晰
- **独立扩展**：AI 模块可独立升级、扩展，不影响业务服务
- **高性能**：Java 保证业务服务的高并发处理能力（>= 1000 并发）
- **灵活性**：Python 生态丰富的 AI 库支持快速迭代
- **从零开发**：全新设计，不修改现有项目代码

---

## 2. 用户角色

| 角色 | 描述 | 核心需求 |
|------|------|----------|
| 普通用户 | 使用 AI 应用的终端用户 | 获得情感咨询、恋爱建议、复杂任务自动化 |

> **说明**：系统不区分管理员和高级用户，所有用户均为普通用户，简化设计。

---

## 3. 功能需求

### 3.1 用户管理

#### 3.1.1 用户注册

**功能描述**：用户通过用户名+密码注册账号。

**技术要求**：
- 用户名唯一性校验
- 密码加密存储（BCrypt）
- 最简注册流程，无需邮箱/手机验证

**接口设计**：
```
POST /api/v1/user/register
{
    "username": "string",
    "password": "string"
}

Response:
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "username": "string",
        "create_time": "2026-06-18T10:00:00Z"
    }
}
```

#### 3.1.2 用户登录

**功能描述**：用户通过用户名+密码登录，获取 JWT Token。

**技术要求**：
- JWT Token 认证
- Token 过期时间：24小时
- JWT Secret Key 通过环境变量管理
- **Token 过期处理**：Token 过期后不支持刷新，用户需重新登录。Gateway 验证 JWT 失败时返回 HTTP 401，前端收到 401 后跳转登录页

**接口设计**：
```
POST /api/v1/user/login
{
    "username": "string",
    "password": "string"
}

Response:
{
    "code": 200,
    "message": "success",
    "data": {
        "token": "jwt_token",
        "user": {
            "id": 1,
            "username": "string"
        }
    }
}
```

---

### 3.2 AI 恋爱大师应用

#### 3.2.1 多轮对话

**功能描述**：用户可以与 AI 进行连续对话，AI 能够记住上下文，提供连贯的咨询服务。

**技术要求**：
- 支持会话 ID 管理（UUID 格式），每个用户独立的对话历史
- **对话记忆窗口：跨会话累计最近 20 条消息**（同一用户所有会话的最近 20 条消息，用户+AI 消息总和，不分 app_type）
- 支持同步和 SSE 流式两种响应方式
- 流式接口统一使用 POST 方法
- **情感状态为会话级别**：用户在创建会话时选择情感状态（单身/恋爱/已婚），会话内不可更改
- **情感状态存储格式**：message.metadata 中的 emotion_status **直接存储中文值**（单身/恋爱/已婚），chat 表 emotion_status 仍使用英文存储（single/relationship/married），后端接口返回时直接携带中文值
- **对话历史统一存储在 Java 端**（MySQL 数据库），Python 服务不存储对话历史
- **消息存储时机**：AI 回复成功后，用户消息和 AI 消息一起存储到数据库
- **Java 转发调用 Python**：Java 接收对话请求，组装上下文（含跨会话记忆），转发调用 Python AI 服务，再将结果返回客户端

**情感状态选择**（会话创建时一次性选择，会话内不可更改）：

| 英文值（chat 表存储） | 中文值（message.metadata 存储及接口返回） | 推荐内容方向 |
|----------------------|------------------------------------------|--------------|
| single | 单身 | 社交圈拓展、追求技巧 |
| relationship | 恋爱 | 沟通技巧、矛盾处理 |
| married | 已婚 | 家庭责任、亲属关系 |

> **说明**：chat 表 emotion_status 使用英文存储（single/relationship/married），message.metadata 中的 emotion_status 直接存储中文值（单身/恋爱/已婚），后端接口返回时直接携带中文值，前端无需再做映射。

**接口设计**：
```
# 同步对话（Java 接收后转发调用 Python）
POST /api/v1/ai/love/chat/sync
{
    "chat_id": "uuid",
    "message": "string"
}

Response:
{
    "code": 200,
    "message": "success",
    "data": {
        "chat_id": "uuid",
        "role": "assistant",
        "content": "AI 回复内容",
        "create_time": "2026-06-18T10:00:00Z"
    }
}

# 流式对话 (SSE) - 统一使用 POST（Java 接收后转发调用 Python）
POST /api/v1/ai/love/chat/sse
{
    "chat_id": "uuid",
    "message": "string"
}

# SSE 流式响应格式（每个 answer 事件为完整句子，结束前返回 metadata）
data: {"type":"thinking","content":"正在思考..."}
data: {"type":"answer","content":"完整句子回复内容。"}
data: {"type":"metadata","content":{"tokens_used":150,"model":"qwen-turbo","tool_calls":[],"rag_sources":[]}}
data: [DONE]
```

**转发调用流程**：
```
客户端 → Gateway(JWT验证+提取user_id) → Java(业务处理+组装上下文) → Python(AI推理) → Java(AI回复成功后存储用户消息和AI消息+返回结果) → 客户端
```

#### 3.2.2 RAG 知识库问答

**功能描述**：基于恋爱心理学知识库，AI 能够检索相关文档并结合知识进行回答。

**技术要求**：
- 支持 Markdown + PDF + TXT 文档导入和向量化
- **文档内容存储在数据库中**（MySQL `knowledge_document.content` 字段，LONGTEXT 类型）
- 向量化后的向量数据存储在 PgVector 向量数据库
- 支持混合检索策略（向量相似度 + 关键词）
- 支持查询重写，提高检索准确率

**知识库内容**：
- 单身状态：社交圈拓展、追求技巧
- 恋爱状态：沟通技巧、矛盾处理
- 已婚状态：家庭责任、亲属关系

#### 3.2.3 工具调用

**功能描述**：AI 能够根据用户需求自主调用外部工具完成任务。

**内置工具**：
- 联网搜索（SearchAPI）
- 文件操作（读写文件）
- 网页抓取（Jsoup）
- 资源下载（文件下载）
- 终端操作（命令执行）
- PDF 生成（iText）

#### 3.2.4 MCP 服务调用

**功能描述**：通过 MCP（Model Context Protocol）协议调用外部服务。

**已实现服务**：
- 图片搜索服务（Pexels API）

**扩展能力**：
- 支持 SSE 和 Stdio 两种 MCP 连接方式
- 支持动态加载 MCP 服务配置

---

### 3.3 AI 超级智能体（YuManus）

#### 3.3.1 自主规划能力

**功能描述**：智能体能够根据用户需求自主分解任务、选择工具、执行步骤，直到完成目标。

**技术要求**：
- 基于 ReAct（Reasoning + Acting）模式
- 最大执行步骤：20 步（不限制执行时间，仅限制步数）
- 达到执行上限时强制终止并返回当前结果
- **每用户同时只能运行 1 个智能体任务**（用户级并发限制，非系统全局限制）
- **前端轮询频率：每 3 秒轮询一次任务状态**
- **支持取消智能体任务**：pending 和 running 状态均可取消
- **取消任务流程**：Java 调用 Python 端的取消接口（POST /internal/agent/cancel/{task_id}），Python 立即中断当前步骤并停止执行，Java 清空 agent_task 的 steps 字段并将状态更新为 cancelled
- **任务结果回写机制**：Python 通过回调接口通知 Java 更新任务状态，**仅在任务完成时一次性回写 steps 字段**（执行过程中不逐步回写）
- **Manus 类型会话**：仅有 `agent/run` 接口，无同步/流式对话接口；用户消息和 AI 结果都存储在 message 表中，agent_task 表仅存储任务信息（task_id、status、steps、result）

**接口设计**：
```
# 提交智能体任务 - Java 接收后转发调用 Python
POST /api/v1/agent/run
{
    "message": "任务描述",
    "chat_id": "uuid"  // 关联会话ID（Manus 类型必填，用于消息历史关联）
}

Response:
{
    "code": 200,
    "message": "success",
    "data": {
        "task_id": "uuid",
        "status": "pending"
    }
}

# 查询任务状态 - 前端每 3 秒轮询
GET /api/v1/agent/status/{task_id}

Response:
{
    "code": 200,
    "message": "success",
    "data": {
        "task_id": "uuid",
        "status": "pending|running|completed|failed|cancelled",
        "result": "最终结果（仅在 completed 时返回）",
        "steps": [
            {
                "step": 1,
                "tool": "search",
                "input": "查询内容",
                "output": "搜索结果",
                "status": "completed",
                "start_time": "2026-06-18T10:00:00Z",
                "end_time": "2026-06-18T10:00:05Z"
            }
        ],
        "create_time": "2026-06-18T10:00:00Z",
        "update_time": "2026-06-18T10:01:00Z"
    }
}

# 取消智能体任务 - pending 和 running 状态均可取消
# 取消流程：Java 调用 Python 取消接口 → Python 立即中断执行 → Java 清空 steps 并更新状态为 cancelled
POST /api/v1/agent/cancel/{task_id}

Response:
{
    "code": 200,
    "message": "success",
    "data": {
        "task_id": "uuid",
        "status": "cancelled"
    }
}
```

**智能体任务状态流转时序**：

```
客户端          Java 端              Python 端
  │                │                    │
  │  POST /agent/run                   │
  │───────────────>│                    │
  │                │  创建任务(pending)  │
  │                │  POST /internal/agent/run
  │                │──────────────────>│
  │  返回 task_id  │  返回 task_id     │
  │<───────────────│<──────────────────│
  │                │                    │
  │  GET /agent/status (每3秒轮询)      │  开始执行任务
  │───────────────>│                    │  status: running
  │  返回 pending  │                    │
  │<───────────────│                    │
  │                │                    │  执行各步骤...
  │  GET /agent/status                  │
  │───────────────>│                    │
  │  返回 running  │                    │
  │<───────────────│                    │
  │                │                    │  任务完成
  │                │  POST /internal/agent/callback
  │                │<──────────────────│  (一次性回写: status + steps + result)
  │                │  更新任务状态       │
  │                │  (completed/failed) │
  │                │                    │
  │  GET /agent/status                  │
  │───────────────>│                    │
  │  返回 completed│                    │
  │<───────────────│                    │
```

**状态说明**：

| 状态 | 说明 | 触发方式 |
|------|------|----------|
| pending | 任务已创建，等待执行 | Java 创建任务后 |
| running | 任务执行中 | Python 开始执行后 |
| completed | 任务完成 | Python 回调通知 |
| failed | 任务失败 | Python 回调通知 |
| cancelled | 任务已取消 | 用户主动取消（Java 调用 Python 取消接口，立即中断执行，清空 steps） |

> **关键设计**：Python 在任务执行过程中不逐步回写 steps，仅在任务完成（completed 或 failed）时通过回调接口一次性回写完整的 steps 和 result。前端在任务完成前轮询到的状态为 pending/running，steps 字段为空。取消任务时，Java 调用 Python 取消接口立即中断执行，清空 agent_task 的 steps 字段。

#### 3.3.1.1 Manus 智能体

**功能描述**：Manus 类型的智能体，专注于复杂任务的自主规划和执行。

**技术要求**：
- **交互方式**：Manus 类型会话仅有 `POST /api/v1/agent/run` 接口，不支持同步/流式对话
- **消息存储**：用户消息和 AI 结果都存储在 message 表中（通过 chat_id 字段关联会话），agent_task 表仅存储任务信息（task_id、status、steps、result 等），不重复存储消息内容
- **消息存储时机**：AI 回复成功后，用户消息和 AI 消息一起存储到 message 表
- **emotion_status 约束**：Manus 类型会话忽略 emotion_status 字段（可传 null），love_app 类型会话 emotion_status 为必填项，接口层面做校验
- **状态回写**：与其他智能体相同，Python 通过回调接口一次性回写任务结果

**Manus 消息存储流程**：
```
客户端提交任务 → Java 创建 agent_task（pending）→ Java 存储用户消息到 message 表
→ Java 转发调用 Python → Python 执行任务 → Python 回调通知 Java（completed/failed）
→ Java 存储 AI 结果到 message 表 → Java 更新 agent_task 状态和 steps
```

#### 3.3.2 多工具协同

**功能描述**：智能体能够组合使用多个工具完成复杂任务。

**典型场景**：
- 制定约会计划：搜索地点 → 下载图片 → 生成 PDF 文档
- 信息收集：网页搜索 → 内容抓取 → 整理总结

#### 3.3.3 流式输出

**功能描述**：实时展示智能体的思考过程和执行结果。

**技术要求**：
- 使用 SSE（Server-Sent Events）流式传输
- 统一使用 POST 方法
- 展示工具调用详情和执行结果

---

### 3.4 知识库管理

#### 3.4.1 文档管理

**功能描述**：用户可以上传、查看、删除知识库文档。每个用户拥有独立的知识库空间，文档数据按用户隔离。

**技术要求**：
- 支持 Markdown + PDF + TXT 格式
- **文件内容提取**：Java 接收上传文件后提取文本内容（解析 Markdown/PDF/TXT），再将文本内容传给 Python 进行向量化
- **向量化触发**：Python 端有独立的队列消费机制，异步执行向量化任务
- **向量化重试**：向量化失败的文档支持用户手动重试
- **文档更新**：暂不支持直接更新文档内容，只能删除后重新上传
- 软删除（is_deleted 字段）
- **用户隔离**：每个用户只能访问自己上传的文档，通过 `user_id` 字段实现隔离
- **文档标题自动提取**：上传时自动从文件名提取标题（去掉文件扩展名），无需用户手动输入

**接口设计**：
```
# 上传文档 - 文档内容存储在数据库中，标题自动从文件名提取
POST /api/v1/knowledge/document
Content-Type: multipart/form-data

Response:
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "title": "文档标题（自动从文件名提取，去掉扩展名）",
        "file_type": "markdown",
        "status": 0,
        "create_time": "2026-06-18T10:00:00Z"
    }
}

# 获取文档列表 - 分页查询（仅返回当前用户的文档）
GET /api/v1/knowledge/documents?page=1&page_size=10

# 删除文档（软删除，仅能删除自己的文档）
DELETE /api/v1/knowledge/document/{id}

# 重试文档向量化（仅对 status=2 失败的文档生效）
POST /api/v1/knowledge/document/{id}/retry

Response:
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "title": "文档标题",
        "status": 0,
        "message": "向量化任务已重新提交"
    }
}
```

**知识库文档上传与向量化流程**：

```
客户端              Java 端                Python 端
  │                    │                      │
  │  POST /knowledge/document (上传文件)       │
  │───────────────────>│                      │
  │                    │  1. 接收文件           │
  │                    │  2. 提取文本内容       │
  │                    │     (Markdown/PDF/TXT)│
  │                    │  3. 存入数据库         │
  │                    │     (content 字段)    │
  │                    │  4. 设置 status=0     │
  │  返回文档信息       │     (待处理)          │
  │<───────────────────│                      │
  │                    │                      │
  │                    │  POST /internal/knowledge/index
  │                    │  (发送文本内容)        │
  │                    │─────────────────────>│
  │                    │                      │  5. 放入向量化队列
  │                    │                      │  6. 异步执行向量化
  │                    │                      │  7. 存储向量到 PgVector
  │                    │                      │
  │                    │  回调: 向量化完成      │
  │                    │<─────────────────────│
  │                    │  8. 更新 status=1     │
  │                    │     (已向量化)        │
  │                    │                      │
  │  轮询文档列表       │                      │
  │───────────────────>│                      │
  │  返回 status=1     │                      │
  │<───────────────────│                      │
```

**向量化重试流程**：

```
用户点击"重试" → POST /api/v1/knowledge/document/{id}/retry
  → Java 检查文档 status 是否为 2（失败）
  → 重置 status 为 0（待处理）
  → 重新调用 Python /internal/knowledge/index 接口
  → Python 重新放入队列执行向量化
```

> **说明**：文档上传后 status=0（待处理），向量化完成后 status 更新为 1（已向量化），失败则 status=2（处理失败）。用户可对失败文档点击重试。

---

## 4. 技术架构

### 4.1 整体架构

> **架构核心原则**：所有客户端请求统一由 Java 端接收，Java 负责业务逻辑处理和对话历史存储。需要 AI 能力时，Java 内部转发调用 Python 服务。Python 不直接对外暴露接口。

```
┌─────────────────────────────────────────────────────────────┐
│                      前端应用层                               │
│              Vue 3 + Vite + Element Plus                    │
│              响应式设计（桌面 + 移动端）                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API 网关层 (Java)                          │
│            Spring Boot 3 + Spring Cloud Gateway              │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│    │  JWT 认证     │  │  路由转发     │  │  用户ID提取   │     │
│    │  (验证Token)  │  │  (全部→Java)  │  │  (X-User-Id) │     │
│    └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼  (所有请求统一路由到 Java)
┌─────────────────────────────────────────────────────────────┐
│                  业务服务层 (Java) - 统一入口                   │
│                      Spring Boot 3                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 用户管理   │  │ 会话管理   │  │ 对话管理   │  │ 知识库管理 │   │
│  │ 注册/登录  │  │ CRUD     │  │ 消息存储   │  │ 文档管理   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐                                │
│  │ 智能体管理 │  │ MCP 服务  │                                │
│  │ 任务调度   │  │ 工具调用   │                                │
│  └──────────┘  └──────────┘                                │
│         │                                                   │
│         │  内部 HTTP 调用 (/internal/*)                      │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              AI 服务层 (Python) - 内部服务             │   │
│  │                      FastAPI                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │ 模型调用   │  │ RAG 知识库 │  │ 智能体推理 │          │   │
│  │  │ LLM API  │  │ 向量检索   │  │ ReAct    │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                               │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  MySQL    │  │  PgVector    │  │  Redis               │  │
│  │  业务数据  │  │  向量数据     │  │  缓存/会话            │  │
│  │  用户/会话 │  │  知识库向量   │  │                      │  │
│  │  消息/任务 │  │              │  │                      │  │
│  └──────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    服务治理层                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Nacos（服务发现 + 配置管理）                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 技术栈选型

#### 4.2.1 Java 后端

| 组件       | 技术选型                   | 版本     | 说明           |
| -------- | ---------------------- | ------ | ------------ |
| 核心框架     | Spring Boot            | 3.2.x  | 主服务框架        |
| API 网关   | Spring Cloud Gateway   | 4.1.x  | 路由转发、鉴权      |
| 服务治理     | Nacos                  | 2.3.x  | 服务发现 + 配置管理  |
| 数据库      | MySQL                  | 8.0    | 业务数据存储       |
| 缓存       | Redis                  | 7.x    | 会话缓存、热点数据    |
| ORM      | MyBatis-Plus           | 3.5.x  | 数据访问层        |
| 接口文档     | Knife4j                | 4.x    | OpenAPI 3.0  |
| 序列化      | Kryo                   | 5.x    | 高性能序列化       |
| 工具库      | Hutool                 | 5.8.x  | 常用工具集        |
| PDF 生成   | iText                  | 9.x    | PDF 文档生成     |
| 网页解析     | Jsoup                  | 1.19.x | HTML 解析      |
| HTTP 客户端 | RestTemplate/WebClient | -      | 调用 Python 服务 |
|          |                        |        |              |

#### 4.2.2 Python AI 模块

| 组件 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| Web 框架 | FastAPI | 0.110.x | 异步 API 服务 |
| AI 框架 | LangChain | 0.2.x | AI 应用开发框架 |
| 向量数据库 | PgVector | 0.3.x | 向量存储和检索 |
| Embedding | DashScope | - | 阿里云向量模型 |
| LLM | DashScope/OpenAI | - | 大语言模型调用 |
| 文档处理 | Unstructured | 0.x | 文档解析（支持 Markdown/PDF/TXT） |
| HTTP 客户端 | httpx | 0.27.x | 异步 HTTP 请求（含回调 Java 服务） |
| 配置管理 | PyYAML | 6.x | 混合配置：敏感配置（API Key 等）通过环境变量管理，其他配置使用本地 YAML 配置文件 |

#### 4.2.3 前端

| 组件 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| 框架 | Vue | 3.x | 前端框架 |
| 构建工具 | Vite | 5.x | 开发构建工具 |
| UI 组件 | Element Plus | 2.x | UI 组件库（支持响应式） |
| HTTP | Axios | 1.x | HTTP 请求 |
| 路由 | Vue Router | 4.x | 前端路由 |
| 响应式 | CSS Media Queries + Flexbox | - | 桌面 + 移动端适配 |

---

## 5. 模块详细设计

### 5.1 Java 后端模块

#### 5.1.1 项目结构

```
yu-ai-agent-java/
├── src/main/java/com/yuaiagent/
│   ├── gateway/                    # API 网关
│   │   ├── config/                # 网关配置
│   │   ├── filter/                # 过滤器（认证、日志）
│   │   └── route/                 # 路由配置
│   ├── service/                   # 业务服务
│   │   ├── user/                  # 用户服务
│   │   │   ├── controller/
│   │   │   ├── service/
│   │   │   ├── mapper/
│   │   │   └── model/
│   │   ├── chat/                  # 对话服务
│   │   │   ├── controller/
│   │   │   ├── service/
│   │   │   ├── mapper/
│   │   │   └── model/
│   │   └── knowledge/             # 知识库服务
│   │       ├── controller/
│   │       ├── service/
│   │       ├── mapper/
│   │       └── model/
│   ├── mcp/                       # MCP 服务
│   │   ├── tools/                 # 工具实现
│   │   └── config/                # MCP 配置
│   ├── common/                    # 公共模块
│   │   ├── config/                # 公共配置
│   │   ├── exception/             # 异常处理
│   │   ├── response/              # 响应封装
│   │   └── utils/                 # 工具类
│   └── YuAiAgentApplication.java  # 启动类
├── src/main/resources/
│   ├── application.yml            # 主配置
│   ├── application-dev.yml        # 开发环境
│   ├── application-prod.yml       # 生产环境
│   └── mapper/                    # MyBatis 映射
└── pom.xml                        # Maven 配置
```

#### 5.1.2 核心接口设计

> **架构说明**：所有接口统一使用 `/api/v1/` 前缀。Java 端作为统一入口，接收客户端请求后进行业务处理，需要 AI 能力时转发调用 Python 服务。Gateway 验证 JWT 后将用户 ID 通过请求头 `X-User-Id` 传递给 Java 服务。

**用户服务**
```java
// 用户注册
POST /api/v1/user/register

// 用户登录
POST /api/v1/user/login

// 获取用户信息
GET /api/v1/user/info

// 更新用户信息（昵称、头像）- 暂不支持
// PUT /api/v1/user/info
```

**会话管理服务**
```java
// 创建会话（含情感状态选择）
POST /api/v1/chat/createk
{
    "app_type": "love_app|manus",
    "emotion_status": "single|relationship|married",  // love_app 必填，manus 可传 null 或不传
    "title": "会话标题（可选）"
}

// emotion_status 校验规则：
// - app_type = love_app 时：emotion_status 为必填项，值必须为 single/relationship/married 之一
// - app_type = manus 时：emotion_status 忽略，可传 null 或不传
// - chat 表存储英文值（single/relationship/married），后端接口返回时直接返回中文值（单身/恋爱/已婚）
// - message.metadata 中的 emotion_status 直接存储中文值（单身/恋爱/已婚）

// 获取会话列表（分页，按 last_message_time 倒序排序，仅排序不做搜索/筛选）
GET /api/v1/chat/list?page=1&page_size=10&app_type=love_app

// 获取会话详情
GET /api/v1/chat/{chat_id}

// 删除会话（软删除，级联软删除该会话下所有消息和关联的 agent_task）
DELETE /api/v1/chat/{chat_id}

// 获取会话内的消息历史（分页，时间倒序，最新消息在前）
GET /api/v1/chat/{chat_id}/messages?page=1&page_size=20
```

**AI 对话服务**（Java 转发调用 Python）
```java
// 同步对话
POST /api/v1/ai/love/chat/sync

// 流式对话 (SSE) - POST 方法
POST /api/v1/ai/love/chat/sse
```

**智能体服务**（Java 转发调用 Python）
```java
// 提交智能体任务
POST /api/v1/agent/run

// 查询任务状态（前端每 3 秒轮询）
GET /api/v1/agent/status/{task_id}

// 取消智能体任务（Java 调用 Python 取消接口，立即中断执行，清空 steps）
POST /api/v1/agent/cancel/{task_id}
```

**知识库服务**
```java
// 上传文档（文档内容存储在数据库中）
POST /api/v1/knowledge/document
Content-Type: multipart/form-data

// 获取文档列表（分页）
GET /api/v1/knowledge/documents?page=1&page_size=10

// 删除文档（软删除）
DELETE /api/v1/knowledge/document/{id}

// 重试文档向量化
POST /api/v1/knowledge/document/{id}/retry
```

**Python 回调接口**（Java 端提供，供 Python 调用）
```java
// Python 回调通知 Java 更新智能体任务状态
// 对于 Manus 类型任务，Java 收到回调后还需将 AI 结果存储到 message 表
POST /api/v1/internal/callback/agent/task
Headers: X-Internal-Token: {internal_token}
{
    "task_id": "uuid",
    "status": "completed|failed",
    "result": "任务最终结果",
    "steps": [...]  // 完整的执行步骤数组，一次性回写
}

Response:
{
    "code": 200,
    "message": "success",
    "data": {
        "task_id": "uuid",
        "status": "completed"
    }
}
```

> **说明**：回调接口使用 `/api/v1/internal/` 前缀，通过内部 Token 认证（非 JWT），仅允许 Python 服务调用。Python 在任务完成（completed 或 failed）时一次性回写 steps 和 result。

**健康检查**
```java
// 统一健康检查路径
GET /api/health

Response:
{
    "code": 200,
    "message": "success",
    "data": {
        "status": "UP",
        "timestamp": "2026-06-18T10:00:00Z",
        "services": {
            "java": "UP",
            "python": "UP",
            "mysql": "UP",
            "redis": "UP",
            "nacos": "UP",
            "pgvector": "UP"
        }
    }
}
```

#### 5.1.3 Gateway 路由配置

> **架构变更说明**：所有客户端请求统一路由到 Java 服务。Python 服务不再直接对外暴露，仅由 Java 内部调用。Gateway 负责 JWT 验证并将用户 ID 通过 `X-User-Id` 请求头传递给 Java 服务。

```yaml
spring:
  cloud:
    gateway:
      routes:
        # 所有 API 请求统一路由到 Java 服务
        - id: java-api-service
          uri: lb://yu-ai-agent-java
          predicates:
            - Path=/api/v1/**
          filters:
            - name: JwtAuthFilter  # JWT 认证过滤器
              args:
                excludePaths: /api/v1/user/register,/api/v1/user/login,/api/v1/internal/**

        # 健康检查（不需要认证）
        - id: java-health
          uri: lb://yu-ai-agent-java
          predicates:
            - Path=/api/health

      # 全局过滤器：提取 JWT 中的用户 ID 并通过 X-User-Id 请求头传递
      default-filters:
        - name: GlobalJwtFilter
          args:
            headerName: X-User-Id
```

**Gateway 认证流程**：
```
1. 客户端携带 JWT Token 请求 Gateway
2. Gateway JwtAuthFilter 验证 JWT 有效性
3. 从 JWT 中提取 user_id
4. 将 user_id 放入请求头 X-User-Id
5. 路由转发到 Java 服务
6. Java 服务从 X-User-Id 获取当前用户 ID
```

**Java 内部调用 Python 服务**：
```yaml
# Java 服务配置
python:
  service:
    base-url: http://yu-ai-agent-python:8000
    timeout: 30000
    endpoints:
      chat-sync: /internal/ai/love/chat/sync
      chat-sse: /internal/ai/love/chat/sse
      agent-run: /internal/agent/run
      agent-cancel: /internal/agent/cancel
      knowledge-index: /internal/knowledge/index
      knowledge-search: /internal/knowledge/search
      health: /internal/health
  callback:
    url: http://yu-ai-agent-java:8123/api/v1/internal/callback/agent/task
    token: ${INTERNAL_CALLBACK_TOKEN}  # 内部认证 Token，通过环境变量配置
```

> **说明**：Python 服务的内部接口使用 `/internal/` 前缀，不通过 Gateway 暴露，仅由 Java 服务内部 HTTP 调用。

---

### 5.2 Python AI 模块

#### 5.2.1 项目结构

```
yu-ai-agent-python/
├── app/
│   ├── api/                       # API 路由
│   │   ├── __init__.py
│   │   ├── chat.py               # 对话接口
│   │   ├── agent.py              # 智能体接口
│   │   ├── knowledge.py          # 知识库接口
│   │   └── health.py             # 健康检查接口
│   ├── core/                      # 核心模块
│   │   ├── __init__.py
│   │   ├── config.py             # 配置管理（混合方式：敏感配置用环境变量，其他用配置文件）
│   │   ├── security.py           # 安全认证
│   │   └── logging.py            # 日志配置
│   ├── ai/                        # AI 核心
│   │   ├── __init__.py
│   │   ├── llm/                  # LLM 调用
│   │   │   ├── __init__.py
│   │   │   ├── dashscope.py      # 阿里云模型
│   │   │   └── openai.py         # OpenAI 模型
│   │   ├── rag/                  # RAG 模块
│   │   │   ├── __init__.py
│   │   │   ├── loader.py         # 文档加载（Markdown/PDF/TXT）
│   │   │   ├── splitter.py       # 文档分割
│   │   │   ├── vectorstore.py    # 向量存储
│   │   │   └── retriever.py      # 混合检索器（向量+关键词）
│   │   ├── agent/                # 智能体
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # 基础智能体
│   │   │   ├── react.py          # ReAct 智能体
│   │   │   └── manus.py          # Manus 智能体
│   │   ├── tools/                # 工具集
│   │   │   ├── __init__.py
│   │   │   ├── search.py         # 搜索工具
│   │   │   ├── file.py           # 文件工具
│   │   │   ├── web.py            # 网页工具
│   │   │   └── pdf.py            # PDF 工具
│   │   └── memory/               # 对话记忆
│   │       ├── __init__.py
│   │       └── buffer.py         # 跨会话累计记忆（由 Java 组装传入）
│   ├── models/                    # 数据模型
│   │   ├── __init__.py
│   │   ├── chat.py               # 对话模型
│   │   └── knowledge.py          # 知识库模型
│   └── services/                  # 业务服务
│       ├── __init__.py
│       ├── chat_service.py       # 对话服务
│       ├── agent_service.py      # 智能体服务（每用户单任务并发限制）
│       └── knowledge_service.py  # 知识库服务
├── tests/                         # 测试
├── config/                        # 本地配置文件目录
│   ├── config.yaml               # 主配置文件
│   ├── config-dev.yaml           # 开发环境配置
│   └── config-prod.yaml          # 生产环境配置
├── requirements.txt               # 依赖
├── Dockerfile                     # Docker 配置
└── main.py                        # 启动入口
```

#### 5.2.2 核心接口设计

> **说明**：Python 服务仅提供内部接口，使用 `/internal/` 前缀，不通过 Gateway 对外暴露。Java 服务通过内部 HTTP 调用访问这些接口。用户 ID 通过请求头 `X-User-Id` 从 Java 服务传递给 Python 服务。

**对话接口**（由 Java 转发调用）
```python
# 同步对话
POST /internal/ai/love/chat/sync
Headers: X-User-Id: {user_id}
{
    "message": "用户消息",
    "chat_id": "uuid",
    "emotion_status": "single|relationship|married",  # 英文值，用于 AI 理解用户情感状态
    "history": [...]  # Java 组装的跨会话记忆（最近20条）
}

# 流式对话 - POST 方法
POST /internal/ai/love/chat/sse
Headers: X-User-Id: {user_id}
{
    "message": "用户消息",
    "chat_id": "uuid",
    "emotion_status": "single|relationship|married",  # 英文值，用于 AI 理解用户情感状态
    "history": [...]
}
```

**智能体接口**（由 Java 转发调用）
```python
# 执行智能体任务 - 异步返回 task_id
# Python 执行完成后通过回调接口 POST /api/v1/internal/callback/agent/task 通知 Java
POST /internal/agent/run
Headers: X-User-Id: {user_id}
{
    "message": "任务描述",
    "task_id": "uuid",           # Java 预生成的 task_id
    "chat_id": "uuid",           # 关联会话ID（Manus 类型用于消息历史关联）
    "callback_url": "http://yu-ai-agent-java:8123/api/v1/internal/callback/agent/task",  # 回调地址
    "callback_token": "xxx"      # 内部认证 Token
}

Response:
{
    "code": 200,
    "data": {
        "task_id": "uuid"
    }
}

# 取消智能体任务 - Python 立即中断当前步骤并停止执行
POST /internal/agent/cancel/{task_id}
Headers: X-User-Id: {user_id}
```

**知识库接口**（由 Java 转发调用）
```python
# 文档向量化
POST /internal/knowledge/index
{
    "document_id": "文档ID",
    "content": "文档内容",
    "file_type": "markdown|pdf|txt"
}

# 知识检索 - 混合检索策略
POST /internal/knowledge/search
{
    "query": "查询内容",
    "top_k": 5,
    "strategy": "hybrid"  # hybrid | vector | keyword
}
```

**健康检查接口**
```python
# Python 服务健康检查（内部接口）
GET /internal/health

Response:
{
    "code": 200,
    "message": "success",
    "data": {
        "status": "UP",
        "timestamp": "2026-06-18T10:00:00Z",
        "services": {
            "langchain": "UP",
            "pgvector": "UP",
            "dashscope": "UP"
        }
    }
}
```

---

### 5.3 前端模块

#### 5.3.1 项目结构

```
yu-ai-agent-frontend/
├── src/
│   ├── api/                       # API 请求
│   │   ├── index.js
│   │   ├── user.js
│   │   ├── chat.js
│   │   ├── agent.js
│   │   └── knowledge.js
│   ├── views/                     # 页面
│   │   ├── Home.vue
│   │   ├── LoveMaster.vue
│   │   ├── SuperAgent.vue
│   │   └── Knowledge.vue
│   ├── components/                # 组件
│   │   ├── ChatRoom.vue
│   │   ├── MessageBubble.vue
│   │   ├── AiAvatar.vue
│   │   ├── EmotionSelector.vue    # 情感状态选择器
│   │   ├── TaskStatus.vue         # 任务状态展示
│   │   └── AppFooter.vue
│   ├── router/                    # 路由
│   ├── stores/                    # 状态管理
│   ├── utils/                     # 工具函数
│   ├── styles/                    # 响应式样式
│   │   └── responsive.css
│   └── App.vue
├── public/
├── package.json
└── vite.config.js
```

#### 5.3.2 响应式设计要求

- **桌面端**：>= 1024px，完整布局
- **平板端**：768px - 1023px，适配布局
- **移动端**：< 768px，单列布局，优化触控体验

---

## 6. 数据库设计

### 6.1 MySQL 业务数据库

#### 6.1.1 用户表 (user)

```sql
CREATE TABLE `user` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `password` VARCHAR(255) NOT NULL,
    `nickname` VARCHAR(50),
    `avatar` VARCHAR(255),
    `status` TINYINT DEFAULT 1 COMMENT '0-禁用 1-启用',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '0-未删除 1-已删除',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_username` (`username`)
);
```

> **说明**：移除了 `role`、`email`、`phone` 字段，简化用户模型。

#### 6.1.2 对话表 (chat)

```sql
CREATE TABLE `chat` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `chat_id` VARCHAR(36) NOT NULL COMMENT 'UUID 格式',
    `user_id` BIGINT NOT NULL,
    `app_type` VARCHAR(20) NOT NULL COMMENT 'love_app | manus',
    `emotion_status` VARCHAR(20) COMMENT 'single | relationship | married（会话创建时设定，不可更改）',
    `title` VARCHAR(255),
    `last_message_time` DATETIME COMMENT '最后一条消息时间，用于会话列表排序',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '0-未删除 1-已删除',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_chat_id` (`chat_id`),
    INDEX `idx_user_app_type` (`user_id`, `app_type`)
);
```

> **说明**：`emotion_status` 在会话创建时设定，会话内不可更改。`last_message_time` 用于会话列表按最新消息时间排序。**删除会话时，该会话下的所有消息和关联的 agent_task 同步软删除**（级联操作）。

#### 6.1.3 消息表 (message)

```sql
CREATE TABLE `message` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `chat_id` VARCHAR(36) NOT NULL COMMENT 'UUID 格式',
    `role` VARCHAR(20) NOT NULL COMMENT 'user | assistant | system',
    `content` TEXT NOT NULL,
    `metadata` JSON COMMENT '消息元数据，结构见下方 JSON 字段定义',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '0-未删除 1-已删除',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_chat_id` (`chat_id`)
);
```

**`metadata` JSON 字段结构**：
```json
{
    "emotion_status": "单身|恋爱|已婚",
    "tokens_used": 150,
    "model": "qwen-turbo",
    "tool_calls": [
        {
            "tool": "search",
            "input": "查询内容",
            "output": "搜索结果"
        }
    ],
    "rag_sources": [
        {
            "document_id": 1,
            "title": "文档标题",
            "relevance_score": 0.95,
            "excerpt": "相关片段"
        }
    ]
}
```

#### 6.1.4 知识库文档表 (knowledge_document)

```sql
CREATE TABLE `knowledge_document` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL COMMENT '文档所属用户ID，实现用户隔离',
    `title` VARCHAR(255) NOT NULL COMMENT '文档标题，自动从上传文件名提取',
    `content` LONGTEXT COMMENT '文档内容，直接存储在数据库中',
    `file_type` VARCHAR(20) NOT NULL COMMENT 'markdown | pdf | txt',
    `status` TINYINT DEFAULT 0 COMMENT '0-待处理 1-已向量化 2-处理失败',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '0-未删除 1-已删除',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_user_id` (`user_id`)
);
```

> **说明**：文档内容直接存储在 `content` 字段（LONGTEXT 类型）中，不使用文件系统存储。移除了 `file_path` 字段。

#### 6.1.5 智能体任务表 (agent_task)

```sql
CREATE TABLE `agent_task` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `task_id` VARCHAR(36) NOT NULL COMMENT 'UUID 格式',
    `user_id` BIGINT NOT NULL,
    `chat_id` VARCHAR(36) COMMENT '关联会话ID，Manus 类型通过此字段与 message 表关联',
    `message` TEXT NOT NULL COMMENT '任务描述（用户输入的任务指令）',
    `status` VARCHAR(20) DEFAULT 'pending' COMMENT 'pending | running | completed | failed | cancelled',
    `result` TEXT COMMENT '任务最终结果',
    `steps` JSON COMMENT '执行步骤详情，Python 完成时一次性回写，取消任务时清空',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '0-未删除 1-已删除',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_task_id` (`task_id`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_chat_id` (`chat_id`)
);
```

> **说明**：agent_task 表仅存储任务信息（任务描述、状态、执行步骤、结果），用户消息和 AI 回复内容存储在 message 表中。删除会话时，关联的 agent_task 也同步软删除。

**`steps` JSON 字段结构**：
```json
[
    {
        "step": 1,
        "tool": "search",
        "input": "查询内容",
        "output": "搜索结果",
        "status": "completed",
        "start_time": "2026-06-18T10:00:00Z",
        "end_time": "2026-06-18T10:00:05Z",
        "error": null
    },
    {
        "step": 2,
        "tool": "web_fetch",
        "input": "URL",
        "output": "网页内容",
        "status": "completed",
        "start_time": "2026-06-18T10:00:05Z",
        "end_time": "2026-06-18T10:00:10Z",
        "error": null
    }
]
```

### 6.2 PgVector 向量数据库

```sql
-- 向量表由 LangChain 自动管理
-- 维度：1536 (DashScope Embedding)
-- 索引类型：HNSW
-- 距离类型：COSINE_DISTANCE
-- 支持混合检索：向量相似度 + 关键词
```

---

## 7. 接口规范

### 7.1 统一响应格式

**成功响应**：
```json
{
    "code": 200,
    "message": "success",
    "data": {}
}
```

**错误响应**：
```json
{
    "code": 400,
    "message": "请求参数错误",
    "data": null,
    "error": {
        "type": "ValidationError",
        "detail": "username 不能为空",
        "timestamp": "2026-06-18T10:00:00Z"
    }
}
```

**分页响应**：
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "list": [],
        "pagination": {
            "page": 1,
            "page_size": 10,
            "total": 100,
            "total_pages": 10
        }
    }
}
```

### 7.2 错误码定义

| 错误码 | 说明 | HTTP 状态码 |
|--------|------|------------|
| 200 | 成功 | 200 |
| 400 | 请求参数错误 | 400 |
| 401 | 未认证（JWT 无效或过期） | 401 |
| 403 | 无权限 | 403 |
| 404 | 资源不存在 | 404 |
| 500 | 服务器内部错误 | 500 |
| 1001 | AI 服务调用失败 | 502 |
| 1002 | 知识库检索失败 | 500 |
| 1003 | 工具调用失败 | 500 |
| 1004 | 智能体任务执行失败 | 500 |
| 1005 | 智能体任务已满（该用户已有任务运行中） | 429 |
| 1006 | 会话不存在 | 404 |
| 1007 | 情感状态不可更改 | 400 |
| 1008 | 任务取消失败 | 500 |
| 1009 | 文档向量化重试失败（文档状态非失败） | 400 |
| 1010 | 内部回调认证失败 | 401 |

### 7.3 SSE 流式响应格式

> **内容格式说明**：每个 `answer` 事件的 `content` 字段为一个完整的句子（不是单个 token），前端可直接渲染。流式结束前返回完整的 `metadata` 事件（包含 token 用量、模型信息等），最后发送 `[DONE]` 标记。

```
data: {"type":"thinking","content":"正在思考..."}
data: {"type":"tool_call","tool":"search","args":{"query":"xxx"}}
data: {"type":"tool_result","tool":"search","result":"..."}
data: {"type":"answer","content":"根据您的情感状态，我建议您可以尝试以下方法来改善沟通。"}
data: {"type":"answer","content":"首先，选择一个双方都放松的时间进行真诚的对话。"}
data: {"type":"answer","content":"其次，使用'我'语句表达感受，避免指责性的'你'语句。"}
data: {"type":"metadata","content":{"tokens_used":350,"model":"qwen-turbo","tool_calls":[],"rag_sources":[]}}
data: [DONE]
```

**SSE 消息类型说明**：

| type | 说明 | 字段 |
|------|------|------|
| thinking | AI 思考过程 | content（字符串） |
| tool_call | 工具调用请求 | tool, args |
| tool_result | 工具执行结果 | tool, result |
| answer | 回答内容（完整句子） | content（字符串） |
| metadata | 消息元数据（流结束前发送） | content（JSON 对象，包含 tokens_used、model、tool_calls、rag_sources） |
| error | 错误信息 | message |

### 7.4 接口路径统一规范

> **所有对外接口统一使用 `/api/v1/` 前缀。健康检查使用 `/api/health`。**

**对外暴露路径**（通过 Gateway 统一路由到 Java）：
```
/api/v1/user/**              # 用户服务
/api/v1/user/register        # 注册
/api/v1/user/login           # 登录
/api/v1/user/info            # 用户信息（仅 GET，暂不支持 PUT 更新）

/api/v1/chat/**              # 会话管理
/api/v1/chat/create          # 创建会话
/api/v1/chat/list            # 会话列表
/api/v1/chat/{chat_id}       # 会话详情/删除
/api/v1/chat/{chat_id}/messages  # 消息历史

/api/v1/ai/**                # AI 对话服务（Java 转发 Python）
/api/v1/ai/love/chat/sync    # 同步对话
/api/v1/ai/love/chat/sse     # 流式对话

/api/v1/agent/**             # 智能体服务（Java 转发 Python）
/api/v1/agent/run            # 提交任务
/api/v1/agent/status/{task_id}   # 查询状态
/api/v1/agent/cancel/{task_id}   # 取消任务

/api/v1/knowledge/**         # 知识库服务
/api/v1/knowledge/document   # 文档上传
/api/v1/knowledge/documents  # 文档列表
/api/v1/knowledge/document/{id}  # 文档删除
/api/v1/knowledge/document/{id}/retry  # 重试向量化

/api/v1/internal/**          # 内部回调接口（Python 调用）
/api/v1/internal/callback/agent/task  # 智能体任务回调

/api/health                  # 健康检查（不需要认证）
```

**Python 内部服务路径**（不对外暴露，仅 Java 内部调用）：
```
/internal/ai/love/chat/sync     # 同步对话
/internal/ai/love/chat/sse      # 流式对话
/internal/agent/run             # 智能体任务
/internal/agent/cancel/{task_id}  # 取消任务
/internal/knowledge/index       # 向量化
/internal/knowledge/search      # 检索
/internal/health                # 健康检查
```

**Java 内部回调路径**（不对外暴露，仅 Python 回调使用）：
```
/api/v1/internal/callback/agent/task  # Python 回调更新任务状态
```

### 7.5 通信方式

- **前端 → Gateway**：HTTP REST + SSE（POST 方法），携带 JWT Token
- **Gateway → Java**：HTTP REST，JWT 验证后通过 `X-User-Id` 传递用户 ID
- **Java → Python**：HTTP REST 内部调用（`/internal/` 前缀），携带 `X-User-Id`
- **服务发现**：Nacos 注册中心

### 7.6 Java-Python 内部 API 契约

> Python 服务仅通过内部网络被 Java 调用，使用 `/internal/` 前缀，不对外暴露。

**对话接口**
```
POST /internal/ai/love/chat/sync
Headers: X-User-Id: {user_id}, Content-Type: application/json
{
    "chat_id": "uuid",
    "message": "用户消息",
    "emotion_status": "single|relationship|married",  # 英文值，用于 AI 理解用户情感状态
    "history": [
        {"role": "user", "content": "历史消息1"},
        {"role": "assistant", "content": "历史回复1"}
    ]
}

Response:
{
    "code": 200,
    "data": {
        "content": "AI 回复内容",
        "metadata": {
            "tokens_used": 150,
            "model": "qwen-turbo",
            "tool_calls": [],
            "rag_sources": []
        }
    }
}

POST /internal/ai/love/chat/sse
Headers: X-User-Id: {user_id}, Content-Type: application/json
(Request body 同上，响应为 SSE 流)
```

**智能体接口**
```
POST /internal/agent/run
Headers: X-User-Id: {user_id}, Content-Type: application/json
{
    "message": "任务描述",
    "task_id": "uuid",           # Java 预生成的 task_id
    "chat_id": "uuid",           # 关联会话ID（Manus 类型用于消息历史关联）
    "callback_url": "http://yu-ai-agent-java:8123/api/v1/internal/callback/agent/task",
    "callback_token": "xxx"      # 内部认证 Token
}

Response:
{
    "code": 200,
    "data": {
        "task_id": "uuid",
        "status": "pending"
    }
}

POST /internal/agent/cancel/{task_id}
Headers: X-User-Id: {user_id}

Response:
{
    "code": 200,
    "data": {
        "task_id": "uuid",
        "status": "cancelled"
    }
}

> **取消流程说明**：Java 收到取消请求后，调用 Python 端的取消接口（POST /internal/agent/cancel/{task_id}），Python 立即中断当前步骤并停止执行，Java 清空 agent_task 的 steps 字段并将状态更新为 cancelled。
```

**知识库接口**
```
POST /internal/knowledge/index
Headers: Content-Type: application/json
{
    "document_id": 1,
    "content": "文档内容",
    "file_type": "markdown|pdf|txt"
}

Response:
{
    "code": 200,
    "data": {
        "document_id": 1,
        "status": "indexed",
        "chunks_count": 50
    }
}

POST /internal/knowledge/search
Headers: Content-Type: application/json
{
    "query": "查询内容",
    "top_k": 5,
    "strategy": "hybrid"
}

Response:
{
    "code": 200,
    "data": {
        "results": [
            {
                "document_id": 1,
                "title": "文档标题",
                "content": "匹配内容",
                "relevance_score": 0.95
            }
        ]
    }
}
```

**健康检查**
```
GET /internal/health

Response:
{
    "code": 200,
    "data": {
        "status": "UP",
        "services": {
            "langchain": "UP",
            "pgvector": "UP",
            "dashscope": "UP"
        }
    }
}
```

**Python 回调 Java 接口**（Python 任务完成后回调通知 Java）
```
POST /api/v1/internal/callback/agent/task
Headers: X-Internal-Token: {internal_token}, Content-Type: application/json
{
    "task_id": "uuid",
    "status": "completed|failed",
    "result": "任务最终结果（completed 时为结果文本，failed 时为错误信息）",
    "steps": [
        {
            "step": 1,
            "tool": "search",
            "input": "查询内容",
            "output": "搜索结果",
            "status": "completed",
            "start_time": "2026-06-18T10:00:00Z",
            "end_time": "2026-06-18T10:00:05Z",
            "error": null
        }
    ]
}

Response:
{
    "code": 200,
    "message": "success",
    "data": {
        "task_id": "uuid",
        "status": "completed"
    }
}

Error Response (任务不存在):
{
    "code": 404,
    "message": "任务不存在",
    "data": null
}

Error Response (认证失败):
{
    "code": 401,
    "message": "内部认证失败",
    "data": null
}
```

> **回调机制说明**：
> - Python 仅在任务完成（completed 或 failed）时回调一次，一次性回写 steps 和 result
> - 执行过程中不逐步回写，前端轮询到的状态为 pending/running，steps 字段为空
> - 回调接口通过 X-Internal-Token 进行内部认证，Token 通过环境变量配置
> - Java 收到回调后更新 agent_task 表的 status、result、steps 字段
> - 取消任务时，Java 调用 Python 取消接口（POST /internal/agent/cancel/{task_id}），Python 立即中断执行，Java 清空 steps 字段并将状态更新为 cancelled

### 7.7 对外接口完整响应格式定义

#### 7.7.1 GET /api/v1/user/info - 获取用户信息

> **说明**：暂不支持更新用户信息（昵称、头像），仅支持获取。

```
Response:
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "username": "zhangsan",
        "nickname": "张三",
        "avatar": "https://example.com/avatar.jpg",
        "status": 1,
        "create_time": "2026-06-18T10:00:00Z"
    }
}
```

#### 7.7.2 POST /api/v1/chat/create - 创建会话

**请求**：
```
{
    "app_type": "love_app",
    "emotion_status": "single",
    "title": "我的恋爱咨询"（可选）
}
```

**响应**：
```
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "chat_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": 1,
        "app_type": "love_app",
        "emotion_status": "单身",
        "title": "我的恋爱咨询",
        "last_message_time": null,
        "create_time": "2026-06-18T10:00:00Z",
        "update_time": "2026-06-18T10:00:00Z"
    }
}
```

#### 7.7.3 GET /api/v1/chat/list - 获取会话列表

**请求参数**：
- `page`：页码，默认 1
- `page_size`：每页数量，默认 10
- `app_type`：应用类型筛选（love_app|manus），可选

**响应**（按 `last_message_time` 倒序排序，仅排序不做搜索/筛选）：
```
{
    "code": 200,
    "message": "success",
    "data": {
        "list": [
            {
                "id": 1,
                "chat_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": 1,
                "app_type": "love_app",
                "emotion_status": "单身",
                "title": "我的恋爱咨询",
                "last_message_time": "2026-06-18T10:30:00Z",
                "create_time": "2026-06-18T10:00:00Z",
                "update_time": "2026-06-18T10:30:00Z"
            },
            {
                "id": 2,
                "chat_id": "660e8400-e29b-41d4-a716-446655440001",
                "user_id": 1,
                "app_type": "manus",
                "emotion_status": null,
                "title": "帮我制定旅行计划",
                "last_message_time": "2026-06-18T09:15:00Z",
                "create_time": "2026-06-18T09:00:00Z",
                "update_time": "2026-06-18T09:15:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "page_size": 10,
            "total": 2,
            "total_pages": 1
        }
    }
}
```

#### 7.7.4 GET /api/v1/chat/{chat_id} - 获取会话详情

**响应**：
```
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "chat_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": 1,
        "app_type": "love_app",
        "emotion_status": "单身",
        "title": "我的恋爱咨询",
        "last_message_time": "2026-06-18T10:30:00Z",
        "create_time": "2026-06-18T10:00:00Z",
        "update_time": "2026-06-18T10:30:00Z"
    }
}
```

#### 7.7.5 GET /api/v1/chat/{chat_id}/messages - 获取消息列表

**请求参数**：
- `page`：页码，默认 1
- `page_size`：每页数量，默认 20

**响应**（时间倒序，最新消息在前）：
```
{
    "code": 200,
    "message": "success",
    "data": {
        "list": [
            {
                "id": 5,
                "chat_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "assistant",
                "content": "建议您可以尝试主动约对方一起参加活动。",
                "metadata": {
                    "emotion_status": "单身",
                    "tokens_used": 120,
                    "model": "qwen-turbo",
                    "tool_calls": [],
                    "rag_sources": [
                        {
                            "document_id": 1,
                            "title": "恋爱心理学入门",
                            "relevance_score": 0.92,
                            "excerpt": "社交圈拓展的关键是..."
                        }
                    ]
                },
                "create_time": "2026-06-18T10:30:00Z"
            },
            {
                "id": 4,
                "chat_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "user",
                "content": "我喜欢一个女生但不知道怎么接近她",
                "metadata": null,
                "create_time": "2026-06-18T10:29:55Z"
            },
            {
                "id": 3,
                "chat_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "assistant",
                "content": "你好！我是恋爱大师，很高兴为你提供情感咨询。",
                "metadata": {
                    "emotion_status": "单身",
                    "tokens_used": 50,
                    "model": "qwen-turbo",
                    "tool_calls": [],
                    "rag_sources": []
                },
                "create_time": "2026-06-18T10:00:05Z"
            }
        ],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total": 3,
            "total_pages": 1
        }
    }
}
```

#### 7.7.6 GET /api/v1/knowledge/documents - 获取文档列表

**请求参数**：
- `page`：页码，默认 1
- `page_size`：每页数量，默认 10

**响应**（仅返回当前用户的文档）：
```
{
    "code": 200,
    "message": "success",
    "data": {
        "list": [
            {
                "id": 1,
                "user_id": 1,
                "title": "恋爱心理学入门",
                "file_type": "markdown",
                "status": 1,
                "create_time": "2026-06-18T08:00:00Z",
                "update_time": "2026-06-18T08:05:00Z"
            },
            {
                "id": 2,
                "user_id": 1,
                "title": "沟通技巧大全",
                "file_type": "pdf",
                "status": 0,
                "create_time": "2026-06-18T09:00:00Z",
                "update_time": "2026-06-18T09:00:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "page_size": 10,
            "total": 2,
            "total_pages": 1
        }
    }
}
```

#### 7.7.7 POST /api/v1/knowledge/document - 上传文档

**请求**：
```
Content-Type: multipart/form-data
file: （文件内容，支持 .md / .pdf / .txt）
```

> **标题自动提取**：服务端自动从上传文件名提取标题（去掉文件扩展名）。例如上传文件 `恋爱心理学入门.md`，自动提取标题为 `恋爱心理学入门`。

**响应**：
```
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 3,
        "user_id": 1,
        "title": "恋爱心理学入门（自动从文件名提取）",
        "file_type": "markdown",
        "status": 0,
        "create_time": "2026-06-18T10:00:00Z"
    }
}
```

> **说明**：`status` 为 0 表示待处理（异步向量化中），1 表示已向量化，2 表示处理失败。上传后异步触发向量化流程。

---

## 8. 部署架构

### 8.1 开发环境

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  nacos:
    image: nacos/nacos-server:v2.3.0
    ports:
      - "8848:8848"
      - "9848:9848"
    environment:
      - MODE=standalone
  
  java-service:
    build: ./yu-ai-agent-java
    ports:
      - "8123:8123"
    environment:
      - SPRING_PROFILES_ACTIVE=dev
      - NACOS_SERVER_ADDR=nacos:8848
      - JWT_SECRET=${JWT_SECRET}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8123/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
  
  python-service:
    build: ./yu-ai-agent-python
    ports:
      - "8000:8000"
    environment:
      - ENV=dev
    volumes:
      - ./yu-ai-agent-python/config:/app/config  # 挂载本地配置文件
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/internal/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
  
  mysql:
    image: mysql:8.0
    ports:
      - "3306:3306"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 3
  
  pgvector:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 3
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
```

### 8.2 生产环境

- **容器化部署**：Docker + Kubernetes
- **负载均衡**：Nginx / ALB（仅暴露 Java 服务，Python 不对外暴露）
- **服务治理**：Nacos（服务发现 + 配置管理）
- **监控告警**：Prometheus + Grafana
- **健康检查**：统一路径 `/api/health`（Java 服务汇总检查所有依赖服务状态）
- **Python 配置**：混合方式 - 敏感配置（API Key 等）通过环境变量管理，其他配置使用本地配置文件（config/config-prod.yaml），通过环境变量 `ENV=prod` 切换

---

## 9. 开发计划

### 9.1 第一阶段：基础架构搭建（2 周）

- [ ] Java 后端项目初始化
- [ ] Python AI 模块初始化
- [ ] 数据库设计和初始化（含 is_deleted 字段）
- [ ] 基础 API 框架搭建
- [ ] Nacos 服务注册与配置
- [ ] 健康检查端点实现
- [ ] Gateway 路由配置

### 9.2 第二阶段：核心功能开发（3 周）

- [ ] 用户注册/登录（用户名+密码）
- [ ] JWT 认证 + Gateway 用户 ID 提取（X-User-Id 请求头）
- [ ] 会话管理（创建、列表、删除、详情）
- [ ] 对话服务开发（跨会话累计 20 条消息记忆窗口）
- [ ] Java 转发调用 Python 架构实现
- [ ] RAG 知识库实现（Markdown/PDF/TXT + 数据库存储 + 混合检索）
- [ ] 情感状态选择功能（会话级别，不可更改）
- [ ] 工具调用框架
- [ ] MCP 服务集成

### 9.3 第三阶段：智能体开发（2 周）

- [ ] ReAct 智能体实现
- [ ] Manus 智能体开发
- [ ] 异步任务机制（task_id + 每 3 秒轮询）
- [ ] 每用户单任务并发限制
- [ ] 执行上限强制终止
- [ ] 智能体任务取消功能
- [ ] 流式输出优化（POST 方法）
- [ ] Python 回调 Java 接口实现（任务状态一次性回写）
- [ ] Manus 智能体消息存储（用户消息和 AI 结果存 message 表，agent_task 仅存任务信息）
- [ ] 向量化重试接口实现

### 9.4 第四阶段：前端开发（2 周）

- [ ] 前端项目搭建
- [ ] 响应式布局设计（桌面+移动端）
- [ ] 会话管理界面（列表、创建、删除）
- [ ] 对话界面开发
- [ ] 情感状态选择器组件（会话创建时）
- [ ] 智能体任务状态轮询（每 3 秒）
- [ ] 智能体任务取消功能
- [ ] 知识库管理界面

### 9.5 第五阶段：测试和优化（1 周）

- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化（>= 1000 并发）
- [ ] 健康检查验证
- [ ] 文档完善

---

## 10. 非功能性需求

### 10.1 性能要求

- API 响应时间：< 200ms（不含 AI 调用）
- AI 流式输出延迟：< 500ms
- 并发请求数：>= 1000
- 知识库检索时间：< 1s

### 10.2 可用性要求

- 系统可用性：99.9%
- 故障恢复时间：< 30 分钟
- 数据备份：每日自动备份
- 健康检查：Java 和 Python 服务均提供健康检查端点

### 10.3 安全要求

- HTTPS 加密传输
- JWT Token 认证（Token 过期后不支持刷新，用户需重新登录）
- JWT Secret Key 通过环境变量管理（不硬编码）
- **内部回调认证**：Python 回调 Java 接口使用 X-Internal-Token 认证，Token 通过环境变量配置
- SQL 注入防护
- XSS 攻击防护
- 软删除保护数据安全

### 10.4 可扩展性

- 支持水平扩展
- 支持多模型切换
- 支持工具插件化
- 支持 MCP 服务热插拔

---

## 11. 附录

### 11.1 术语表

| 术语 | 说明 |
|------|------|
| RAG | Retrieval-Augmented Generation，检索增强生成 |
| MCP | Model Context Protocol，模型上下文协议 |
| ReAct | Reasoning + Acting，推理与行动模式 |
| SSE | Server-Sent Events，服务器推送事件 |
| PgVector | PostgreSQL 向量扩展 |
| Embedding | 文本向量化 |
| LLM | Large Language Model，大语言模型 |
| Nacos | 服务发现 + 配置管理中心 |
| UUID | 通用唯一标识符（用于 chat_id、task_id） |

### 11.2 参考资料

- [Spring AI 官方文档](https://docs.spring.io/spring-ai/reference/)
- [LangChain Python 文档](https://python.langchain.com/docs/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [PgVector 文档](https://github.com/pgvector/pgvector)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [Nacos 官方文档](https://nacos.io/zh-cn/docs/)

---

**文档维护人**：开发团队
**最后更新**：2026-06-18（v1.4 - 第五轮决策修订）

---

## 修订记录

| 版本 | 日期 | 修订内容 |
|------|------|----------|
| v1.0 | 2026-06-18 | 初始版本 |
| v1.1 | 2026-06-18 | 第二轮决策修订：接口路径统一 /api/v1/ 前缀；健康检查统一 /api/health；Java 转发调用 Python 架构；情感状态会话级别不可更改；对话记忆窗口改为跨会话累计 20 条；智能体轮询频率 3 秒；新增任务取消接口；新增会话管理接口；文档内容数据库存储；Python 本地配置文件；定义完整响应结构、错误/分页格式、JSON 字段结构 |
| v1.2 | 2026-06-18 | 第三轮决策修订：智能体并发限制改为每用户 1 个任务；知识库文档增加 user_id 字段实现用户隔离；文档标题自动从文件名提取；跨会话记忆明确为同一用户所有会话最近 20 条（不分 app_type）；情感状态英文存储+中文显示（single/relationship/married）；SSE answer 事件为完整句子；SSE 结束前返回 metadata 事件；消息按时间倒序返回；任务不限制时间仅限制 20 步；取消任务支持 pending 和 running 状态；Python 配置混合方式（环境变量+配置文件）；会话列表仅排序不做搜索/筛选；补充 7 个接口完整响应格式定义 |
| v1.3 | 2026-06-18 | 第四轮决策修订：智能体任务结果回写机制（Python 回调 Java，完成时一次性回写 steps）；新增 Python 回调 Java 接口（/api/v1/internal/callback/agent/task）；知识库文件内容由 Java 提取后传给 Python；Python 独立队列消费向量化；新增向量化重试接口（POST /knowledge/document/{id}/retry）；文档暂不支持更新（删除后重新上传）；Manus 类型仅 agent/run 接口；agent_task 增加 chat_id 关联 message 表；emotion_status 约束（manus 忽略，love_app 必填）；Token 过期需重新登录（不支持刷新）；会话删除级联软删除消息；emotion_status 后端直接返回中文值；新增智能体任务状态流转时序图；新增知识库文档上传与向量化流程图 |
| v1.4 | 2026-06-18 | 第五轮决策修订：message.metadata 中 emotion_status 直接存储中文值（单身/恋爱/已婚）；删除会话时 agent_task 也级联软删除；Manus 类型消息存储流程明确（用户消息和 AI 结果都存 message 表，agent_task 只存任务信息）；取消任务完整流程（Java 调用 Python 取消接口，立即中断，清空 steps）；消息存储时机（AI 回复成功后一起存储）；用户信息更新接口暂不支持（移除 PUT /api/v1/user/info） |