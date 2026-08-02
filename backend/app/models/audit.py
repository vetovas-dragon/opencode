from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="操作用户ID")
    action: Mapped[str] = mapped_column(String(50), index=True, comment="操作类型")
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="对象类型")
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="对象ID")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True, comment="详情")
    ip: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="来源IP")


class AuditLogMixin:
    """审计日志占位扩展：后续接入统一日志中间件。"""
