"""Celery 应用（对应 9.1：异步任务统一承载）。"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "otc",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)

celery_app.conf.update(
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_time_limit=300,
    beat_schedule={
        "dispatch-due-reminders-every-minute": {
            "task": "app.tasks.dispatch_due_reminders",
            "schedule": 60.0,
        },
        "finalize-expired-conversations-every-10-min": {
            "task": "app.tasks.finalize_expired_conversations",
            "schedule": 600.0,
        },
    },
)
