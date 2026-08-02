from datetime import datetime

from pydantic import BaseModel, Field

from app.models.reminder import ReminderCycle, ReminderType
from app.models.health import MetricType


class HealthDataCreate(BaseModel):
    metric_type: MetricType
    value_primary: float
    value_secondary: float | None = None
    unit: str
    measured_at: datetime


class HealthDataOut(BaseModel):
    id: int
    metric_type: str
    value_primary: float
    value_secondary: float | None
    unit: str
    measured_at: datetime
    is_abnormal: bool


class MedicationOut(BaseModel):
    id: int
    medication_name: str
    dosage: str | None
    taken_at: datetime


class ReminderCreate(BaseModel):
    patient_id: int
    reminder_type: ReminderType
    content: str
    detail: str | None = None
    cycle: ReminderCycle
    schedule_cron: str = Field(..., description="cron 表达式")
    start_date: datetime | None = None
    end_date: datetime | None = None


class ReminderOut(BaseModel):
    id: int
    patient_id: int
    reminder_type: str
    content: str
    detail: str | None
    cycle: str
    schedule_cron: str
    status: str
    push_enabled: bool
    created_at: datetime
