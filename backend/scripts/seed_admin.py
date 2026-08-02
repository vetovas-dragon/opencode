"""初始化种子数据：管理员账号（幂等，可重复执行）。

用法：
    PYTHONPATH=. python scripts/seed_admin.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sqlalchemy as sa

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User, UserRole, UserStatus

ADMIN_PHONE = "13900000000"
ADMIN_PASSWORD = "admin123456"


def seed() -> None:
    db = SessionLocal()
    try:
        exists = db.scalar(sa.select(User).where(User.role == UserRole.ADMIN))
        if exists:
            print(f"管理员已存在（id={exists.id}），跳过。")
            return
        admin = User(
            phone=ADMIN_PHONE,
            password_hash=hash_password(ADMIN_PASSWORD),
            role=UserRole.ADMIN,
            name="系统管理员",
            status=UserStatus.ACTIVE,
        )
        db.add(admin)
        db.commit()
        print(f"管理员创建成功：{ADMIN_PHONE} / {ADMIN_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
