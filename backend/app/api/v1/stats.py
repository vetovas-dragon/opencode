"""数据统计与可视化（对应 M10）：三维度统计、Excel 导出（异步）。"""

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.stats import StatsQuery
from app.services.stats_service import business_stats, export_excel, patient_stats, teaching_stats

router = APIRouter(prefix="/stats", tags=["数据统计与可视化"])

stats_required = require_roles("doctor", "admin")


@router.get("")
def get_stats(
    dimension: str = "business",
    start: str | None = None,
    end: str | None = None,
    student_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(stats_required),
):
    """多维度统计：business / teaching / patient。"""
    if dimension == "teaching":
        return teaching_stats(db, start, end, student_id)
    if dimension == "patient":
        return patient_stats(db, start, end)
    return business_stats(db, start, end, student_id)


@router.post("/export")
def export_stats(
    body: StatsQuery,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(stats_required),
):
    """Excel 导出（异步生成，写入 /tmp 供下载；正式版接入 MinIO 与下载中心）。"""
    if body.dimension == "teaching":
        data = teaching_stats(db, body.start, body.end, body.student_id)
        rows = [{"指标": k, "数值": v} for k, v in data.items() if not isinstance(v, dict)]
    elif body.dimension == "patient":
        data = patient_stats(db, body.start, body.end)
        rows = [{"指标": k, "数值": v} for k, v in data.items() if not isinstance(v, dict)]
    else:
        data = business_stats(db, body.start, body.end)
        rows = [{"指标": k, "数值": v} for k, v in data.items()]

    def _job():
        export_excel(rows, f"{body.dimension}_stats")

    background_tasks.add_task(_job)
    return {"message": "导出任务已提交", "row_count": len(rows)}
