import enum
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, SoftDeleteMixin, enum_column


class ReminderType(str, enum.Enum):
    MEDICATION = "medication"    # 用药
    MEASUREMENT = "measurement"  # 测量
    FOLLOW_UP = "follow_up"      # 复诊
    LIFESTYLE = "lifestyle"      # 生活方式


class ReminderCycle(str, enum.Enum):
    ONCE = "once"        # 单次
    DAILY = "daily"      # 每日
    WEEKLY = "weekly"    # 每周
    MONTHLY = "monthly"  # 每月


class ReminderStatus(str, enum.Enum):
    ACTIVE = "active"
    ENDED = "ended"
    PAUSED = "paused"


class HealthReminder(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "health_reminders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, comment="患者用户ID")
    creator_id: Mapped[int] = mapped_column(Integer, comment="创建者用户ID")
    creator_role: Mapped[str] = mapped_column(String(20), comment="创建者角色 doctor/student")
    reminder_type: Mapped[ReminderType] = mapped_column(enum_column(ReminderType), comment="提醒类型")
    content: Mapped[str] = mapped_column(Text, comment="提醒内容")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True, comment="类型扩展信息（药品名称、用法用量、测量指标、复诊科室等）")
    cycle: Mapped[ReminderCycle] = mapped_column(enum_column(ReminderCycle), comment="周期模式")
    schedule_cron: Mapped[str] = mapped_column(String(100), comment="调度表达式（cron）")
    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="生效时间（单次为执行时间）")
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="结束时间")
    status: Mapped[ReminderStatus] = mapped_column(
        enum_column(ReminderStatus), default=ReminderStatus.ACTIVE, server_default="active", comment="状态"
    )
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", comment="推送开关")


class ReminderLog(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "reminder_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reminder_id: Mapped[int] = mapped_column(Integer, index=True, comment="提醒ID")
    patient_id: Mapped[int] = mapped_column(Integer, index=True, comment="患者用户ID")
    sent_at: Mapped[datetime] = mapped_column(DateTime, comment="发送时间")
    delivery_status: Mapped[str] = mapped_column(String(20), default="sent", comment="送达状态 sent/failed")
    feedback: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="患者反馈 done/later/none")
    feedback_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="反馈时间")
