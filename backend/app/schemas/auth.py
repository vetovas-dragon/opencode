from pydantic import BaseModel, Field, field_validator

from app.models.user import UserRole


class SendCodeRequest(BaseModel):
    phone: str | None = Field(default=None, pattern=r"^1\d{10}$")
    email: str | None = Field(default=None, max_length=100)

    @field_validator("phone", "email")
    @classmethod
    def check_contact(cls, v):
        if v is None or v.strip() == "":
            return None
        return v


class RegisterRequest(BaseModel):
    contact: str = Field(..., description="手机号或邮箱")
    code: str = Field(..., min_length=4, max_length=8)
    password: str = Field(..., min_length=6, max_length=64)
    role: UserRole
    name: str = Field(..., min_length=2, max_length=50)
    doctor: dict | None = None      # 医生执业信息
    student: dict | None = None     # 学生学籍信息
    patient: dict | None = None     # 患者健康基础信息


class LoginRequest(BaseModel):
    contact: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    status: str


class UserOut(BaseModel):
    id: int
    phone: str | None
    email: str | None
    role: str
    status: str
    name: str
    reject_reason: str | None
    created_at: object | None = None
