"""文件上传（对应 M5 消息附件、M9 语音文件）：MinIO 存储。"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.deps import get_current_user
from app.models.user import User
from app.services.storage_service import upload_file

router = APIRouter(prefix="/files", tags=["文件上传"])


@router.post("/upload")
def upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """上传图片/语音/文件，返回公开 URL（图片≤10MB，文件≤50MB，语音≤5MB）。"""
    data = file.file.read()
    try:
        url = upload_file(data, file.filename or "", current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="文件上传失败，请稍后重试")
    return {"url": url}
