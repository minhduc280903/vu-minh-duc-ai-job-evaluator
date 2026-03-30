# backend/app/api/settings.py
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.core.scoring import load_profile
from app.schemas.settings import (
    ProfileResponse, ProfileUpdate,
    NotificationSettingsResponse, NotificationSettingsUpdate,
    SchedulerConfigResponse, SchedulerConfigUpdate,
)
from app.models.notification import NotificationSettings
from app.services import scheduler_service, notification_service

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/profile", response_model=ProfileResponse)
def get_profile():
    try:
        profile = load_profile(settings.profile_path)
        return ProfileResponse(data=profile)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Profile not found")


@router.put("/profile")
def update_profile(data: ProfileUpdate):
    with open(settings.profile_path, "w", encoding="utf-8") as f:
        json.dump(data.data, f, ensure_ascii=False, indent=4)
    return {"status": "updated"}


@router.get("/notifications")
def get_notifications(db: Session = Depends(get_db)):
    items = db.query(NotificationSettings).all()
    if not items:
        # Create defaults
        for channel in ["telegram", "email"]:
            ns = NotificationSettings(channel=channel, enabled=0, config="{}")
            db.add(ns)
        db.commit()
        items = db.query(NotificationSettings).all()
    result = []
    for item in items:
        config = json.loads(item.config) if item.config else {}
        result.append({
            "id": item.id,
            "channel": item.channel,
            "enabled": bool(item.enabled),
            "config": config,
            "min_tier": item.min_tier,
            "daily_digest": bool(item.daily_digest),
        })
    return result


@router.put("/notifications/{channel}")
def update_notifications(channel: str, data: NotificationSettingsUpdate, db: Session = Depends(get_db)):
    ns = db.query(NotificationSettings).filter(NotificationSettings.channel == channel).first()
    if not ns:
        raise HTTPException(status_code=404, detail="Channel not found")
    if data.enabled is not None:
        ns.enabled = 1 if data.enabled else 0
    if data.config is not None:
        ns.config = json.dumps(data.config)
    if data.min_tier is not None:
        ns.min_tier = data.min_tier
    if data.daily_digest is not None:
        ns.daily_digest = 1 if data.daily_digest else 0
    db.commit()
    return {"status": "updated"}


@router.post("/test-telegram")
async def test_telegram():
    result = await notification_service.send_telegram("\U0001f9ea Test message from Job Finder v5!")
    return {"success": result}


@router.post("/test-email")
def test_email():
    result = notification_service.send_email(
        "Job Finder v5 - Test", "<h1>Test Email</h1><p>This is a test from Job Finder v5.</p>"
    )
    return {"success": result}


@router.get("/scheduler")
def get_scheduler(db: Session = Depends(get_db)):
    configs = scheduler_service.get_scheduler_configs(db)
    if not configs:
        # Create defaults
        defaults = [
            ("auto_scrape", settings.auto_scrape_cron),
            ("auto_evaluate", settings.auto_evaluate_cron),
            ("daily_report", settings.daily_report_cron),
        ]
        for name, cron in defaults:
            scheduler_service.update_scheduler_config(db, name, enabled=False, cron=cron)
        configs = scheduler_service.get_scheduler_configs(db)
    return [SchedulerConfigResponse.model_validate(c) for c in configs]


@router.put("/scheduler/{task_name}")
def update_scheduler(task_name: str, data: SchedulerConfigUpdate, db: Session = Depends(get_db)):
    config = scheduler_service.update_scheduler_config(
        db, task_name, enabled=data.enabled, cron=data.cron_expression,
    )
    return SchedulerConfigResponse.model_validate(config)
