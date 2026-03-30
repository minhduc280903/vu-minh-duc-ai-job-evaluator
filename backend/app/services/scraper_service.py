# backend/app/services/scraper_service.py
import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.scraper_run import ScraperRun
from app.api.websocket import ws_manager
from app.database import SessionLocal

logger = logging.getLogger(__name__)

# Track running state
_scraper_state = {
    "is_running": False,
    "current_platforms": [],
    "tasks": {},
    "cancelled": False,
}

# Add v4 root to path so we can import existing scrapers
V4_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if V4_ROOT not in sys.path:
    sys.path.insert(0, V4_ROOT)


async def run_scrapers(platforms: List[str] = None, triggered_by: str = "manual"):
    """Run scrapers using existing v4 scraper classes."""
    global _scraper_state
    if _scraper_state["is_running"]:
        raise RuntimeError("Scrapers already running")

    _scraper_state["is_running"] = True
    _scraper_state["cancelled"] = False

    # Import v4 scrapers
    from ybox_scraper import YboxScraper
    from vnw_scraper import VietnamWorksScraper
    from topcv_scraper import TopCVScraper
    from itviec_scraper import ITviecScraper
    from careerviet_scraper import CareerVietScraper
    from joboko_scraper import JobokoScraper

    scraper_map = {
        "ybox": ("Ybox", YboxScraper),
        "vnw": ("VietnamWorks", VietnamWorksScraper),
        "topcv": ("TopCV", TopCVScraper),
        "itviec": ("ITviec", ITviecScraper),
        "careerviet": ("CareerViet", CareerVietScraper),
        "joboko": ("Joboko", JobokoScraper),
    }

    if not platforms or "all" in platforms:
        platforms = list(scraper_map.keys())

    _scraper_state["current_platforms"] = platforms

    for platform_key in platforms:
        if _scraper_state["cancelled"]:
            break

        if platform_key not in scraper_map:
            continue

        name, scraper_class = scraper_map[platform_key]
        db = SessionLocal()

        # Record run
        run = ScraperRun(platform=name, triggered_by=triggered_by)
        db.add(run)
        db.commit()

        try:
            await ws_manager.send_scraper_log(name, "info", f"Starting {name} scraper...")
            scraper = scraper_class()
            jobs = await scraper.scrape()
            jobs_count = len(jobs) if jobs else 0

            run.status = "completed"
            run.completed_at = datetime.now()
            run.jobs_found = jobs_count
            db.commit()

            await ws_manager.send_scraper_complete(name, jobs_count, 0)
            await ws_manager.send_scraper_log(name, "info", f"{name} completed: {jobs_count} jobs")

        except Exception as e:
            logger.error(f"Scraper {name} failed: {e}")
            run.status = "failed"
            run.error_message = str(e)[:500]
            run.completed_at = datetime.now()
            db.commit()
            await ws_manager.send_scraper_log(name, "error", f"{name} failed: {str(e)[:200]}")

        finally:
            db.close()

    _scraper_state["is_running"] = False
    _scraper_state["current_platforms"] = []


def stop_scrapers():
    _scraper_state["cancelled"] = True


def get_scraper_status() -> dict:
    return {
        "is_running": _scraper_state["is_running"],
        "current_platforms": _scraper_state["current_platforms"],
        "progress": {},
    }


def get_scraper_history(db: Session, limit: int = 50):
    return (
        db.query(ScraperRun)
        .order_by(ScraperRun.started_at.desc())
        .limit(limit)
        .all()
    )
