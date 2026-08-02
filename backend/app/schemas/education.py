from datetime import datetime

from pydantic import BaseModel, Field

from app.models.record import SummaryStatus
from app.models.education import PlanStatus


class SummaryCreate(BaseModel):
    conversation_id: int
    chief_complaint: str = Field(..., max_length=100)
    present_illness: str
    past_illness: str | None = None
    consultation_process: str | None = None
    initial_diagnosis: str
    treatment_advice: str


class SummaryOut(BaseModel):
    id: int
    conversation_id: int
    student_id: int
    chief_complaint: str
    present_illness: str
    initial_diagnosis: str
    treatment_advice: str
    status: SummaryStatus
    review_comment: str | None
    reviewed_by: int | None
    created_at: datetime


class PlanCreate(BaseModel):
    title: str
    period: str
    goal: str


class PlanTodoCreate(BaseModel):
    plan_id: int
    title: str
    due_at: datetime | None = None
    priority: str = "medium"


class PlanOut(BaseModel):
    id: int
    student_id: int
    title: str
    period: str
    goal: str
    status: PlanStatus
    review_comment: str | None
    created_at: datetime


class ReviewRequest(BaseModel):
    target_id: int
    result: str = Field(..., pattern="^(pass|reject)$")
    comment: str | None = None


class ScoreRequest(BaseModel):
    student_id: int
    summary_id: int | None = None
    q_consultation: int = Field(default=0, ge=0, le=100)
    q_history: int = Field(default=0, ge=0, le=100)
    q_communication: int = Field(default=0, ge=0, le=100)
    q_summary: int = Field(default=0, ge=0, le=100)
    comment: str


class ScoreOut(BaseModel):
    id: int
    student_id: int
    total: int
    grade: str
    comment: str
    created_at: datetime
