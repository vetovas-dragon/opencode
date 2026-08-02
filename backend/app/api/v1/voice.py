"""多语言语音互转（对应 M9 特色需求）：双向互转、STT/TTS、医疗术语适配。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.adapters.voice import voice_adapter
from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.models.voice import VoiceTranslation, TranslationStatus
from app.schemas.stats import VoiceTranslateRequest, VoiceTranslateResponse

router = APIRouter(prefix="/voice", tags=["多语言语音互转"])

voice_required = require_roles("patient", "student", "doctor")


@router.post("/translate", response_model=VoiceTranslateResponse)
async def translate_text(
    body: VoiceTranslateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(voice_required),
):
    """文本互转接口（流式语音互转走 WebSocket /ws/voice，见 WebSocket 端点）。"""
    result = await voice_adapter.translate(body.source_text, body.source_lang, body.target_lang)
    record = VoiceTranslation(
        conversation_id=0,
        source_lang=body.source_lang,
        target_lang=body.target_lang,
        source_text=body.source_text,
        target_text=result["target_text"],
        term_hit_count=result["term_hit"],
        status=TranslationStatus.SUCCESS,
    )
    db.add(record)
    db.commit()
    db.add(AuditLog(
        user_id=current_user.id, action="voice_translate",
        target_type="voice", target_id=record.id,
    ))
    db.commit()
    return VoiceTranslateResponse(
        target_text=result["target_text"],
        source_lang=body.source_lang,
        target_lang=body.target_lang,
        term_hit=result["term_hit"],
    )
