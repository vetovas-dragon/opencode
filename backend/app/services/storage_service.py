"""对象存储服务（MinIO）：上传、URL 生成、bucket 初始化。"""

import io
import uuid
from pathlib import Path

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure,
)

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_FILE_EXT = {".pdf", ".doc", ".docx", ".xlsx", ".jpg", ".jpeg", ".png"}
ALLOWED_VOICE_EXT = {".webm", ".mp3", ".ogg", ".wav"}
IMAGE_MAX_SIZE = 10 * 1024 * 1024
FILE_MAX_SIZE = 50 * 1024 * 1024
VOICE_MAX_SIZE = 5 * 1024 * 1024


def ensure_bucket() -> None:
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def public_url(object_name: str) -> str:
    scheme = "https" if settings.minio_secure else "http"
    return f"{scheme}://{settings.minio_endpoint}/{settings.minio_bucket}/{object_name}"


def upload_bytes(data: bytes, ext: str, folder: str, content_type: str | None = None) -> str:
    """上传文件对象，返回公开 URL。ext 含点号前缀。"""
    object_name = f"{folder}/{uuid.uuid4().hex}{ext}"
    client.put_object(
        settings.minio_bucket,
        object_name,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return public_url(object_name)


def upload_file(file_bytes: bytes, filename: str, user_id: int) -> str:
    """按扩展名分发到对应目录并校验大小（PRD 6.5.6 规则 2）。"""
    ext = Path(filename).suffix.lower()
    if ext in ALLOWED_IMAGE_EXT:
        if len(file_bytes) > IMAGE_MAX_SIZE:
            raise ValueError("图片大小不能超过 10MB")
        return upload_bytes(file_bytes, ext, f"user/{user_id}/images", "image/" + ext.lstrip("."))
    if ext in ALLOWED_VOICE_EXT:
        if len(file_bytes) > VOICE_MAX_SIZE:
            raise ValueError("语音文件大小不能超过 5MB")
        return upload_bytes(file_bytes, ext, f"user/{user_id}/voices", "audio/" + ext.lstrip("."))
    if ext in ALLOWED_FILE_EXT:
        if len(file_bytes) > FILE_MAX_SIZE:
            raise ValueError("文件大小不能超过 50MB")
        return upload_bytes(file_bytes, ext, f"user/{user_id}/files")
    raise ValueError(f"不支持的文件类型：{ext or '未知'}")


ensure_bucket()
