# backend/app/services/job_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, or_
from typing import Optional
from datetime import datetime, timedelta
from app.models.job import Job
from app.core.scoring import get_tier, TIER_THRESHOLDS


def get_jobs(
    db: Session,
    page: int = 1,
    per_page: int = 50,
    tier: Optional[str] = None,
    platform: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    location: Optional[str] = None,
    has_salary: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = "final_score",
    sort_order: str = "desc",
):
    query = db.query(Job)

    # Determine score column
    score_col = Job.final_score if sort_by in ("final_score",) else Job.keyword_score

    # Filter by tier
    if tier:
        thresholds = TIER_THRESHOLDS
        if tier == "S":
            query = query.filter(score_col >= thresholds["S"])
        elif tier == "A":
            query = query.filter(score_col >= thresholds["A"], score_col < thresholds["S"])
        elif tier == "B":
            query = query.filter(score_col >= thresholds["B"], score_col < thresholds["A"])
        elif tier == "C":
            query = query.filter(score_col >= thresholds["C"], score_col < thresholds["B"])

    if platform:
        query = query.filter(Job.platform == platform)
    if min_score is not None:
        query = query.filter(score_col >= min_score)
    if max_score is not None:
        query = query.filter(score_col <= max_score)
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if has_salary:
        query = query.filter(Job.salary.isnot(None), Job.salary != "", Job.salary != "Thoa thuan")
    if search:
        query = query.filter(
            or_(
                Job.title.ilike(f"%{search}%"),
                Job.company.ilike(f"%{search}%"),
                Job.description.ilike(f"%{search}%"),
            )
        )

    # Only show scored jobs (score > 0)
    query = query.filter(score_col > 0)

    total = query.count()

    # Sort
    sort_column = getattr(Job, sort_by, Job.final_score)
    if sort_order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Paginate
    offset = (page - 1) * per_page
    jobs = query.offset(offset).limit(per_page).all()

    return jobs, total


def get_job_by_id(db: Session, job_id: str):
    return db.query(Job).filter(Job.id == job_id).first()


def get_dashboard_stats(db: Session):
    total = db.query(func.count(Job.id)).scalar()

    # Use final_score if available, else keyword_score
    has_final = db.query(func.count(Job.id)).filter(Job.final_score > -1).scalar()
    score_col = Job.final_score if has_final > 0 else Job.keyword_score

    tier_s = db.query(func.count(Job.id)).filter(score_col >= 75).scalar()
    tier_a = db.query(func.count(Job.id)).filter(score_col >= 50, score_col < 75).scalar()
    tier_b = db.query(func.count(Job.id)).filter(score_col >= 35, score_col < 50).scalar()
    tier_c = db.query(func.count(Job.id)).filter(score_col >= 1, score_col < 35).scalar()

    # By platform
    platform_counts = (
        db.query(Job.platform, func.count(Job.id))
        .group_by(Job.platform)
        .all()
    )
    by_platform = {p: c for p, c in platform_counts}

    evaluated = db.query(func.count(Job.id)).filter(Job.llm_score > -1).scalar()
    kw_scored = db.query(func.count(Job.id)).filter(Job.keyword_score > -1).scalar()
    pending = db.query(func.count(Job.id)).filter(
        Job.keyword_score >= 25, Job.llm_score == -1
    ).scalar()

    avg = db.query(func.avg(score_col)).filter(score_col > 0).scalar() or 0

    # New today
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    new_today = db.query(func.count(Job.id)).filter(Job.scraped_at >= today).scalar()

    return {
        "total_jobs": total,
        "tier_s": tier_s,
        "tier_a": tier_a,
        "tier_b": tier_b,
        "tier_c": tier_c,
        "by_platform": by_platform,
        "evaluated": evaluated,
        "pending_eval": pending,
        "avg_score": round(avg, 1),
        "new_today": new_today,
    }
