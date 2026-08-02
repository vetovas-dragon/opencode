import enum

from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, SoftDeleteMixin, enum_column


class HistoryType(str, enum.Enum):
    FAMILY = "family"      # 家族史
    ALLERGY = "allergy"    # 过敏史
    PAST = "past"          # 既往史


class MedicalHistory(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "medical_histories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, comment="患者用户ID")
    history_type: Mapped[HistoryType] = mapped_column(enum_column(HistoryType), comment="病史类型")
    content: Mapped[str] = mapped_column(Text, comment="病史内容")
    source_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="来源用户（协同维护）")
    source_role: Mapped[str] = mapped_column(String(20), default="patient", comment="来源角色")
    version: Mapped[int] = mapped_column(Integer, default=1, comment="版本号（溯源）")


class SummaryStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"     # 待审核
    PASSED = "passed"       # 已通过
    REJECTED = "rejected"   # 已驳回


class ConsultationSummary(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "consultation_summaries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, comment="会话ID")
    student_id: Mapped[int] = mapped_column(Integer, index=True, comment="医学生用户ID")
    chief_complaint: Mapped[str] = mapped_column(String(200), comment="主诉（≤100字）")
    present_illness: Mapped[str] = mapped_column(Text, comment="现病史")
    past_illness: Mapped[str | None] = mapped_column(Text, nullable=True, comment="既往史")
    consultation_process: Mapped[str | None] = mapped_column(Text, nullable=True, comment="问诊过程")
    initial_diagnosis: Mapped[str] = mapped_column(String(300), comment="初步判断")
    treatment_advice: Mapped[str] = mapped_column(Text, comment="诊疗建议")
    status: Mapped[SummaryStatus] = mapped_column(
        enum_column(SummaryStatus), default=SummaryStatus.DRAFT, server_default="draft", comment="审核状态"
    )
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True, comment="审核意见")
    reviewed_by: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="审核医生ID")
    reviewed_at: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="审核时间")


class ConsultationRecord(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "consultation_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, comment="患者用户ID")
    conversation_id: Mapped[int] = mapped_column(Integer, index=True, comment="会话ID")
    summary_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="问诊总结ID（归档来源）")
    archived_type: Mapped[str] = mapped_column(String(20), default="reviewed", comment="归档类型 reviewed/awaiting")
    record_summary: Mapped[str | None] = mapped_column(Text, nullable=True, comment="归档摘要")
