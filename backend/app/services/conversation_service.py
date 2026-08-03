"""会话业务服务（对应 M5）：创建、结束、消息持久化、未读、超时自动结束。"""

from datetime import datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.chat import Conversation, ConversationStatus, Message
from app.models.user import User

END_AUTO_AFTER_HOURS = 24


def create_conversation(
    db: Session,
    patient: User,
    doctor_direct: bool = False,
    doctor_id: int | None = None,
) -> Conversation:
    if doctor_direct:
        from app.models.user import DoctorProfile, UserRole, UserStatus

        if doctor_id:
            doctor = db.get(User, doctor_id)
            if not doctor or doctor.role.value != "doctor" or doctor.status != UserStatus.ACTIVE:
                raise ValueError("所选医生不可用，请稍后再试")
        else:
            row = db.execute(
                select(User.id)
                .join(DoctorProfile, DoctorProfile.user_id == User.id)
                .where(User.role == UserRole.DOCTOR, User.status == UserStatus.ACTIVE)
                .order_by(User.id)
            ).first()
            if row is None:
                raise ValueError("当前无可用医生，请稍后再试")
            doctor_id = row[0]
        conv = Conversation(patient_id=patient.id, doctor_id=doctor_id)
    else:
        # 分配策略：优先负载最少（进行中会话数最少）的在岗医学生；后续可扩展排班策略
        from app.models.chat import ConversationStatus
        from app.models.user import StudentProfile, UserRole, UserStatus

        stmt = (
            select(
                StudentProfile.user_id,
                select(func.count(Conversation.id))
                .where(
                    Conversation.student_id == StudentProfile.user_id,
                    Conversation.status == ConversationStatus.ACTIVE,
                )
                .scalar_subquery().label("active_count"),
            )
            .join(User, User.id == StudentProfile.user_id)
            .where(User.role == UserRole.STUDENT, User.status == UserStatus.ACTIVE)
            .order_by("active_count", StudentProfile.id)
        )
        row = db.execute(stmt).first()
        if row is None:
            raise ValueError("当前无可用接诊医学生，请稍后再试")
        conv = Conversation(patient_id=patient.id, student_id=row[0])
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def end_conversation(db: Session, conv: Conversation, requester_id: int) -> Conversation:
    """结束问诊：双方确认，或对方 24h 未响应自动生效（PRD 6.5.6 规则 5）。"""
    if conv.status == ConversationStatus.ENDED:
        return conv
    if conv.end_requester_id is None:
        conv.end_requester_id = requester_id
        conv.end_requested_at = datetime.now()
        db.commit()
        db.refresh(conv)
        return conv
    if conv.end_requester_id == requester_id:
        return conv
    conv.status = ConversationStatus.ENDED
    conv.ended_at = datetime.now()
    conv.end_confirm_id = requester_id
    conv.summary_triggered = True
    db.commit()
    db.refresh(conv)
    return conv


def maybe_auto_end(db: Session, conv: Conversation) -> bool:
    """懒过期：结束请求发出超过 24h 自动结束（查询链路上兜底执行）。"""
    if conv.status != ConversationStatus.ACTIVE or not conv.end_requested_at:
        return False
    if datetime.now() - conv.end_requested_at >= timedelta(hours=END_AUTO_AFTER_HOURS):
        conv.status = ConversationStatus.ENDED
        conv.ended_at = datetime.now()
        conv.summary_triggered = True
        db.commit()
        return True
    return False


def unread_count(db: Session, conversation_id: int, user_id: int) -> int:
    return db.scalar(
        select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id,
            Message.sender_id != user_id,
            Message.read_at.is_(None),
        )
    ) or 0


def total_unread(db: Session, user_id: int, conversation_ids: list[int]) -> int:
    if not conversation_ids:
        return 0
    return db.scalar(
        select(func.count(Message.id)).where(
            Message.conversation_id.in_(conversation_ids),
            Message.sender_id != user_id,
            Message.read_at.is_(None),
        )
    ) or 0


def mark_conversation_read(db: Session, conversation_id: int, user_id: int) -> int:
    """将该会话中对方发来的未读消息置为已读，返回更新条数。"""
    result = db.execute(
        update(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.sender_id != user_id,
            Message.read_at.is_(None),
        )
        .values(read_at=datetime.now())
    )
    db.commit()
    return result.rowcount or 0


def persist_message(
    db: Session,
    *,
    conversation_id: int,
    sender_id: int,
    sender_role: str,
    msg_type: str,
    content: str | None,
    translated_text: str | None = None,
    target_audio_url: str | None = None,
) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        sender_role=sender_role,
        msg_type=msg_type,
        content=content,
        translated_text=translated_text,
        target_audio_url=target_audio_url,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
