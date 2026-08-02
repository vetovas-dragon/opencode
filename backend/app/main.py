"""应用入口：路由挂载、CORS、WebSocket、健康检查。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.api.ws.chat import router as ws_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="在线问诊教学系统 API（对应 PRD V1.1）\n\n"
    "模块覆盖：注册与角色选择(M1)/医生管理后台(M2)/医学生工作台(M3)/患者端(M4)/"
    "即时通讯(M5)/患者档案(M6)/审核流程(M7)/健康提醒(M8)/多语言语音互转(M9)/数据统计(M10)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(ws_router)


@app.get("/health", tags=["系统"])
def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}
