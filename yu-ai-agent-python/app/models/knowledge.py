"""
Knowledge Base Pydantic Models
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class KnowledgeIndexRequest(BaseModel):
    """知识库文档向量化请求"""
    document_id: int
    user_id: int
    title: str
    content: str
    file_type: str  # markdown | pdf | txt


class KnowledgeIndexResponse(BaseModel):
    """知识库文档向量化响应"""
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None


class KnowledgeCallbackRequest(BaseModel):
    """回调 Java 的请求体"""
    document_id: int = Field(alias="documentId")
    status: int  # 1-已向量化 2-处理失败
    message: Optional[str] = None

    class Config:
        # 允许使用别名
        populate_by_name = True


class KnowledgeSearchRequest(BaseModel):
    """知识库检索请求"""
    query: str
    user_id: int
    top_k: Optional[int] = None
    similarity_threshold: Optional[float] = None


class KnowledgeSearchResultItem(BaseModel):
    """知识库检索结果项"""
    id: int
    content: str
    metadata: dict
    similarity: float


class KnowledgeSearchResponse(BaseModel):
    """知识库检索响应"""
    code: int = 200
    message: str = "success"
    data: List[KnowledgeSearchResultItem] = []
