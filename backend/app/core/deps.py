from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core import security
from app.db.session import get_db
from app.models.user import User, UserStatus

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

ROLE_DOCTOR = "doctor"
ROLE_STUDENT = "student"
ROLE_PATIENT = "patient"
ROLE_ADMIN = "admin"

ALL_ROLES = (ROLE_DOCTOR, ROLE_STUDENT, ROLE_PATIENT, ROLE_ADMIN)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证失败，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_access_token(token)
        user_id = int(payload.get("sub", ""))
    except (ValueError, TypeError):
        raise credentials_exc

    user = db.get(User, user_id)
    if not user or user.status != UserStatus.ACTIVE:
        raise credentials_exc
    return user


def require_roles(*roles: str):
    def _checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权限执行该操作（角色：{current_user.role}）",
            )
        return current_user

    return _checker
