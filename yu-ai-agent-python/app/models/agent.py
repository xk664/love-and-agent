from typing import Optional

from pydantic import BaseModel


class AgentRunRequest(BaseModel):
    """agent任务执行请求"""
    task_id: str
    chat_id: str
    message: str
    agent_type: str = "manus"  # manus | react

class AgentCancelRequest(BaseModel):
    """agent任务取消请求"""
    task_id: str

class AgentCallbackRequest(BaseModel):
    """agent任务执行回调请求"""
    task_id: str
    status: str  # completed | failed
    result: Optional[str] = None
    steps: Optional[list] = None
class AgentRunResponse(BaseModel):
    """agent任务执行响应"""
    code: int=200 # 状态码
    message:  str="success"
    data: Optional[dict]=None

class AgentCancelResponse(BaseModel):
    """agent任务取消响应"""
    code: int=200 # 状态码
    message: str="success"
