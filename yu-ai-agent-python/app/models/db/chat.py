"""Chat ORM Model"""
from datetime import datetime

from sqlalchemy import BigInteger, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Chat(Base):
    __tablename__ = "chat"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    app_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="love_app | manus")
    emotion_status: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="single | relationship | married")
    friend_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="关联的数字朋友ID")
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_message_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="软删除标记")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
