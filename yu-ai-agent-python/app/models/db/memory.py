"""
记忆系统数据库模型

UserMemory: 用户长期记忆（画像、关键事实、偏好）
SessionSummary: 会话摘要
"""

from datetime import datetime

from sqlalchemy import Column, Integer, BigInteger, String, Text, Float, DateTime, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserMemory(Base):
    """用户长期记忆表"""
    __tablename__ = "user_memory"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")
    memory_type = Column(String(32), nullable=False, comment="记忆类型: profile/preference/key_fact/episodic")
    content_json = Column(JSON, comment="JSON格式的记忆内容")
    content_text = Column(Text, comment="文本格式的内容（便于查询）")
    embedding_id = Column(String(64), comment="PgVector中的向量ID")
    importance_score = Column(Float, default=0.5, comment="重要性评分(0-1)")
    access_count = Column(Integer, default=0, comment="访问次数")
    last_accessed = Column(DateTime, comment="最后访问时间")
    is_deleted = Column(Boolean, default=False, comment="软删除标记")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<UserMemory(id={self.id}, user_id={self.user_id}, type={self.memory_type})>"


class SessionSummary(Base):
    """会话摘要表"""
    __tablename__ = "session_summary"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chat_id = Column(String(36), nullable=False, index=True, comment="会话ID")
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")
    summary = Column(Text, nullable=False, comment="会话摘要")
    key_topics = Column(JSON, comment="关键话题标签")
    emotion_trend = Column(String(20), comment="情感趋势")
    message_count = Column(Integer, comment="消息数量")
    is_deleted = Column(Boolean, default=False, comment="软删除标记")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")

    def __repr__(self):
        return f"<SessionSummary(id={self.id}, chat_id={self.chat_id}, user_id={self.user_id})>"
