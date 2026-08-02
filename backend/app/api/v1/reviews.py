"""审核流程（对应 M7）：医生审核总结/计划，驳回重提，结果归档。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.chat import Conversation
from app.models.education import PlanStatus, ReviewRecord, TrainingPlan
from app.models.record import ConsultationRecord, ConsultationSummary, SummaryStatus
from app.models.user import User
from app.schemas.education import ReviewRequest
from app.services.review_service import review_summary

router = APIRouter(prefix="/reviews", tags=["审核流程"])

doctor_required = require_roles("doctor")


@router.get("/pending")
def pending_reviews(db: Session = Depends(get_db), current_user: User = Depends(doctor_required)):
    """待审核列表（问诊总结 + 实训计划）。"""
    summaries = db.scalars(
        select(ConsultationSummary).where(ConsultationSummary.status == SummaryStatus.PENDING)
    ).all()
    plans = db.scalars(
        select(TrainingPlan).where(TrainingPlan.status == PlanStatus.PENDING)
    ).all()
    return {
        "summaries": [
            {
                "id": s.id,
                "student_id": s.student_id,
                "conversation_id": s.conversation_id,
                "chief_complaint": s.chief_complaint,
                "present_illness": s.present_illness,
                "initial_diagnosis": s.initial_diagnosis,
                "treatment_advice": s.treatment_advice,
                "created_at": s.created_at.isoformat(),
            }
            for s in summaries
        ],
        "plans": [
            {"id": p.id, "student_id": p.student_id, "title": p.title, "goal": p.goal, "period": p.period}
            for p in plans
        ],
    }


@router.get("/passed")
def passed_summaries(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    """已通过总结列表（评分入口）。"""
    rows = db.scalars(
        select(ConsultationSummary)
        .where(ConsultationSummary.status == SummaryStatus.PASSED)
        .order_by(ConsultationSummary.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return [
        {
            "id": s.id,
            "student_id": s.student_id,
            "conversation_id": s.conversation_id,
            "chief_complaint": s.chief_complaint,
            "created_at": s.created_at.isoformat(),
        }
        for s in rows
    ]


@router.post("/summary")
def review_summary_endpoint(
    body: ReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    """问诊总结审核：通过/驳回（驳回必填意见）。通过后归档诊疗记录。"""
    summary = db.get(ConsultationSummary, body.target_id)
    if not summary:
        raise HTTPException(status_code=404, detail="总结不存在")
    if summary.status != SummaryStatus.PENDING:
        raise HTTPException(status_code=400, detail="该总结不在待审核状态")
    try:
        review_summary(db, summary, current_user.id, body.result, body.comment)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if summary.status == SummaryStatus.PASSED:
        conv_record = ConsultationRecord(
            patient_id=db.get(Conversation, summary.conversation_id).patient_id,
            conversation_id=summary.conversation_id,
            summary_id=summary.id,
            archived_type="reviewed",
            record_summary=f"主诉：{summary.chief_complaint}",
        )
        db.add(conv_record)
        db.commit()
    return {"message": "审核完成", "status": summary.status.value}


@router.post("/plan")
def review_plan_endpoint(
    body: ReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    """实训计划审核。"""
    plan = db.get(TrainingPlan, body.target_id)
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")
    if body.result == "reject" and not (body.comment and body.comment.strip()):
        raise HTTPException(status_code=400, detail="驳回必须填写审核意见")
    plan.status = PlanStatus.PASSED if body.result == "pass" else PlanStatus.REJECTED
    plan.review_comment = body.comment
    db.add(ReviewRecord(
        target_type="plan", target_id=plan.id, reviewer_id=current_user.id,
        result=body.result, comment=body.comment, created_by=plan.student_id,
    ))
    db.commit()
    return {"message": "审核完成", "status": plan.status.value}


@router.get("/history")
def review_history(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    """审核结果归档查询（留痕，不可修改）。"""
    rows = db.scalars(
        select(ReviewRecord)
        .order_by(ReviewRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return [
        {
            "id": r.id,
            "target_type": r.target_type.value,
            "target_id": r.target_id,
            "result": r.result.value,
            "comment": r.comment,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
