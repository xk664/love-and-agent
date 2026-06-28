"""
工作记忆 (Working Memory)

跨会话的近期记忆，保留最近对话和会话摘要
存储: Redis (热数据) + MySQL (持久化)
"""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.db.chat import Chat
from app.models.db.message import Message

logger = get_logger(__name__)

# Redis键前缀
REDIS_PREFIX_WORKING = "memory:working:"
REDIS_PREFIX_SUMMARY = "memory:summary:"
REDIS_PREFIX_SESSION = "memory:session:"


class WorkingMemory:
    """工作记忆：跨会话的近期记忆，支持Redis缓存和会话摘要"""

    def __init__(self, user_id: int, redis_client=None):
        """
        初始化工作记忆

        Args:
            user_id: 用户ID
            redis_client: Redis客户端（可选，不传则只用MySQL）
        """
        self.user_id = user_id
        self.redis = redis_client
        self.recent_limit = 20  # 最近20条消息
        self.summary_limit = 5  # 最近5个会话摘要
        self.cache_ttl = 3600  # Redis缓存1小时

    async def get_recent_messages(self, db: AsyncSession) -> list[dict]:
        """
        获取跨会话的最近N条消息

        Args:
            db: 数据库会话

        Returns:
            最近的消息列表
        """
        # 1. 先查Redis缓存
        if self.redis:
            cached = await self._get_from_cache(f"{REDIS_PREFIX_WORKING}{self.user_id}")
            if cached:
                logger.debug(f"工作记忆缓存命中: user_id={self.user_id}")
                return cached

        # 2. 查MySQL
        messages = await self._query_recent_messages(db)

        # 3. 写入Redis缓存
        if self.redis and messages:
            await self._set_cache(
                f"{REDIS_PREFIX_WORKING}{self.user_id}",
                messages,
                self.cache_ttl
            )

        return messages

    async def get_session_summaries(self, db: AsyncSession, limit: int = None) -> list[dict]:
        """
        获取最近的会话摘要

        Args:
            db: 数据库会话
            limit: 返回数量限制

        Returns:
            会话摘要列表
        """
        limit = limit or self.summary_limit

        # 从Redis获取摘要列表
        if self.redis:
            cache_key = f"{REDIS_PREFIX_SUMMARY}{self.user_id}"
            cached_summaries = await self._get_from_cache(cache_key)
            if cached_summaries:
                return cached_summaries[:limit]

        # 从MySQL查询会话和最后几条消息，构建摘要
        summaries = await self._build_session_summaries(db, limit)

        # 缓存到Redis
        if self.redis and summaries:
            await self._set_cache(
                f"{REDIS_PREFIX_SUMMARY}{self.user_id}",
                summaries,
                self.cache_ttl * 24  # 摘要缓存24小时
            )

        return summaries

    async def save_session_summary(self, db: AsyncSession, chat_id: str, summary: str, key_topics: list = None) -> None:
        """
        保存会话摘要（同一会话复用时更新摘要，不重复）

        Args:
            db: 数据库会话
            chat_id: 会话ID
            summary: 摘要内容
            key_topics: 关键话题标签
        """
        from sqlalchemy import select
        from app.models.db.memory import SessionSummary

        # 1. 保存到MySQL
        existing = await db.execute(
            select(SessionSummary).where(
                SessionSummary.chat_id == chat_id,
                SessionSummary.user_id == self.user_id,
                SessionSummary.is_deleted == False
            )
        )
        existing_summary = existing.scalar_one_or_none()

        if existing_summary:
            # 更新现有摘要
            existing_summary.summary = summary
            existing_summary.key_topics = key_topics or []
            existing_summary.create_time = datetime.now()
        else:
            # 创建新摘要
            summary_record = SessionSummary(
                chat_id=chat_id,
                user_id=self.user_id,
                summary=summary,
                key_topics=key_topics or []
            )
            db.add(summary_record)

        await db.commit()

        # 2. 存储到Redis（热缓存）
        if self.redis:
            summary_data = {
                "chat_id": chat_id,
                "summary": summary,
                "key_topics": key_topics or [],
                "create_time": datetime.now().isoformat()
            }

            # 获取现有摘要列表
            cache_key = f"{REDIS_PREFIX_SUMMARY}{self.user_id}"
            summaries = await self._get_from_cache(cache_key) or []

            # 查找是否已存在该会话的摘要
            existing_index = next(
                (i for i, s in enumerate(summaries) if s.get("chat_id") == chat_id),
                None
            )

            if existing_index is not None:
                # 已存在：更新摘要并移到开头
                summaries.pop(existing_index)
                summaries.insert(0, summary_data)
                logger.debug(f"更新会话摘要: chat_id={chat_id}")
            else:
                # 不存在：添加到开头
                summaries.insert(0, summary_data)

            # 保留最近N个
            summaries = summaries[:self.summary_limit]

            await self._set_cache(cache_key, summaries, self.cache_ttl * 24)

        logger.info(f"会话摘要已保存: user_id={self.user_id}, chat_id={chat_id}")

    async def get_current_session_context(self, db: AsyncSession, chat_id: str, limit: int = 10) -> list[dict]:
        """
        获取当前会话的最近消息

        Args:
            db: 数据库会话
            chat_id: 会话ID
            limit: 消息数量限制

        Returns:
            当前会话的消息列表
        """
        # 先查Redis
        if self.redis:
            cached = await self._get_from_cache(f"{REDIS_PREFIX_SESSION}{chat_id}")
            if cached:
                return cached[-limit:]

        # 查MySQL
        query = (
            select(Message)
            .where(
                Message.chat_id == chat_id,
                Message.role.in_(["user", "assistant"]),
                Message.is_deleted == False
            )
            .order_by(Message.create_time.desc())
            .limit(limit)
        )
        result = await db.execute(query)
        messages = result.scalars().all()

        # 按时间正序
        messages_list = [
            {"role": m.role, "content": m.content}
            for m in reversed(messages)
        ]

        # 缓存到Redis
        if self.redis and messages_list:
            await self._set_cache(
                f"{REDIS_PREFIX_SESSION}{chat_id}",
                messages_list,
                self.cache_ttl
            )

        return messages_list

    async def refresh_cache(self, db: AsyncSession) -> None:
        """刷新缓存（对话结束后调用）"""
        if self.redis:
            # 清除工作记忆缓存，下次查询会重新从MySQL加载
            await self._delete_cache(f"{REDIS_PREFIX_WORKING}{self.user_id}")
            logger.debug(f"工作记忆缓存已刷新: user_id={self.user_id}")

    async def _query_recent_messages(self, db: AsyncSession) -> list[dict]:
        """从MySQL查询最近消息"""
        # 1. 查询用户所有会话ID
        chat_ids_result = await db.execute(
            select(Chat.chat_id).where(
                Chat.user_id == self.user_id,
                Chat.is_deleted == False
            )
        )
        chat_ids = [row[0] for row in chat_ids_result.all()]
        if not chat_ids:
            return []

        # 2. 查询这些会话的最近消息
        query = (
            select(Message)
            .where(
                Message.chat_id.in_(chat_ids),
                Message.role.in_(["user", "assistant"]),
                Message.is_deleted == False
            )
            .order_by(Message.create_time.desc())
            .limit(self.recent_limit)
        )
        result = await db.execute(query)
        messages = result.scalars().all()

        # 3. 按时间正序返回
        messages_list = list(reversed(messages))
        return [{"role": m.role, "content": m.content} for m in messages_list]

    async def _build_session_summaries(self, db: AsyncSession, limit: int) -> list[dict]:
        """构建会话摘要（从最近会话的最后几条消息生成）"""
        # 查询用户最近的会话
        query = (
            select(Chat)
            .where(
                Chat.user_id == self.user_id,
                Chat.is_deleted == False
            )
            .order_by(Chat.last_message_time.desc())
            .limit(limit)
        )
        result = await db.execute(query)
        chats = result.scalars().all()

        summaries = []
        for chat in chats:
            # 获取每个会话的最后几条消息
            msg_query = (
                select(Message)
                .where(
                    Message.chat_id == chat.chat_id,
                    Message.role.in_(["user", "assistant"]),
                    Message.is_deleted == False
                )
                .order_by(Message.create_time.desc())
                .limit(5)
            )
            msg_result = await db.execute(msg_query)
            messages = msg_result.scalars().all()

            if messages:
                # 生成简单摘要（取最后一条用户消息作为摘要）
                last_user_msg = next(
                    (m.content for m in messages if m.role == "user"),
                    messages[0].content
                )
                summary = {
                    "chat_id": chat.chat_id,
                    "title": chat.title or "未命名会话",
                    "summary": last_user_msg[:100] + ("..." if len(last_user_msg) > 100 else ""),
                    "message_count": len(messages),
                    "last_time": chat.last_message_time.isoformat() if chat.last_message_time else None
                }
                summaries.append(summary)

        return summaries

    async def _get_from_cache(self, key: str) -> Optional[any]:
        """从Redis获取缓存"""
        if not self.redis:
            return None
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Redis获取缓存失败: {e}")
        return None

    async def _set_cache(self, key: str, value: any, ttl: int) -> None:
        """设置Redis缓存"""
        if not self.redis:
            return
        try:
            await self.redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"Redis设置缓存失败: {e}")

    async def _delete_cache(self, key: str) -> None:
        """删除Redis缓存"""
        if not self.redis:
            return
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Redis删除缓存失败: {e}")
