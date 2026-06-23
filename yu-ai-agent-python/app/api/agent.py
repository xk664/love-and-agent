"""
Agent API - 智能体任务接口

提供智能体任务的提交、取消和回调功能
"""
import asyncio
from typing import Dict

import httpx
from fastapi import APIRouter
from fastapi.params import Header

from app.ai.agent.manus import ManusAgent
from app.ai.agent.react import ReactAgent
from app.ai.tools import tool_registry
from app.core.config import settings
from app.core.logging import get_logger
from app.models.agent import (
    AgentRunRequest, AgentRunResponse, AgentCallbackRequest,
    AgentCancelRequest, AgentCancelResponse
)

router = APIRouter(prefix="/internal/agent", tags=["agent"])
logger = get_logger(__name__)

# 运行中的任务字典：task_id -> asyncio.Task
_running_tasks: Dict[str, asyncio.Task] = {}


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
        request: AgentRunRequest,
        x_user_id: int = Header(..., alias="X-User-Id")
):
    """
    智能体任务运行接口

    接收 Java 端提交的任务，异步执行后回调通知结果
    """
    logger.info(f"Agent task submitted: task_id={request.task_id}, chat_id={request.chat_id}")

    # 创建异步任务并保存到字典
    task = asyncio.create_task(_agent_task_run(request, x_user_id))
    _running_tasks[request.task_id] = task

    # 任务完成时自动清理
    task.add_done_callback(lambda t: _running_tasks.pop(request.task_id, None))

    return AgentRunResponse(
        code=200,
        message="任务已提交",
        data={"task_id": request.task_id}
    )


@router.post("/cancel", response_model=AgentCancelResponse)
async def cancel_agent(request: AgentCancelRequest):
    """
    取消智能体任务

    立即中断当前执行中的任务
    """
    task_id = request.task_id
    logger.info(f"Agent cancel request: task_id={task_id}")

    # 查找运行中的任务
    task = _running_tasks.get(task_id)
    if task is None:
        logger.warning(f"Agent cancel failed: task_id={task_id}, task not found or already completed")
        return AgentCancelResponse(
            code=404,
            message="任务不存在或已结束",
        )

    # 取消任务
    if not task.done():
        task.cancel()
        logger.info(f"Agent task cancelled: task_id={task_id}")

    return AgentCancelResponse(
        code=200,
        message="任务已取消",
    )


async def _agent_task_run(request: AgentRunRequest, user_id: int):
    """
    后台执行智能体任务

    流程：初始化 Manus Agent → 规划 → 执行 → 回调 Java
    """
    try:
        logger.info(
            f"Agent task started: task_id={request.task_id}, "
            f"chat_id={request.chat_id}, message={request.message}"
        )

        # 1. 根据 agent_type 创建对应的 Agent
        agent_type = getattr(request, 'agent_type', 'manus')
        if agent_type == 'react':
            agent = ReactAgent(
                max_steps=20,
                tools=tool_registry.list_tools(),
            )
        else:
            agent = ManusAgent(
                max_steps=30,
                tools=tool_registry.list_tools(),
            )

        # 2. 注册步骤回调
        async def on_step(step):
            logger.debug(
                f"Agent step: task_id={request.task_id}, "
                f"step={step.step_number}, action={step.action}"
            )

        logger.info(f"Using agent type: {agent_type}")

        agent.on_step(on_step)

        # 3. 执行智能体
        state = await agent.run(
            task_id=request.task_id,
            chat_id=request.chat_id,
            message=request.message,
            user_id=user_id,
        )

        # 4. 回调 Java 通知成功
        await _callback_java(
            task_id=request.task_id,
            status="completed",
            result=state.final_answer,
            steps=state.to_callback_steps(),
        )

        logger.info(
            f"Agent task completed: task_id={request.task_id}, "
            f"steps={state.current_step}, reason={state.finish_reason}"
        )

    except asyncio.CancelledError:
        # 任务被取消
        logger.info(f"Agent task cancelled during execution: task_id={request.task_id}")
        # 注意：Java 端取消时已更新状态，无需回调

    except Exception as e:
        logger.error(f"Agent task failed: task_id={request.task_id}, error={str(e)}")
        # 回调 Java 通知失败
        await _callback_java(
            task_id=request.task_id,
            status="failed",
            result=str(e),
        )


async def _callback_java(task_id: str, status: str, result: str = None, steps: list = None):
    """
    回调 Java 端通知任务执行结果

    Args:
        task_id: 任务ID
        status: 状态（completed | failed）
        result: 任务结果
        steps: 执行步骤
    """
    callback_url = f"{settings.callback.CALLBACK_BASE_URL}/api/v1/internal/callback/agent/task"
    callback_token = settings.callback.CALLBACK_TOKEN

    payload = AgentCallbackRequest(
        task_id=task_id,
        status=status,
        result=result,
        steps=steps,
    ).model_dump()

    headers = {"Content-Type": "application/json"}
    if callback_token:
        headers["X-Internal-Token"] = callback_token

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(callback_url, json=payload, headers=headers)
            if response.status_code == 200:
                logger.info(f"Callback succeeded: task_id={task_id}, status={status}")
            else:
                logger.warning(
                    f"Callback failed: task_id={task_id}, "
                    f"status_code={response.status_code}, body={response.text}"
                )
    except Exception as e:
        logger.error(f"Callback error: task_id={task_id}, error={str(e)}")
