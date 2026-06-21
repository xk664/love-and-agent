    # AI 超级智能体系统 - 分模块开发流程

> **项目名称**：AI 超级智能体系统
> **技术架构**：Java + Python 完全分离微服务架构
> **创建日期**：2026-06-18

---

## 一、模块依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (Vue 3)                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Java 业务服务 (Spring Boot 3)               │
│  - JWT 认证 (JwtAuthInterceptor)                            │
│  - 请求追踪 (RequestTraceFilter)                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 用户管理  │  │ 会话管理  │  │ 对话管理  │  │ 知识库管理│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐                                │
│  │ 智能体管理│  │ 内部回调  │                                │
│  └──────────┘  └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (内部HTTP调用)
┌─────────────────────────────────────────────────────────────┐
│                  Python AI 服务 (FastAPI)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ LLM调用   │  │ RAG知识库 │  │ 智能体推理│                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                               │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐              │
│  │  MySQL    │  │  PgVector    │  │  Redis   │              │
│  └──────────┘  └──────────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、开发阶段规划

### 阶段一：基础架构搭建（第1-2周）
### 阶段二：用户管理模块（第2-3周）
### 阶段三：会话管理模块（第3-4周）
### 阶段四：对话服务模块（第4-5周）
### 阶段五：知识库管理模块（第5-6周）
### 阶段六：智能体模块（第6-8周）
### 阶段七：前端开发（第8-10周）
### 阶段八：测试与优化（第10-11周）

---

## 三、详细任务清单

---

### 阶段一：基础架构搭建

#### 1.1 数据库初始化

**任务编号**：DB-001
**优先级**：P0
**前置依赖**：无

- [x] 创建 MySQL 数据库 `yu_ai_agent`
- [x] 执行用户表 `user` 建表语句
- [x] 执行对话表 `chat` 建表语句
- [x] 执行消息表 `message` 建表语句
- [x] 执行知识库文档表 `knowledge_document` 建表语句
- [x] 执行智能体任务表 `agent_task` 建表语句
- [x] 创建必要的索引
- [x] 插入测试数据（可选）

**建表语句参考 PRD 第6节**

---

#### 1.2 Java 后端项目初始化

**任务编号**：JAVA-001
**优先级**：P0
**前置依赖**：无

**项目结构**：
```
yu-ai-agent-java/
├── yu-ai-service/                 # 业务服务模块
│   ├── src/main/java/
│   │   └── com/yuaiagent/service/
│   │       ├── user/             # 用户服务
│   │       │   ├── controller/
│   │       │   ├── service/
│   │       │   ├── mapper/
│   │       │   └── model/
│   │       ├── chat/             # 会话服务
│   │       ├── knowledge/        # 知识库服务
│   │       └── agent/            # 智能体服务
│   ├── src/main/resources/
│   │   ├── application.yml
│   │   ├── application-dev.yml
│   │   └── mapper/
│   └── pom.xml
├── yu-ai-common/                  # 公共模块
│   ├── src/main/java/
│   │   └── com/yuaiagent/common/
│   │       ├── config/           # 公共配置（JWT拦截器、CORS、MVC）
│   │       ├── exception/        # 异常处理
│   │       ├── response/         # 响应封装
│   │       └── utils/            # 工具类（JWT等）
│   └── pom.xml
└── pom.xml                        # 父POM
```

**核心任务**：
- [x] 创建 Maven 多模块项目
- [x] 配置 Spring Boot 3.2.x 父POM
- [x] 配置 MyBatis-Plus 3.5.x
- [x] 配置 MySQL 8.0 连接
- [x] 配置 Redis 7.x 连接
- [x] 配置 Knife4j 4.x 接口文档
- [x] 创建统一响应类 `Result<T>`
- [x] 创建全局异常处理器
- [x] 创建通用工具类（JWT、日期等）
- [x] 配置跨域（CORS）
- [x] 配置健康检查端点 `/api/health`
- [x] 实现 JWT 认证拦截器 `JwtAuthInterceptor`
- [x] 实现请求追踪过滤器 `RequestTraceFilter`
- [x] 配置 WebMvc 拦截器注册
- [x] 配置 JWT secret

---

#### 1.3 Python AI 服务初始化

**任务编号**：PYTHON-001
**优先级**：P0
**前置依赖**：无

**项目结构**：
```
yu-ai-agent-python/
├── app/
│   ├── api/                       # API 路由
│   │   ├── __init__.py
│   │   ├── chat.py               # 对话接口
│   │   ├── agent.py              # 智能体接口
│   │   ├── knowledge.py          # 知识库接口
│   │   └── health.py             # 健康检查
│   ├── core/                      # 核心模块
│   │   ├── __init__.py
│   │   ├── config.py             # 配置管理
│   │   ├── security.py           # 安全认证
│   │   └── logging.py            # 日志配置
│   ├── ai/                        # AI 核心
│   │   ├── __init__.py
│   │   ├── llm/                  # LLM 调用
│   │   ├── rag/                  # RAG 模块
│   │   ├── agent/                # 智能体
│   │   ├── tools/                # 工具集
│   │   └── memory/               # 对话记忆
│   ├── models/                    # 数据模型
│   ├── services/                  # 业务服务
│   └── __init__.py
├── config/                        # 配置文件
│   ├── config.yaml               # 主配置
│   ├── config-dev.yaml           # 开发环境
│   └── config-prod.yaml          # 生产环境
├── requirements.txt               # 依赖
├── Dockerfile                     # Docker 配置
└── main.py                        # 启动入口
```

**核心任务**：
- [x] 创建 FastAPI 项目骨架
- [x] 配置依赖管理 requirements.txt
- [x] 实现配置管理（混合方式：环境变量 + 配置文件）
- [x] 实现内部 Token 认证中间件
- [x] 配置日志系统
- [x] 实现健康检查端点 `/internal/health`
- [x] 配置 PgVector 连接
- [x] 配置 DashScope API
- [x] 创建 Dockerfile

---

#### 1.4 Docker Compose 开发环境

**任务编号**：DOCKER-001
**优先级**：P1
**前置依赖**：JAVA-001, PYTHON-001

**核心任务**：
- [x] 创建 `docker-compose.dev.yml`
- [x] 配置 MySQL 8.0 容器
- [x] 配置 PgVector 容器
- [x] 配置 Redis 7 容器
- [x] 配置 Java 服务容器
- [x] 配置 Python 服务容器
- [x] 配置健康检查
- [x] 配置数据卷挂载

---

### 阶段二：用户管理模块

#### 2.1 用户注册

**任务编号**：USER-001
**优先级**：P0
**前置依赖**：DB-001, JAVA-001

**Java 端任务**：
- [x] 创建用户实体类 `User`
- [x] 创建用户 Mapper 接口
- [x] 实现用户 Service 层
  - [ ] 用户名唯一性校验
  - [ ] 密码 BCrypt 加密
  - [ ] 保存用户到数据库
- [x] 实现用户 Controller
  - [ ] `POST /api/v1/user/register` 接口
  - [ ] 参数校验（用户名、密码非空）
- [x] 单元测试

**接口参考 PRD 第3.1.1节**

---

#### 2.2 用户登录

**任务编号**：USER-002
**优先级**：P0
**前置依赖**：USER-001
**Java 端任务**：
- [x] 实现 JWT 工具类
  - [ ] 生成 Token
  - [ ] 解析 Token
  - [ ] Token 过期时间：24小时
- [x] 实现用户 Service 登录方法
  - [x] 用户名密码校验
  - [x] 生成 JWT Token
- [x] 实现用户 Controller
  - [x] `POST /api/v1/user/login` 接口
  - [x] `GET /api/v1/user/info` 接口
- [x] 单元测试

**接口参考 PRD 第3.1.2节**

---

### 阶段三：会话管理模块

#### 3.1 会话创建

**任务编号**：CHAT-001
**优先级**：P0
**前置依赖**：DB-001, USER-002

**Java 端任务**：
- [ ] 创建会话实体类 `Chat`
- [ ] 创建会话 Mapper 接口
- [ ] 实现会话 Service 层
  - [ ] 生成 UUID 格式的 chat_id
  - [ ] 保存会话信息
  - [ ] 情感状态校验（love_app 必填，manus 忽略）
  - [ ] 情感状态中英文转换（存储英文，返回中文）
- [ ] 实现会话 Controller
  - [ ] `POST /api/v1/chat/create` 接口
- [ ] 单元测试

**接口参考 PRD 第5.1.2节 会话管理服务**

---

#### 3.2 会话列表与详情

**任务编号**：CHAT-002
**优先级**：P0
**前置依赖**：CHAT-001

**Java 端任务**：
- [ ] 实现会话列表查询
  - [ ] 分页查询（page、page_size）
  - [ ] 按 app_type 筛选（可选）
  - [ ] 按 last_message_time 倒序排序
  - [ ] 仅返回当前用户的会话
- [ ] 实现会话详情查询
- [x] 实现会话 Controller
  - [ ] `GET /api/v1/chat/list` 接口
  - [ ] `GET /api/v1/chat/{chat_id}` 接口
- [x] 分页响应封装
- [x] 单元测试

---

#### 3.3 会话删除（级联软删除）

**任务编号**：CHAT-003
**优先级**：P0
**前置依赖**：CHAT-002, MSG-001, AGENT-001

**Java 端任务**：
- [x] 实现会话软删除
- [x] 实现级联软删除该会话下所有消息
- [x] 实现级联软删除该会话关联的 agent_task
- [x] 实现会话 Controller
  - [x] `DELETE /api/v1/chat/{chat_id}` 接口
- [x] 单元测试

**说明**：删除会话时，该会话下的所有消息和关联的 agent_task 同步软删除

---

### 阶段四：对话服务模块

#### 4.1 消息存储

**任务编号**：MSG-001
**优先级**：P0
**前置依赖**：DB-001, CHAT-001

**Java 端任务**：
- [ ] 创建消息实体类 `Message`
- [ ] 创建消息 Mapper 接口
- [ ] 实现消息 Service 层
  - [ ] 保存用户消息
  - [ ] 保存 AI 消息
  - [ ] metadata JSON 字段处理
  - [ ] emotion_status 存储中文值
- [ ] 实现消息历史查询
  - [ ] 分页查询
  - [ ] 时间倒序（最新消息在前）
- [ ] 更新会话的 last_message_time
- [ ] 实现消息 Controller
  - [ ] `GET /api/v1/chat/{chat_id}/messages` 接口
- [ ] 单元测试

**metadata JSON 结构参考 PRD 第6.1.3节**

---

#### 4.2 对话历史组装

**任务编号**：MSG-002
**优先级**：P0
**前置依赖**：MSG-001

**Java 端任务**：
- [x] 实现跨会话记忆窗口（最近20条消息）
  - [ ] 查询同一用户所有会话的最近20条消息
  - [ ] 不分 app_type
  - [ ] 用户+AI 消息总和
- [x] 组装对话上下文
  - [ ] 格式：[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
- [x] 单元测试

---

#### 4.3 同步对话（Java 转发 Python）

**任务编号**：CHAT-SYNC-001
**优先级**：P0
**前置依赖**：MSG-002, PYTHON-001

**Java 端任务**：
- [x] 实现 HTTP 客户端调用 Python 服务
  - [ ] 配置 Python 服务地址和超时时间
  - [ ] 传递 X-User-Id 请求头
  - [ ] 传递对话上下文（含跨会话记忆）
- [ ] 实现对话 Service 层
  - [ ] 接收对话请求
  - [ ] 组装上下文
  - [ ] 调用 Python 服务
  - [ ] 保存用户消息和 AI 消息
  - [ ] 返回结果
- [x] 实现对话 Controller
  - [x] `POST /api/v1/ai/love/chat/sync` 接口
- [ ] 单元测试

**Python 端任务**：
- [x] 实现同步对话接口 `/internal/ai/love/chat/sync`
- [x] 接收请求参数（message, chat_id, emotion_status, history）
- [x] 调用 LLM 模型
- [x] 返回 AI 回复和 metadata

---

#### 4.4 流式对话 SSE（Java 转发 Python）

**任务编号**：CHAT-SSE-001
**优先级**：P0
**前置依赖**：MSG-002, PYTHON-001

**Java 端任务**：
- [x] 实现 SSE 流式响应
  - [x] 配置 SSE 相关依赖
  - [x] 实现流式转发逻辑
- [x] 实现对话 Controller
  - [x] `POST /api/v1/ai/love/chat/sse` 接口（POST 方法）
- [x] 处理 SSE 消息类型
  - [x] thinking: AI 思考过程
  - [x] tool_call: 工具调用请求
  - [x] tool_result: 工具执行结果
  - [x] answer: 完整句子回复
  - [x] metadata: 消息元数据（流结束前发送）
  - [x] [DONE]: 结束标记
- [x] 保存对话历史（流结束后）
- [x] 单元测试

**Python 端任务**：
- [x] 实现流式对话接口 `/internal/ai/love/chat/sse`
- [x] 实现 SSE 流式响应
- [x] 返回完整句子（非单个 token）
- [x] 流结束前返回 metadata 事件

**SSE 格式参考 PRD 第7.3节**

---

### 阶段五：知识库管理模块

#### 5.1 文档上传

**任务编号**：KNOW-001
**优先级**：P0
**前置依赖**：DB-001, USER-002, PYTHON-001

**Java 端任务**：
- [ ] 创建知识库文档实体类 `KnowledgeDocument`
- [ ] 创建文档 Mapper 接口
- [ ] 实现文件内容提取
  - [ ] Markdown 文件解析
  - [ ] PDF 文件解析
  - [ ] TXT 文件解析
- [ ] 实现文档 Service 层
  - [ ] 接收上传文件
  - [ ] 提取文本内容
  - [ ] 自动从文件名提取标题（去掉扩展名）
  - [ ] 存储到数据库（content 字段）
  - [ ] 设置 status=0（待处理）
  - [ ] 调用 Python 向量化接口
- [ ] 实现文档 Controller
  - [ ] `POST /api/v1/knowledge/document` 接口
- [ ] 单元测试

**Python 端任务**：
- [ ] 实现文档向量化接口 `/internal/knowledge/index`
- [ ] 接收文档内容
- [ ] 放入向量化队列
- [ ] 异步执行向量化
- [ ] 存储向量到 PgVector
- [ ] 回调通知 Java 向量化完成

---

#### 5.2 文档列表查询

**任务编号**：KNOW-002
**优先级**：P0
**前置依赖**：KNOW-001

**Java 端任务**：
- [x] 实现文档列表查询
  - [x] 分页查询
  - [x] 仅返回当前用户的文档（user_id 隔离）
- [x] 实现文档 Controller
  - [x] `GET /api/v1/knowledge/documents` 接口
- [x] 单元测试

---

#### 5.3 文档删除

**任务编号**：KNOW-003
**优先级**：P0
**前置依赖**：KNOW-001

**Java 端任务**：
- [x] 实现文档软删除（is_deleted 字段）
- [x] 校验文档所属用户（只能删除自己的文档）
- [x] 实现文档 Controller
  - [x] `DELETE /api/v1/knowledge/document/{id}` 接口
- [x] 单元测试

---

#### 5.4 向量化重试

**任务编号**：KNOW-004
**优先级**：P1
**前置依赖**：KNOW-001

**Java 端任务**：
- [ ] 实现向量化重试逻辑
  - [ ] 检查文档 status 是否为 2（失败）
  - [ ] 重置 status 为 0（待处理）
  - [ ] 重新调用 Python 向量化接口
- [ ] 实现文档 Controller
  - [ ] `POST /api/v1/knowledge/document/{id}/retry` 接口
- [ ] 单元测试

**重试流程参考 PRD 第3.4.1节**

---

#### 5.5 知识检索

**任务编号**：KNOW-005
**优先级**：P0
**前置依赖**：KNOW-001

**Python 端任务**：
- [ ] 实现混合检索策略
  - [ ] 向量相似度检索
  - [ ] 关键词检索
  - [ ] 混合排序
- [ ] 实现查询重写（提高检索准确率）
- [ ] 实现检索接口 `/internal/knowledge/search`
- [ ] 单元测试

---

### 阶段六：智能体模块

#### 6.1 智能体任务管理

**任务编号**：AGENT-001
**优先级**：P0
**前置依赖**：DB-001, USER-002, PYTHON-001

**Java 端任务**：
- [ ] 创建智能体任务实体类 `AgentTask`
- [ ] 创建任务 Mapper 接口
- [ ] 实现任务 Service 层
  - [ ] 创建任务（生成 UUID task_id）
  - [ ] 设置状态为 pending
  - [ ] 每用户同时只能运行 1 个任务
  - [ ] 存储用户消息到 message 表（Manus 类型）
- [ ] 实现任务 Controller
  - [ ] `POST /api/v1/agent/run` 接口
- [ ] 单元测试

**Python 端任务**：
- [ ] 实现智能体任务接口 `/internal/agent/run`
- [ ] 接收任务参数（message, task_id, chat_id, callback_url, callback_token）
- [ ] 异步执行任务
- [ ] 执行完成后回调 Java

---

#### 6.2 任务状态查询

**任务编号**：AGENT-002
**优先级**：P0
**前置依赖**：AGENT-001

**Java 端任务**：
- [ ] 实现任务状态查询
- [ ] 实现任务 Controller
  - [ ] `GET /api/v1/agent/status/{task_id}` 接口
- [ ] 响应格式
  - [ ] pending: steps 字段为空
  - [ ] running: steps 字段为空
  - [ ] completed: 返回完整的 steps 和 result
  - [ ] failed: 返回错误信息
  - [ ] cancelled: 返回取消状态
- [ ] 单元测试

**前端每 3 秒轮询一次**

---

#### 6.3 Python 回调接口

**任务编号**：AGENT-003
**优先级**：P0
**前置依赖**：AGENT-001

**Java 端任务**：
- [ ] 实现内部回调接口
  - [ ] `POST /api/v1/internal/callback/agent/task`
  - [ ] X-Internal-Token 认证
- [ ] 实现回调 Service 层
  - [ ] 更新任务状态（completed/failed）
  - [ ] 一次性回写 steps 和 result
  - [ ] Manus 类型：存储 AI 结果到 message 表
- [ ] 单元测试

**回调格式参考 PRD 第7.6节**

---

#### 6.4 任务取消

**任务编号**：AGENT-004
**优先级**：P0
**前置依赖**：AGENT-001

**Java 端任务**：
- [ ] 实现任务取消逻辑
  - [ ] 调用 Python 取消接口
  - [ ] 清空 agent_task 的 steps 字段
  - [ ] 更新状态为 cancelled
- [ ] 实现任务 Controller
  - [ ] `POST /api/v1/agent/cancel/{task_id}` 接口
- [ ] 支持 pending 和 running 状态取消
- [ ] 单元测试

**Python 端任务**：
- [ ] 实现任务取消接口 `/internal/agent/cancel/{task_id}`
- [ ] 立即中断当前步骤
- [ ] 停止执行

**取消流程参考 PRD 第3.3.1节**

---

#### 6.5 ReAct 智能体实现

**任务编号**：AGENT-005
**优先级**：P0
**前置依赖**：AGENT-001

**Python 端任务**：
- [ ] 实现基础智能体类 `BaseAgent`
- [ ] 实现 ReAct 智能体 `ReactAgent`
  - [ ] Reasoning（推理）阶段
  - [ ] Acting（行动）阶段
  - [ ] 最大执行步骤：20 步
  - [ ] 达到上限强制终止
- [ ] 实现步骤记录
  - [ ] 记录每步的工具、输入、输出、状态、时间
- [ ] 集成工具调用框架
- [ ] 单元测试

---

#### 6.6 Manus 智能体实现

**任务编号**：AGENT-006
**优先级**：P0
**前置依赖**：AGENT-005

**Python 端任务**：
- [ ] 实现 Manus 智能体 `ManusAgent`
  - [ ] 继承 ReAct 智能体
  - [ ] 复杂任务自主规划
  - [ ] 多工具协同
- [ ] 实现消息存储流程
  - [ ] 用户消息和 AI 结果都存储在 message 表
  - [ ] agent_task 仅存储任务信息
- [ ] 实现回调通知
  - [ ] 任务完成时一次性回写 steps 和 result
- [ ] 单元测试

---

#### 6.7 工具调用框架

**任务编号**：TOOL-001
**优先级**：P1
**前置依赖**：PYTHON-001

**Python 端任务**：
- [ ] 实现工具基类 `BaseTool`
- [ ] 实现内置工具
  - [ ] 搜索工具 `SearchTool`（SearchAPI）
  - [ ] 文件工具 `FileTool`（读写文件）
  - [ ] 网页工具 `WebTool`（Jsoup）
  - [ ] PDF 工具 `PdfTool`（iText）
- [ ] 实现工具注册机制
- [ ] 实现工具调用日志
- [ ] 单元测试

---

#### 6.8 MCP 服务集成

**任务编号**：MCP-001
**优先级**：P1
**前置依赖**：PYTHON-001

**Python 端任务**：
- [ ] 实现 MCP 客户端
  - [ ] SSE 连接方式
  - [ ] Stdio 连接方式
- [ ] 实现 MCP 服务配置加载
- [ ] 实现已集成服务
  - [ ] 图片搜索服务（Pexels API）
- [ ] 实现服务热插拔
- [ ] 单元测试

---

### 阶段七：前端开发

#### 7.1 前端项目搭建

**任务编号**：FE-001
**优先级**：P0
**前置依赖**：无

**项目结构**：
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
│   │   ├── EmotionSelector.vue
│   │   ├── TaskStatus.vue
│   │   └── AppFooter.vue
│   ├── router/                    # 路由
│   ├── stores/                    # 状态管理
│   ├── utils/                     # 工具函数
│   ├── styles/                    # 响应式样式
│   └── App.vue
├── public/
├── package.json
└── vite.config.js
```

**核心任务**：
- [ ] 使用 Vite 创建 Vue 3 项目
- [ ] 安装 Element Plus
- [ ] 安装 Axios、Vue Router、Pinia
- [ ] 配置 API 请求封装（Axios）
- [ ] 配置路由
- [ ] 配置状态管理
- [ ] 配置响应式样式

---

#### 7.2 登录注册页面

**任务编号**：FE-002
**优先级**：P0
**前置依赖**：FE-001, USER-002

**核心任务**：
- [ ] 实现登录页面
  - [ ] 用户名输入框
  - [ ] 密码输入框
  - [ ] 登录按钮
  - [ ] 错误提示
- [ ] 实现注册页面
  - [ ] 用户名输入框
  - [ ] 密码输入框
  - [ ] 确认密码输入框
  - [ ] 注册按钮
- [ ] 实现 Token 存储（localStorage）
- [ ] 实现登录状态持久化
- [ ] 实现 401 跳转登录页

---

#### 7.3 主布局与导航

**任务编号**：FE-003
**优先级**：P0
**前置依赖**：FE-001

**核心任务**：
- [ ] 实现主布局组件
  - [ ] 侧边栏导航
  - [ ] 顶部栏
  - [ ] 内容区域
- [ ] 实现响应式布局
  - [ ] 桌面端（>= 1024px）：完整布局
  - [ ] 平板端（768px - 1023px）：适配布局
  - [ ] 移动端（< 768px）：单列布局
- [ ] 实现导航菜单
  - [ ] 首页
  - [ ] 恋爱大师
  - [ ] 超级智能体
  - [ ] 知识库

---

#### 7.4 会话管理界面

**任务编号**：FE-004
**优先级**：P0
**前置依赖**：FE-003, CHAT-002

**核心任务**：
- [ ] 实现会话列表组件
  - [ ] 显示会话标题
  - [ ] 显示最后消息时间
  - [ ] 显示应用类型标签
  - [ ] 分页加载
- [ ] 实现创建会话
  - [ ] 选择应用类型（love_app/manus）
  - [ ] 选择情感状态（仅 love_app）
  - [ ] 输入会话标题（可选）
- [ ] 实现会话删除
  - [ ] 确认对话框
- [ ] 实现会话切换

---

#### 7.5 情感状态选择器

**任务编号**：FE-005
**优先级**：P0
**前置依赖**：FE-004

**核心任务**：
- [ ] 实现情感状态选择器组件 `EmotionSelector`
  - [ ] 单身选项
  - [ ] 恋爱选项
  - [ ] 已婚选项
- [ ] 会话创建时显示
- [ ] 会话内不可更改
- [ ] 中文显示

---

#### 7.6 对话界面

**任务编号**：FE-006
**优先级**：P0
**前置依赖**：FE-004, CHAT-SSE-001

**核心任务**：
- [ ] 实现对话组件 `ChatRoom`
  - [ ] 消息列表
  - [ ] 输入框
  - [ ] 发送按钮
- [ ] 实现消息气泡组件 `MessageBubble`
  - [ ] 用户消息样式
  - [ ] AI 消息样式
  - [ ] 显示时间
  - [ ] 显示 metadata（token 用量、RAG 来源等）
- [ ] 实现 SSE 流式接收
  - [ ] 接收 thinking 事件
  - [ ] 接收 answer 事件（完整句子）
  - [ ] 接收 metadata 事件
  - [ ] 接收 [DONE] 结束标记
- [ ] 实现消息历史加载
  - [ ] 分页加载
  - [ ] 滚动到底部

---

#### 7.7 智能体任务界面

**任务编号**：FE-007
**优先级**：P0
**前置依赖**：FE-004, AGENT-002

**核心任务**：
- [ ] 实现任务提交界面
  - [ ] 输入任务描述
  - [ ] 提交按钮
- [ ] 实现任务状态组件 `TaskStatus`
  - [ ] 显示任务状态（pending/running/completed/failed/cancelled）
  - [ ] 显示执行步骤（completed 时）
  - [ ] 显示最终结果
- [ ] 实现状态轮询
  - [ ] 每 3 秒轮询一次
  - [ ] 任务完成停止轮询
- [ ] 实现任务取消按钮
  - [ ] pending 和 running 状态可取消

---

#### 7.8 知识库管理界面

**任务编号**：FE-008
**优先级**：P1
**前置依赖**：FE-003, KNOW-002

**核心任务**：
- [ ] 实现文档列表
  - [ ] 显示文档标题
  - [ ] 显示文件类型
  - [ ] 显示状态（待处理/已向量化/处理失败）
  - [ ] 分页加载
- [ ] 实现文档上传
  - [ ] 支持 .md / .pdf / .txt 格式
  - [ ] 上传进度显示
  - [ ] 上传成功刷新列表
- [ ] 实现文档删除
  - [ ] 确认对话框
- [ ] 实现向量化重试
  - [ ] 仅对 status=2 失败的文档显示重试按钮

---

### 阶段八：测试与优化

#### 8.1 单元测试

**任务编号**：TEST-001
**优先级**：P0
**前置依赖**：所有功能模块

**核心任务**：
- [ ] Java 端单元测试
  - [ ] 用户服务测试
  - [ ] 会话服务测试
  - [ ] 对话服务测试
  - [ ] 知识库服务测试
  - [ ] 智能体服务测试
- [ ] Python 端单元测试
  - [ ] LLM 调用测试
  - [ ] RAG 检索测试
  - [ ] 智能体推理测试
  - [ ] 工具调用测试

---

#### 8.2 集成测试

**任务编号**：TEST-002
**优先级**：P0
**前置依赖**：TEST-001

**核心任务**：
- [ ] 端到端测试
  - [ ] 用户注册登录流程
  - [ ] 创建会话 → 对话 → 查看历史
  - [ ] 上传文档 → 向量化 → 知识检索
  - [ ] 提交智能体任务 → 轮询状态 → 查看结果
- [ ] 接口联调测试
  - [ ] Java ↔ Python 接口联调
  - [ ] 前端 ↔ Java 接口联调

---

#### 8.3 性能优化

**任务编号**：PERF-001
**优先级**：P1
**前置依赖**：TEST-002

**核心任务**：
- [ ] 数据库优化
  - [ ] 索引优化
  - [ ] 查询优化
- [ ] 缓存优化
  - [ ] Redis 缓存热点数据
- [ ] 接口响应优化
  - [ ] 目标：< 200ms（不含 AI 调用）
- [ ] 并发测试
  - [ ] 目标：>= 1000 并发

---

#### 8.4 文档完善

**任务编号**：DOC-001
**优先级**：P2
**前置依赖**：TEST-002

**核心任务**：
- [ ] API 接口文档（Knife4j）
- [ ] 部署文档
- [ ] 开发文档
- [ ] 用户手册

---

## 四、任务执行顺序

### 后端任务顺序

```
第一阶段：基础架构
DB-001 → JAVA-001 → PYTHON-001 → DOCKER-001

第二阶段：用户管理
USER-001 → USER-002

第三阶段：会话管理
CHAT-001 → CHAT-002 → CHAT-003

第四阶段：对话服务
MSG-001 → MSG-002 → CHAT-SYNC-001 → CHAT-SSE-001

第五阶段：知识库
KNOW-001 → KNOW-002 → KNOW-003 → KNOW-004 → KNOW-005

第六阶段：智能体
AGENT-001 → AGENT-002 → AGENT-003 → AGENT-004
TOOL-001 → MCP-001
AGENT-005 → AGENT-006
```

### 前端任务顺序

```
FE-001 → FE-002 → FE-003 → FE-004 → FE-005
                                         ↓
FE-006 ← CHAT-SSE-001                   ↓
                                         ↓
FE-007 ← AGENT-002                      ↓
                                         ↓
FE-008 ← KNOW-002                       ↓
```

---

## 五、里程碑

| 里程碑 | 时间 | 交付物 |
|--------|------|--------|
| M1: 基础架构完成 | 第2周末 | 可运行的 Java + Python 服务框架 |
| M2: 用户管理完成 | 第3周末 | 用户注册登录功能 |
| M3: 对话功能完成 | 第5周末 | 恋爱大师对话功能 |
| M4: 知识库完成 | 第6周末 | RAG 知识库问答 |
| M5: 智能体完成 | 第8周末 | Manus 智能体功能 |
| M6: 前端完成 | 第10周末 | 完整的前端界面 |
| M7: 项目上线 | 第11周末 | 测试通过，部署上线 |

---

## 六、风险与依赖

### 外部依赖
- DashScope API（阿里云 LLM + Embedding）
- SearchAPI（搜索工具）
- Pexels API（图片搜索 MCP）

### 技术风险
- LLM 响应时间不稳定
- 向量化性能瓶颈
- SSE 长连接稳定性

### 缓解措施
- 设置合理的超时时间
- 异步处理向量化任务
- 实现重试机制

---

**文档维护人**：开发团队
**最后更新**：2026-06-18
