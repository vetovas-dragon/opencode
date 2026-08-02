from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: T | None = None


class PageResult(BaseModel, Generic[T]):
    total: int
    page: int
    page_size: int
    items: list[T]


class PageQuery(BaseModel):
    page: int = 1
    page_size: int = 20


class AuditCreate(BaseModel):
    action: str
    target_type: str | None = None
    target_id: int | None = None
    detail: str | None = None
