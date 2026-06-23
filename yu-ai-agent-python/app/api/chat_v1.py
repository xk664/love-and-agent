"""
会话管理外部 API
迁移自 Java ChatController.java / ChatServiceImpl.java
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.chat import ChatCreateRequest
from app.services import chat_service

router = APIRouter(prefix="/api/v1/chat", tags=["会话管理"])


@router.post("/create")
async def create_chat(
    request: ChatCreateRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建会话"""
    result = await chat_service.create_chat(
        db, user_id,
        app_type=request.app_type,
        emotion_status=request.emotion_status,
        title=request.title,
    )
    return {"code": 200, "message": "success", "data": result}


@router.get("/list")
async def list_chats(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    app_type: str | None = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """会话列表（分页）"""
    result = await chat_service.list_chats(db, user_id, page, page_size, app_type)
    return {"code": 200, "message": "success", "data": result}


@router.get("/{chat_id}")
async def get_chat_detail(
    chat_id: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """会话详情"""
    result = await chat_service.get_chat_detail(db, user_id, chat_id)
    return {"code": 200, "message": "success", "data": result}


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除会话（级联软删除 messages + agent_tasks）"""
    await chat_service.delete_chat(db, user_id, chat_id)
    return {"code": 200, "message": "success", "data": None}
