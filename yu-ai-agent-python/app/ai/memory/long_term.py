"""
长期记忆 (Long-term Memory)

持久化的用户画像和关键事实记忆
存储: MySQL (结构化数据) + PgVector (向量检索)
"""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.db.memory import UserMemory, SessionSummary

logger = get_logger(__name__)


class LongTermMemory:
    """长期记忆：持久化的用户画像、关键事实、语义记忆"""

    def __init__(self, user_id: int, llm_client=None, vector_store=None):
        """
        初始化长期记忆

        Args:
            user_id: 用户ID
            llm_client: LLM客户端（用于提取用户画像）
            vector_store: 向量存储（用于语义检索）
        """
        self.user_id = user_id
        self.llm = llm_client
        self.vector_store = vector_store

    async def get_user_profile(self, db: AsyncSession) -> dict:
        """
        获取用户画像

        Args:
            db: 数据库会话

        Returns:
            用户画像字典
        """
        query = select(UserMemory).where(
            UserMemory.user_id == self.user_id,
            UserMemory.memory_type == "profile",
            UserMemory.is_deleted == False
        )
        result = await db.execute(query)
        memory = result.scalar_one_or_none()

        if memory and memory.content_json:
            return memory.content_json

        return {}

    async def update_user_profile(self, db: AsyncSession, profile_data: dict) -> None:
        """
        更新用户画像

        Args:
            db: 数据库会话
            profile_data: 画像数据
        """
        query = select(UserMemory).where(
            UserMemory.user_id == self.user_id,
            UserMemory.memory_type == "profile",
            UserMemory.is_deleted == False
        )
        result = await db.execute(query)
        memory = result.scalar_one_or_none()

        if memory:
            # 更新现有画像
            memory.content_json = profile_data
            memory.content_text = json.dumps(profile_data, ensure_ascii=False)
            memory.update_time = datetime.now()
        else:
            # 创建新画像
            memory = UserMemory(
                user_id=self.user_id,
                memory_type="profile",
                content_json=profile_data,
                content_text=json.dumps(profile_data, ensure_ascii=False),
                importance_score=1.0
            )
            db.add(memory)

        await db.commit()
        logger.info(f"用户画像已更新: user_id={self.user_id}")

    async def extract_and_update_profile(self, db: AsyncSession, conversation: list[dict]) -> None:
        """
        从对话中提取关键信息并更新画像

        Args:
            db: 数据库会话
            conversation: 对话消息列表
        """
        if not self.llm:
            logger.warning("LLM客户端未配置，跳过画像提取")
            return

        try:
            # 获取现有画像
            existing_profile = await self.get_user_profile(db)

            # 构建提取提示词
            extraction_prompt = self._build_extraction_prompt(existing_profile, conversation)

            # 调用LLM提取
            response = self.llm.chat(
                messages=[{"role": "user", "content": extraction_prompt}],
                stream=False
            )

            # 解析提取结果
            extracted = self._parse_extraction_result(response)
            logger.info(f"LLM提取结果: {extracted}")

            # 合并到现有画像
            merged_profile = self._merge_profiles(existing_profile, extracted)

            # 更新到数据库
            await self.update_user_profile(db, merged_profile)

            # 保存关键事实到向量库（只有 key_events 才保存）
            if self.vector_store and extracted.get("key_events"):
                await self._save_key_facts_to_vector(extracted["key_events"])

            logger.info(f"用户画像提取完成: user_id={self.user_id}")

        except Exception as e:
            logger.error(f"用户画像提取失败: {e}")

    async def save_key_fact(self, db: AsyncSession, fact: str, fact_type: str = "general") -> None:
        """
        保存关键事实

        Args:
            db: 数据库会话
            fact: 事实内容
            fact_type: 事实类型 (general/relationship/event)
        """
        # 保存到MySQL
        memory = UserMemory(
            user_id=self.user_id,
            memory_type="key_fact",
            content_json={"fact": fact, "type": fact_type},
            content_text=fact,
            importance_score=0.7
        )
        db.add(memory)
        await db.commit()

        # 保存到向量库（用于语义检索）
        if self.vector_store:
            try:
                await self.vector_store.add_texts(
                    texts=[fact],
                    metadatas=[{
                        "user_id": self.user_id,
                        "memory_type": "key_fact",
                        "fact_type": fact_type
                    }]
                )
            except Exception as e:
                logger.warning(f"关键事实向量化失败: {e}")

        logger.info(f"关键事实已保存: user_id={self.user_id}, type={fact_type}")

    async def save_preference(self, db: AsyncSession, preference: str, category: str = "general") -> None:
        """
        保存用户偏好

        Args:
            db: 数据库会话
            preference: 偏好内容
            category: 偏好类别 (general/communication/style)
        """
        memory = UserMemory(
            user_id=self.user_id,
            memory_type="preference",
            content_json={"preference": preference, "category": category},
            content_text=preference,
            importance_score=0.8
        )
        db.add(memory)
        await db.commit()

        logger.info(f"用户偏好已保存: user_id={self.user_id}, category={category}")

    async def semantic_search(self, query: str, top_k: int = 3) -> list[dict]:
        """
        语义检索相关记忆

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            相关记忆列表
        """
        if not self.vector_store:
            logger.warning("向量存储未配置，跳过语义检索")
            return []

        try:
            results = await self.vector_store.similarity_search(
                query=query,
                filter={"user_id": self.user_id},
                k=top_k
            )

            return [
                {
                    "content": r.get("content", ""),
                    "metadata": r.get("metadata", {}),
                    "score": r.get("score", 0)
                }
                for r in results
            ]
        except Exception as e:
            logger.warning(f"语义检索失败: {e}")
            return []

    async def save_episodic_memory(self, db: AsyncSession, chat_id: str, summary: str, key_events: list = None) -> None:
        """
        保存情景记忆（重要会话的摘要）

        Args:
            db: 数据库会话
            chat_id: 会话ID
            summary: 会话摘要
            key_events: 关键事件列表
        """
        # 保存到MySQL
        memory = UserMemory(
            user_id=self.user_id,
            memory_type="episodic",
            content_json={
                "chat_id": chat_id,
                "summary": summary,
                "key_events": key_events or []
            },
            content_text=summary,
            importance_score=0.9
        )
        db.add(memory)
        await db.commit()

        # 保存到向量库
        if self.vector_store:
            try:
                await self.vector_store.add_texts(
                    texts=[summary],
                    metadatas=[{
                        "user_id": self.user_id,
                        "memory_type": "episodic",
                        "chat_id": chat_id
                    }]
                )
            except Exception as e:
                logger.warning(f"情景记忆向量化失败: {e}")

        # 同时保存到会话摘要表
        summary_record = SessionSummary(
            chat_id=chat_id,
            user_id=self.user_id,
            summary=summary,
            key_topics=key_events or []
        )
        db.add(summary_record)
        await db.commit()

        logger.info(f"情景记忆已保存: user_id={self.user_id}, chat_id={chat_id}")

    def _build_extraction_prompt(self, existing_profile: dict, conversation: list[dict]) -> str:
        """构建画像提取提示词"""
        conversation_text = "\n".join([
            f"{'用户' if msg['role'] == 'user' else 'AI'}：{msg['content']}"
            for msg in conversation[-10:]  # 只取最近10条
        ])

        existing_text = ""
        if existing_profile:
            existing_text = f"\n用户现有画像：\n{json.dumps(existing_profile, ensure_ascii=False, indent=2)}"

        return f"""请从以下对话中提取用户的关键信息，返回JSON格式。

对话内容：
{conversation_text}
{existing_text}

请提取以下信息（只提取新信息，不要重复已有信息）：
{{
    "personal_info": {{
        "age_range": "年龄段（如20-25）",
        "occupation": "职业",
        "location": "所在地"
    }},
    "relationship_status": "感情状态描述",
    "preferences": ["偏好1", "偏好2"],
    "concerns": ["关注点1", "关注点2"],
    "key_events": ["重要事件1", "重要事件2"],
    "personality_traits": ["性格特点1", "性格特点2"]
}}

注意：
1. 只提取明确提到的信息，不要推测
2. 如果没有新信息，对应字段返回null或空数组
3. 返回纯JSON，不要有其他文字"""

    def _parse_extraction_result(self, response: str) -> dict:
        """解析LLM提取结果"""
        try:
            # 尝试提取JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"解析提取结果失败: {e}")
        return {}

    def _merge_profiles(self, existing: dict, new_data: dict) -> dict:
        """合并用户画像"""
        merged = existing.copy()

        # 合并各字段
        for key in ["personal_info", "relationship_status", "preferences", "concerns", "key_events", "personality_traits"]:
            if key in new_data and new_data[key]:
                if key in ["preferences", "concerns", "key_events", "personality_traits"]:
                    # 列表类型：合并去重
                    existing_list = merged.get(key, [])
                    new_list = new_data[key] if isinstance(new_data[key], list) else [new_data[key]]
                    merged[key] = list(set(existing_list + new_list))
                elif key == "personal_info":
                    # 字典类型：深度合并
                    merged[key] = {**merged.get(key, {}), **new_data[key]}
                else:
                    # 其他类型：直接覆盖
                    merged[key] = new_data[key]

        return merged

    async def _save_key_facts_to_vector(self, key_events: list) -> None:
        """保存关键事实到向量库"""
        if not key_events or not self.vector_store:
            return

        try:
            await self.vector_store.add_texts(
                texts=key_events,
                metadatas=[{
                    "user_id": self.user_id,
                    "memory_type": "key_fact"
                }] * len(key_events)
            )
        except Exception as e:
            logger.warning(f"关键事实向量化失败: {e}")
