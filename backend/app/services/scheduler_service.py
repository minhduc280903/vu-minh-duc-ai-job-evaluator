# backend/app/services/scheduler_service.py
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.models.scheduler import SchedulerConfig
from app.config import settings
from app.database import SessionLocal

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def init_scheduler():
    """Initialize scheduler with saved configs."""
    scheduler.start()
    logger.info("APScheduler started")

    # Load saved configs from DB
    db = SessionLocal()
    try:
        configs = db.query(SchedulerConfig).filter(SchedulerConfig.enabled == 1).all()
        for config in configs:
            add_scheduled_job(config.task_name, config.cron_expression)
    finally:
        db.close()


def add_scheduled_job(task_name: str, cron_expression: str):
    """Add or replace a scheduled job."""
    # Parse cron: "minute hour day month weekday"
    parts = cron_expression.split()
    if len(parts) != 5:
        logger.error(f"Invalid cron: {cron_expression}")
        return

    trigger = CronTrigger(
        minute=parts[0], hour=parts[1], day=parts[2],
        month=parts[3], day_of_week=parts[4],
    )

    job_func = _get_job_func(task_name)
    if not job_func:
        logger.error(f"Unknown task: {task_name}")
        return

    # Remove existing if any
    existing = scheduler.get_job(task_name)
    if existing:
        scheduler.remove_job(task_name)

    scheduler.add_job(job_func, trigger, id=task_name, replace_existing=True)
    logger.info(f"Scheduled job: {task_name} with cron: {cron_expression}")


def remove_scheduled_job(task_name: str):
    existing = scheduler.get_job(task_name)
    if existing:
        scheduler.remove_job(task_name)


def _get_job_func(task_name: str):
    async def auto_scrape():
        from app.services.scraper_service import run_scrapers
        logger.info("Auto-scrape triggered by scheduler")
        await run_scrapers(triggered_by="scheduler")

    async def auto_evaluate():
        from app.services.evaluator_service import run_keyword_scoring, run_llm_evaluation
        logger.info("Auto-evaluate triggered by scheduler")
        db = SessionLocal()
        try:
            run_keyword_scoring(db)
            await run_llm_evaluation(db)
        finally:
            db.close()

    async def daily_report():
        from app.services.notification_service import send_telegram, format_job_notification
        from app.services.job_service import get_jobs
        logger.info("Daily report triggered by scheduler")
        db = SessionLocal()
        try:
            jobs, _ = get_jobs(db, page=1, per_page=10, sort_by="final_score")
            if jobs:
                job_dicts = [{"title": j.title, "company": j.company,
                             "final_score": j.final_score, "url": j.url} for j in jobs]
                msg = format_job_notification(job_dicts)
                await send_telegram(msg)
        finally:
            db.close()

    funcs = {
        "auto_scrape": auto_scrape,
        "auto_evaluate": auto_evaluate,
        "daily_report": daily_report,
    }
    return funcs.get(task_name)


def get_scheduler_configs(db: Session):
    return db.query(SchedulerConfig).all()


def update_scheduler_config(db: Session, task_name: str, enabled: bool = None, cron: str = None):
    config = db.query(SchedulerConfig).filter(SchedulerConfig.task_name == task_name).first()
    if not config:
        config = SchedulerConfig(
            task_name=task_name,
            enabled=0,
            cron_expression=cron or "0 6 * * *",
        )
        db.add(config)

    if enabled is not None:
        config.enabled = 1 if enabled else 0
    if cron:
        config.cron_expression = cron

    db.commit()

    if config.enabled:
        add_scheduled_job(task_name, config.cron_expression)
    else:
        remove_scheduled_job(task_name)

    return config


def shutdown_scheduler():
    scheduler.shutdown(wait=False)
