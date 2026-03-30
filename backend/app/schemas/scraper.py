from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ScraperStartRequest(BaseModel):
    platforms: List[str] = ["all"]


class ScraperRunResponse(BaseModel):
    id: int
    platform: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    jobs_found: int = 0
    jobs_new: int = 0
    jobs_updated: int = 0
    error_message: Optional[str] = None
    triggered_by: str = "manual"

    class Config:
        from_attributes = True


class ScraperStatusResponse(BaseModel):
    is_running: bool
    current_platforms: List[str] = []
    progress: dict = {}
