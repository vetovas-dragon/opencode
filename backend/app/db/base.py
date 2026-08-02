from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def enum_column(enum_cls):
    """数据库枚举列：存储枚举值（小写字符串），支持字符串比较与字段扩展。"""
    return Enum(enum_cls, values_callable=lambda e: [m.value for m in e], native_enum=False)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", comment="软删除标记")
