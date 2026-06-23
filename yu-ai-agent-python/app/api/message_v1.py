"""
消息管理外部 API
迁移自 Java MessageController.java / MessageServiceImpl.java
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services import message_service

router = APIRouter(prefix="/api/v1/chat/{chat_id}/messages", tags=["消息管理"])


@router.get("")
async def get_message_history(
    chat_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取消息历史（分页，时间倒序）"""
    result = await message_service.get_message_history(
        db, user_id, chat_id, page, page_size,
    )
    return {"code": 200, "message": "success", "data": result}
