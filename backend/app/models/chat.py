import enum
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, SoftDeleteMixin, enum_column


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"      # 进行中
    ENDED = "ended"        # 已结束


class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    FILE = "file"
    SYSTEM = "system"


class Conversation(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, comment="患者用户ID")
    student_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True, comment="医学生用户ID")
    doctor_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True, comment="介入/直接问诊医生ID")
    status: Mapped[ConversationStatus] = mapped_column(
        enum_column(ConversationStatus), default=ConversationStatus.ACTIVE, server_default="active", comment="会话状态"
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="结束时间")
    end_requested_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="结束请求时间（24h 超时自动生效）")
    summary_triggered: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", comment="已触发总结填报")
    end_requester_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="发起结束请求的用户ID")
    end_confirm_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="确认结束的用户ID")


class Message(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(Integer, index=True, comment="会话ID")
    sender_id: Mapped[int] = mapped_column(Integer, index=True, comment="发送者用户ID")
    sender_role: Mapped[str] = mapped_column(String(20), comment="发送者角色")
    msg_type: Mapped[MessageType] = mapped_column(enum_column(MessageType), comment="消息类型")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="文本内容/文件URL/语音URL")
    translated_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="互转后的目标语言文本")
    target_audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="互转后的合成语音URL")
    status: Mapped[str] = mapped_column(String(20), default="sent", server_default="sent", comment="发送状态 sent/failed")
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="已读时间")

    __table_args__ = (Index("ix_messages_conv_time", "conversation_id", "created_at"),)
