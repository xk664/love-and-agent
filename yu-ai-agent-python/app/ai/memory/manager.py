"""
记忆管理器 (Memory Manager)

整合三层记忆：短期、工作、长期
提供统一的记忆访问接口
"""

import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.ai.memory.short_term import ShortTermMemory
from app.ai.memory.working import WorkingMemory
from app.ai.memory.long_term import LongTermMemory

logger = get_logger(__name__)


class MemoryManager:
    """记忆管理器：整合三层记忆，提供统一访问接口"""

    def __init__(
        self,
        user_id: int,
        chat_id: str,
        redis_client=None,
        llm_client=None,
        vector_store=None
    ):
        """
        初始化记忆管理器

        Args:
            user_id: 用户ID
            chat_id: 当前会话ID
            redis_client: Redis客户端
            llm_client: LLM客户端（用于画像提取）
            vector_store: 向量存储（用于语义检索）
        """
        self.user_id = user_id
        self.chat_id = chat_id

        # 初始化三层记忆
        self.short_term = ShortTermMemory()
        self.working = WorkingMemory(user_id, redis_client)
        self.long_term = LongTermMemory(user_id, llm_client, vector_store)

        # 缓存
        self._context_cache: Optional[dict] = None

    async def build_context(self, db: AsyncSession, current_message: str) -> dict:
        """
        构建完整的上下文（用于发送给LLM）

        Args:
            db: 数据库会话
            current_message: 当前用户消息

        Returns:
            包含三层记忆的上下文字典
        """
        # 并行获取各层记忆
        recent_messages, user_profile, relevant_memories = await asyncio.gather(
            self.working.get_recent_messages(db),
            self.long_term.get_user_profile(db),
            self.long_term.semantic_search(current_message)
        )

        # 获取当前会话的最近消息
        session_messages = await self.working.get_current_session_context(db, self.chat_id)

        context = {
            "short_term": self.short_term.get_context(),
            "working_memory": recent_messages,
            "session_context": session_messages,
            "user_profile": user_profile,
            "relevant_memories": relevant_memories
        }

        self._context_cache = context
        return context

    def build_memory_prompt(self, context: dict) -> str:
        """
        将三层记忆构建为可注入system prompt的文本

        Args:
            context: build_context返回的上下文

        Returns:
            格式化的记忆文本
        """
        parts = []

        # 1. 用户画像
        profile = context.get("user_profile", {})
        if profile:
            profile_text = self._format_user_profile(profile)
            parts.append(f"## 用户画像\n{profile_text}")

        # 2. 语义相关的记忆
        relevant = context.get("relevant_memories", [])
        if relevant:
            relevant_text = "\n".join([
                f"- {m['content']}" for m in relevant
            ])
            parts.append(f"## 相关历史记忆\n{relevant_text}")

        # 3. 近期对话记忆（工作记忆）
        working_memory = context.get("working_memory", [])
        if working_memory:
            memory_text = "\n".join([
                f"{'用户' if msg['role'] == 'user' else '恋爱大师'}：{msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}"
                for msg in working_memory[-10:]  # 只取最近10条
            ])
            parts.append(f"## 近期对话记录\n{memory_text}")

        # 4. 当前会话上下文（短期记忆）
        session_context = context.get("session_context", [])
        if session_context and len(session_context) > 1:
            session_text = "\n".join([
                f"{'用户' if msg['role'] == 'user' else '恋爱大师'}：{msg['content'][:80]}{'...' if len(msg['content']) > 80 else ''}"
                for msg in session_context[-5:]  # 只取最近5条
            ])
            parts.append(f"## 当前会话上下文\n{session_text}")

        return "\n\n".join(parts) if parts else ""

    async def after_conversation(self, db: AsyncSession, messages: list[dict], is_important: bool = False) -> None:
        """
        对话结束后的记忆处理

        Args:
            db: 数据库会话
            messages: 本次对话消息列表
            is_important: 是否为重要对话（决定是否保存为情景记忆）
        """
        try:
            # 1. 用LLM生成会话摘要（异步）
            summary = await self._generate_summary(messages)
            await self.working.save_session_summary(db, self.chat_id, summary)

            # 2. 提取并更新长期记忆（异步执行，不阻塞）
            asyncio.create_task(
                self._extract_and_update_async(db, messages)
            )

            # 3. 如果是重要对话，保存为情景记忆
            if is_important and len(messages) >= 5:
                await self.long_term.save_episodic_memory(
                    db, self.chat_id, summary
                )

            # 4. 刷新工作记忆缓存
            await self.working.refresh_cache(db)

            logger.info(f"对话后记忆处理完成: user_id={self.user_id}, chat_id={self.chat_id}")

        except Exception as e:
            logger.error(f"对话后记忆处理失败: {e}")

    async def add_message(self, role: str, content: str) -> None:
        """
        添加消息到短期记忆

        Args:
            role: 角色
            content: 消息内容
        """
        self.short_term.add(role, content)

    async def save_key_fact(self, db: AsyncSession, fact: str, fact_type: str = "general") -> None:
        """
        保存关键事实到长期记忆

        Args:
            db: 数据库会话
            fact: 事实内容
            fact_type: 事实类型
        """
        await self.long_term.save_key_fact(db, fact, fact_type)

    async def save_preference(self, db: AsyncSession, preference: str, category: str = "general") -> None:
        """
        保存用户偏好到长期记忆

        Args:
            db: 数据库会话
            preference: 偏好内容
            category: 偏好类别
        """
        await self.long_term.save_preference(db, preference, category)

    def get_short_term_context(self) -> list[dict]:
        """获取短期记忆上下文"""
        return self.short_term.get_context()

    async def get_user_profile(self, db: AsyncSession) -> dict:
        """获取用户画像"""
        return await self.long_term.get_user_profile(db)

    def _format_user_profile(self, profile: dict) -> str:
        """格式化用户画像为文本"""
        parts = []

        # 个人信息
        personal = profile.get("personal_info", {})
        if personal:
            if personal.get("age_range"):
                parts.append(f"- 年龄段：{personal['age_range']}")
            if personal.get("occupation"):
                parts.append(f"- 职业：{personal['occupation']}")
            if personal.get("location"):
                parts.append(f"- 所在地：{personal['location']}")

        # 感情状态
        if profile.get("relationship_status"):
            parts.append(f"- 感情状态：{profile['relationship_status']}")

        # 性格特点
        traits = profile.get("personality_traits", [])
        if traits:
            parts.append(f"- 性格特点：{'、'.join(traits)}")

        # 关注点
        concerns = profile.get("concerns", [])
        if concerns:
            parts.append(f"- 关注点：{'、'.join(concerns)}")

        # 偏好
        preferences = profile.get("preferences", [])
        if preferences:
            parts.append(f"- 偏好：{'、'.join(preferences)}")

        return "\n".join(parts) if parts else "暂无用户画像信息"

    async def _generate_summary(self, messages: list[dict]) -> str:
        """
        用LLM生成精炼的会话摘要

        Args:
            messages: 对话消息列表

        Returns:
            LLM生成的摘要（不超过100字）
        """
        if not messages:
            return ""

        # 提取用户消息
        user_messages = [m["content"] for m in messages if m["role"] == "user"]
        if not user_messages:
            return ""

        # 如果没有LLM客户端，使用简单摘要作为fallback
        if not self.long_term.llm:
            return self._generate_simple_summary(messages)

        try:
            # 构建对话文本
            conversation_text = "\n".join([
                f"{'用户' if msg['role'] == 'user' else 'AI'}：{msg['content'][:100]}"
                for msg in messages[-10:]  # 只取最近10条
            ])

            # LLM生成摘要
            prompt = f"""请用一句话总结以下对话的核心内容（不超过100字）：

{conversation_text}

要求：
1. 只输出摘要，不要有其他内容
2. 不超过50字
3. 突出用户的核心问题或需求"""

            response = self.long_term.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )

            # 清理响应（去除可能的引号、换行符等）
            summary = response.strip().strip('"').strip("'").strip()
            if len(summary) > 100:
                summary = summary[:100] + "..."

            logger.info(f"LLM生成会话摘要成功: {summary[:30]}...")
            return summary

        except Exception as e:
            logger.warning(f"LLM生成摘要失败，使用简单摘要: {e}")
            return self._generate_simple_summary(messages)

    def _generate_simple_summary(self, messages: list[dict]) -> str:
        """简单摘要（fallback方案）"""
        if not messages:
            return ""

        user_messages = [m["content"] for m in messages if m["role"] == "user"]
        if not user_messages:
            return ""

        first_msg = user_messages[0][:50]
        last_msg = user_messages[-1][:50]

        if len(user_messages) == 1:
            return f"用户咨询：{first_msg}"
        else:
            return f"用户咨询：{first_msg}... 最后讨论：{last_msg}..."

    async def _extract_and_update_async(self, db: AsyncSession, messages: list[dict]) -> None:
        """异步提取并更新用户画像（创建独立数据库会话）"""
        from app.core.database import async_session
        try:
            async with async_session() as new_session:
                await self.long_term.extract_and_update_profile(new_session, messages)
        except Exception as e:
            logger.error(f"异步画像提取失败: {e}")

    @staticmethod
    def is_important_conversation(messages: list[dict]) -> bool:
        """
        判断是否为重要对话

        Args:
            messages: 对话消息列表

        Returns:
            是否重要
        """
        # 判断标准：
        # 1. 消息数量 >= 10
        # 2. 用户消息中包含关键词
        if len(messages) < 10:
            return False

        important_keywords = [
            "分手", "结婚", "离婚", "异地", "出轨",
            "见家长", "求婚", "怀孕", "孩子", "未来",
            "规划", "决定", "选择", "放弃", "坚持"
        ]

        user_messages = [m["content"] for m in messages if m["role"] == "user"]
        full_text = " ".join(user_messages)

        return any(keyword in full_text for keyword in important_keywords)
