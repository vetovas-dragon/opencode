import enum
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, SoftDeleteMixin, enum_column


class UserRole(str, enum.Enum):
    DOCTOR = "doctor"
    STUDENT = "student"
    PATIENT = "patient"
    ADMIN = "admin"


class UserStatus(str, enum.Enum):
    PENDING = "pending"      # 待审核（医生/医学生）
    ACTIVE = "active"
    REJECTED = "rejected"    # 审核驳回
    DISABLED = "disabled"    # 停用


class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, comment="手机号")
    email: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, comment="邮箱")
    password_hash: Mapped[str] = mapped_column(String(255), comment="密码哈希")
    role: Mapped[UserRole] = mapped_column(enum_column(UserRole), comment="角色（唯一绑定）")
    status: Mapped[UserStatus] = mapped_column(
        enum_column(UserStatus), default=UserStatus.PENDING, server_default="pending", comment="账号状态"
    )
    name: Mapped[str] = mapped_column(String(50), comment="姓名")
    reject_reason: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="审核驳回原因")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="最近登录时间")


class DoctorProfile(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "doctor_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, comment="用户ID")
    license_no: Mapped[str] = mapped_column(String(50), comment="执业医师证书编号")
    practice_scope: Mapped[str] = mapped_column(String(100), comment="执业范围")
    organization: Mapped[str] = mapped_column(String(200), comment="执业机构")
    title: Mapped[str] = mapped_column(String(50), comment="职称")


class StudentProfile(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, comment="用户ID")
    school: Mapped[str] = mapped_column(String(200), comment="院校")
    major: Mapped[str] = mapped_column(String(100), comment="专业")
    grade: Mapped[str] = mapped_column(String(50), comment="年级")
    student_no: Mapped[str] = mapped_column(String(50), comment="学号")
    mentor_doctor_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="带教医生用户ID")


class PatientProfile(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "patient_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, comment="用户ID")
    gender: Mapped[str] = mapped_column(String(10), comment="性别")
    birth_date: Mapped[str] = mapped_column(String(20), comment="出生日期")
    ethnicity: Mapped[str] = mapped_column(String(30), comment="民族（必填，用于语言适配）")
    address: Mapped[str | None] = mapped_column(String(300), nullable=True, comment="住址")
    allergy_history: Mapped[str | None] = mapped_column(Text, nullable=True, comment="过敏史")
    language_pref: Mapped[str] = mapped_column(String(10), default="zh", server_default="zh", comment="语言偏好 zh/yi")
