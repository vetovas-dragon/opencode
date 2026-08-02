"""WebSocket 实时通信（对应 M5 实时部分 + M9 流式语音互转）。"""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis import asyncio as aioredis
from sqlalchemy import select

from app.adapters.voice import voice_adapter
from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.chat import Conversation, Message, MessageType
from app.models.user import User
from app.services.conversation_service import persist_message

router = APIRouter()

_redis = aioredis.from_url(settings.redis_url, decode_responses=True)
ONLINE_KEY = "ws:online"
CONV_PARTICIPANTS = "ws:conv:{cid}"


class ConnectionManager:
    def __init__(self) -> None:
        self.active: dict[int, list[WebSocket]] = {}

    async def connect(self, user_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self.active.setdefault(user_id, []).append(ws)

    def disconnect(self, user_id: int, ws: WebSocket) -> None:
        if user_id in self.active:
            try:
                self.active[user_id].remove(ws)
            except ValueError:
                pass
            if not self.active[user_id]:
                del self.active[user_id]

    async def send_to_user(self, user_id: int, payload: dict) -> None:
        for ws in self.active.get(user_id, []):
            try:
                await ws.send_text(json.dumps(payload, ensure_ascii=False))
            except Exception:
                continue


manager = ConnectionManager()


async def _auth_user(token: str) -> User | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", ""))
    except (ValueError, TypeError):
        return None
    db = SessionLocal()
    try:
        return db.get(User, user_id)
    finally:
        db.close()


def _can_access(conv: Conversation, user: User) -> bool:
    return user.id in (conv.patient_id, conv.student_id, conv.doctor_id)


def _receiver_lang(db, conv: Conversation, sender_id: int) -> str:
    """接收方语言偏好：接收方为患者时按其 language_pref，否则默认汉语。"""
    from app.models.user import PatientProfile

    for pid in (conv.patient_id, conv.student_id, conv.doctor_id):
        if pid and pid != sender_id:
            if pid == conv.patient_id:
                profile = db.scalar(select(PatientProfile).where(PatientProfile.user_id == pid))
                return profile.language_pref if profile else "zh"
            return "zh"
    return "zh"


@router.websocket("/ws/chat")
async def chat_socket(ws: WebSocket, token: str):
    """聊天消息通道：入参为 JWT token。消息帧：{"type":"chat","conversation_id":1,"msg_type":"text","content":"..."}"""
    user = await _auth_user(token)
    if not user:
        await ws.close(code=4001, reason="认证失败")
        return
    await manager.connect(user.id, ws)
    await _redis.sadd(ONLINE_KEY, user.id)
    try:
        while True:
            raw = await ws.receive_text()
            frame = json.loads(raw)
            if frame.get("type") != "chat":
                continue
            conversation_id = int(frame["conversation_id"])
            db = SessionLocal()
            try:
                conv = db.get(Conversation, conversation_id)
                if not conv or not _can_access(conv, user):
                    await ws.send_text(json.dumps({"type": "error", "message": "无权访问该会话"}, ensure_ascii=False))
                    continue
                msg_type = frame.get("msg_type", "text")
                msg = persist_message(
                    db,
                    conversation_id=conversation_id,
                    sender_id=user.id,
                    sender_role=user.role.value,
                    msg_type=msg_type,
                    content=frame.get("content") or frame.get("file_url"),
                )
                # 语音消息按接收方语言偏好自动互转（PRD 6.9：发语音即得双语结果）
                if msg.msg_type == MessageType.VOICE:
                    target_lang = _receiver_lang(db, conv, user.id)
                    if target_lang != "zh":
                        stt = await voice_adapter.stt(msg.content or "", "zh")
                        result = await voice_adapter.translate(stt["text"] or "语音内容", "zh", target_lang)
                        target_audio_url = await voice_adapter.tts(result["target_text"], target_lang)
                        msg.translated_text = result["target_text"]
                        msg.target_audio_url = target_audio_url
                        db.add(msg)
                        db.commit()
                        db.refresh(msg)
                payload = {
                    "type": "message",
                    "message": {
                        "id": msg.id,
                        "conversation_id": conversation_id,
                        "sender_id": user.id,
                        "sender_role": user.role.value,
                        "msg_type": msg.msg_type.value,
                        "content": msg.content,
                        "translated_text": msg.translated_text,
                        "target_audio_url": msg.target_audio_url,
                        "created_at": msg.created_at.isoformat(),
                    },
                }
                await _redis.sadd(CONV_PARTICIPANTS.format(cid=conversation_id), *(
                    [conv.patient_id, conv.student_id, conv.doctor_id]
                ))
                for pid in (conv.patient_id, conv.student_id, conv.doctor_id):
                    if pid and pid != user.id:
                        await manager.send_to_user(pid, payload)
            finally:
                db.close()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user.id, ws)
        await _redis.srem(ONLINE_KEY, user.id)


@router.websocket("/ws/voice")
async def voice_socket(ws: WebSocket, token: str):
    """流式语音互转通道：入参为 JWT token。
    上行分片帧：{"type":"audio","chunk":"base64...","source_lang":"zh","target_lang":"yi"}
    下行：{"type":"partial","text":"..."}  {"type":"final","text":"...","target_text":"...","term_hit":n}
    """
    user = await _auth_user(token)
    if not user:
        await ws.close(code=4001, reason="认证失败")
        return
    await manager.connect(user.id, ws)
    try:
        source_lang = "zh"
        target_lang = "yi"
        collected: list[str] = []
        while True:
            raw = await ws.receive_text()
            frame = json.loads(raw)
            if frame.get("type") == "config":
                source_lang = frame.get("source_lang", "zh")
                target_lang = frame.get("target_lang", "yi")
                continue
            if frame.get("type") != "audio":
                continue
            collected.append(frame.get("chunk", ""))
            await ws.send_text(json.dumps({"type": "partial", "text": f"已接收 {len(collected)} 个音频分片"}, ensure_ascii=False))
            if frame.get("final", False):
                # Mock 阶段：直接回显；真实实现：组合音频 → STT → 翻译 → TTS
                stt = await voice_adapter.stt("stream://placeholder", source_lang)
                result = await voice_adapter.translate(stt["text"] or "语音内容", source_lang, target_lang)
                audio_url = await voice_adapter.tts(result["target_text"], target_lang)
                await ws.send_text(json.dumps({
                    "type": "final",
                    "source_text": stt["text"],
                    "target_text": result["target_text"],
                    "target_audio_url": audio_url,
                    "term_hit": result["term_hit"],
                    "confidence": stt["confidence"],
                }, ensure_ascii=False))
                collected.clear()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user.id, ws)
