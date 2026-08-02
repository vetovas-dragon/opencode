"""用户注册与角色选择（对应 M1）。"""

import random
import re
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from redis import Redis
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.adapters.sms import sms_adapter
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.user import (
    DoctorProfile,
    PatientProfile,
    StudentProfile,
    User,
    UserRole,
    UserStatus,
)
from app.schemas.auth import LoginRequest, RegisterRequest, SendCodeRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["认证与注册"])

CODE_TTL = 300
CODE_FREQ_SEC = 60
CODE_DAILY_LIMIT = 10


def _get_redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


@router.post("/send-code")
def send_code(body: SendCodeRequest):
    """发送验证码（手机号/邮箱）。"""
    contact = body.phone or body.email
    if not contact:
        raise HTTPException(status_code=400, detail="手机号或邮箱至少填写一项")
    r = _get_redis()
    freq_key = f"code:freq:{contact}"
    if r.exists(freq_key):
        raise HTTPException(status_code=429, detail="发送过于频繁，请稍后再试")
    day_key = f"code:day:{contact}"
    if int(r.get(day_key) or 0) >= CODE_DAILY_LIMIT:
        raise HTTPException(status_code=429, detail="今日验证码发送次数已达上限")
    code = f"{random.randint(1000, 9999)}"
    r.setex(f"code:{contact}", CODE_TTL, code)
    r.setex(freq_key, CODE_FREQ_SEC, "1")
    r.incr(day_key)
    r.expire(day_key, 86400)
    sms_adapter.send_code(contact, code)
    return {"message": "验证码已发送", "expire_seconds": CODE_TTL}


def _find_user(db: Session, contact: str) -> User | None:
    is_phone = re.fullmatch(r"1\d{10}", contact) is not None
    field = User.phone if is_phone else User.email
    return db.scalar(select(User).where(field == contact))


@router.post("/register")
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """分角色注册：差异化信息填报、角色唯一绑定、医生/医学生人工审核。"""
    r = _get_redis()
    if r.get(f"code:{body.contact}") != body.code:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")
    if _find_user(db, body.contact):
        raise HTTPException(status_code=400, detail="该手机号/邮箱已被注册")

    user = User(
        phone=body.contact if re.fullmatch(r"1\d{10}", body.contact) else None,
        email=body.contact if "@" in body.contact else None,
        password_hash=hash_password(body.password),
        role=UserRole(body.role.value),
        name=body.name,
        status=UserStatus.ACTIVE if body.role == UserRole.PATIENT else UserStatus.PENDING,
    )
    db.add(user)
    db.flush()

    if body.role == UserRole.DOCTOR:
        info = body.doctor or {}
        for field in ("license_no", "practice_scope", "organization", "title"):
            if not info.get(field):
                raise HTTPException(status_code=400, detail=f"医生执业信息缺失：{field}")
        db.add(DoctorProfile(user_id=user.id, **info))
    elif body.role == UserRole.STUDENT:
        info = body.student or {}
        for field in ("school", "major", "grade", "student_no"):
            if not info.get(field):
                raise HTTPException(status_code=400, detail=f"学籍信息缺失：{field}")
        db.add(StudentProfile(user_id=user.id, **info))
    elif body.role == UserRole.PATIENT:
        info = body.patient or {}
        for field in ("gender", "birth_date", "ethnicity"):
            if not info.get(field):
                raise HTTPException(status_code=400, detail=f"患者基础信息缺失：{field}")
        db.add(PatientProfile(user_id=user.id, language_pref=info.get("language_pref", "zh"), **{
            k: v for k, v in info.items() if k != "language_pref"
        }))
    else:
        raise HTTPException(status_code=400, detail="不支持的角色")

    db.add(AuditLog(user_id=user.id, action="register", target_type="user", target_id=user.id, detail=body.role.value))
    db.commit()
    return {
        "message": "注册成功",
        "role": body.role.value,
        "status": user.status.value,
        "need_review": user.status == UserStatus.PENDING,
    }


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """登录：校验账号密码与状态，返回令牌（注册后自动跳转对应工作台由前端路由承担）。"""
    user = _find_user(db, body.contact)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    if user.status == UserStatus.PENDING:
        raise HTTPException(status_code=403, detail="账号待审核，请等待审核通过")
    if user.status == UserStatus.REJECTED:
        raise HTTPException(status_code=403, detail=f"账号审核未通过：{user.reject_reason or '请联系管理员'}")
    if user.status == UserStatus.DISABLED:
        raise HTTPException(status_code=403, detail="账号已被停用")
    user.last_login_at = datetime.now()
    db.add(AuditLog(user_id=user.id, action="login", target_type="user", target_id=user.id))
    db.commit()
    token = create_access_token(str(user.id), user.role.value)
    return TokenResponse(access_token=token, role=user.role.value, name=user.name, status=user.status.value)


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "role": current_user.role.value,
        "phone": current_user.phone,
        "email": current_user.email,
        "status": current_user.status.value,
    }
