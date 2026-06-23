"""Message ORM Model"""
from datetime import datetime

from sqlalchemy import BigInteger, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, comment="user | assistant | system")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True, comment="消息元数据")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="软删除标记")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
