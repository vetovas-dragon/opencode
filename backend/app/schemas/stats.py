from pydantic import BaseModel


class VoiceTranslateRequest(BaseModel):
    source_text: str
    source_lang: str = "zh"
    target_lang: str = "yi"


class VoiceTranslateResponse(BaseModel):
    target_text: str
    source_lang: str
    target_lang: str
    term_hit: int
    degraded: bool = False


class StatsQuery(BaseModel):
    dimension: str = "business"     # business / teaching / patient
    start: str | None = None
    end: str | None = None
    student_id: int | None = None
