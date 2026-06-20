from typing import Optional, List, Any

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role:str  #assitant/user
    content:str # 消息内容

class SyncChatRequest(BaseModel):
    chat_id:str
    message:str
    emotion_status:Optional[str]=None # single|relationship|married
    history:List[ChatMessage]=[]

class ChatMetadata(BaseModel):
    tokens_used: Optional[int] = None
    model: Optional[str] = None
    tool_calls: Optional[List] = None
    rag_sources: Optional[List] = None

class SyncChatData(BaseModel):
    content: str
    metadata: Optional[ChatMetadata] = None

class SyncChatResponse(BaseModel):
    code: int = 200
    data: SyncChatData
    message: str = "success"


# ===== SSE 事件模型 =====

class SSEEventType:
    """SSE 事件类型常量"""
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ANSWER = "answer"
    METADATA = "metadata"
    ERROR = "error"


def make_sse_event(event_type: str, **kwargs) -> str:
    """
    构建 SSE 事件数据（JSON 字符串）

    Args:
        event_type: 事件类型（thinking/answer/tool_call/tool_result/metadata/error）
        **kwargs: 业务数据字段（content/tool/args/result/message）

    Returns:
        JSON 字符串，可直接作为 SSE data 字段发送
    """
    import json
    event = {"type": event_type}
    event.update(kwargs)
    return json.dumps(event, ensure_ascii=False)