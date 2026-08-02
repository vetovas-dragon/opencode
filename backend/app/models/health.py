import enum
from datetime import datetime

from sqlalchemy import String, Integer, Float, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, SoftDeleteMixin, enum_column


class MetricType(str, enum.Enum):
    BLOOD_PRESSURE = "bp"   # 血压
    BLOOD_GLUCOSE = "bg"    # 血糖
    WEIGHT = "weight"       # 体重


class HealthData(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "health_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, comment="患者用户ID")
    metric_type: Mapped[MetricType] = mapped_column(enum_column(MetricType), comment="指标类型")
    value_primary: Mapped[float] = mapped_column(Float, comment="主值（收缩压/血糖值/体重）")
    value_secondary: Mapped[float | None] = mapped_column(Float, nullable=True, comment="次值（舒张压）")
    unit: Mapped[str] = mapped_column(String(20), comment="单位")
    measured_at: Mapped[datetime] = mapped_column(DateTime, comment="测量时间")
    is_abnormal: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", comment="是否超出正常范围")
    source: Mapped[str] = mapped_column(String(20), default="patient", comment="来源 patient/student/doctor")


class MedicationLog(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "medication_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True, comment="患者用户ID")
    medication_name: Mapped[str] = mapped_column(String(100), comment="药品名称")
    dosage: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="用量")
    taken_at: Mapped[datetime] = mapped_column(DateTime, comment="服用时间（用药时间轴）")
