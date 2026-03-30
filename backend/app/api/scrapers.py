# backend/app/api/scrapers.py
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.scraper import ScraperStartRequest, ScraperRunResponse, ScraperStatusResponse
from app.services import scraper_service

router = APIRouter(prefix="/api/scrapers", tags=["scrapers"])


@router.post("/run")
async def start_scraping(req: ScraperStartRequest, background_tasks: BackgroundTasks):
    if scraper_service.get_scraper_status()["is_running"]:
        return {"error": "Scrapers already running"}
    background_tasks.add_task(scraper_service.run_scrapers, req.platforms)
    return {"status": "started", "platforms": req.platforms}


@router.get("/status", response_model=ScraperStatusResponse)
def get_status():
    return scraper_service.get_scraper_status()


@router.get("/history", response_model=List[ScraperRunResponse])
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    return scraper_service.get_scraper_history(db, limit)


@router.post("/stop")
def stop_scraping():
    scraper_service.stop_scrapers()
    return {"status": "stopping"}
