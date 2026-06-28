"""
对话 AI 外部 API（需 JWT 认证）
迁移自 Java AiController.java / AiServiceImpl.java

关键变化：
- JWT 认证（不再依赖 Java 注入 X-User-Id）
- 内部保存消息（不再依赖 Java）
- 内部查询跨会话记忆（不再依赖 Java 传入 history）
"""

import json
import re

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import get_current_user_id
from app.core.redis import redis_client
from app.ai.llm.dashscope_client import dashscope_client
from app.ai.rag.retriever import hybrid_retrieve
from app.ai.memory import MemoryManager
from app.ai.memory.vector_store_adapter import get_memory_vector_store
from app.models.chat import ChatMetadata, SSEEventType, make_sse_event
from app.services import message_service

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/ai/love/chat", tags=["AI 对话"])

# 句子结束符正则
_SENTENCE_END_PATTERN = re.compile(r'(?<=[。！？.!?\n])')

# 情感状态映射
EMOTION_STATUS_MAP = {
    "single": "单身",
    "relationship": "恋爱",
    "married": "已婚",
}

EMOTION_GUIDANCE_MAP = {
    "single": "社交圈拓展、追求技巧、自我提升、约会建议",
    "relationship": "沟通技巧、矛盾处理、感情升温、相处之道",
    "married": "家庭责任、亲属关系、婚姻经营、夫妻沟通",
}


def build_system_prompt(emotion_status: str = None) -> str:
    """构建系统提示词"""
    base_prompt = """你是一位专业的情感咨询师"恋爱大师"，擅长提供恋爱和情感方面的建议。

你的特点：
- 温暖、耐心、善于倾听
- 给出具体、可操作的建议
- 尊重用户隐私，保守秘密
- 用通俗易懂的语言沟通
- 必要时会引用相关心理学知识

你的职责：
- 帮助用户解决情感困惑
- 提供恋爱、婚姻方面的建议
- 帮助用户提升社交能力
- 分析情感问题，给出解决方案

注意事项：
- 你不能代替用户做决定，只能提供建议和分析
- 如果遇到严重的心理问题，建议用户寻求专业心理咨询
- 保持中立客观，不偏袒任何一方"""

    if emotion_status and emotion_status in EMOTION_STATUS_MAP:
        chinese_status = EMOTION_STATUS_MAP[emotion_status]
        guidance = EMOTION_GUIDANCE_MAP[emotion_status]
        base_prompt += f"""

当前用户的情感状态：{chinese_status}
咨询重点方向：{guidance}

请根据用户的情感状态，提供更有针对性的建议。"""

    return base_prompt


def _build_rag_context(results: list) -> str:
    """将检索结果拼接为可注入 system prompt 的上下文文本"""
    if not results:
        return ""
    parts = []
    for i, item in enumerate(results, 1):
        title = item.get("metadata", {}).get("title", "未知文档")
        content = item.get("content", "")
        parts.append(f"[{i}] 来源：《{title}》\n{content}")
    return "\n\n".join(parts)


def _build_memory_context(history: list[dict]) -> str:
    """将跨会话记忆拼接为上下文文本"""
    if not history:
        return ""
    parts = []
    for msg in history:
        role_label = "用户" if msg["role"] == "user" else "恋爱大师"
        parts.append(f"{role_label}：{msg['content']}")
    return "\n".join(parts)


async def _retrieve_knowledge(query: str, user_id: int) -> tuple[list, list]:
    """检索知识库"""
    try:
        results = await hybrid_retrieve(query=query, user_id=user_id)
        sources = [
            {
                "document_id": r.get("metadata", {}).get("document_id"),
                "title": r.get("metadata", {}).get("title", ""),
                "chunk_content": r["content"][:200],
                "similarity": r["similarity"],
            }
            for r in results
        ]
        return results, sources
    except Exception as e:
        logger.warning(f"Knowledge retrieval failed, proceeding without RAG: {e}")
        return [], []


async def _validate_chat_ownership(db: AsyncSession, user_id: int, chat_id: str):
    """校验会话归属（内部方法）"""
    from sqlalchemy import select
    from app.models.db.chat import Chat
    result = await db.execute(
        select(Chat).where(Chat.chat_id == chat_id, Chat.user_id == user_id, Chat.is_deleted == False)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        from app.core.exceptions import BusinessException
        raise BusinessException(400, "会话不存在或无权访问")
    return chat


async def _load_friend_system_prompt(db: AsyncSession, friend_id: int | None) -> str | None:
    """加载数字朋友的系统提示词"""
    if not friend_id:
        return None
    from sqlalchemy import select
    from app.models.db.digital_friend import DigitalFriend
    result = await db.execute(
        select(DigitalFriend).where(
            DigitalFriend.id == friend_id,
            DigitalFriend.is_deleted == False,
        )
    )
    friend = result.scalar_one_or_none()
    if friend and friend.system_prompt and friend.status == "ready":
        return friend.system_prompt
    return None


# ===== 请求模型 =====

from pydantic import BaseModel, Field
from typing import Optional


class ChatAIRequest(BaseModel):
    """对话请求（新版：无需传 history，内部自动获取跨会话记忆）"""
    chat_id: str = Field(..., description="会话 ID")
    message: str = Field(..., description="用户消息", min_length=1)
    emotion_status: Optional[str] = Field(None, description="情感状态: single/relationship/married")


# ===== 同步对话 =====

@router.post("/sync")
async def sync_chat(
    request: ChatAIRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    同步对话接口

    使用三层记忆架构：
    - 短期记忆：当前会话上下文
    - 工作记忆：跨会话近期记忆 + 会话摘要
    - 长期记忆：用户画像、关键事实、语义记忆
    """
    # 1. 校验会话归属
    chat = await _validate_chat_ownership(db, user_id, request.chat_id)

    # 2. 保存用户消息到 MySQL
    await message_service.save_user_message(db, request.chat_id, request.message)

    # 3. 初始化记忆管理器
    redis = await redis_client.get_client()
    memory_manager = MemoryManager(
        user_id=user_id,
        chat_id=request.chat_id,
        redis_client=redis,
        llm_client=dashscope_client,
        vector_store=get_memory_vector_store(user_id)
    )

    # 4. 添加消息到短期记忆
    await memory_manager.add_message("user", request.message)

    # 5. 构建三层记忆上下文
    context = await memory_manager.build_context(db, request.message)
    memory_prompt = memory_manager.build_memory_prompt(context)

    # 6. 检索知识库
    rag_results, rag_sources = await _retrieve_knowledge(request.message, user_id)

    # 7. 构建系统提示词（优先使用数字朋友的 system_prompt）
    friend_system_prompt = await _load_friend_system_prompt(db, getattr(chat, 'friend_id', None))
    if friend_system_prompt:
        system_prompt = friend_system_prompt
    else:
        system_prompt = build_system_prompt(request.emotion_status)

    if rag_results:
        rag_context = _build_rag_context(rag_results)
        system_prompt += f"""

以下是从用户知识库中检索到的相关内容，请参考这些信息来回答用户的问题：

{rag_context}

如果检索到的内容与用户问题相关，请结合这些内容给出更精准的回答。如果无关，请忽略这些内容，正常回答。"""

    if memory_prompt:
        system_prompt += f"""

{memory_prompt}"""

    # 8. 组装消息列表
    messages = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "user", "content": request.message})

    # 9. 调用 LLM
    logger.info(f"Sync chat: user={user_id}, chat={request.chat_id}, rag={len(rag_results)}, memory_layers=3")
    content = dashscope_client.chat(messages=messages, stream=False)

    # 10. 保存 AI 回复到 MySQL
    await message_service.save_assistant_message(db, request.chat_id, content)

    # 11. 添加回复到短期记忆
    await memory_manager.add_message("assistant", content)

    # 12. 对话后记忆处理（异步）
    conversation_messages = [
        {"role": "user", "content": request.message},
        {"role": "assistant", "content": content}
    ]
    is_important = MemoryManager.is_important_conversation(conversation_messages)
    await memory_manager.after_conversation(db, conversation_messages, is_important)

    # 13. 返回
    metadata = ChatMetadata(
        tokens_used=None,
        model="mimo-v2.5",
        rag_sources=rag_sources if rag_sources else None,
    )

    return {
        "code": 200,
        "message": "success",
        "data": {"content": content, "metadata": metadata.model_dump()},
    }


# ===== SSE 流式对话 =====

@router.post("/sse")
async def stream_chat(
    request: ChatAIRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    流式对话接口（SSE）

    使用三层记忆架构：
    - 短期记忆：当前会话上下文
    - 工作记忆：跨会话近期记忆 + 会话摘要
    - 长期记忆：用户画像、关键事实、语义记忆
    """
    # 1. 校验会话归属（在 generator 外部执行，失败直接返回错误）
    chat = await _validate_chat_ownership(db, user_id, request.chat_id)

    # 2. 保存用户消息到 MySQL
    await message_service.save_user_message(db, request.chat_id, request.message)

    # 3. 初始化记忆管理器
    redis = await redis_client.get_client()
    memory_manager = MemoryManager(
        user_id=user_id,
        chat_id=request.chat_id,
        redis_client=redis,
        llm_client=dashscope_client,
        vector_store=get_memory_vector_store(user_id)
    )

    # 4. 添加消息到短期记忆
    await memory_manager.add_message("user", request.message)

    # 5. 构建三层记忆上下文
    context = await memory_manager.build_context(db, request.message)
    memory_prompt = memory_manager.build_memory_prompt(context)

    # 6. 检索知识库
    rag_results, rag_sources = await _retrieve_knowledge(request.message, user_id)

    # 7. 构建系统提示词（优先使用数字朋友的 system_prompt）
    friend_system_prompt = await _load_friend_system_prompt(db, getattr(chat, 'friend_id', None))
    if friend_system_prompt:
        system_prompt = friend_system_prompt
    else:
        system_prompt = build_system_prompt(request.emotion_status)

    if rag_results:
        rag_context = _build_rag_context(rag_results)
        system_prompt += f"""

以下是从用户知识库中检索到的相关内容，请参考这些信息来回答用户的问题：

{rag_context}

如果检索到的内容与用户问题相关，请结合这些内容给出更精准的回答。如果无关，请忽略这些内容，正常回答。"""

    if memory_prompt:
        system_prompt += f"""

{memory_prompt}"""

    # 8. 组装消息列表
    messages = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "user", "content": request.message})

    logger.info(f"SSE chat: user={user_id}, chat={request.chat_id}, rag={len(rag_results)}, memory_layers=3")

    async def event_generator():
        full_response = ""
        try:
            # 发送 thinking 事件
            yield make_sse_event(SSEEventType.THINKING, content="正在思考...")

            # 流式调用 LLM，按句子切分发送
            buffer = ""
            for token in dashscope_client.chat(messages=messages, stream=True):
                buffer += token
                full_response += token

                parts = _SENTENCE_END_PATTERN.split(buffer)
                if len(parts) > 1:
                    for sentence in parts[:-1]:
                        if sentence.strip():
                            yield make_sse_event(SSEEventType.ANSWER, content=sentence)
                    buffer = parts[-1]

            # 发送剩余内容
            if buffer.strip():
                yield make_sse_event(SSEEventType.ANSWER, content=buffer)

            # 发送 metadata
            metadata = ChatMetadata(
                tokens_used=None,
                model="mimo-v2.5",
                rag_sources=rag_sources if rag_sources else None,
            )
            yield make_sse_event(SSEEventType.METADATA, content=metadata.model_dump())

            # 保存完整 AI 回复到 MySQL
            await message_service.save_assistant_message(db, request.chat_id, full_response)

            # 添加回复到短期记忆
            await memory_manager.add_message("assistant", full_response)

            # 对话后记忆处理（异步）
            conversation_messages = [
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": full_response}
            ]
            is_important = MemoryManager.is_important_conversation(conversation_messages)
            await memory_manager.after_conversation(db, conversation_messages, is_important)

            yield "[DONE]"
            logger.info(f"SSE chat completed: user={user_id}, chat={request.chat_id}")

        except Exception as e:
            logger.error(f"SSE chat error: {e}")
            yield make_sse_event(SSEEventType.ERROR, message=str(e))
            yield "[DONE]"

    return EventSourceResponse(event_generator())
