"""会话 REST 接口（对应 M5 非实时部分）：创建、列表、历史消息、未读、检索、结束。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.chat import Conversation, ConversationStatus, Message
from app.models.user import User
from app.schemas.chat import ConversationCreate, EndRequest
from app.services.conversation_service import (
    create_conversation,
    end_conversation,
    mark_conversation_read,
    maybe_auto_end,
    total_unread,
    unread_count,
)

router = APIRouter(prefix="/conversations", tags=["会话管理"])


def _participant_conv_ids(db: Session, user: User) -> list[int]:
    rows = db.scalars(
        select(Conversation.id).where(
            Conversation.is_deleted.is_(False),
            or_(
                Conversation.patient_id == user.id,
                Conversation.student_id == user.id,
                Conversation.doctor_id == user.id,
            ),
        )
    ).all()
    return list(rows)


@router.post("")
def start_conversation(
    body: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("patient", "doctor")),
):
    """发起问诊：患者发起（分配医学生）或医生直接问诊。"""
    try:
        conv = create_conversation(
            db,
            patient=current_user if current_user.role.value == "patient" else db.get(User, body.patient_id),
            doctor_direct=body.doctor_direct or current_user.role.value == "doctor",
            doctor_id=current_user.id if current_user.role.value == "doctor" else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"id": conv.id, "status": conv.status.value}


@router.get("/mine")
def my_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("patient", "student", "doctor")),
):
    """当前用户参与的全部会话（含未读数，附 24h 超时自动结束兜底）。"""
    q = select(Conversation).where(
        Conversation.is_deleted.is_(False),
        or_(
            Conversation.patient_id == current_user.id,
            Conversation.student_id == current_user.id,
            Conversation.doctor_id == current_user.id,
        ),
    )
    rows = db.scalars(q.order_by(Conversation.id.desc())).all()
    items = []
    for c in rows:
        maybe_auto_end(db, c)
        items.append({
            "id": c.id,
            "patient_id": c.patient_id,
            "student_id": c.student_id,
            "doctor_id": c.doctor_id,
            "status": c.status.value,
            "created_at": c.created_at.isoformat(),
            "ended_at": c.ended_at.isoformat() if c.ended_at else None,
            "unread_count": unread_count(db, c.id, current_user.id) if c.status == ConversationStatus.ACTIVE else 0,
        })
    return items


@router.get("/unread-total")
def unread_total(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("patient", "student", "doctor")),
):
    """全部会话未读总数（前端红点）。"""
    conv_ids = _participant_conv_ids(db, current_user)
    return {"unread_total": total_unread(db, current_user.id, conv_ids)}


@router.post("/{conversation_id}/read")
def mark_read(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("patient", "student", "doctor")),
):
    """标记会话全部已读（进入会话时调用）。"""
    conv = db.get(Conversation, conversation_id)
    if not conv or current_user.id not in (conv.patient_id, conv.student_id, conv.doctor_id):
        raise HTTPException(status_code=403, detail="无权访问该会话")
    count = mark_conversation_read(db, conversation_id, current_user.id)
    return {"message": "已读", "marked": count}


@router.get("/search")
def search_messages(
    keyword: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("patient", "student", "doctor")),
):
    """历史消息全文检索（MySQL FULLTEXT ngram；短词回退 LIKE）。"""
    conv_ids = _participant_conv_ids(db, current_user)
    if not conv_ids:
        return []
    if len(keyword.strip()) < 2:
        raise HTTPException(status_code=400, detail="关键词至少 2 个字符")
    if len(keyword) >= 2:
        stmt = (
            select(Message)
            .where(
                Message.conversation_id.in_(conv_ids),
                text("MATCH(content, translated_text) AGAINST (:kw IN NATURAL LANGUAGE MODE)"),
            )
            .order_by(Message.id.desc())
            .limit(limit)
        )
        try:
            rows = db.scalars(stmt.params(kw=keyword)).all()
        except Exception:
            rows = None
        if rows:
            return _format_messages(rows)
    rows = db.scalars(
        select(Message)
        .where(
            Message.conversation_id.in_(conv_ids),
            or_(Message.content.like(f"%{keyword}%"), Message.translated_text.like(f"%{keyword}%")),
        )
        .order_by(Message.id.desc())
        .limit(limit)
    ).all()
    return _format_messages(rows)


def _format_messages(rows) -> list[dict]:
    return [
        {
            "id": m.id,
            "conversation_id": m.conversation_id,
            "sender_id": m.sender_id,
            "sender_role": m.sender_role,
            "msg_type": m.msg_type.value,
            "content": m.content,
            "translated_text": m.translated_text,
            "created_at": m.created_at.isoformat(),
        }
        for m in rows
    ]


@router.get("/{conversation_id}/messages")
def history_messages(
    conversation_id: int,
    before_id: int | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("patient", "student", "doctor")),
):
    """历史消息持久化存储与检索（分页按 id 逆序拉取）。"""
    conv = db.get(Conversation, conversation_id)
    if not conv or current_user.id not in (conv.patient_id, conv.student_id, conv.doctor_id):
        raise HTTPException(status_code=403, detail="无权查看该会话")
    q = select(Message).where(Message.conversation_id == conversation_id)
    if before_id:
        q = q.where(Message.id < before_id)
    rows = db.scalars(q.order_by(Message.id.desc()).limit(limit)).all()
    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_role": m.sender_role,
            "msg_type": m.msg_type.value,
            "content": m.content,
            "translated_text": m.translated_text,
            "target_audio_url": m.target_audio_url,
            "created_at": m.created_at.isoformat(),
        }
        for m in reversed(rows)
    ]


@router.post("/{conversation_id}/end")
def end_consultation(
    conversation_id: int,
    body: EndRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("patient", "student")),
):
    """结束问诊（双方确认或 24h 自动生效，结束后自动触发总结填报）。"""
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    if current_user.id not in (conv.patient_id, conv.student_id):
        raise HTTPException(status_code=403, detail="无权结束该会话")
    conv = end_conversation(db, conv, current_user.id)
    return {
        "message": "会话已结束，已触发问诊总结填报流程" if conv.status.value == "ended" else "已发送结束请求，等待对方确认",
        "status": conv.status.value,
        "summary_triggered": conv.summary_triggered,
    }
