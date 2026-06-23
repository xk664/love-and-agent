"""AgentTask ORM Model"""
from datetime import datetime

from sqlalchemy import BigInteger, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentTask(Base):
    __tablename__ = "agent_task"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    chat_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True, comment="关联会话ID")
    message: Mapped[str] = mapped_column(Text, nullable=False, comment="任务描述")
    status: Mapped[str] = mapped_column(String(20), default="pending", comment="pending|running|completed|failed|cancelled")
    result: Mapped[str | None] = mapped_column(Text, nullable=True, comment="任务最终结果")
    steps: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="执行步骤详情")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="软删除标记")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
