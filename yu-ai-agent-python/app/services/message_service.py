"""
消息服务
迁移自 Java MessageServiceImpl.java
"""
from datetime import datetime

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.core.logging import get_logger
from app.models.db.chat import Chat
from app.models.db.message import Message

logger = get_logger(__name__)


async def save_message(
    db: AsyncSession,
    chat_id: str,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> dict:
    """
    保存消息（内部方法，save_user_message / save_assistant_message 调用）
    """
    # 1. 校验会话存在
    chat_result = await db.execute(
        select(Chat).where(Chat.chat_id == chat_id, Chat.is_deleted == False)
    )
    chat = chat_result.scalar_one_or_none()
    if not chat:
        raise BusinessException("会话不存在")

    # 2. 创建消息
    message = Message(
        chat_id=chat_id,
        role=role,
        content=content,
        metadata_=metadata,
    )
    db.add(message)
    await db.flush()
    await db.refresh(message)

    # 3. 更新会话最后消息时间
    chat.last_message_time = datetime.now()
    await db.flush()

    logger.info("保存消息成功: chat_id=%s, role=%s, message_id=%d", chat_id, role, message.id)

    return _to_response(message)


async def save_user_message(
    db: AsyncSession,
    chat_id: str,
    content: str,
    metadata: dict | None = None,
) -> dict:
    """保存用户消息"""
    return await save_message(db, chat_id, "user", content, metadata)


async def save_assistant_message(
    db: AsyncSession,
    chat_id: str,
    content: str,
    metadata: dict | None = None,
) -> dict:
    """保存 AI 消息"""
    return await save_message(db, chat_id, "assistant", content, metadata)


async def get_message_history(
    db: AsyncSession,
    user_id: int,
    chat_id: str,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    获取消息历史（分页，时间倒序）
    返回格式：{ list: [...], page, page_size, total }
    """
    # 1. 校验会话归属
    chat_result = await db.execute(
        select(Chat).where(
            Chat.chat_id == chat_id,
            Chat.user_id == user_id,
            Chat.is_deleted == False,
        )
    )
    chat = chat_result.scalar_one_or_none()
    if not chat:
        raise BusinessException("会话不存在")

    # 2. 统计总数
    count_query = (
        select(func.count())
        .select_from(Message)
        .where(Message.chat_id == chat_id, Message.is_deleted == False)
    )
    total = (await db.execute(count_query)).scalar() or 0

    # 3. 分页查询，时间倒序
    offset = (page - 1) * page_size
    query = (
        select(Message)
        .where(Message.chat_id == chat_id, Message.is_deleted == False)
        .order_by(Message.create_time.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    messages = result.scalars().all()

    return {
        "list": [_to_response(m) for m in messages],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


async def get_recent_messages_across_chats(
    db: AsyncSession,
    user_id: int,
    limit: int = 20,
) -> list[dict]:
    """
    获取跨会话记忆窗口（最近 N 条消息）
    查询同一用户所有会话最近 limit 条消息，按时间正序返回
    """
    # 1. 查询用户所有会话 ID
    chat_ids_result = await db.execute(
        select(Chat.chat_id).where(Chat.user_id == user_id, Chat.is_deleted == False)
    )
    chat_ids = [row[0] for row in chat_ids_result.all()]
    if not chat_ids:
        return []

    # 2. 查询这些会话的最近消息（按时间倒序，取 limit 条）
    query = (
        select(Message)
        .where(
            Message.chat_id.in_(chat_ids),
            Message.role.in_(["user", "assistant"]),
            Message.is_deleted == False,
        )
        .order_by(Message.create_time.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    messages = result.scalars().all()

    # 3. 按时间正序返回
    messages_list = list(reversed(messages))
    return [{"role": m.role, "content": m.content} for m in messages_list]


def _to_response(message: Message) -> dict:
    """消息实体 → 响应 dict"""
    return {
        "id": message.id,
        "chat_id": message.chat_id,
        "role": message.role,
        "content": message.content,
        "metadata": message.metadata_,
        "create_time": message.create_time.strftime("%Y-%m-%d %H:%M:%S"),
    }
