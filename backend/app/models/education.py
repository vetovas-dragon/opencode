import enum
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, SoftDeleteMixin, enum_column


class PlanStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PASSED = "passed"
    REJECTED = "rejected"


class TrainingPlan(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "training_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, index=True, comment="医学生用户ID")
    title: Mapped[str] = mapped_column(String(200), comment="计划名称")
    period: Mapped[str] = mapped_column(String(50), comment="计划周期")
    goal: Mapped[str] = mapped_column(Text, comment="目标说明")
    status: Mapped[PlanStatus] = mapped_column(
        enum_column(PlanStatus), default=PlanStatus.DRAFT, server_default="draft", comment="审核状态"
    )
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True, comment="审核意见")


class TodoStatus(str, enum.Enum):
    PENDING = "pending"
    DONE = "done"
    OVERDUE = "overdue"
    DEFERRED = "deferred"


class PlanTodo(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "plan_todos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(Integer, index=True, comment="计划ID")
    student_id: Mapped[int] = mapped_column(Integer, index=True, comment="医学生用户ID")
    title: Mapped[str] = mapped_column(String(200), comment="待办标题")
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="截止时间")
    priority: Mapped[str] = mapped_column(String(10), default="medium", comment="优先级 high/medium/low")
    status: Mapped[TodoStatus] = mapped_column(
        enum_column(TodoStatus), default=TodoStatus.PENDING, server_default="pending", comment="状态"
    )


class ReviewTargetType(str, enum.Enum):
    SUMMARY = "summary"
    PLAN = "plan"


class ReviewResult(str, enum.Enum):
    PASS = "pass"
    REJECT = "reject"


class ReviewRecord(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "review_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_type: Mapped[ReviewTargetType] = mapped_column(enum_column(ReviewTargetType), comment="审核对象类型")
    target_id: Mapped[int] = mapped_column(Integer, index=True, comment="审核对象ID")
    reviewer_id: Mapped[int] = mapped_column(Integer, comment="审核医生ID")
    result: Mapped[ReviewResult] = mapped_column(enum_column(ReviewResult), comment="审核结果")
    comment: Mapped[str | None] = mapped_column(Text, nullable=True, comment="审核意见（驳回必填）")
    created_by: Mapped[int] = mapped_column(Integer, comment="提交人ID")


class ScoreRecord(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "score_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, index=True, comment="医学生用户ID")
    summary_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="关联总结ID")
    reviewer_id: Mapped[int] = mapped_column(Integer, comment="评分医生ID")
    q_consultation: Mapped[int] = mapped_column(Integer, default=0, comment="问诊规范性得分")
    q_history: Mapped[int] = mapped_column(Integer, default=0, comment="病史采集完整性得分")
    q_communication: Mapped[int] = mapped_column(Integer, default=0, comment="沟通能力得分")
    q_summary: Mapped[int] = mapped_column(Integer, default=0, comment="总结质量得分")
    total: Mapped[int] = mapped_column(Integer, comment="总分（百分制）")
    grade: Mapped[str] = mapped_column(String(10), comment="等级 优秀/良好/合格/不合格")
    comment: Mapped[str] = mapped_column(Text, comment="评语（必填）")
