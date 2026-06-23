"""
Agent API - 智能体任务内部接口

迁移后保留，供 Java 端兼容调用。
外部 API 已迁移到 agent_v1.py（使用 JWT 认证）。
"""
from fastapi import APIRouter, Header

from app.core.logging import get_logger
from app.services.agent_task_service import _running_tasks, _agent_task_run
from app.models.agent import (
    AgentRunRequest, AgentRunResponse,
    AgentCancelRequest, AgentCancelResponse,
)
import asyncio

router = APIRouter(prefix="/internal/agent", tags=["agent"])
logger = get_logger(__name__)


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    request: AgentRunRequest,
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    """
    智能体任务运行接口（内部，供 Java 兼容）

    接收 Java 端提交的任务，异步执行后直接更新 DB（不再回调 Java）
    """
    logger.info("Agent task submitted: task_id=%s, chat_id=%s", request.task_id, request.chat_id)

    task = asyncio.create_task(_agent_task_run(request.task_id, x_user_id, request.chat_id, request.message))
    _running_tasks[request.task_id] = task
    task.add_done_callback(lambda t: _running_tasks.pop(request.task_id, None))

    return AgentRunResponse(code=200, message="任务已提交", data={"task_id": request.task_id})


@router.post("/cancel", response_model=AgentCancelResponse)
async def cancel_agent(request: AgentCancelRequest):
    """
    取消智能体任务（内部，供 Java 兼容）

    直接取消 asyncio.Task，不再调用外部接口
    """
    task_id = request.task_id
    logger.info("Agent cancel request: task_id=%s", task_id)

    task = _running_tasks.get(task_id)
    if task is None:
        return AgentCancelResponse(code=404, message="任务不存在或已结束")

    if not task.done():
        task.cancel()
        logger.info("Agent task cancelled: task_id=%s", task_id)

    return AgentCancelResponse(code=200, message="任务已取消")
