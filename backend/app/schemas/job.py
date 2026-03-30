from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class JobResponse(BaseModel):
    id: str
    platform: str
    title: str
    company: Optional[str] = None
    url: Optional[str] = None
    salary: Optional[str] = None
    location: Optional[str] = None
    level: Optional[str] = None
    skills: Optional[str] = None
    deadline: Optional[str] = None
    keyword_score: int = -1
    llm_score: int = -1
    final_score: int = -1
    tier: Optional[str] = None
    llm_rationale: Optional[str] = None
    llm_pros: Optional[str] = None
    llm_cons: Optional[str] = None
    scraped_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobDetailResponse(JobResponse):
    summary: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    domain: Optional[str] = None
    views: int = 0
    published_at: Optional[str] = None


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
