"""
Chat Service - 会话业务逻辑
"""
import uuid
from datetime import datetime

from sqlalchemy import select, func, update, case, literal
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.core.logging import get_logger
from app.models.db.chat import Chat
from app.models.db.message import Message
from app.models.db.agent_task import AgentTask

logger = get_logger(__name__)

# 情感状态映射：英文 → 中文
EMOTION_STATUS_MAP = {
    "single": "单身",
    "relationship": "恋爱",
    "married": "已婚",
}


def _to_response(chat: Chat) -> dict:
    """Convert Chat ORM to response dict"""
    return {
        "chat_id": chat.chat_id,
        "app_type": chat.app_type,
        "emotion_status": EMOTION_STATUS_MAP.get(chat.emotion_status, chat.emotion_status),
        "friend_id": chat.friend_id,
        "title": chat.title,
        "last_message_time": chat.last_message_time.isoformat() if chat.last_message_time else None,
        "create_time": chat.create_time.isoformat() if chat.create_time else None,
    }


async def create_chat(db: AsyncSession, user_id: int, app_type: str, emotion_status: str = None, title: str = None, friend_id: int = None) -> dict:
    """
    创建会话

    - love_app 类型必须选择 emotion_status
    - manus 类型忽略 emotion_status
    - 生成 UUID chat_id
    - friend_id 可选，关联数字朋友
    """
    # 1. 校验情感状态
    if app_type == "love_app":
        if not emotion_status:
            raise BusinessException(code=400, message="恋爱大师应用必须选择情感状态")
    elif app_type == "manus":
        emotion_status = None

    # 2. 校验 friend_id 是否存在且属于当前用户
    if friend_id:
        from sqlalchemy import select as sel
        from app.models.db.digital_friend import DigitalFriend
        friend_result = await db.execute(
            sel(DigitalFriend).where(
                DigitalFriend.id == friend_id,
                DigitalFriend.user_id == user_id,
                DigitalFriend.is_deleted == False,
            )
        )
        friend = friend_result.scalar_one_or_none()
        if not friend:
            raise BusinessException(code=400, message="数字朋友不存在")
        if not friend.system_prompt or friend.status != "ready":
            raise BusinessException(code=400, message="该数字朋友尚未完成人格蒸馏")

    # 3. 创建会话
    chat = Chat(
        chat_id=str(uuid.uuid4()),
        user_id=user_id,
        app_type=app_type,
        emotion_status=emotion_status,
        friend_id=friend_id,
        title=title or ("智能体任务" if app_type == "manus" else "新对话"),
    )
    db.add(chat)
    await db.flush()
    await db.refresh(chat)

    logger.info(f"创建会话成功: chat_id={chat.chat_id}, user_id={user_id}, app_type={app_type}, friend_id={friend_id}")

    return _to_response(chat)


async def list_chats(db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10, app_type: str = None) -> dict:
    """
    获取会话列表

    - 分页查询
    - 按 app_type 筛选（可选）
    - 按 last_message_time 倒序
    - 仅返回当前用户的会话
    """
    # 1. 构建查询
    query = select(Chat).where(Chat.user_id == user_id, Chat.is_deleted == False)

    if app_type:
        query = query.where(Chat.app_type == app_type)

    # 2. 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 3. 分页查询，按 last_message_time 倒序（NULL 排最后）
    null_order = case((Chat.last_message_time.is_(None), literal(1)), else_=literal(0))
    query = query.order_by(null_order, Chat.last_message_time.desc(), Chat.create_time.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    chats = result.scalars().all()

    return {
        "list": [_to_response(c) for c in chats],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


async def get_chat_detail(db: AsyncSession, user_id: int, chat_id: str) -> dict:
    """
    获取会话详情

    - 校验会话属于当前用户
    """
    stmt = select(Chat).where(Chat.chat_id == chat_id, Chat.user_id == user_id, Chat.is_deleted == False)
    result = await db.execute(stmt)
    chat = result.scalar_one_or_none()

    if chat is None:
        raise BusinessException(code=404, message="会话不存在")

    return _to_response(chat)


async def delete_chat(db: AsyncSession, user_id: int, chat_id: str):
    """
    删除会话（软删除）

    - 级联软删除该会话下所有消息
    - 级联软删除该会话关联的 agent_task
    """
    # 1. 查询会话
    stmt = select(Chat).where(Chat.chat_id == chat_id, Chat.user_id == user_id, Chat.is_deleted == False)
    result = await db.execute(stmt)
    chat = result.scalar_one_or_none()

    if chat is None:
        raise BusinessException(code=404, message="会话不存在")

    # 2. 级联软删除消息
    await db.execute(
        update(Message).where(Message.chat_id == chat_id, Message.is_deleted == False).values(is_deleted=True)
    )

    # 3. 级联软删除 agent_task
    await db.execute(
        update(AgentTask).where(AgentTask.chat_id == chat_id, AgentTask.is_deleted == False).values(is_deleted=True)
    )

    # 4. 软删除会话
    await db.execute(
        update(Chat).where(Chat.id == chat.id).values(is_deleted=True)
    )

    logger.info(f"删除会话成功: chat_id={chat_id}, user_id={user_id}")


async def validate_chat_ownership(db: AsyncSession, user_id: int, chat_id: str) -> Chat:
    """
    校验会话是否属于当前用户，返回 Chat 对象

    Args:
        user_id: 用户ID
        chat_id: 会话ID

    Returns:
        Chat ORM object

    Raises:
        BusinessException: 会话不存在或不属于当前用户
    """
    stmt = select(Chat).where(Chat.chat_id == chat_id, Chat.user_id == user_id, Chat.is_deleted == False)
    result = await db.execute(stmt)
    chat = result.scalar_one_or_none()

    if chat is None:
        raise BusinessException(code=404, message="会话不存在")

    return chat


async def get_chat_by_id(db: AsyncSession, chat_id: str) -> Chat | None:
    """根据 chat_id 获取会话（不校验用户）"""
    stmt = select(Chat).where(Chat.chat_id == chat_id, Chat.is_deleted == False)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
