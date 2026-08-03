"""医学生工作台（对应 M3）：实训计划、待办、问诊总结、实训全程记录。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.chat import Conversation
from app.models.education import PlanStatus, PlanTodo, ScoreRecord, TodoStatus, TrainingPlan
from app.models.health import HealthData
from app.models.record import ConsultationSummary, SummaryStatus
from app.models.user import PatientProfile, User
from app.schemas.education import PlanCreate, PlanTodoCreate, SummaryCreate

router = APIRouter(prefix="/student", tags=["医学生工作台"])

student_required = require_roles("student")


@router.get("/conversations")
def my_conversations(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """我的问诊会话列表。"""
    q = select(Conversation).where(Conversation.student_id == current_user.id)
    if status:
        q = q.where(Conversation.status == status)
    convs = db.scalars(q.order_by(Conversation.id.desc())).all()
    return [
        {
            "id": c.id,
            "patient_id": c.patient_id,
            "status": c.status.value,
            "created_at": c.created_at.isoformat(),
            "summary_triggered": c.summary_triggered,
        }
        for c in convs
    ]


@router.get("/conversations/{conversation_id}/patient-card")
def patient_card(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """患者档案悬浮卡片（问诊中最小必要信息，对应 PRD 6.3.6 规则 1）。"""
    conv = db.get(Conversation, conversation_id)
    if not conv or conv.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看该会话")
    patient = db.get(User, conv.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    profile = db.scalar(select(PatientProfile).where(PatientProfile.user_id == conv.patient_id))
    health = db.scalars(
        select(HealthData)
        .where(HealthData.patient_id == conv.patient_id)
        .order_by(HealthData.measured_at.desc())
        .limit(5)
    ).all()
    return {
        "name": patient.name,
        "phone": patient.phone,
        "gender": profile.gender if profile else None,
        "birth_date": profile.birth_date if profile else None,
        "ethnicity": profile.ethnicity if profile else None,
        "address": profile.address if profile else None,
        "allergy_history": profile.allergy_history if profile else None,
        "last_activity": patient.last_login_at.isoformat() if patient.last_login_at else None,
        "recent_health": [
            {
                "metric_type": h.metric_type.value,
                "value_primary": h.value_primary,
                "value_secondary": h.value_secondary,
                "unit": h.unit,
                "measured_at": h.measured_at.isoformat(),
                "is_abnormal": h.is_abnormal,
            }
            for h in health
        ],
    }


@router.post("/plans")
def create_plan(
    body: PlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    plan = TrainingPlan(
        student_id=current_user.id, title=body.title, period=body.period, goal=body.goal
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return {"id": plan.id, "status": plan.status.value}


@router.get("/plans")
def list_plans(db: Session = Depends(get_db), current_user: User = Depends(student_required)):
    rows = db.scalars(
        select(TrainingPlan)
        .where(TrainingPlan.student_id == current_user.id)
        .order_by(TrainingPlan.id.desc())
    ).all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "period": p.period,
            "goal": p.goal,
            "status": p.status.value,
            "review_comment": p.review_comment,
        }
        for p in rows
    ]


@router.post("/plans/{plan_id}/submit")
def submit_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """提交实训计划进入审核流程（M7 联动）。"""
    plan = db.get(TrainingPlan, plan_id)
    if not plan or plan.student_id != current_user.id:
        raise HTTPException(status_code=404, detail="计划不存在")
    if plan.status == PlanStatus.PASSED:
        raise HTTPException(status_code=400, detail="已通过的计划不可重复提交")
    plan.status = PlanStatus.PENDING
    db.commit()
    return {"message": "已提交审核", "status": plan.status.value}


@router.post("/todos")
def create_todo(
    body: PlanTodoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    todo = PlanTodo(
        plan_id=body.plan_id, student_id=current_user.id,
        title=body.title, due_at=body.due_at, priority=body.priority,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return {"id": todo.id, "status": todo.status.value}


@router.get("/todos")
def list_todos(db: Session = Depends(get_db), current_user: User = Depends(student_required)):
    rows = db.scalars(
        select(PlanTodo).where(PlanTodo.student_id == current_user.id).order_by(PlanTodo.due_at)
    ).all()
    return [
        {"id": t.id, "plan_id": t.plan_id, "title": t.title, "due_at": t.due_at.isoformat() if t.due_at else None,
         "priority": t.priority, "status": t.status.value}
        for t in rows
    ]


@router.post("/todos/{todo_id}/toggle")
def toggle_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    todo = db.get(PlanTodo, todo_id)
    if not todo or todo.student_id != current_user.id:
        raise HTTPException(status_code=404, detail="待办不存在")
    todo.status = TodoStatus.DONE if todo.status != TodoStatus.DONE else TodoStatus.PENDING
    db.commit()
    return {"message": "操作成功", "status": todo.status.value}


@router.post("/summaries")
def submit_summary(
    body: SummaryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """问诊总结编辑提交：标准化校验 → 待审核（M7 联动）。"""
    from app.services.review_service import validate_summary_fields

    errors = validate_summary_fields(body.model_dump())
    if errors:
        raise HTTPException(status_code=400, detail="；".join(errors))
    conv = db.get(Conversation, body.conversation_id)
    if not conv or conv.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权填写该会话总结")
    existing = db.scalar(
        select(ConsultationSummary).where(ConsultationSummary.conversation_id == body.conversation_id)
    )
    if existing:
        if existing.status in (SummaryStatus.PENDING, SummaryStatus.PASSED):
            raise HTTPException(status_code=400, detail="总结已提交，不可重复提交")
        for field, value in body.model_dump(exclude={"conversation_id"}).items():
            setattr(existing, field, value)
        existing.status = SummaryStatus.PENDING
        db.commit()
        return {"id": existing.id, "status": existing.status.value}
    summary = ConsultationSummary(student_id=current_user.id, status=SummaryStatus.PENDING, **body.model_dump())
    db.add(summary)
    conv.summary_triggered = True
    db.commit()
    db.refresh(summary)
    return {"id": summary.id, "status": summary.status.value}


@router.get("/summaries")
def my_summaries(db: Session = Depends(get_db), current_user: User = Depends(student_required)):
    rows = db.scalars(
        select(ConsultationSummary)
        .where(ConsultationSummary.student_id == current_user.id)
        .order_by(ConsultationSummary.id.desc())
    ).all()
    return [
        {
            "id": s.id,
            "conversation_id": s.conversation_id,
            "chief_complaint": s.chief_complaint,
            "present_illness": s.present_illness,
            "past_illness": s.past_illness,
            "consultation_process": s.consultation_process,
            "initial_diagnosis": s.initial_diagnosis,
            "treatment_advice": s.treatment_advice,
            "status": s.status.value,
            "review_comment": s.review_comment,
        }
        for s in rows
    ]


@router.get("/records")
def my_training_records(db: Session = Depends(get_db), current_user: User = Depends(student_required)):
    """问诊实训全程记录（会话+总结+审核+评分，F-205）。"""
    convs = db.scalars(
        select(Conversation).where(Conversation.student_id == current_user.id).order_by(Conversation.id.desc())
    ).all()
    summaries = {
        s.conversation_id: s
        for s in db.scalars(
            select(ConsultationSummary).where(ConsultationSummary.student_id == current_user.id)
        ).all()
    }
    scores = db.scalars(select(ScoreRecord).where(ScoreRecord.student_id == current_user.id)).all()
    score_by_summary = {s.summary_id: s for s in scores}
    items = []
    for c in convs:
        summary = summaries.get(c.id)
        score = score_by_summary.get(summary.id) if summary else None
        items.append(
            {
                "conversation_id": c.id,
                "status": c.status.value,
                "created_at": c.created_at.isoformat(),
                "summary": {
                    "id": summary.id,
                    "status": summary.status.value,
                    "review_comment": summary.review_comment,
                    "updated_at": summary.updated_at.isoformat() if summary.updated_at else None,
                }
                if summary
                else None,
                "score": {
                    "total": score.total,
                    "grade": score.grade,
                    "comment": score.comment,
                    "created_at": score.created_at.isoformat(),
                }
                if score
                else None,
            }
        )
    return items
