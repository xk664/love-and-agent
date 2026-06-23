"""
智能体任务外部 API
迁移自 Java AgentTaskController.java / AgentTaskServiceImpl.java

核心变化：
- Java: 创建 task → 异步 HTTP 调 Python → Python 回调 Java
- Python: 创建 task → 直接异步执行 Agent → 直接更新 task（无回调）
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services import agent_task_service

router = APIRouter(prefix="/api/v1/agent", tags=["智能体任务"])


# ===== 请求模型 =====

class AgentRunRequest(BaseModel):
    """提交任务请求"""
    message: str = Field(..., description="任务描述", min_length=1)
    chat_id: str | None = Field(None, description="关联会话ID，不传则自动创建 manus 会话")


# ===== 路由 =====

@router.post("/run")
async def run_task(
    request: AgentRunRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    运行智能体任务

    每用户同时只能运行 1 个任务（pending/running 状态检查）
    若无 chatId，自动创建 manus 类型会话
    """
    result = await agent_task_service.run_task(
        db, user_id,
        message=request.message,
        chat_id=request.chat_id,
    )
    return {"code": 200, "message": "success", "data": result}


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """查询任务状态（前端每 3 秒轮询一次）"""
    result = await agent_task_service.get_task_status(db, user_id, task_id)
    return {"code": 200, "message": "success", "data": result}


@router.post("/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    取消任务

    支持 pending 和 running 状态的任务
    running 状态取消时同时取消 asyncio.Task
    """
    result = await agent_task_service.cancel_task(db, user_id, task_id)
    return {"code": 200, "message": "success", "data": result}
