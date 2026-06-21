"""
Chat API - 恋爱大师对话接口
"""
import re

from fastapi import APIRouter
from fastapi.params import Header
from sse_starlette.sse import EventSourceResponse

from app.ai.llm.dashscope_client import dashscope_client
from app.ai.rag.retriever import hybrid_retrieve
from app.core.logging import get_logger
from app.models.chat import (
    SyncChatResponse, SyncChatRequest, ChatMetadata, SyncChatData,
    SSEEventType, make_sse_event,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/internal/ai/love/chat", tags=["chat"])

# 句子结束符正则：中文句号、感叹号、问号、英文句号/感叹号/问号、换行
_SENTENCE_END_PATTERN = re.compile(r'(?<=[。！？.!?\n])')


# 情感状态映射：英文 → 中文
EMOTION_STATUS_MAP = {
    "single": "单身",
    "relationship": "恋爱",
    "married": "已婚",
}

# 情感状态对应的咨询方向
EMOTION_GUIDANCE_MAP = {
    "single": "社交圈拓展、追求技巧、自我提升、约会建议",
    "relationship": "沟通技巧、矛盾处理、感情升温、相处之道",
    "married": "家庭责任、亲属关系、婚姻经营、夫妻沟通",
}


def build_system_prompt(emotion_status: str = None) -> str:
    """
    构建系统提示词

    Args:
        emotion_status: 情感状态（英文值：single/relationship/married）

    Returns:
        系统提示词
    """
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


async def _retrieve_knowledge(query: str, user_id: int) -> tuple[list, list]:
    """
    检索知识库，返回 (检索结果列表, rag_sources 列表)

    Args:
        query: 用户查询
        user_id: 用户 ID

    Returns:
        (results, sources): results 是原始检索结果，sources 是精简的来源信息
    """
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


@router.post("/sync", response_model=SyncChatResponse)
async def sync_chat(
        request: SyncChatRequest,
        x_user_id: str = Header(..., alias="X-User-Id")
):
    """
    同步对话接口

    Args:
        request: 对话请求（包含 chat_id, message, emotion_status, history）
        x_user_id: 用户ID（从请求头获取）
    """
    # 1. 检索知识库
    user_id = int(x_user_id)
    rag_results, rag_sources = await _retrieve_knowledge(request.message, user_id)

    # 2. 构建系统提示词（注入 RAG 上下文）
    system_prompt = build_system_prompt(request.emotion_status)
    if rag_results:
        rag_context = _build_rag_context(rag_results)
        system_prompt += f"""

以下是从用户知识库中检索到的相关内容，请参考这些信息来回答用户的问题：

{rag_context}

如果检索到的内容与用户问题相关，请结合这些内容给出更精准的回答。如果无关，请忽略这些内容，正常回答。"""

    # 3. 组装消息列表（system → history → 当前用户消息）
    messages = [{"role": "system", "content": system_prompt}]
    for msg in request.history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": request.message})

    # 4. 调用 LLM
    logger.info(f"Chat request: user_id={x_user_id}, chat_id={request.chat_id}, history_count={len(request.history)}, rag_chunks={len(rag_results)}")

    content = dashscope_client.chat(messages=messages, stream=False)

    # 5. 构造 metadata
    metadata = ChatMetadata(
        tokens_used=None,
        model="mimo-v2.5",
        rag_sources=rag_sources if rag_sources else None,
    )

    # 6. 返回
    logger.info(f"Chat response: user_id={x_user_id}, content_length={len(content)}")

    return SyncChatResponse(data=SyncChatData(content=content, metadata=metadata))


@router.post("/sse")
async def stream_chat(
        request: SyncChatRequest,
        x_user_id: str = Header(..., alias="X-User-Id")
):
    """
    流式对话接口（SSE）

    Args:
        request: 对话请求（包含 chat_id, message, emotion_status, history）
        x_user_id: 用户ID（从请求头获取）

    Returns:
        EventSourceResponse: SSE 事件流
    """
    logger.info(f"SSE chat request: user_id={x_user_id}, chat_id={request.chat_id}, history_count={len(request.history)}")

    async def event_generator():
        try:
            # 1. 发送 thinking 事件
            yield make_sse_event(SSEEventType.THINKING, content="正在思考...")

            # 2. 检索知识库
            user_id = int(x_user_id)
            rag_results, rag_sources = await _retrieve_knowledge(request.message, user_id)

            # 3. 构建系统提示词（注入 RAG 上下文）
            system_prompt = build_system_prompt(request.emotion_status)
            if rag_results:
                rag_context = _build_rag_context(rag_results)
                system_prompt += f"""

以下是从用户知识库中检索到的相关内容，请参考这些信息来回答用户的问题：

{rag_context}

如果检索到的内容与用户问题相关，请结合这些内容给出更精准的回答。如果无关，请忽略这些内容，正常回答。"""

            # 4. 组装消息列表
            messages = [{"role": "system", "content": system_prompt}]
            for msg in request.history:
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": request.message})

            # 5. 调用 LLM 流式接口，聚合为完整句子后发送
            buffer = ""
            for token in dashscope_client.chat(messages=messages, stream=True):
                buffer += token

                # 按句子结束符切分
                parts = _SENTENCE_END_PATTERN.split(buffer)
                # 最后一个元素是不完整的部分，保留到下一轮
                if len(parts) > 1:
                    for sentence in parts[:-1]:
                        if sentence.strip():
                            yield make_sse_event(SSEEventType.ANSWER, content=sentence)
                    buffer = parts[-1]

            # 6. 流结束后，发送 buffer 中剩余的内容
            if buffer.strip():
                yield make_sse_event(SSEEventType.ANSWER, content=buffer)

            # 7. 发送 metadata 事件（包含 rag_sources）
            metadata = ChatMetadata(
                tokens_used=None,
                model="mimo-v2.5",
                rag_sources=rag_sources if rag_sources else None,
            )
            yield make_sse_event(SSEEventType.METADATA, content=metadata.model_dump())

            # 8. 发送结束标记
            yield "[DONE]"

            logger.info(f"SSE chat completed: user_id={x_user_id}, chat_id={request.chat_id}, rag_chunks={len(rag_results)}")

        except Exception as e:
            logger.error(f"SSE chat error: {str(e)}")
            yield make_sse_event(SSEEventType.ERROR, message=str(e))
            yield "[DONE]"

    return EventSourceResponse(event_generator())
