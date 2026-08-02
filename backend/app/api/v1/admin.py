"""管理员审核（对应 M1）：医生/医学生身份人工审核。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.user import User, UserStatus

router = APIRouter(prefix="/admin", tags=["管理员审核"])

admin_required = require_roles("admin")


class ReviewBody(BaseModel):
    user_id: int
    result: str  # approve / reject
    reason: str | None = None


@router.get("/pending-users")
def pending_users(db: Session = Depends(get_db), current_user: User = Depends(admin_required)):
    rows = db.scalars(
        select(User).where(User.status == UserStatus.PENDING).order_by(User.id)
    ).all()
    return [
        {"id": u.id, "name": u.name, "role": u.role.value, "phone": u.phone, "email": u.email,
         "created_at": u.created_at.isoformat()}
        for u in rows
    ]


@router.post("/users/review")
def review_user(
    body: ReviewBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    user = db.get(User, body.user_id)
    if not user or user.status != UserStatus.PENDING:
        raise HTTPException(status_code=400, detail="该用户不在待审核状态")
    if body.result == "approve":
        user.status = UserStatus.ACTIVE
    elif body.result == "reject":
        if not (body.reason and body.reason.strip()):
            raise HTTPException(status_code=400, detail="驳回必须填写原因")
        user.status = UserStatus.REJECTED
        user.reject_reason = body.reason
    else:
        raise HTTPException(status_code=400, detail="审核结果非法")
    db.add(AuditLog(
        user_id=current_user.id, action="review_user",
        target_type="user", target_id=user.id, detail=body.result,
    ))
    db.commit()
    return {"message": "审核完成", "status": user.status.value}
