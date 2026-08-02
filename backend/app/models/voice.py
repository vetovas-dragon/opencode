import enum

from sqlalchemy import String, Integer, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, SoftDeleteMixin, enum_column


class TranslationStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    DEGRADED = "degraded"    # 降级（原始语音直发）


class VoiceTranslation(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "voice_translations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True, comment="关联消息ID")
    conversation_id: Mapped[int] = mapped_column(Integer, index=True, comment="会话ID")
    source_lang: Mapped[str] = mapped_column(String(10), comment="源语言 zh/yi")
    target_lang: Mapped[str] = mapped_column(String(10), comment="目标语言 zh/yi")
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="源语言文本（STT 结果）")
    target_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="目标语言文本（翻译结果）")
    source_audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="源语音URL")
    target_audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="合成语音URL（TTS）")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True, comment="识别置信度")
    term_hit_count: Mapped[int] = mapped_column(Integer, default=0, comment="医疗术语词典命中数")
    status: Mapped[TranslationStatus] = mapped_column(
        enum_column(TranslationStatus), default=TranslationStatus.SUCCESS, server_default="success", comment="转换状态"
    )
    error_msg: Mapped[str | None] = mapped_column(String(300), nullable=True, comment="失败原因")
