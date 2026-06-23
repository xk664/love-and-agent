from typing import Optional, List, Any

from pydantic import BaseModel, Field


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


# ===== 外部 API 模型（会话 CRUD）=====

EMOTION_STATUS_MAP = {"single": "单身", "relationship": "恋爱", "married": "已婚"}


class ChatCreateRequest(BaseModel):
    """创建会话请求"""
    app_type: str = Field(..., description="应用类型: love_app / manus")
    emotion_status: str | None = Field(None, description="情感状态: single/relationship/married，love_app 必填")
    title: str | None = Field(None, description="会话标题，不传则自动生成")


class ChatInfo(BaseModel):
    """会话信息"""
    chat_id: str
    app_type: str
    emotion_status: str | None = None
    title: str | None = None
    create_time: str


class ChatPageData(BaseModel):
    """会话分页数据"""
    list: list[ChatInfo]
    page: int
    page_size: int
    total: int


# ===== 外部 API 模型（消息管理）=====

class MessageInfo(BaseModel):
    """消息信息"""
    id: int
    chat_id: str
    role: str
    content: str
    metadata: dict | None = None
    create_time: str


class MessagePageData(BaseModel):
    """消息分页数据"""
    list: list[MessageInfo]
    page: int
    page_size: int
    total: int