"""数据统计服务（对应 M10）：业务/教学/患者三维度聚合，支持导出。"""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.chat import Conversation, ConversationStatus, Message
from app.models.education import ScoreRecord
from app.models.record import ConsultationSummary, SummaryStatus
from app.models.user import PatientProfile, User


def _date_range(start: str | None, end: str | None) -> tuple[datetime, datetime]:
    today = datetime.now()
    if end:
        end_dt = datetime.fromisoformat(end)
    else:
        end_dt = today
    if start:
        start_dt = datetime.fromisoformat(start)
    else:
        start_dt = end_dt - timedelta(days=30)
    return start_dt, end_dt


def business_stats(db: Session, start: str | None, end: str | None, student_id: int | None = None) -> dict:
    start_dt, end_dt = _date_range(start, end)
    q = select(Conversation).where(Conversation.created_at.between(start_dt, end_dt))
    if student_id:
        q = q.where(Conversation.student_id == student_id)
    convs = db.scalars(q).all()
    patient_ids = {c.patient_id for c in convs}
    total_messages = 0
    for c in convs:
        total_messages += db.scalar(
            select(func.count(Message.id)).where(
                Message.conversation_id == c.id, Message.msg_type != "system"
            )
        ) or 0
    return {
        "consultation_count": len(convs),
        "ended_count": sum(1 for c in convs if c.status == ConversationStatus.ENDED),
        "message_count": total_messages,
        "service_patient_count": len(patient_ids),
    }


def teaching_stats(db: Session, start: str | None, end: str | None, student_id: int | None = None) -> dict:
    start_dt, end_dt = _date_range(start, end)
    summaries = db.scalars(
        select(ConsultationSummary).where(ConsultationSummary.created_at.between(start_dt, end_dt))
    ).all()
    if student_id:
        summaries = [s for s in summaries if s.student_id == student_id]
    passed = [s for s in summaries if s.status == SummaryStatus.PASSED]
    scores = db.scalars(select(ScoreRecord)).all()
    if student_id:
        scores = [s for s in scores if s.student_id == student_id]
    grades = {"优秀": 0, "良好": 0, "合格": 0, "不合格": 0}
    for s in scores:
        grades[s.grade] = grades.get(s.grade, 0) + 1
    return {
        "summary_count": len(summaries),
        "passed_count": len(passed),
        "pass_rate": round(len(passed) / len(summaries), 4) if summaries else 0,
        "score_count": len(scores),
        "grade_distribution": grades,
        "avg_score": round(sum(s.total for s in scores) / len(scores), 1) if scores else 0,
    }


def patient_stats(db: Session, start: str | None, end: str | None) -> dict:
    start_dt, end_dt = _date_range(start, end)
    profiles = db.scalars(
        select(PatientProfile)
        .join(User, User.id == PatientProfile.user_id)
        .where(User.created_at.between(start_dt, end_dt))
    ).all()
    ethnicity: dict[str, int] = {}
    gender: dict[str, int] = {}
    for p in profiles:
        ethnicity[p.ethnicity] = ethnicity.get(p.ethnicity, 0) + 1
        gender[p.gender] = gender.get(p.gender, 0) + 1
    return {
        "patient_count": len(profiles),
        "ethnicity_distribution": ethnicity,
        "gender_distribution": gender,
    }


def export_excel(rows: list[dict], filename: str = "stats") -> str:
    """生成 Excel 报表（应通过 Celery 异步调用，返回文件 URL/路径）。"""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = filename
    if rows:
        ws.append(list(rows[0].keys()))
        for row in rows:
            ws.append(list(row.values()))
    path = f"/tmp/{filename}_{datetime.now():%Y%m%d%H%M%S}.xlsx"
    wb.save(path)
    return path
