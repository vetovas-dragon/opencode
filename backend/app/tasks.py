"""Celery 异步任务：健康提醒调度（M8）、统计预聚合/导出（M10）。"""

import logging
from datetime import datetime

from celery import shared_task

from app.db.session import SessionLocal
from app.services.reminder_service import dispatch_reminder, due_reminders
from app.services.stats_service import export_excel

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.dispatch_due_reminders")
def dispatch_due_reminders() -> int:
    """每分钟调度：筛选到期提醒并推送（失败自动重试 3 次由 Celery 机制保证）。"""
    db = SessionLocal()
    try:
        due = due_reminders(db)
        sent = 0
        for reminder in due:
            if dispatch_reminder(db, reminder):
                sent += 1
        logger.info("reminder dispatch: due=%s sent=%s", len(due), sent)
        return sent
    finally:
        db.close()


@shared_task(name="app.tasks.finalize_expired_conversations")
def finalize_expired_conversations() -> int:
    """每 10 分钟扫描：结束请求超 24h 的会话自动结束（PRD 6.5.6 规则 5）。"""
    from datetime import datetime, timedelta

    from sqlalchemy import select

    from app.models.chat import Conversation, ConversationStatus
    from app.services.conversation_service import maybe_auto_end

    db = SessionLocal()
    try:
        rows = db.scalars(
            select(Conversation).where(
                Conversation.status == ConversationStatus.ACTIVE,
                Conversation.end_requested_at.is_not(None),
                Conversation.end_requested_at < datetime.now() - timedelta(hours=24),
            )
        ).all()
        count = 0
        for conv in rows:
            if maybe_auto_end(db, conv):
                count += 1
        if count:
            logger.info("auto-ended conversations: %s", count)
        return count
    finally:
        db.close()


@shared_task(name="app.tasks.export_stats_excel")
def export_stats_excel(rows: list[dict], filename: str) -> str:
    """统计报表异步导出。"""
    path = export_excel(rows, filename)
    logger.info("excel exported: %s", path)
    return path
