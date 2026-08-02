"""审核与评分业务服务（对应 M7）：标准化校验、通过/驳回、评分等级。"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.education import ReviewRecord, ReviewResult, ReviewTargetType, ScoreRecord
from app.models.record import ConsultationSummary, SummaryStatus


def validate_summary_fields(data: dict) -> list[str]:
    """审核要点标准化校验（PRD 6.7.6 规则 1）。返回缺失/不合规项。"""
    errors: list[str] = []
    if not data.get("chief_complaint") or len(data["chief_complaint"]) > 100:
        errors.append("主诉必填且不超过100字")
    if not data.get("present_illness"):
        errors.append("现病史必填")
    if not data.get("initial_diagnosis"):
        errors.append("初步判断必填")
    if not data.get("treatment_advice"):
        errors.append("诊疗建议必填")
    return errors


def review_summary(db: Session, summary: ConsultationSummary, reviewer_id: int, result: str, comment: str | None) -> None:
    if result == ReviewResult.REJECT.value and not (comment and comment.strip()):
        raise ValueError("驳回必须填写审核意见")
    summary.status = SummaryStatus.PASSED if result == ReviewResult.PASS.value else SummaryStatus.REJECTED
    summary.review_comment = comment
    summary.reviewed_by = reviewer_id
    summary.reviewed_at = str(datetime.now())
    db.add(ReviewRecord(
        target_type=ReviewTargetType.SUMMARY,
        target_id=summary.id,
        reviewer_id=reviewer_id,
        result=ReviewResult(result),
        comment=comment,
        created_by=summary.student_id,
    ))
    db.commit()


def compute_grade(total: int) -> str:
    if total >= 90:
        return "优秀"
    if total >= 80:
        return "良好"
    if total >= 60:
        return "合格"
    return "不合格"


def create_score(db: Session, *, student_id: int, reviewer_id: int, **dims) -> ScoreRecord:
    total = sum(int(v) for k, v in dims.items() if k.startswith("q_"))
    record = ScoreRecord(
        student_id=student_id,
        reviewer_id=reviewer_id,
        **{k: int(v) for k, v in dims.items() if k.startswith("q_")},
        total=total,
        grade=compute_grade(total),
        comment=dims.get("comment") or "",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
