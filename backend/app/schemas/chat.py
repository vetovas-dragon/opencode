from datetime import datetime

from pydantic import BaseModel, Field

from app.models.chat import MessageType
from app.models.user import UserRole


class ConversationCreate(BaseModel):
    patient_id: int | None = Field(default=None, description="默认取当前登录患者")
    doctor_direct: bool = Field(default=False, description="医生直接问诊（跳过医学生）")
    doctor_id: int | None = Field(default=None, description="指定医生（医生直连问诊时）")


class ConversationOut(BaseModel):
    id: int
    patient_id: int
    student_id: int | None
    doctor_id: int | None
    status: str
    created_at: datetime
    ended_at: datetime | None
    patient_name: str | None = None
    student_name: str | None = None
    doctor_name: str | None = None
    unread_count: int = 0


class MessageCreate(BaseModel):
    conversation_id: int
    msg_type: MessageType = MessageType.TEXT
    content: str | None = None
    file_url: str | None = None


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    sender_role: str
    msg_type: str
    content: str | None
    translated_text: str | None
    target_audio_url: str | None
    status: str
    created_at: datetime


class EndRequest(BaseModel):
    conversation_id: int


class ConversationSearch(BaseModel):
    student_id: int | None = None
    patient_keyword: str | None = None
    status: str | None = None
    start: str | None = None
    end: str | None = None
