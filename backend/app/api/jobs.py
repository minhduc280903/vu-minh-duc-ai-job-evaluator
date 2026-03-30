# backend/app/api/jobs.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.job import JobResponse, JobDetailResponse, JobListResponse
from app.schemas.stats import DashboardStats
from app.services import job_service
from app.core.scoring import get_tier
import math

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    tier: Optional[str] = None,
    platform: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    location: Optional[str] = None,
    has_salary: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = "final_score",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
):
    jobs, total = job_service.get_jobs(
        db, page, per_page, tier, platform, min_score, max_score,
        location, has_salary, search, sort_by, sort_order,
    )
    job_responses = []
    for j in jobs:
        score = j.final_score if j.final_score > -1 else j.keyword_score
        resp = JobResponse.model_validate(j)
        resp.tier = get_tier(score) if score > 0 else None
        job_responses.append(resp)

    return JobListResponse(
        jobs=job_responses,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    from app.services.application_service import get_application_stats
    stats = job_service.get_dashboard_stats(db)
    app_stats = get_application_stats(db)
    stats["applications_count"] = sum(app_stats.values())
    stats["interviews_count"] = app_stats.get("interview", 0)
    return DashboardStats(**stats)


@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = job_service.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    score = job.final_score if job.final_score > -1 else job.keyword_score
    resp = JobDetailResponse.model_validate(job)
    resp.tier = get_tier(score) if score > 0 else None
    return resp
