"""医生管理后台（对应 M2）：学生管理、聊天记录查阅、评分评价、介入问诊。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.chat import Conversation, ConversationStatus, Message
from app.models.education import ScoreRecord
from app.models.record import ConsultationSummary
from app.models.user import StudentProfile, User, UserStatus
from app.schemas.education import ScoreRequest

router = APIRouter(prefix="/doctor", tags=["医生管理后台"])

doctor_required = require_roles("doctor")


@router.get("/students")
def list_students(
    keyword: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    """学生信息管理：展示名下学生 + 未认领学生（可"设为名下"认领，PRD 6.2.6 归属约束）。"""
    q = (
        select(StudentProfile, User)
        .join(User, User.id == StudentProfile.user_id)
        .where(
            User.role == "student",
            User.is_deleted.is_(False),
            or_(StudentProfile.mentor_doctor_id == current_user.id, StudentProfile.mentor_doctor_id.is_(None)),
        )
    )
    if keyword:
        q = q.where(User.name.like(f"%{keyword}%") | StudentProfile.student_no.like(f"%{keyword}%"))
    if status:
        q = q.where(User.status == UserStatus(status))
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    rows = db.execute(q.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": sp.user_id,
                "name": u.name,
                "school": sp.school,
                "major": sp.major,
                "grade": sp.grade,
                "student_no": sp.student_no,
                "status": u.status.value,
                "mentor_doctor_id": sp.mentor_doctor_id,
            }
            for sp, u in rows
        ],
    }


@router.post("/students/{student_id}/take")
def take_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    """将未认领学生设为名下学生（教学归属绑定，幂等）。"""
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == student_id))
    if not profile:
        raise HTTPException(status_code=404, detail="学生不存在")
    if profile.mentor_doctor_id not in (None, current_user.id):
        raise HTTPException(status_code=400, detail="该学生已有归属医生")
    profile.mentor_doctor_id = current_user.id
    db.add(AuditLog(
        user_id=current_user.id, action="take_student", target_type="student", target_id=student_id,
    ))
    db.commit()
    return {"message": "已设为名下学生"}


@router.post("/conversations/{conversation_id}/join")
def join_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    """介入问诊（F-108）：仅限名下学生会话或医生直接会话；介入后成为会话参与者。"""
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    if conv.student_id is not None:
        sp = db.scalar(select(StudentProfile).where(StudentProfile.user_id == conv.student_id))
        if not sp or sp.mentor_doctor_id != current_user.id:
            raise HTTPException(status_code=403, detail="仅可介入名下学生的问诊会话")
    if conv.doctor_id and conv.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="该会话已有其他医生介入")
    if conv.status == ConversationStatus.ENDED:
        raise HTTPException(status_code=400, detail="会话已结束，无法介入")
    conv.doctor_id = current_user.id
    db.add(AuditLog(
        user_id=current_user.id, action="join_conversation", target_type="conversation", target_id=conversation_id,
    ))
    db.commit()
    return {"message": "已介入问诊", "conversation_id": conversation_id}


@router.get("/students/{student_id}/stats")
def student_stats(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    """学生实训统计：问诊次数、总结通过率、评分。"""
    conv_count = db.scalar(
        select(func.count(Conversation.id)).where(Conversation.student_id == student_id)
    ) or 0
    summaries = db.scalars(
        select(ConsultationSummary).where(ConsultationSummary.student_id == student_id)
    ).all()
    passed = sum(1 for s in summaries if s.status.value == "passed")
    scores = db.scalars(select(ScoreRecord).where(ScoreRecord.student_id == student_id)).all()
    return {
        "student_id": student_id,
        "consultation_count": conv_count,
        "summary_count": len(summaries),
        "pass_rate": round(passed / len(summaries), 4) if summaries else 0,
        "score_count": len(scores),
        "avg_score": round(sum(s.total for s in scores) / len(scores), 1) if scores else 0,
    }


@router.post("/students/{student_id}/toggle")
def toggle_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    """学生启停用（二次确认由前端承担）。"""
    user = db.get(User, student_id)
    if not user or user.role.value != "student":
        raise HTTPException(status_code=404, detail="学生不存在")
    user.status = UserStatus.DISABLED if user.status != UserStatus.DISABLED else UserStatus.ACTIVE
    db.add(AuditLog(user_id=current_user.id, action="student_toggle", target_type="user", target_id=student_id))
    db.commit()
    return {"message": "操作成功", "status": user.status.value}


@router.get("/conversations")
def list_conversations(
    student_id: int | None = None,
    patient_keyword: str | None = None,
    status: str | None = None,
    start: str | None = None,
    end: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    """问诊聊天记录筛选查阅（本人介入的 + 名下学生的全部会话，全程留痕）。"""
    q = (
        select(Conversation)
        .outerjoin(StudentProfile, StudentProfile.user_id == Conversation.student_id)
        .where(
            Conversation.is_deleted.is_(False),
            or_(
                Conversation.doctor_id == current_user.id,
                StudentProfile.mentor_doctor_id == current_user.id,
            ),
        )
    )
    if student_id:
        q = q.where(Conversation.student_id == student_id)
    if status:
        q = q.where(Conversation.status == status)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    convs = db.scalars(q.order_by(Conversation.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": c.id,
                "patient_id": c.patient_id,
                "student_id": c.student_id,
                "doctor_id": c.doctor_id,
                "status": c.status.value,
                "created_at": c.created_at.isoformat(),
                "ended_at": c.ended_at.isoformat() if c.ended_at else None,
            }
            for c in convs
        ],
    }


@router.put("/patients/{patient_id}/profile")
def update_patient_profile(
    patient_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    """医患协同维护档案（F-503）：医生更新患者基础非临床字段。"""
    from app.models.user import PatientProfile

    profile = db.scalar(select(PatientProfile).where(PatientProfile.user_id == patient_id))
    if not profile:
        raise HTTPException(status_code=404, detail="患者档案不存在")
    if "address" in body:
        profile.address = body["address"]
    if "allergy_history" in body:
        profile.allergy_history = body["allergy_history"]
    db.add(AuditLog(
        user_id=current_user.id, action="update_patient_profile",
        target_type="patient", target_id=patient_id,
    ))
    db.commit()
    return {"message": "档案已更新"}


@router.get("/conversations/{conversation_id}/messages")
def conversation_messages(
    conversation_id: int,
    page: int = 1,
    page_size: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    """查看指定会话的完整聊天记录。"""
    msgs = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    db.add(AuditLog(
        user_id=current_user.id, action="view_messages",
        target_type="conversation", target_id=conversation_id,
    ))
    db.commit()
    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_role": m.sender_role,
            "msg_type": m.msg_type.value,
            "content": m.content,
            "translated_text": m.translated_text,
            "created_at": m.created_at.isoformat(),
        }
        for m in reversed(msgs)
    ]


@router.post("/scores")
def create_score(
    body: ScoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    """学生实训成绩评价（百分制四维 + 等级 + 评语）。"""
    from app.services.review_service import create_score

    record = create_score(
        db,
        student_id=body.student_id,
        reviewer_id=current_user.id,
        summary_id=body.summary_id,
        q_consultation=body.q_consultation,
        q_history=body.q_history,
        q_communication=body.q_communication,
        q_summary=body.q_summary,
        comment=body.comment,
    )
    db.add(AuditLog(
        user_id=current_user.id, action="score", target_type="student",
        target_id=body.student_id, detail=f"total={record.total}",
    ))
    db.commit()
    return {"id": record.id, "total": record.total, "grade": record.grade}


@router.get("/students/{student_id}/scores")
def student_scores(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    rows = db.scalars(select(ScoreRecord).where(ScoreRecord.student_id == student_id)).all()
    return [
        {"id": s.id, "total": s.total, "grade": s.grade, "comment": s.comment, "created_at": s.created_at.isoformat()}
        for s in rows
    ]
