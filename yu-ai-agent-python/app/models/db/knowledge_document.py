"""KnowledgeDocument ORM Model"""
from datetime import datetime

from sqlalchemy import BigInteger, String, Text, DateTime, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_document"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="文档所属用户ID")
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="文档标题")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="文档内容")
    file_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="markdown | pdf | txt")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="0-待处理 1-已向量化 2-处理失败")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="软删除标记")
    vector_deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="向量是否已清理")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
