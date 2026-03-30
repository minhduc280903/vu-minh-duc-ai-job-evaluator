# backend/app/services/application_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime
from app.models.application import Application
from app.models.job import Job
from app.core.scoring import get_tier


def get_applications(db: Session, status: Optional[str] = None) -> List[dict]:
    query = db.query(Application, Job).join(Job, Application.job_id == Job.id)
    if status:
        query = query.filter(Application.status == status)
    query = query.order_by(Application.updated_at.desc())
    results = query.all()

    apps = []
    for app, job in results:
        score = job.final_score if job.final_score > -1 else job.keyword_score
        apps.append({
            "id": app.id,
            "job_id": app.job_id,
            "status": app.status,
            "applied_at": app.applied_at,
            "notes": app.notes,
            "interview_date": app.interview_date,
            "interview_notes": app.interview_notes,
            "salary_offered": app.salary_offered,
            "created_at": app.created_at,
            "updated_at": app.updated_at,
            "job_title": job.title,
            "job_company": job.company,
            "job_platform": job.platform,
            "job_tier": get_tier(score) if score > 0 else "C",
            "job_score": score,
            "job_url": job.url,
        })
    return apps


def create_application(db: Session, job_id: str, status: str = "saved", notes: str = None):
    app = Application(
        job_id=job_id,
        status=status,
        notes=notes,
        applied_at=datetime.now() if status == "applied" else None,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def update_application(db: Session, app_id: int, **kwargs):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(app, key):
            setattr(app, key, value)
    if kwargs.get("status") == "applied" and not app.applied_at:
        app.applied_at = datetime.now()
    app.updated_at = datetime.now()
    db.commit()
    db.refresh(app)
    return app


def delete_application(db: Session, app_id: int):
    app = db.query(Application).filter(Application.id == app_id).first()
    if app:
        db.delete(app)
        db.commit()
        return True
    return False


def get_application_stats(db: Session):
    stats = (
        db.query(Application.status, func.count(Application.id))
        .group_by(Application.status)
        .all()
    )
    return {s: c for s, c in stats}
