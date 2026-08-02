"""健康提醒调度服务（对应 M8）：cron 解析、到期触发、补偿调度。"""

import logging
from datetime import datetime

from croniter import croniter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.push import push_adapter
from app.models.reminder import HealthReminder, ReminderLog, ReminderStatus

logger = logging.getLogger(__name__)


def due_reminders(db: Session, now: datetime | None = None) -> list[HealthReminder]:
    """筛选到期的有效提醒（基于 cron 表达式逐条解析，按分钟对齐）。"""
    now = now or datetime.now()
    reminders = db.scalars(
        select(HealthReminder).where(HealthReminder.status == ReminderStatus.ACTIVE)
    ).all()
    due: list[HealthReminder] = []
    for r in reminders:
        try:
            itr = croniter(r.schedule_cron, now)
            prev = itr.get_prev(datetime)
            if (now - prev).total_seconds() <= 60:
                due.append(r)
        except Exception as exc:  # cron 非法时跳过并告警
            logger.warning("提醒 %s cron 非法: %s", r.id, exc)
    return due


def dispatch_reminder(db: Session, reminder: HealthReminder) -> bool:
    """向患者推送提醒并记录日志。"""
    from app.models.user import User

    patient = db.get(User, reminder.patient_id)
    if not patient or not reminder.push_enabled:
        return False
    ok = await_push(reminder)
    db.add(ReminderLog(
        reminder_id=reminder.id,
        patient_id=reminder.patient_id,
        sent_at=datetime.now(),
        delivery_status="sent" if ok else "failed",
    ))
    db.commit()
    return ok


def await_push(reminder: HealthReminder) -> bool:
    """推送适配调用（同步包装，真实实现走 push_adapter）。"""
    try:
        return push_adapter.push(
            reminder.patient_id,
            title=f"{reminder.reminder_type}提醒",
            body=reminder.content,
        )
    except Exception:
        return False
