"""患者端（对应 M4、M6、M8）：档案、健康数据、用药时间轴、提醒。"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.chat import Conversation
from app.models.health import HealthData, MedicationLog, MetricType
from app.models.reminder import HealthReminder, ReminderLog
from app.models.user import PatientProfile, User
from app.schemas.health import HealthDataCreate, ReminderCreate

router = APIRouter(prefix="/patient", tags=["患者端"])

patient_required = require_roles("patient")

BP_LIMITS = {"value_primary": (40, 280), "value_secondary": (20, 200)}
BG_LIMITS = {"value_primary": (0.5, 50)}
WEIGHT_LIMITS = {"value_primary": (5, 400)}
UNIT_MAP = {MetricType.BLOOD_PRESSURE: "mmHg", MetricType.BLOOD_GLUCOSE: "mmol/L", MetricType.WEIGHT: "kg"}


def _validate_range(metric_type: MetricType, primary: float, secondary: float | None) -> bool:
    limits = {"bp": BP_LIMITS, "bg": BG_LIMITS, "weight": WEIGHT_LIMITS}.get(metric_type.value, {})
    if not limits:
        return False
    lo, hi = limits["value_primary"]
    if not (lo <= primary <= hi):
        return False
    if secondary is not None and metric_type == MetricType.BLOOD_PRESSURE:
        slo, shi = limits["value_secondary"]
        if not (slo <= secondary <= shi):
            return False
    return True


@router.get("/profile")
def my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(patient_required),
):
    """个人健康档案查询。"""
    profile = db.scalar(select(PatientProfile).where(PatientProfile.user_id == current_user.id))
    if not profile:
        raise HTTPException(status_code=404, detail="暂无档案信息，请先完善建档")
    return {
        "name": current_user.name,
        "phone": current_user.phone,
        "gender": profile.gender,
        "birth_date": profile.birth_date,
        "ethnicity": profile.ethnicity,
        "address": profile.address,
        "allergy_history": profile.allergy_history,
        "language_pref": profile.language_pref,
    }


@router.put("/profile")
def update_profile(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(patient_required),
):
    """个人健康信息维护（仅允许非关键字段自助修改）。"""
    profile = db.scalar(select(PatientProfile).where(PatientProfile.user_id == current_user.id))
    if not profile:
        raise HTTPException(status_code=404, detail="档案不存在")
    allowed = {"address", "allergy_history", "language_pref"}
    for key, value in body.items():
        if key not in allowed:
            raise HTTPException(status_code=400, detail=f"字段 {key} 不可自助修改")
        setattr(profile, key, value)
    db.commit()
    return {"message": "已更新"}


@router.post("/health-data")
def add_health_data(
    body: HealthDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(patient_required),
):
    """健康数据录入（越界校验，异常值提示）。"""
    if not _validate_range(body.metric_type, body.value_primary, body.value_secondary):
        raise HTTPException(status_code=400, detail="数值超出合理范围，请核对后重新录入")
    abnormal = _is_abnormal(body)
    row = HealthData(
        patient_id=current_user.id,
        metric_type=body.metric_type,
        value_primary=body.value_primary,
        value_secondary=body.value_secondary,
        unit=body.unit,
        measured_at=body.measured_at,
        is_abnormal=abnormal,
    )
    db.add(row)
    db.commit()
    return {"message": "已保存", "is_abnormal": abnormal}


def _is_abnormal(body: HealthDataCreate) -> bool:
    """基础异常判定（阈值可配置化，后续接入临床标准库）。"""
    if body.metric_type == MetricType.BLOOD_PRESSURE:
        return body.value_primary > 140 or (body.value_secondary or 0) > 90
    if body.metric_type == MetricType.BLOOD_GLUCOSE:
        return body.value_primary > 7.0
    return False


@router.get("/health-data")
def list_health_data(
    metric_type: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(patient_required),
):
    """健康数据可视化数据源（趋势）。"""
    q = select(HealthData).where(HealthData.patient_id == current_user.id)
    if metric_type:
        q = q.where(HealthData.metric_type == metric_type)
    rows = db.scalars(q.order_by(HealthData.measured_at)).all()
    return [
        {
            "id": r.id,
            "metric_type": r.metric_type.value,
            "value_primary": r.value_primary,
            "value_secondary": r.value_secondary,
            "unit": r.unit,
            "measured_at": r.measured_at.isoformat(),
            "is_abnormal": r.is_abnormal,
        }
        for r in rows
    ]


@router.get("/medications")
def medication_timeline(db: Session = Depends(get_db), current_user: User = Depends(patient_required)):
    """用药记录时间轴。"""
    rows = db.scalars(
        select(MedicationLog)
        .where(MedicationLog.patient_id == current_user.id)
        .order_by(MedicationLog.taken_at.desc())
    ).all()
    return [
        {
            "id": m.id,
            "medication_name": m.medication_name,
            "dosage": m.dosage,
            "taken_at": m.taken_at.isoformat(),
        }
        for m in rows
    ]


@router.get("/conversations")
def my_conversations(db: Session = Depends(get_db), current_user: User = Depends(patient_required)):
    rows = db.scalars(
        select(Conversation)
        .where(Conversation.patient_id == current_user.id)
        .order_by(Conversation.id.desc())
    ).all()
    return [
        {"id": c.id, "status": c.status.value, "created_at": c.created_at.isoformat()}
        for c in rows
    ]


@router.post("/reminders")
def create_reminder(
    body: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("doctor", "student")),
):
    """健康提醒创建（医生/医学生）。"""
    reminder = HealthReminder(
        patient_id=body.patient_id,
        creator_id=current_user.id,
        creator_role=current_user.role.value,
        reminder_type=body.reminder_type,
        content=body.content,
        detail=body.detail,
        cycle=body.cycle,
        schedule_cron=body.schedule_cron,
        start_date=body.start_date,
        end_date=body.end_date,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return {"id": reminder.id, "status": reminder.status.value}


@router.get("/reminders")
def my_reminders(db: Session = Depends(get_db), current_user: User = Depends(patient_required)):
    rows = db.scalars(
        select(HealthReminder)
        .where(HealthReminder.patient_id == current_user.id)
        .order_by(HealthReminder.id.desc())
    ).all()
    return [
        {
            "id": r.id,
            "reminder_type": r.reminder_type.value,
            "content": r.content,
            "cycle": r.cycle.value,
            "schedule_cron": r.schedule_cron,
            "status": r.status.value,
            "push_enabled": r.push_enabled,
        }
        for r in rows
    ]


@router.post("/reminders/{reminder_id}/feedback")
def feedback_reminder(
    reminder_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(patient_required),
):
    """提醒状态反馈（已完成/稍后处理）。"""
    log = db.scalar(
        select(ReminderLog)
        .where(ReminderLog.reminder_id == reminder_id, ReminderLog.patient_id == current_user.id)
        .order_by(ReminderLog.id.desc())
    )
    if not log:
        raise HTTPException(status_code=404, detail="提醒记录不存在")
    feedback = body.get("feedback")
    if feedback not in ("done", "later"):
        raise HTTPException(status_code=400, detail="反馈状态非法")
    log.feedback = feedback
    log.feedback_at = datetime.now()
    db.commit()
    return {"message": "已反馈"}
