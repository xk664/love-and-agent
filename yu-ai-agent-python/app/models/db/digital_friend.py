"""DigitalFriend ORM Model"""
from datetime import datetime

from sqlalchemy import BigInteger, String, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DigitalFriend(Base):
    __tablename__ = "digital_friend"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="创建者用户ID")
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="朋友昵称")
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="头像URL")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="用户对朋友的一句话描述")
    source_materials: Mapped[str | None] = mapped_column(Text, nullable=True, comment="用户上传的原始素材（JSON格式）")
    calibration_questions: Mapped[str | None] = mapped_column(Text, nullable=True, comment="校准问题列表（JSON格式）")
    calibration_answers: Mapped[str | None] = mapped_column(Text, nullable=True, comment="校准回答列表（JSON格式）")
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True, comment="LLM根据素材+校准回答生成的完整系统提示词")
    status: Mapped[str] = mapped_column(String(20), default="draft", comment="draft/processing/calibrating/ready/failed")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="软删除标记")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
