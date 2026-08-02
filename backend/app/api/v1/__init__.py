"""API v1 路由聚合（对应 PRD 十大功能模块）。"""

from fastapi import APIRouter

from app.api.v1 import admin, auth, conversations, doctors, files, patients, reviews, stats, students, voice

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(admin.router)
api_router.include_router(auth.router)
api_router.include_router(files.router)
api_router.include_router(doctors.router)
api_router.include_router(students.router)
api_router.include_router(patients.router)
api_router.include_router(conversations.router)
api_router.include_router(reviews.router)
api_router.include_router(voice.router)
api_router.include_router(stats.router)
