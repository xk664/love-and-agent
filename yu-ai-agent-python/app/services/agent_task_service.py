"""
智能体任务服务
迁移自 Java AgentTaskServiceImpl.java

核心变化：
- Java: 创建 task → HTTP 调 Python → Python 回调 Java
- Python: 创建 task → 直接执行 Agent → 直接更新 task
- 回调机制完全消除，改为内部函数调用
"""
import asyncio
import json
from datetime import datetime

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.core.logging import get_logger
from app.core.redis import redis_client
from app.models.db.agent_task import AgentTask
from app.models.db.chat import Chat
from app.models.db.message import Message
from app.ai.memory import MemoryManager
from app.ai.memory.vector_store_adapter import get_memory_vector_store

logger = get_logger(__name__)

# 运行中的任务字典：task_id -> asyncio.Task（用于取消）
_running_tasks: dict[str, asyncio.Task] = {}


async def run_task(
    db: AsyncSession,
    user_id: int,
    message: str,
    chat_id: str | None = None,
) -> dict:
    """
    提交智能体任务

    流程：
    1. 检查用户是否有运行中的任务
    2. 若无 chatId，自动创建 manus 类型会话
    3. 创建 AgentTask 记录
    4. 保存用户消息
    5. 异步启动 Agent 执行
    """
    # 1. 检查是否有运行中的任务
    await _check_running_task(db, user_id)

    # 2. 处理会话
    if not chat_id:
        chat_id = await _create_manus_chat(db, user_id)
    else:
        await _validate_chat_ownership(db, user_id, chat_id)

    # 3. 创建任务
    import uuid
    task_id = str(uuid.uuid4())

    task = AgentTask(
        task_id=task_id,
        user_id=user_id,
        chat_id=chat_id,
        message=message,
        status="pending",
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)

    logger.info("创建智能体任务: task_id=%s, user_id=%d, chat_id=%s", task_id, user_id, chat_id)

    # 4. 保存用户消息
    user_msg = Message(chat_id=chat_id, role="user", content=message)
    db.add(user_msg)
    await db.flush()

    # 5. 更新会话最后消息时间
    chat_result = await db.execute(select(Chat).where(Chat.chat_id == chat_id))
    chat = chat_result.scalar_one_or_none()
    if chat:
        chat.last_message_time = datetime.now()
        await db.flush()

    # 6. 异步启动 Agent 执行
    asyncio_task = asyncio.create_task(_agent_task_run(task_id, user_id, chat_id, message))
    _running_tasks[task_id] = asyncio_task
    asyncio_task.add_done_callback(lambda t: _running_tasks.pop(task_id, None))

    return _to_response(task)


async def get_task_status(db: AsyncSession, user_id: int, task_id: str) -> dict:
    """查询任务状态"""
    result = await db.execute(
        select(AgentTask).where(
            AgentTask.task_id == task_id,
            AgentTask.user_id == user_id,
            AgentTask.is_deleted == False,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise BusinessException(404, "任务不存在")

    return _to_status_response(task)


async def cancel_task(db: AsyncSession, user_id: int, task_id: str) -> dict:
    """
    取消任务

    流程：
    1. 校验任务存在且属于当前用户
    2. 校验状态为 pending 或 running
    3. 取消 asyncio.Task
    4. 更新数据库状态
    """
    result = await db.execute(
        select(AgentTask).where(
            AgentTask.task_id == task_id,
            AgentTask.user_id == user_id,
            AgentTask.is_deleted == False,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise BusinessException(404, "任务不存在")

    if task.status not in ("pending", "running"):
        raise BusinessException(400, f"当前状态不允许取消: {task.status}")

    # 取消 asyncio.Task
    if task.status == "running":
        asyncio_task = _running_tasks.get(task_id)
        if asyncio_task and not asyncio_task.done():
            asyncio_task.cancel()
            logger.info("已取消 asyncio.Task: task_id=%s", task_id)

    # 更新数据库
    task.status = "cancelled"
    task.steps = None
    task.result = "用户取消任务"
    task.update_time = datetime.now()
    await db.flush()

    logger.info("任务已取消: task_id=%s, user_id=%d", task_id, user_id)

    return _to_response(task)


async def _check_running_task(db: AsyncSession, user_id: int):
    """检查用户是否有运行中的任务"""
    count_result = await db.execute(
        select(func.count())
        .select_from(AgentTask)
        .where(
            AgentTask.user_id == user_id,
            AgentTask.status.in_(["pending", "running"]),
            AgentTask.is_deleted == False,
        )
    )
    count = count_result.scalar() or 0
    if count > 0:
        raise BusinessException(409, "您有任务正在运行中，请等待完成后再提交新任务")


async def _create_manus_chat(db: AsyncSession, user_id: int) -> str:
    """自动创建 manus 类型会话"""
    import uuid
    chat_id = str(uuid.uuid4())

    chat = Chat(
        chat_id=chat_id,
        user_id=user_id,
        app_type="manus",
        title="智能体任务",
    )
    db.add(chat)
    await db.flush()

    logger.info("自动创建 manus 会话: chat_id=%s, user_id=%d", chat_id, user_id)
    return chat_id


async def _validate_chat_ownership(db: AsyncSession, user_id: int, chat_id: str):
    """校验会话归属"""
    result = await db.execute(
        select(Chat).where(
            Chat.chat_id == chat_id,
            Chat.user_id == user_id,
            Chat.is_deleted == False,
        )
    )
    if not result.scalar_one_or_none():
        raise BusinessException(404, "会话不存在")


# ===== 内部执行函数 =====

async def _agent_task_run(task_id: str, user_id: int, chat_id: str, message: str):
    """
    后台执行智能体任务（取代 Java → Python HTTP 调用 + Python 回调 Java）

    流程：
    1. 更新任务状态为 running
    2. 创建 ManusAgent / ReactAgent
    3. 执行 Agent
    4. 直接更新任务状态 + 保存 AI 结果到 message 表
    5. 更新用户画像（三层记忆架构）
    """
    from app.ai.agent.manus import ManusAgent
    from app.ai.agent.react import ReactAgent
    from app.ai.tools import tool_registry
    from app.ai.llm.dashscope_client import dashscope_client
    from app.core.database import async_session

    try:
        logger.info("Agent 任务开始执行: task_id=%s, chat_id=%s", task_id, chat_id)

        # 1. 更新状态为 running
        async with async_session() as db:
            await _update_task_status(db, task_id, "running")
            await db.commit()

        # 2. 创建 Agent
        agent = ManusAgent(
            max_steps=30,
            tools=tool_registry.list_tools(),
        )

        # 3. 注册步骤回调
        async def on_step(step):
            logger.debug("Agent step: task_id=%s, step=%d, action=%s",
                         task_id, step.step_number, step.action)

        agent.on_step(on_step)

        # 4. 执行 Agent
        state = await agent.run(
            task_id=task_id,
            chat_id=chat_id,
            message=message,
            user_id=user_id,
        )

        # 5. 直接更新任务状态（取代 HTTP 回调）
        async with async_session() as db:
            await _complete_task(db, task_id, state.final_answer, state.to_callback_steps())
            await db.commit()

        # 6. 更新用户画像（三层记忆架构）
        try:
            async with async_session() as db:
                redis = await redis_client.get_client()
                memory_manager = MemoryManager(
                    user_id=user_id,
                    chat_id=chat_id,
                    redis_client=redis,
                    llm_client=dashscope_client,
                    vector_store=get_memory_vector_store(user_id)
                )

                # 构建对话消息
                conversation_messages = [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": state.final_answer or ""}
                ]

                # 智能体任务通常比较重要，标记为重要对话
                is_important = True
                await memory_manager.after_conversation(db, conversation_messages, is_important)
                await db.commit()

                logger.info("智能体任务画像更新完成: task_id=%s", task_id)
        except Exception as memory_error:
            logger.warning(f"智能体任务画像更新失败（不影响任务完成）: {memory_error}")

        logger.info("Agent 任务完成: task_id=%s, steps=%d", task_id, state.current_step)

    except asyncio.CancelledError:
        logger.info("Agent 任务被取消: task_id=%s", task_id)
        # 取消时 status 已由 cancel_task 更新，无需额外操作

    except Exception as e:
        logger.error("Agent 任务失败: task_id=%s, error=%s", task_id, str(e))
        # 直接更新失败状态（取代 HTTP 回调）
        try:
            async with async_session() as db:
                await _fail_task(db, task_id, str(e))
                await db.commit()
        except Exception as inner_e:
            logger.error("更新失败状态也出错: task_id=%s, error=%s", task_id, str(inner_e))


async def _update_task_status(db: AsyncSession, task_id: str, status: str):
    """更新任务状态"""
    result = await db.execute(
        select(AgentTask).where(AgentTask.task_id == task_id, AgentTask.is_deleted == False)
    )
    task = result.scalar_one_or_none()
    if task:
        task.status = status
        task.update_time = datetime.now()
        await db.flush()


async def _complete_task(db: AsyncSession, task_id: str, result_text: str | None, steps: list | None):
    """
    任务完成处理（取代 Java handleCallback）

    更新任务状态 + 保存 AI 结果到 message 表
    """
    task_result = await db.execute(
        select(AgentTask).where(AgentTask.task_id == task_id, AgentTask.is_deleted == False)
    )
    task = task_result.scalar_one_or_none()
    if not task:
        logger.warn("完成任务时找不到记录: task_id=%s", task_id)
        return

    task.status = "completed"
    task.result = result_text
    task.steps = steps
    task.update_time = datetime.now()
    await db.flush()

    # 保存 AI 结果到 message 表
    if result_text:
        msg = Message(chat_id=task.chat_id, role="assistant", content=result_text)
        db.add(msg)
        await db.flush()

        # 更新会话最后消息时间
        chat_result = await db.execute(select(Chat).where(Chat.chat_id == task.chat_id))
        chat = chat_result.scalar_one_or_none()
        if chat:
            chat.last_message_time = datetime.now()
            await db.flush()

        logger.info("AI 结果已存入 message 表: chat_id=%s", task.chat_id)


async def _fail_task(db: AsyncSession, task_id: str, error_msg: str):
    """任务失败处理（取代 Java updateTaskStatus + handleCallback）"""
    task_result = await db.execute(
        select(AgentTask).where(AgentTask.task_id == task_id, AgentTask.is_deleted == False)
    )
    task = task_result.scalar_one_or_none()
    if not task:
        return

    task.status = "failed"
    task.result = error_msg
    task.update_time = datetime.now()
    await db.flush()


# ===== 响应格式化 =====

def _to_response(task: AgentTask) -> dict:
    """任务实体 → 响应 dict（提交/取消返回）"""
    return {
        "task_id": task.task_id,
        "chat_id": task.chat_id,
        "message": task.message,
        "status": task.status,
        "create_time": task.create_time.strftime("%Y-%m-%d %H:%M:%S") if task.create_time else None,
    }


def _to_status_response(task: AgentTask) -> dict:
    """任务实体 → 状态响应 dict（查询状态返回，含 result 和 steps）"""
    steps = task.steps
    # AgentTask.steps 在 DB 中是 JSON，可能已经是 list
    # 如果是 str（JSON 字符串），需要解析
    if isinstance(steps, str):
        try:
            steps = json.loads(steps)
        except (json.JSONDecodeError, TypeError):
            steps = None

    return {
        "task_id": task.task_id,
        "chat_id": task.chat_id,
        "message": task.message,
        "status": task.status,
        "result": task.result,
        "steps": steps,
        "create_time": task.create_time.strftime("%Y-%m-%d %H:%M:%S") if task.create_time else None,
        "update_time": task.update_time.strftime("%Y-%m-%d %H:%M:%S") if task.update_time else None,
    }
